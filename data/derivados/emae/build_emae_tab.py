#!/usr/bin/env python3
"""Construye los derivados auditables e integra el tab EMAE en el dashboard.

El script es deliberadamente autocontenido (biblioteca estándar). Toma el
dashboard versionado más alto que todavía no contiene el tab EMAE y genera la
versión siguiente. Si la última versión ya es una salida EMAE, la regenera a
partir del último insumo sin tocar ese insumo.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from bisect import bisect_right
from datetime import date, datetime
from pathlib import Path


HERE = Path(__file__).resolve().parent
DATA = HERE.parents[1]
ROOT = DATA.parent
SOURCES = DATA / "fuentes" / "emae"
INDEC_EMAE_CSV = SOURCES / "indec" / "datos_argentina_emae_mensual.csv"
INDEC_POP_CSV = SOURCES / "poblacion" / "proyecciones_nacionales_2022_2040_base.csv"
WB_POP_JSON = SOURCES / "poblacion" / "world_bank_SP_POP_TOTL_ARG.json"
FUENTES_CSV = DATA / "fuentes" / "FUENTES.csv"
MARKER = "<!-- EMAE_TAB_VERSION:1 -->"
AS_OF = "2026-08-21"


def fnum(value: str | float | int) -> float:
    return float(value)


def month_distance(a: date, b: date) -> int:
    return (b.year - a.year) * 12 + b.month - a.month


def iso_month(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def pct_change(a: float, b: float) -> float:
    return (b / a - 1.0) * 100.0


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_emae() -> list[dict]:
    rows: list[dict] = []
    with INDEC_EMAE_CSV.open("r", encoding="utf-8-sig", newline="") as fh:
        for src in csv.DictReader(fh):
            d = datetime.strptime(src["indice_tiempo"], "%Y-%m-%d").date()
            rows.append(
                {
                    "date": d,
                    "original": fnum(src["emae_original"]),
                    "sa": fnum(src["emae_desestacionalizada"]),
                    "tc": fnum(src["emae_tendencia_ciclo"]),
                }
            )
    if not rows or rows[0]["date"] != date(2004, 1, 1):
        raise AssertionError("La serie EMAE no comienza en 2004-01 como se esperaba")
    if rows[-1]["date"] != date(2026, 6, 1):
        raise AssertionError("La serie EMAE no termina en 2026-06 como se esperaba")
    return rows


def parse_population_anchors() -> tuple[dict[int, float], dict[int, float], dict[int, float]]:
    indec: dict[int, float] = {}
    with INDEC_POP_CSV.open("r", encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh, delimiter=";"):
            year = int(row["Fecha"])
            indec[year] = indec.get(year, 0.0) + fnum(row["Poblacion"])

    payload = json.loads(WB_POP_JSON.read_text(encoding="utf-8-sig"))
    wb_rows = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
    wb = {int(r["date"]): fnum(r["value"]) for r in wb_rows if r.get("value") is not None}
    if 2022 not in indec or 2022 not in wb:
        raise AssertionError("Falta el año de empalme 2022 en población")
    factor = indec[2022] / wb[2022]
    anchors = {year: value * factor for year, value in wb.items() if year <= 2021}
    anchors.update(indec)
    return anchors, indec, wb


def monthly_population(d: date, anchors: dict[int, float]) -> float:
    """Interpola linealmente entre estimaciones anuales ubicadas al 1 de julio."""
    points = sorted((date(y, 7, 1), p) for y, p in anchors.items())
    dates = [p[0] for p in points]
    i = bisect_right(dates, d)
    if i == 0 or i == len(points):
        raise AssertionError(f"No se puede interpolar población para {d}")
    d0, p0 = points[i - 1]
    d1, p1 = points[i]
    w = (d - d0).days / (d1 - d0).days
    return p0 + (p1 - p0) * w


def value_at(rows: list[dict], target: date, field: str) -> float:
    for row in rows:
        if row["date"] == target:
            return float(row[field])
    raise KeyError((target, field))


def augment_monthly(rows: list[dict], pop_anchors: dict[int, float]) -> list[dict]:
    for row in rows:
        row["population"] = monthly_population(row["date"], pop_anchors)
        row["pc_sa_raw"] = row["sa"] / row["population"]
        row["pc_tc_raw"] = row["tc"] / row["population"]

    ref = date(2023, 11, 1)
    bases = {
        "sa": value_at(rows, ref, "sa"),
        "tc": value_at(rows, ref, "tc"),
        "pc_sa_raw": value_at(rows, ref, "pc_sa_raw"),
        "pc_tc_raw": value_at(rows, ref, "pc_tc_raw"),
    }
    running_peak = -math.inf
    running_peak_pc = -math.inf
    cum_loss = cum_recovery = cum_net = 0.0
    for row in rows:
        for field in ("sa", "tc", "pc_sa_raw", "pc_tc_raw"):
            row[f"{field}_nov2023_100"] = row[field] / bases[field] * 100.0
        running_peak = max(running_peak, row["sa"])
        running_peak_pc = max(running_peak_pc, row["pc_sa_raw"])
        row["running_peak_sa"] = running_peak
        row["drawdown_sa_pct"] = (row["sa"] / running_peak - 1.0) * 100.0
        row["running_peak_pc"] = running_peak_pc
        row["drawdown_pc_pct"] = (row["pc_sa_raw"] / running_peak_pc - 1.0) * 100.0
        gap = row["sa"] / bases["sa"] - 1.0
        row["gap_nov2023"] = gap
        if row["date"] > ref:
            cum_loss += max(0.0, -gap)
            cum_recovery += max(0.0, gap)
            cum_net += gap
        row["cum_loss_months_base"] = cum_loss
        row["cum_recovery_months_base"] = cum_recovery
        row["cum_net_months_base"] = cum_net
    return rows


MANDATES = [
    ("Néstor Kirchner", date(2004, 1, 1), date(2007, 11, 1), True),
    ("Cristina Fernández", date(2007, 12, 1), date(2015, 11, 1), False),
    ("Mauricio Macri", date(2015, 12, 1), date(2019, 11, 1), False),
    ("Alberto Fernández", date(2019, 12, 1), date(2023, 11, 1), False),
    ("Javier Milei", date(2023, 12, 1), date(2026, 6, 1), True),
]


def recovery_months(segment: list[dict], field: str, threshold: float) -> int | None:
    first_below = next((i for i, r in enumerate(segment) if r[field] < threshold), None)
    if first_below is None:
        return 0
    for i in range(first_below + 1, len(segment)):
        if segment[i][field] >= threshold:
            return i
    return None


def mandate_summary(rows: list[dict]) -> list[dict]:
    out: list[dict] = []
    for name, start, end, partial in MANDATES:
        seg = [r for r in rows if start <= r["date"] <= end]
        if not seg:
            continue
        initial = seg[0]["sa"]
        initial_pc = seg[0]["pc_sa_raw"]
        prior = [r["sa"] for r in rows if r["date"] < start]
        prior_peak = max(prior) if prior else initial
        running = -math.inf
        max_dd = 0.0
        for r in seg:
            running = max(running, r["sa"])
            max_dd = min(max_dd, (r["sa"] / running - 1.0) * 100.0)
        rec_prior = next(
            (i for i, r in enumerate(seg) if r["sa"] >= prior_peak),
            None,
        )
        out.append(
            {
                "mandate": name,
                "start": iso_month(seg[0]["date"]),
                "end": iso_month(seg[-1]["date"]),
                "partial_series": "sí" if partial else "no",
                "months": len(seg),
                "initial_sa": initial,
                "final_sa": seg[-1]["sa"],
                "change_total_pct": pct_change(initial, seg[-1]["sa"]),
                "change_per_capita_pct": pct_change(initial_pc, seg[-1]["pc_sa_raw"]),
                "maximum_sa": max(r["sa"] for r in seg),
                "minimum_sa": min(r["sa"] for r in seg),
                "max_drawdown_pct": max_dd,
                "months_to_recover_initial": recovery_months(seg, "sa", initial),
                "prior_peak_sa": prior_peak,
                "months_to_recover_prior_peak": rec_prior,
                "months_below_initial": sum(r["sa"] < initial for r in seg),
                "months_below_prior_peak": sum(r["sa"] < prior_peak for r in seg),
                "underwater_initial_months_base": sum(max(0.0, 1.0 - r["sa"] / initial) for r in seg),
                "net_area_initial_months_base": sum(r["sa"] / initial - 1.0 for r in seg),
            }
        )
    return out


def mirror_window(rows: list[dict]) -> tuple[list[dict], dict]:
    post = [r for r in rows if date(2023, 12, 1) <= r["date"] <= rows[-1]["date"]]
    pre_end_index = next(i for i, r in enumerate(rows) if r["date"] == date(2023, 11, 1))
    pre = rows[pre_end_index - len(post) + 1 : pre_end_index + 1]
    if len(pre) != len(post):
        raise AssertionError("Ventanas espejo desiguales")
    pre0, post0 = pre[0]["sa"], post[0]["sa"]
    prepc0, postpc0 = pre[0]["pc_sa_raw"], post[0]["pc_sa_raw"]
    out: list[dict] = []
    pre_cum = post_cum = 0.0
    for i, (a, b) in enumerate(zip(pre, post)):
        ai = a["sa"] / pre0 * 100.0
        bi = b["sa"] / post0 * 100.0
        apc = a["pc_sa_raw"] / prepc0 * 100.0
        bpc = b["pc_sa_raw"] / postpc0 * 100.0
        pre_gap = ai / 100.0 - 1.0
        post_gap = bi / 100.0 - 1.0
        pre_cum += pre_gap
        post_cum += post_gap
        out.append(
            {
                "relative_month": i,
                "mirror_date": iso_month(a["date"]),
                "post_date": iso_month(b["date"]),
                "mirror_sa_index": ai,
                "post_sa_index": bi,
                "mirror_pc_index": apc,
                "post_pc_index": bpc,
                "mirror_gap": pre_gap,
                "post_gap": post_gap,
                "mirror_cumulative_months_base": pre_cum,
                "post_cumulative_months_base": post_cum,
            }
        )

    def stats(seg: list[dict], field: str) -> dict:
        initial = seg[0][field]
        values = [r[field] / initial * 100.0 for r in seg]
        peak = -math.inf
        dd = 0.0
        for value in values:
            peak = max(peak, value)
            dd = min(dd, value / peak - 1.0)
        trough_i = min(range(len(values)), key=values.__getitem__)
        return {
            "start": iso_month(seg[0]["date"]),
            "end": iso_month(seg[-1]["date"]),
            "initial": seg[0][field],
            "final": seg[-1][field],
            "final_index": values[-1],
            "minimum_index": min(values),
            "maximum_index": max(values),
            "max_drawdown_pct": dd * 100.0,
            "floor_to_final_pct": pct_change(values[trough_i], values[-1]),
            "saldo_months_base": sum(v / 100.0 - 1.0 for v in values),
        }

    summary = {
        "n_months": len(post),
        "mirror": stats(pre, "sa"),
        "post": stats(post, "sa"),
        "mirror_pc": stats(pre, "pc_sa_raw"),
        "post_pc": stats(post, "pc_sa_raw"),
    }
    summary["differential_months_base"] = (
        summary["post"]["saldo_months_base"] - summary["mirror"]["saldo_months_base"]
    )
    return out, summary


CRISES = [
    ("Crisis global 2008–2009", date(2007, 1, 1), date(2008, 8, 1), date(2010, 12, 1)),
    ("Recesión 2018–2019", date(2017, 1, 1), date(2018, 6, 1), date(2019, 12, 1)),
    ("Pandemia 2020", date(2019, 1, 1), date(2020, 3, 1), date(2021, 12, 1)),
    ("Shock 2023–2024", date(2022, 1, 1), date(2023, 11, 1), date(2026, 6, 1)),
]


def drawdown_summary(rows: list[dict]) -> list[dict]:
    out: list[dict] = []
    for label, peak_search_start, peak_search_end, observation_end in CRISES:
        candidates = [r for r in rows if peak_search_start <= r["date"] <= peak_search_end]
        peak = max(candidates, key=lambda r: r["sa"])
        # El piso se busca dentro del episodio indicado; la recuperación puede
        # ocurrir después y se rastrea hasta el último dato disponible.
        observed = [r for r in rows if peak["date"] <= r["date"] <= observation_end]
        trough = min(observed, key=lambda r: r["sa"])
        recovery = next(
            (r for r in rows if r["date"] > trough["date"] and r["sa"] >= peak["sa"]),
            None,
        )
        out.append(
            {
                "episode": label,
                "method": "pico local previo definido; caída respecto de ese pico",
                "peak_date": iso_month(peak["date"]),
                "peak_sa": peak["sa"],
                "trough_date": iso_month(trough["date"]),
                "trough_sa": trough["sa"],
                "max_drawdown_pct": pct_change(peak["sa"], trough["sa"]),
                "recovery_date": iso_month(recovery["date"]) if recovery else "no recuperado al corte",
                "months_peak_to_recovery": month_distance(peak["date"], recovery["date"]) if recovery else None,
                "months_peak_to_trough": month_distance(peak["date"], trough["date"]),
            }
        )
    return out


def rebound_summary(rows: list[dict]) -> dict:
    cutoff = date(2023, 12, 1)
    before = [r for r in rows if r["date"] < cutoff]
    after = [r for r in rows if r["date"] >= cutoff]

    def one(field: str) -> dict:
        peak = max(before, key=lambda r: r[field])
        recoveries = [r for r in after if r[field] >= peak[field]]
        first = recoveries[0] if recoveries else None
        current = rows[-1]
        return {
            "peak_date": iso_month(peak["date"]),
            "peak_value": peak[field],
            "first_recovery": iso_month(first["date"]) if first else None,
            "months_from_shock_to_recovery": month_distance(cutoff, first["date"]) if first else None,
            "current_vs_peak_pct": pct_change(peak[field], current[field]),
            "currently_above": current[field] >= peak[field],
            "ever_recovered": bool(first),
        }

    return {"total": one("sa"), "per_capita": one("pc_sa_raw")}


def compute_kpis(rows: list[dict], mirror: dict, rebound: dict) -> dict:
    ref = next(r for r in rows if r["date"] == date(2023, 11, 1))
    current = rows[-1]
    post = [r for r in rows if r["date"] >= date(2023, 12, 1)]
    floor = min(post, key=lambda r: r["sa"])
    return {
        "latest_date": iso_month(current["date"]),
        "latest_sa": current["sa"],
        "current_vs_nov2023_pct": pct_change(ref["sa"], current["sa"]),
        "current_pc_vs_nov2023_pct": pct_change(ref["pc_sa_raw"], current["pc_sa_raw"]),
        "complete_post_months": len(post),
        "floor_date": iso_month(floor["date"]),
        "recovery_from_floor_pct": pct_change(floor["sa"], current["sa"]),
        "current_vs_prior_peak_pct": rebound["total"]["current_vs_peak_pct"],
        "loss_months_base": current["cum_loss_months_base"],
        "recovery_months_base": current["cum_recovery_months_base"],
        "net_months_base": current["cum_net_months_base"],
        "mirror_differential_months_base": mirror["differential_months_base"],
        "months_below_nov2023": sum(r["sa"] < ref["sa"] for r in post),
        "underwater_nov2023_months_base": sum(max(0.0, 1.0 - r["sa"] / ref["sa"]) for r in post),
    }


def fmt_num(value: float | int | None, digits: int = 2) -> str:
    if value is None:
        return "—"
    return f"{value:.{digits}f}".replace("-0.00", "0.00").replace(".", ",")


def signed(value: float, digits: int = 2, suffix: str = "%") -> str:
    prefix = "+" if value > 0 else ""
    return f"{prefix}{fmt_num(value, digits)}{suffix}"


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    if not rows:
        raise AssertionError(f"Sin filas para {path.name}")
    fields = fields or list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def serializable_rows(rows: list[dict]) -> list[dict]:
    out = []
    for row in rows:
        out.append({k: (iso_month(v) if isinstance(v, date) else v) for k, v in row.items()})
    return out


def run_tests(rows: list[dict], mandates: list[dict], mirror_rows: list[dict], kpis: dict) -> list[str]:
    tests: list[str] = []
    ref = next(r for r in rows if r["date"] == date(2023, 11, 1))
    for field in ("sa_nov2023_100", "tc_nov2023_100", "pc_sa_raw_nov2023_100", "pc_tc_raw_nov2023_100"):
        assert abs(ref[field] - 100.0) < 1e-10
    tests.append("PASS · nov-2023 produce exactamente 100 en las cuatro series reescaladas")

    for r in rows:
        assert abs(r["pc_sa_raw"] - r["sa"] / r["population"]) < 1e-15
        assert abs(r["pc_tc_raw"] - r["tc"] / r["population"]) < 1e-15
    tests.append("PASS · EMAE per cápita = EMAE / población mensual")

    for m in mandates:
        seg = [r for r in rows if iso_month(r["date"]) >= m["start"] and iso_month(r["date"]) <= m["end"]]
        assert abs(seg[0]["sa"] - m["initial_sa"]) < 1e-12
        assert abs(seg[-1]["sa"] - m["final_sa"]) < 1e-12
        assert len(seg) == m["months"]
    tests.append("PASS · resúmenes por mandato concilian con la serie mensual")

    peak = -math.inf
    for r in rows:
        peak = max(peak, r["sa"])
        assert abs(peak - r["running_peak_sa"]) < 1e-12
        assert abs((r["sa"] / peak - 1.0) * 100.0 - r["drawdown_sa_pct"]) < 1e-12
    tests.append("PASS · drawdown usa el máximo acumulado correcto mes a mes")

    n = kpis["complete_post_months"]
    assert len(mirror_rows) == n
    tests.append(f"PASS · ventana espejo y post-shock tienen exactamente {n} meses")

    current = rows[-1]
    post = [r for r in rows if r["date"] >= date(2023, 12, 1)]
    floor = min(post, key=lambda r: r["sa"])
    prior_peak = max(r["sa"] for r in rows if r["date"] < date(2023, 12, 1))
    expected = {
        "latest_sa": current["sa"],
        "current_vs_nov2023_pct": pct_change(ref["sa"], current["sa"]),
        "current_pc_vs_nov2023_pct": pct_change(ref["pc_sa_raw"], current["pc_sa_raw"]),
        "complete_post_months": len(post),
        "recovery_from_floor_pct": pct_change(floor["sa"], current["sa"]),
        "current_vs_prior_peak_pct": pct_change(prior_peak, current["sa"]),
        "loss_months_base": sum(max(0.0, -(r["sa"] / ref["sa"] - 1.0)) for r in post),
        "recovery_months_base": sum(max(0.0, r["sa"] / ref["sa"] - 1.0) for r in post),
        "net_months_base": sum(r["sa"] / ref["sa"] - 1.0 for r in post),
        "mirror_differential_months_base": mirror_rows[-1]["post_cumulative_months_base"] - mirror_rows[-1]["mirror_cumulative_months_base"],
        "months_below_nov2023": sum(r["sa"] < ref["sa"] for r in post),
        "underwater_nov2023_months_base": sum(max(0.0, 1.0 - r["sa"] / ref["sa"]) for r in post),
    }
    for key, value in expected.items():
        assert abs(float(kpis[key]) - float(value)) < 1e-11, key
    tests.append("PASS · todos los KPIs se recalculan exactamente desde la serie mensual")
    return tests


def conclusion(kpis: dict, rebound: dict, mirror: dict) -> str:
    total_dir = "por encima" if kpis["current_vs_nov2023_pct"] >= 0 else "por debajo"
    pc_dir = "por encima" if kpis["current_pc_vs_nov2023_pct"] >= 0 else "por debajo"
    mirror_dir = "mejor" if kpis["mirror_differential_months_base"] >= 0 else "peor"
    if rebound["total"]["currently_above"]:
        peak_text = f"hoy supera el máximo total previo en {fmt_num(abs(rebound['total']['current_vs_peak_pct']))}%"
    elif rebound["total"]["ever_recovered"]:
        peak_text = (
            f"recuperó transitoriamente el máximo previo en {rebound['total']['first_recovery']}, "
            f"pero al último dato volvió a quedar {fmt_num(abs(rebound['total']['current_vs_peak_pct']))}% debajo"
        )
    else:
        peak_text = f"todavía está {fmt_num(abs(rebound['total']['current_vs_peak_pct']))}% debajo del máximo previo"
    pc_peak = rebound["per_capita"]
    pc_peak_text = (
        f"lo supera en {fmt_num(abs(pc_peak['current_vs_peak_pct']))}%"
        if pc_peak["currently_above"]
        else f"permanece {fmt_num(abs(pc_peak['current_vs_peak_pct']))}% debajo"
    )
    return (
        f"Al {kpis['latest_date']}, la actividad desestacionalizada está "
        f"{fmt_num(abs(kpis['current_vs_nov2023_pct']))}% {total_dir} de nov-2023; por habitante, "
        f"{fmt_num(abs(kpis['current_pc_vs_nov2023_pct']))}% {pc_dir}. Desde el piso de "
        f"{kpis['floor_date']} rebotó {fmt_num(kpis['recovery_from_floor_pct'])}%. En el recorrido hubo "
        f"{fmt_num(kpis['loss_months_base'])} meses-base de pérdida y "
        f"{fmt_num(kpis['recovery_months_base'])} de actividad por encima de la referencia, con saldo neto "
        f"{signed(kpis['net_months_base'], 2, ' meses-base')}. La ventana post-shock resultó "
        f"{mirror_dir} que su espejo por {fmt_num(abs(kpis['mirror_differential_months_base']))} meses-base. "
        f"Respecto del pico anterior, {peak_text}; per cápita, {pc_peak_text}. Esto distingue el rebote "
        f"desde el piso de una expansión sostenida por encima de máximos previos."
    )


def select_dashboard() -> tuple[Path, Path]:
    candidates: list[tuple[int, Path, bool]] = []
    for path in DATA.glob("dashboard_kawaii_*.html"):
        match = re.match(r"dashboard_kawaii_(\d+)", path.name)
        if match:
            text = path.read_text(encoding="utf-8", errors="replace")
            candidates.append((int(match.group(1)), path, MARKER in text))
    if not candidates:
        raise FileNotFoundError("No hay dashboards versionados en /data")
    candidates.sort()
    top_version, top_path, top_is_output = candidates[-1]
    if top_is_output:
        inputs = [(v, p) for v, p, is_output in candidates if v < top_version and not is_output]
        if not inputs:
            raise RuntimeError("No se encontró un dashboard de entrada sin EMAE")
        return inputs[-1][1], top_path
    output = DATA / f"dashboard_kawaii_{top_version + 1:03d}_emae_actividad_real.html"
    return top_path, output


def html_css() -> str:
    return r'''
/* ===== EMAE / ACTIVIDAD REAL ===== */
#tab-emae{--emae-violet:#5b3aa5;--emae-pink:#e75e9b;--emae-green:#2f8b70;--emae-orange:#ef8d4d;--emae-ink:#4b315f}
#tab-emae .emae-shell{display:grid;gap:18px}
#tab-emae .emae-hero,#tab-emae .emae-panel{border:1px solid rgba(174,123,214,.42);border-radius:22px;background:rgba(255,255,255,.88);box-shadow:0 12px 28px rgba(103,66,133,.08);padding:22px}
#tab-emae .emae-hero{background:linear-gradient(135deg,rgba(250,241,255,.96),rgba(241,255,250,.92))}
#tab-emae .emae-head{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;flex-wrap:wrap}
#tab-emae h2,#tab-emae h3{color:var(--emae-ink);margin:0}
#tab-emae .emae-sub{max-width:900px;margin:8px 0 0;color:#6b5379;line-height:1.5}
#tab-emae .emae-controls{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
#tab-emae .emae-control{border:1px solid #e4c9ef;border-radius:999px;background:#fff;padding:9px 13px;color:#5c3e70;font:inherit}
#tab-emae .emae-control input{accent-color:var(--emae-violet)}
#tab-emae .emae-kpis{display:grid;grid-template-columns:repeat(7,minmax(145px,1fr));gap:10px;margin-top:18px}
#tab-emae .emae-kpi{min-width:0;border:1px solid #ead9f3;border-radius:16px;padding:13px;background:rgba(255,255,255,.78)}
#tab-emae .emae-kpi small{display:block;color:#846b91;font-size:.73rem;font-weight:800;text-transform:uppercase;letter-spacing:.02em}
#tab-emae .emae-kpi strong{display:block;color:var(--emae-violet);font-size:1.45rem;line-height:1.1;margin:7px 0 5px}
#tab-emae .emae-kpi span{display:block;color:#745c80;font-size:.78rem;line-height:1.25}
#tab-emae .emae-reading{margin-top:16px;border-left:5px solid var(--emae-violet);border-radius:14px;background:#faf7ff;padding:15px 17px;color:#513961;line-height:1.55}
#tab-emae .emae-grid-2{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:16px}
#tab-emae .emae-grid-3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
#tab-emae .emae-stat{border:1px solid #e7d9ef;border-radius:16px;background:#fff;padding:15px}
#tab-emae .emae-stat.loss{background:#fff7fa;border-color:#f1c7d8}.emae-stat.gain{background:#f5fff9;border-color:#bfe4d3}
#tab-emae .emae-stat small{display:block;color:#80688c;font-weight:800;text-transform:uppercase}.emae-stat strong{display:block;font-size:1.55rem;color:#52346e;margin:7px 0}
#tab-emae .emae-chart{width:100%;height:430px;min-height:360px}
#tab-emae .emae-chart.tall{height:500px}
#tab-emae .emae-note{font-size:.82rem;line-height:1.5;color:#735d7e;margin:10px 0 0}
#tab-emae .emae-table-wrap{overflow:auto;border:1px solid #eadcf1;border-radius:15px;margin-top:14px}
#tab-emae table{width:100%;border-collapse:collapse;min-width:980px;background:#fff;font-size:.78rem}
#tab-emae th{position:sticky;top:0;background:#f7f0fb;color:#674578;text-align:left;padding:10px;border-bottom:1px solid #e2d1eb;white-space:nowrap}
#tab-emae td{padding:9px 10px;border-bottom:1px solid #f0e7f4;color:#594166;white-space:nowrap}
#tab-emae .emae-downloads,#tab-emae .emae-links{display:flex;gap:9px;flex-wrap:wrap;margin-top:14px}
#tab-emae .emae-btn{appearance:none;border:1px solid #d9b8ea;border-radius:999px;background:#fff;color:#5f3d75;padding:9px 13px;font:inherit;font-weight:750;cursor:pointer;text-decoration:none}
#tab-emae .emae-btn:hover{background:#f8effd}
#tab-emae .emae-source-list{columns:2;column-gap:32px;margin:12px 0 0;padding-left:20px;color:#644d70;line-height:1.55}
#tab-emae .emae-source-list li{break-inside:avoid;margin-bottom:7px}
#tab-emae .emae-badge{display:inline-block;border:1px solid #e0c9ec;border-radius:999px;padding:5px 9px;background:#fff;color:#725087;font-size:.76rem;font-weight:800}
@media(max-width:1366px){#tab-emae .emae-kpis{grid-template-columns:repeat(4,minmax(145px,1fr))}}
@media(max-width:1024px){#tab-emae .emae-kpis{grid-template-columns:repeat(3,minmax(140px,1fr))}#tab-emae .emae-grid-2{grid-template-columns:1fr}#tab-emae .emae-chart{height:400px}}
@media(max-width:768px){#tab-emae .emae-hero,#tab-emae .emae-panel{padding:16px;border-radius:18px}#tab-emae .emae-kpis{grid-template-columns:repeat(2,minmax(0,1fr))}#tab-emae .emae-grid-3{grid-template-columns:1fr}#tab-emae .emae-source-list{columns:1}#tab-emae .emae-chart,#tab-emae .emae-chart.tall{height:370px;min-height:330px}}
@media(max-width:430px){#tab-emae .emae-kpis{grid-template-columns:1fr 1fr;gap:8px}#tab-emae .emae-kpi{padding:10px}#tab-emae .emae-kpi strong{font-size:1.2rem}#tab-emae .emae-control{width:100%;box-sizing:border-box}#tab-emae .emae-chart,#tab-emae .emae-chart.tall{height:350px}#tab-emae .emae-panel{padding:13px}}
@media(max-width:390px){#tab-emae .emae-kpis{grid-template-columns:1fr}#tab-emae .emae-chart,#tab-emae .emae-chart.tall{height:340px;min-height:310px}}
'''


def html_section(kpis: dict, mirror: dict, rebound: dict, auto_reading: str) -> str:
    mirror_label = "mejor" if kpis["mirror_differential_months_base"] >= 0 else "peor"
    prior_label = "exceso" if kpis["current_vs_prior_peak_pct"] >= 0 else "falta"
    return f'''\n  {MARKER}
  <section id="tab-emae" class="tab-panel">
    <div class="emae-shell">
      <div class="emae-hero">
        <div class="emae-head">
          <div><span class="emae-badge">INDEC · mensual · último dato {kpis['latest_date']}</span><h2>Actividad real · ¿crecimiento o rebote? ♡</h2><p class="emae-sub">Nivel total, lectura por habitante, cicatriz acumulada, comparación simétrica y tiempo bajo el agua. La imagen de referencia sólo inspiró la pregunta: todos los números salen de fuentes archivadas y fórmulas reproducibles.</p></div>
          <div class="emae-controls"><select id="emaeBase" class="emae-control" aria-label="Base del índice"><option value="nov2023">nov-2023 = 100</option><option value="jan2017">ene-2017 = 100</option><option value="source">Base INDEC 2004=100</option></select><label class="emae-control"><input id="emaeOriginalToggle" type="checkbox"> mostrar serie original</label></div>
        </div>
        <div class="emae-kpis">
          <div class="emae-kpi"><small>Actividad vs nov-23</small><strong>{signed(kpis['current_vs_nov2023_pct'])}</strong><span>desestacionalizada</span></div>
          <div class="emae-kpi"><small>Por habitante vs nov-23</small><strong>{signed(kpis['current_pc_vs_nov2023_pct'])}</strong><span>población mensual estimada</span></div>
          <div class="emae-kpi"><small>Meses post-shock</small><strong>{kpis['complete_post_months']}</strong><span>dic-2023 a {kpis['latest_date']}</span></div>
          <div class="emae-kpi"><small>Rebote desde el piso</small><strong>{signed(kpis['recovery_from_floor_pct'])}</strong><span>piso: {kpis['floor_date']}</span></div>
          <div class="emae-kpi"><small>{prior_label} vs máximo previo</small><strong>{signed(kpis['current_vs_prior_peak_pct'])}</strong><span>máximo total previo</span></div>
          <div class="emae-kpi"><small>Saldo acumulado</small><strong>{signed(kpis['net_months_base'],2,'')}</strong><span>meses-base vs nov-23</span></div>
          <div class="emae-kpi"><small>Post vs espejo</small><strong>{signed(kpis['mirror_differential_months_base'],2,'')}</strong><span>meses-base · {mirror_label}</span></div>
        </div>
        <div class="emae-reading"><strong>Lectura automática:</strong> {auto_reading}</div>
      </div>

      <div class="emae-panel"><div class="emae-head"><div><h3>A. Nivel mensual de actividad</h3><p class="emae-note">La desestacionalizada sirve para comparar meses; tendencia-ciclo suaviza ruido y ayuda a leer el movimiento estructural. La base del selector se aplica de forma consistente a título, eje y tooltip.</p></div></div><div id="emaeMainChart" class="emae-chart tall"></div></div>

      <div class="emae-panel"><div class="emae-head"><div><h3>B. Actividad por habitante</h3><p class="emae-note">EMAE dividido por población mensual estimada. Para 2004–2021 se preserva la trayectoria anual del Banco Mundial, empalmada al nivel INDEC 2022; desde 2022 se usan proyecciones INDEC. Entre valores al 1 de julio se interpola linealmente.</p></div></div><div id="emaePcChart" class="emae-chart tall"></div></div>

      <div class="emae-panel">
        <div class="emae-head"><div><h3>C. Resumen por mandato y tiempo bajo el agua</h3><p class="emae-note">El mes de asunción se atribuye al gobierno entrante. Néstor aparece truncado por el inicio de EMAE mensual en ene-2004; Milei es parcial a jun-2026.</p></div></div>
        <div id="emaeMandateChart" class="emae-chart"></div><div id="emaeMandateTable" class="emae-table-wrap"></div>
      </div>

      <div class="emae-panel">
        <div class="emae-head"><div><h3>Cicatriz acumulada desde nov-2023</h3><p class="emae-note"><code>gap_t = EMAE_t / EMAE_nov23 − 1</code>. Pérdida suma sólo gaps negativos; recuperación suma sólo positivos; saldo neto suma ambos. Un mes 5% debajo equivale a −0,05 meses-base.</p></div></div>
        <div class="emae-grid-3"><div class="emae-stat loss"><small>Pérdida acumulada</small><strong>−{fmt_num(kpis['loss_months_base'])}</strong><span>meses-base bajo nov-23</span></div><div class="emae-stat gain"><small>Actividad por encima</small><strong>+{fmt_num(kpis['recovery_months_base'])}</strong><span>meses-base sobre nov-23</span></div><div class="emae-stat"><small>Saldo neto</small><strong>{signed(kpis['net_months_base'],2,'')}</strong><span>meses-base</span></div></div>
        <div id="emaeScarChart" class="emae-chart"></div>
      </div>

      <div class="emae-grid-2">
        <div class="emae-panel"><h3>D. Ventana espejo antes / después</h3><p class="emae-note">{mirror['n_months']} meses por ventana: {mirror['mirror']['start']}–{mirror['mirror']['end']} vs {mirror['post']['start']}–{mirror['post']['end']}. Cada recorrido comienza en 100; el diferencial es saldo post menos saldo espejo.</p><div id="emaeMirrorChart" class="emae-chart"></div><div class="emae-grid-3"><div class="emae-stat"><small>Espejo</small><strong>{signed(mirror['mirror']['saldo_months_base'],2,'')}</strong><span>meses-base</span></div><div class="emae-stat"><small>Post-shock</small><strong>{signed(mirror['post']['saldo_months_base'],2,'')}</strong><span>meses-base</span></div><div class="emae-stat"><small>Diferencial</small><strong>{signed(kpis['mirror_differential_months_base'],2,'')}</strong><span>{mirror_label} que espejo</span></div></div></div>
        <div class="emae-panel"><h3>F. Rebote vs crecimiento nuevo</h3><p class="emae-note">Se compara el nivel actual con el máximo observado antes de dic-2023. Recuperar una vez el pico no garantiza permanecer arriba.</p><div id="emaeReboundChart" class="emae-chart"></div><div class="emae-grid-2"><div class="emae-stat"><small>Total · pico {rebound['total']['peak_date']}</small><strong>{signed(rebound['total']['current_vs_peak_pct'])}</strong><span>primera recuperación: {rebound['total']['first_recovery'] or 'aún no'}</span></div><div class="emae-stat"><small>Per cápita · pico {rebound['per_capita']['peak_date']}</small><strong>{signed(rebound['per_capita']['current_vs_peak_pct'])}</strong><span>primera recuperación: {rebound['per_capita']['first_recovery'] or 'aún no'}</span></div></div></div>
      </div>

      <div class="emae-panel"><div class="emae-head"><div><h3>E. Drawdowns históricos</h3><p class="emae-note">La curva usa el máximo acumulado estándar: <code>EMAE_t / máximo_hasta_t − 1</code>. La tabla resume episodios con picos locales previos explícitos. La serie mensual empieza en 2004, por eso 2001–2002 no se estima artificialmente.</p></div></div><div id="emaeDrawdownChart" class="emae-chart tall"></div><div id="emaeDrawdownTable" class="emae-table-wrap"></div></div>

      <div class="emae-panel"><h3>Descargas, método y trazabilidad</h3><p class="emae-note">Los CSV están embebidos en este HTML y también quedan en <code>/data/derivados/emae/</code>. Las fuentes originales no se modifican.</p><div class="emae-downloads"><button class="emae-btn" onclick="downloadEmaeCsv('monthly')">EMAE mensual CSV</button><button class="emae-btn" onclick="downloadEmaeCsv('percap')">EMAE per cápita CSV</button><button class="emae-btn" onclick="downloadEmaeCsv('mandates')">Mandatos CSV</button><button class="emae-btn" onclick="downloadEmaeCsv('mirror')">Ventana espejo CSV</button><button class="emae-btn" onclick="downloadEmaeCsv('drawdowns')">Drawdowns CSV</button></div>
        <ul class="emae-source-list"><li><a href="https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-9-48" target="_blank" rel="noopener">INDEC · EMAE</a>: original, desestacionalizada y tendencia-ciclo.</li><li><a href="https://www.indec.gob.ar/ftp/cuadros/economia/metodologia_emae_ago_16.pdf" target="_blank" rel="noopener">Metodología EMAE</a>: alcance, ajuste estacional y revisiones.</li><li><a href="https://www.indec.gob.ar/indec/web/Nivel4-Tema-2-24-84" target="_blank" rel="noopener">INDEC · proyecciones 2022–2040</a>: nivel poblacional desde 2022.</li><li><a href="https://data.worldbank.org/indicator/SP.POP.TOTL?locations=AR" target="_blank" rel="noopener">Banco Mundial · población</a>: complemento histórico empalmado.</li></ul>
        <div class="emae-links"><button class="emae-btn" onclick="activateTabAndScroll('tab-growth')">Ir a Crecimiento</button><button class="emae-btn" onclick="activateTabAndScroll('tab-work')">Ir a Trabajo y salarios</button><button class="emae-btn" onclick="activateTabAndScroll('tab-consumption')">Ir a Consumo</button></div>
      </div>
    </div>
  </section>\n'''


def js_payload(rows: list[dict], mandates: list[dict], mirror_rows: list[dict], drawdowns: list[dict], rebound: dict, csv_downloads: dict[str, dict]) -> str:
    compact_rows = [
        {
            "d": iso_month(r["date"]), "o": r["original"], "s": r["sa"], "t": r["tc"],
            "p": r["population"], "ps": r["pc_sa_raw"], "pt": r["pc_tc_raw"],
            "dd": r["drawdown_sa_pct"], "ddp": r["drawdown_pc_pct"],
            "loss": r["cum_loss_months_base"], "gain": r["cum_recovery_months_base"], "net": r["cum_net_months_base"],
        } for r in rows
    ]
    payload = {"monthly": compact_rows, "mandates": mandates, "mirror": mirror_rows, "drawdowns": drawdowns, "rebound": rebound}
    return f'''\n<script>
/* EMAE_TAB_JS */
const EMAE_DATA={json.dumps(payload, ensure_ascii=False, separators=(',', ':'))};
const EMAE_CSVS={json.dumps(csv_downloads, ensure_ascii=False, separators=(',', ':'))};
let emaeRendered=false;
function emaeFmt(v,d=2){{return Number(v).toLocaleString('es-AR',{{minimumFractionDigits:d,maximumFractionDigits:d}})}}
function emaeBaseValues(field,mode){{
  const rows=EMAE_DATA.monthly;
  if(mode==='nov2023') return rows.find(r=>r.d==='2023-11')[field];
  if(mode==='jan2017') return rows.find(r=>r.d==='2017-01')[field];
  if(field==='s'||field==='t'||field==='o') return 100;
  const vals=rows.filter(r=>r.d.startsWith('2004-')).map(r=>r[field]);
  return vals.reduce((a,b)=>a+b,0)/vals.length;
}}
function emaeSeries(field,mode){{const b=emaeBaseValues(field,mode);return EMAE_DATA.monthly.map(r=>r[field]/b*100)}}
function emaeBaseLabel(mode,percap=false){{if(mode==='nov2023')return 'nov-2023 = 100';if(mode==='jan2017')return 'ene-2017 = 100';return percap?'promedio 2004 = 100':'base INDEC 2004 = 100'}}
function emaeLayout(title,ytitle,opts={{}}){{
  const mobile=window.innerWidth<600;
  return {{title:{{text:title,font:{{size:mobile?13:16,color:'#513661'}}}},paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(255,255,255,.55)',font:{{family:'inherit',color:'#5d4769',size:mobile?10:12}},margin:{{l:mobile?48:62,r:mobile?38:30,t:mobile?90:55,b:50}},hovermode:'x unified',legend:{{orientation:mobile?'v':'h',y:mobile?1.2:1.08,x:0,font:{{size:mobile?9:12}}}},xaxis:{{gridcolor:'#eee5f2',tickformat:'%Y',rangeslider:{{visible:false}},automargin:true}},yaxis:{{title:ytitle,gridcolor:'#eadff0',zerolinecolor:'#cab7d4',automargin:true}},...opts}};
}}
function emaeMandateDecorations(){{
 const bands=[['2004-01','2007-12','#f8e8d8','Néstor'],['2007-12','2015-12','#e5f4ed','Cristina'],['2015-12','2019-12','#fff0d8','Macri'],['2019-12','2023-12','#e5f2fb','Alberto'],['2023-12','2026-07','#fde8f0','Milei']];
 const cuts=['2007-12','2015-12','2019-12','2023-12'];
 const bandShapes=bands.map(b=>({{type:'rect',xref:'x',yref:'paper',x0:b[0],x1:b[1],y0:0,y1:1,fillcolor:b[2],opacity:.36,line:{{width:0}},layer:'below'}}));
 const cutLines=cuts.map(c=>({{type:'line',xref:'x',yref:'paper',x0:c,x1:c,y0:0,y1:1,line:{{color:'#8e68a3',width:1.6,dash:'dot'}},layer:'above'}}));
 return {{shapes:[...bandShapes,...cutLines],annotations:bands.map(b=>({{xref:'x',yref:'paper',x:(new Date(b[0]).getTime()+new Date(b[1]).getTime())/2,y:1.02,text:b[3],showarrow:false,font:{{size:9,color:'#765a80'}}}}))}};
}}
function renderEmae(){{
 if(!window.Plotly)return;
 const mode=document.getElementById('emaeBase')?.value||'nov2023';
 const showOriginal=document.getElementById('emaeOriginalToggle')?.checked||false;
 const x=EMAE_DATA.monthly.map(r=>r.d+'-01'); const deco=emaeMandateDecorations();
 Plotly.react('emaeMainChart',[
  {{x,y:emaeSeries('s',mode),name:'Desestacionalizada',line:{{color:'#6046c6',width:3}}}},
  {{x,y:emaeSeries('t',mode),name:'Tendencia-ciclo',line:{{color:'#2f8b70',width:3}}}},
  {{x,y:emaeSeries('o',mode),name:'Original',visible:showOriginal?true:'legendonly',line:{{color:'#e75e9b',width:1.5,dash:'dot'}},opacity:.65}}
 ],emaeLayout('EMAE mensual · '+emaeBaseLabel(mode),emaeBaseLabel(mode),deco),{{responsive:true,displaylogo:false}});
 Plotly.react('emaePcChart',[
  {{x,y:emaeSeries('ps',mode),name:'Desestacionalizada por habitante',line:{{color:'#7b4bc5',width:3}}}},
  {{x,y:emaeSeries('pt',mode),name:'Tendencia-ciclo por habitante',line:{{color:'#d16a9b',width:3}}}}
 ],emaeLayout('Actividad por habitante · '+emaeBaseLabel(mode,true),emaeBaseLabel(mode,true),deco),{{responsive:true,displaylogo:false}});
 const m=EMAE_DATA.mandates;
 Plotly.react('emaeMandateChart',[
  {{type:'bar',x:m.map(r=>r.mandate),y:m.map(r=>r.change_total_pct),name:'Actividad total',marker:{{color:'#7050c2'}}}},
  {{type:'bar',x:m.map(r=>r.mandate),y:m.map(r=>r.change_per_capita_pct),name:'Por habitante',marker:{{color:'#e476a9'}}}}
 ],emaeLayout('Variación entre primer y último mes del mandato','variación %',{{barmode:'group',xaxis:{{tickangle:window.innerWidth<600?-25:0,gridcolor:'#eee5f2'}},shapes:[{{type:'line',xref:'paper',x0:0,x1:1,y0:0,y1:0,line:{{color:'#9d8aa8',width:1}}}}]}}),{{responsive:true,displaylogo:false}});
 const mr=EMAE_DATA.mirror;
 Plotly.react('emaeMirrorChart',[
  {{x:mr.map(r=>r.relative_month),y:mr.map(r=>r.mirror_sa_index),name:'Ventana espejo · total',line:{{color:'#3f8d72',width:3}}}},
  {{x:mr.map(r=>r.relative_month),y:mr.map(r=>r.post_sa_index),name:'Post-shock · total',line:{{color:'#d75d91',width:3}}}},
  {{x:mr.map(r=>r.relative_month),y:mr.map(r=>r.mirror_pc_index),name:'Espejo · per cápita',line:{{color:'#82bda9',dash:'dot'}}}},
  {{x:mr.map(r=>r.relative_month),y:mr.map(r=>r.post_pc_index),name:'Post · per cápita',line:{{color:'#e9a0bf',dash:'dot'}}}}
 ],emaeLayout('Recorridos normalizados: cada ventana comienza en 100','inicio de cada ventana = 100',{{xaxis:{{title:'mes relativo',gridcolor:'#eee5f2'}},shapes:[{{type:'line',xref:'paper',x0:0,x1:1,y0:100,y1:100,line:{{color:'#9b87a6',dash:'dash'}}}}]}}),{{responsive:true,displaylogo:false}});
 Plotly.react('emaeScarChart',[
  {{x,y:EMAE_DATA.monthly.map(r=>-r.loss),name:'Pérdida acumulada',stackgroup:'one',line:{{color:'#d95d91'}}}},
  {{x,y:EMAE_DATA.monthly.map(r=>r.gain),name:'Actividad por encima',stackgroup:'one',line:{{color:'#3b9a78'}}}},
  {{x,y:EMAE_DATA.monthly.map(r=>r.net),name:'Saldo neto',line:{{color:'#5b3aa5',width:3}}}}
 ],emaeLayout('Acumulación desde dic-2023','meses-base',{{xaxis:{{range:['2023-11-01',x[x.length-1]],gridcolor:'#eee5f2'}},shapes:[{{type:'line',xref:'paper',x0:0,x1:1,y0:0,y1:0,line:{{color:'#9b87a6'}}}}]}}),{{responsive:true,displaylogo:false}});
 const rb=EMAE_DATA.rebound; const start='2022-01'; const rr=EMAE_DATA.monthly.filter(r=>r.d>=start); const rbX=rr.map(r=>r.d+'-01');
 Plotly.react('emaeReboundChart',[
  {{x:rbX,y:rr.map(r=>r.s/rb.total.peak_value*100),name:'Total vs pico previo',line:{{color:'#6046c6',width:3}}}},
  {{x:rbX,y:rr.map(r=>r.ps/rb.per_capita.peak_value*100),name:'Per cápita vs su pico previo',line:{{color:'#e75e9b',width:3}}}}
 ],emaeLayout('¿Se superó el máximo previo?','máximo previo propio = 100',{{shapes:[{{type:'line',xref:'paper',x0:0,x1:1,y0:100,y1:100,line:{{color:'#2f8b70',dash:'dash'}}}}]}}),{{responsive:true,displaylogo:false}});
 Plotly.react('emaeDrawdownChart',[
  {{x,y:EMAE_DATA.monthly.map(r=>r.dd),name:'Total',fill:'tozeroy',line:{{color:'#7750bd',width:2}},fillcolor:'rgba(119,80,189,.18)'}},
  {{x,y:EMAE_DATA.monthly.map(r=>r.ddp),name:'Por habitante',line:{{color:'#e0699d',width:2,dash:'dot'}}}}
 ],emaeLayout('Profundidad bajo el máximo acumulado','drawdown %',deco),{{responsive:true,displaylogo:false}});
 emaeRendered=true; renderEmaeTables();
}}
function emaeCell(v,d=2,suffix=''){{return v===null||v===undefined?'—':emaeFmt(v,d)+suffix}}
function renderEmaeTables(){{
 const m=EMAE_DATA.mandates;
 document.getElementById('emaeMandateTable').innerHTML='<table><thead><tr><th>Mandato</th><th>Período</th><th>Total</th><th>Per cápita</th><th>Máx.</th><th>Mín.</th><th>Drawdown</th><th>Recupera inicial</th><th>Recupera pico previo</th><th>Meses bajo inicial</th><th>Meses bajo pico</th><th>Área bajo agua</th></tr></thead><tbody>'+m.map(r=>`<tr><td><b>${{r.mandate}}</b>${{r.partial_series==='sí'?' · parcial':''}}</td><td>${{r.start}}–${{r.end}}</td><td>${{emaeCell(r.change_total_pct,1,'%')}}</td><td>${{emaeCell(r.change_per_capita_pct,1,'%')}}</td><td>${{emaeCell(r.maximum_sa,1)}}</td><td>${{emaeCell(r.minimum_sa,1)}}</td><td>${{emaeCell(r.max_drawdown_pct,1,'%')}}</td><td>${{r.months_to_recover_initial??'no recuperado'}} mes.</td><td>${{r.months_to_recover_prior_peak??'no recuperado'}}</td><td>${{r.months_below_initial}}</td><td>${{r.months_below_prior_peak}}</td><td>${{emaeCell(r.underwater_initial_months_base,2)}}</td></tr>`).join('')+'</tbody></table>';
 const d=EMAE_DATA.drawdowns;
 document.getElementById('emaeDrawdownTable').innerHTML='<table><thead><tr><th>Episodio</th><th>Pico</th><th>Piso</th><th>Caída máxima</th><th>Recuperación</th><th>Meses pico→piso</th><th>Meses pico→recuperación</th></tr></thead><tbody>'+d.map(r=>`<tr><td><b>${{r.episode}}</b></td><td>${{r.peak_date}}</td><td>${{r.trough_date}}</td><td>${{emaeCell(r.max_drawdown_pct,1,'%')}}</td><td>${{r.recovery_date}}</td><td>${{r.months_peak_to_trough}}</td><td>${{r.months_peak_to_recovery??'no recuperado'}}</td></tr>`).join('')+'</tbody></table>';
}}
function downloadEmaeCsv(key){{const item=EMAE_CSVS[key];if(!item)return;const blob=new Blob(['\ufeff'+item.content],{{type:'text/csv;charset=utf-8'}});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=item.filename;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}}
document.getElementById('emaeBase')?.addEventListener('change',renderEmae);
document.getElementById('emaeOriginalToggle')?.addEventListener('change',renderEmae);
document.querySelector('[data-tab="tab-emae"]')?.addEventListener('click',()=>requestAnimationFrame(renderEmae));
window.addEventListener('resize',()=>{{if(!emaeRendered)return;['emaeMainChart','emaePcChart','emaeMandateChart','emaeMirrorChart','emaeScarChart','emaeReboundChart','emaeDrawdownChart'].forEach(id=>{{const el=document.getElementById(id);if(el&&window.Plotly)Plotly.Plots.resize(el)}})}});
</script>\n'''


def csv_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def inject_dashboard(input_path: Path, output_path: Path, section: str, css: str, js: str) -> None:
    html = input_path.read_text(encoding="utf-8")
    if MARKER in html:
        raise AssertionError("El dashboard de entrada ya contiene el tab EMAE")
    nav_anchor = '    <button class="tab-btn" data-tab="tab-growth">Crecimiento</button>'
    fiscal_anchor = '  <section id="tab-fiscal" class="tab-panel">'
    if nav_anchor not in html or fiscal_anchor not in html or "</style>" not in html or "</body>" not in html:
        raise AssertionError("No se encontraron los puntos de integración del dashboard")
    html = html.replace("</style>", css + "\n</style>", 1)
    html = html.replace(nav_anchor, nav_anchor + '\n    <button class="tab-btn" data-tab="tab-emae">Actividad real · ¿crecimiento o rebote?</button>', 1)
    html = html.replace(fiscal_anchor, section + "\n" + fiscal_anchor, 1)
    html = html.replace("</body>", js + "\n</body>", 1)
    output_path.write_text(html, encoding="utf-8")


def update_fuentes() -> None:
    specs = [
        ("emae_indec_xls", "emae", "INDEC", "EMAE mensual base 2004", "https://www.indec.gob.ar/ftp/cuadros/economia/sh_emae_mensual_base2004.xls", SOURCES / "indec" / "sh_emae_mensual_base2004.xls", "XLS oficial", "EMAE original/desestacionalizada/tendencia-ciclo", "2004-01/2026-06", "Original oficial archivado y control"),
        ("emae_datos_argentina_csv", "emae", "Secretaría de Política Económica / Datos Argentina", "EMAE mensual base 2004", "https://infra.datos.gob.ar/catalog/sspm/dataset/143/distribution/143.3/download/emae-valores-anuales-indice-base-2004-mensual.csv", INDEC_EMAE_CSV, "CSV oficial", "EMAE original/desestacionalizada/tendencia-ciclo", "2004-01/2026-06", "Entrada tabular; conciliada con publicación INDEC"),
        ("emae_indec_informe_202606", "emae", "INDEC", "Estimador mensual de actividad económica. Junio de 2026", "https://www.indec.gob.ar/uploads/informesdeprensa/emae_08_26AADBE275B1.pdf", SOURCES / "indec" / "emae_08_26.pdf", "PDF oficial", "Informe EMAE", "2026-06", "Control del último dato y variaciones publicadas"),
        ("emae_indec_metodologia", "emae", "INDEC", "Metodología del EMAE", "https://www.indec.gob.ar/ftp/cuadros/economia/metodologia_emae_ago_16.pdf", SOURCES / "metodologia" / "metodologia_emae_ago_16.pdf", "PDF metodológico", "Metodología EMAE", "base 2004", "Definiciones y cautelas"),
        ("poblacion_indec_base_csv", "poblacion", "INDEC", "Base de proyecciones nacionales 2022–2040", "https://www.indec.gob.ar/ftp/cuadros/poblacion/proyecciones_nacionales_2022_2040_base.csv", INDEC_POP_CSV, "CSV oficial", "Población por edad y sexo", "2022/2040", "Nivel anual desde 2022; suma nacional al 1 de julio"),
        ("poblacion_indec_xlsx", "poblacion", "INDEC", "Proyecciones nacionales 2022–2040", "https://www.indec.gob.ar/ftp/cuadros/poblacion/proyecciones_nacionales_2022_2040_c1_c2.xlsx", SOURCES / "poblacion" / "proyecciones_nacionales_2022_2040_c1_c2.xlsx", "XLSX oficial", "Población nacional", "2022/2040", "Original oficial archivado y control"),
        ("poblacion_indec_metadatos", "poblacion", "INDEC", "Metadatos de proyecciones nacionales", "https://www.indec.gob.ar/ftp/cuadros/poblacion/metadatos_base_proyecciones_nacionales_2022_2040.pdf", SOURCES / "poblacion" / "metadatos_base_proyecciones_nacionales_2022_2040.pdf", "PDF metodológico", "Metadatos población", "2022/2040", "Fecha de referencia y método"),
        ("poblacion_world_bank_arg", "poblacion", "Banco Mundial", "Population, total - Argentina", "https://api.worldbank.org/v2/country/ARG/indicator/SP.POP.TOTL?format=json&per_page=100", WB_POP_JSON, "JSON institucional", "SP.POP.TOTL", "2003/2021 usado", "Trayectoria histórica empalmada multiplicativamente a INDEC 2022"),
    ]
    with FUENTES_CSV.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        fields = reader.fieldnames or []
        rows = list(reader)
    by_id = {r["id"]: r for r in rows}
    for sid, topic, institution, title, url, path, typ, series, period, note in specs:
        rel = "/" + path.relative_to(ROOT).as_posix()
        item = {
            "id": sid, "tema": topic, "institucion": institution, "titulo": title,
            "url_original": url, "archivo_local": rel, "fecha_descarga": AS_OF,
            "fecha_publicacion": "", "codigo_serie": series, "periodo_utilizado": period,
            "tipo": typ, "sha256": sha256(path), "nota": note,
        }
        if sid in by_id:
            by_id[sid].update(item)
        else:
            rows.append(item)
    with FUENTES_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)


def audit_markdown(input_path: Path, output_path: Path, tests: list[str], pop_anchors: dict[int, float], indec: dict[int, float], wb: dict[int, float], mirror: dict, kpis: dict, rebound: dict) -> str:
    wb_factor = indec[2022] / wb[2022]
    lines = [
        "# Auditoría metodológica · EMAE / actividad real", "",
        f"Corte de datos: **{kpis['latest_date']}**. Construcción: **{AS_OF}**.", "",
        "## Archivos y fuentes", "",
        "- EMAE original, desestacionalizada y tendencia-ciclo: INDEC, base 2004=100. Como entrada tabular se usa el CSV oficial de Datos Argentina, conciliado con el XLS y el informe de junio de 2026 archivados.",
        "- Población 2022 en adelante: proyecciones INDEC derivadas del Censo 2022; el total anual se obtiene sumando edades y sexos y corresponde al 1 de julio.",
        f"- Población histórica 2003–2021: trayectoria anual del Banco Mundial, reescalada por un factor único `{wb_factor:.12f}` para coincidir exactamente con INDEC en 2022. Es un complemento institucional, no una serie publicada como empalme por INDEC.",
        "- Metodología EMAE: documento oficial INDEC archivado en `/data/fuentes/emae/metodologia/`.", "",
        "## Transformaciones", "",
        "### Bases", "",
        "La interfaz permite: `nov-2023 = 100`, `ene-2017 = 100` y la base original INDEC `2004 = 100`. Para per cápita, la tercera opción usa **promedio mensual 2004 = 100**, porque el cociente EMAE/población no conserva mecánicamente la base publicada del EMAE.", "",
        "### Población mensual y per cápita", "",
        "Cada estimación anual se ubica al 1 de julio. Entre dos puntos anuales se interpola linealmente por días. Luego: `EMAE_pc_t = EMAE_t / población_t`. El resultado es un índice de actividad agregada por habitante, no PIB per cápita ni ingreso por persona.", "",
        "### Cicatriz", "",
        "Con referencia nov-2023: `gap_t = EMAE_SA_t / EMAE_SA_nov23 - 1`. Desde dic-2023, pérdida = `Σ max(0,-gap_t)`, recuperación = `Σ max(0,gap_t)` y saldo = `Σ gap_t`. La unidad es **meses equivalentes de actividad-base**.", "",
        "### Drawdown y tiempo bajo el agua", "",
        "El drawdown mensual estándar es `EMAE_t / max(EMAE_1…EMAE_t) - 1`. Para los episodios históricos se informa además un pico local previo explícito, su piso y la primera recuperación. `Meses bajo el agua` cuenta observaciones debajo del umbral; la profundidad acumulada suma `max(0, 1 - EMAE_t/umbral)`.", "",
        "### Mandatos", "",
        "El mes de asunción se atribuye al gobierno entrante: dic-2007, dic-2015, dic-2019 y dic-2023. Néstor está truncado a ene-2004 por el inicio de la serie mensual; Milei está truncado al último dato disponible. Recuperación del nivel inicial se mide luego de la primera caída bajo ese nivel. Recuperación del pico previo usa el máximo observado antes del mandato.", "",
        "### Ventana espejo", "",
        f"Hay {mirror['n_months']} meses completos post-shock ({mirror['post']['start']}–{mirror['post']['end']}) y exactamente {mirror['n_months']} meses previos ({mirror['mirror']['start']}–{mirror['mirror']['end']}). Cada ventana se normaliza a 100 en su primer mes. El diferencial es `saldo_post - saldo_espejo`; positivo significa mejor recorrido relativo, no necesariamente nivel absoluto alto.", "",
        "### Rebote vs crecimiento nuevo", "",
        f"El máximo total previo fue {rebound['total']['peak_date']}; el máximo per cápita previo fue {rebound['per_capita']['peak_date']}. Se informa por separado si alguna vez se recuperó y si el último dato permanece arriba. Esto evita confundir una recuperación transitoria con un nuevo máximo sostenido.", "",
        "## Limitaciones", "",
        "- EMAE es provisional y revisable; tendencia-ciclo también cambia con nuevos extremos de serie.",
        "- EMAE per cápita es una construcción analítica: usa población interpolada y no reemplaza PIB per cápita.",
        "- La serie mensual comienza en 2004; no se inventa un drawdown 2001–2002.",
        "- Las comparaciones de mandatos no controlan por contexto internacional, pandemia, punto de partida ni composición sectorial.",
        "- El saldo en meses-base mide trayectoria relativa, no pesos, bienestar ni causalidad política.", "",
        "## Pruebas programáticas", "",
    ]
    lines.extend(f"- {t}" for t in tests)
    lines.extend(["", "## Resultado de construcción", "", f"- Insumo HTML: `{input_path.name}` (no sobrescrito).", f"- Salida HTML: `{output_path.name}`.", f"- Último EMAE SA: `{kpis['latest_sa']:.12f}`.", f"- Saldo post-shock: `{kpis['net_months_base']:.12f}` meses-base.", ""])
    return "\n".join(lines)


def main() -> None:
    HERE.mkdir(parents=True, exist_ok=True)
    rows = augment_monthly(parse_emae(), parse_population_anchors()[0])
    pop_anchors, indec_pop, wb_pop = parse_population_anchors()
    mandates = mandate_summary(rows)
    mirror_rows, mirror = mirror_window(rows)
    drawdowns = drawdown_summary(rows)
    rebound = rebound_summary(rows)
    kpis = compute_kpis(rows, mirror, rebound)
    input_html, output_html = select_dashboard()

    monthly_path = HERE / "emae_mensual_limpio.csv"
    percap_path = HERE / "emae_per_capita.csv"
    mandate_path = HERE / "emae_mandatos.csv"
    mirror_path = HERE / "emae_ventana_espejo.csv"
    drawdown_path = HERE / "emae_drawdowns.csv"

    monthly_serial = serializable_rows(rows)
    write_csv(monthly_path, monthly_serial)
    percap_rows = [
        {k: r[k] for k in ("date", "population", "sa", "tc", "pc_sa_raw", "pc_tc_raw", "pc_sa_raw_nov2023_100", "pc_tc_raw_nov2023_100", "running_peak_pc", "drawdown_pc_pct")}
        for r in monthly_serial
    ]
    write_csv(percap_path, percap_rows)
    write_csv(mandate_path, mandates)
    write_csv(mirror_path, mirror_rows)
    write_csv(drawdown_path, drawdowns)

    tests = run_tests(rows, mandates, mirror_rows, kpis)
    with monthly_path.open("r", encoding="utf-8", newline="") as fh:
        monthly_reread = list(csv.DictReader(fh))
    with mirror_path.open("r", encoding="utf-8", newline="") as fh:
        mirror_reread = list(csv.DictReader(fh))
    assert abs(float(monthly_reread[-1]["sa"]) - kpis["latest_sa"]) < 1e-11
    assert abs(float(monthly_reread[-1]["cum_net_months_base"]) - kpis["net_months_base"]) < 1e-11
    assert abs(
        float(mirror_reread[-1]["post_cumulative_months_base"])
        - float(mirror_reread[-1]["mirror_cumulative_months_base"])
        - kpis["mirror_differential_months_base"]
    ) < 1e-11
    tests.append("PASS · KPIs concilian también al releer los CSV derivados escritos")
    auto_reading = conclusion(kpis, rebound, mirror)
    downloads = {
        "monthly": {"filename": "emae_mensual.csv", "content": csv_text(monthly_path)},
        "percap": {"filename": "emae_per_capita.csv", "content": csv_text(percap_path)},
        "mandates": {"filename": "emae_mandatos.csv", "content": csv_text(mandate_path)},
        "mirror": {"filename": "emae_ventana_espejo.csv", "content": csv_text(mirror_path)},
        "drawdowns": {"filename": "emae_drawdowns.csv", "content": csv_text(drawdown_path)},
    }
    inject_dashboard(
        input_html, output_html,
        html_section(kpis, mirror, rebound, auto_reading),
        html_css(),
        js_payload(rows, mandates, mirror_rows, drawdowns, rebound, downloads),
    )

    html_text = output_html.read_text(encoding="utf-8")
    for required in ("nov-2023 = 100", "ene-2017 = 100", "Base INDEC 2004=100", "promedio 2004 = 100"):
        assert required in html_text, f"Falta etiqueta de base: {required}"
    assert "Base 2015" not in html_text
    tests.append("PASS · títulos, selector, ejes y notas declaran bases consistentes")
    for filename in ("emae_mensual.csv", "emae_per_capita.csv", "emae_mandatos.csv", "emae_ventana_espejo.csv", "emae_drawdowns.csv"):
        assert f'"filename":"{filename}"' in html_text
    assert html_text.count("downloadEmaeCsv('") == 5
    tests.append("PASS · los cinco CSV y sus controles de descarga quedaron embebidos")

    update_fuentes()
    audit = audit_markdown(input_html, output_html, tests, pop_anchors, indec_pop, wb_pop, mirror, kpis, rebound)
    (HERE / "AUDITORIA_EMAE.md").write_text(audit, encoding="utf-8")
    manifest = {
        "generated_at": AS_OF,
        "input_html": str(input_html.relative_to(ROOT)).replace("\\", "/"),
        "output_html": str(output_html.relative_to(ROOT)).replace("\\", "/"),
        "sources": {str(p.relative_to(ROOT)).replace("\\", "/"): sha256(p) for p in [INDEC_EMAE_CSV, INDEC_POP_CSV, WB_POP_JSON, SOURCES / "indec" / "sh_emae_mensual_base2004.xls", SOURCES / "indec" / "emae_08_26.pdf", SOURCES / "metodologia" / "metodologia_emae_ago_16.pdf"]},
        "outputs": {str(p.relative_to(ROOT)).replace("\\", "/"): sha256(p) for p in [monthly_path, percap_path, mandate_path, mirror_path, drawdown_path, output_html]},
        "kpis": kpis, "mirror": mirror, "rebound": rebound, "tests": tests,
    }
    (HERE / "manifest_emae.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"input": str(input_html), "output": str(output_html), "kpis": kpis, "tests": tests}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
