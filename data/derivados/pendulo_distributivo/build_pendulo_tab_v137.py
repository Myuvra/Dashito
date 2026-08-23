from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE_HTML = ROOT / "data" / "dashboard_kawaii_135_morosidad.html"
OUTPUT_HTML = ROOT / "data" / "dashboard_kawaii_137_pendulo_en_criollo.html"
RAW_JSON = ROOT / "data" / "derivados" / "pendulo_distributivo" / "cgi_raw.json"
DERIVED_DIR = RAW_JSON.parent
SERIES_CSV = DERIVED_DIR / "cgi_pendulo.csv"
MANDATES_CSV = DERIVED_DIR / "cgi_mandatos.csv"
AUDIT_MD = DERIVED_DIR / "AUDITORIA_PENDULO_DISTRIBUTIVO.md"
TESTS_JSON = DERIVED_DIR / "TESTS_PENDULO.json"
SOURCES_CSV = ROOT / "data" / "fuentes" / "FUENTES.csv"


MANDATE_ORDER = [
    "Carlos Menem",
    "Fernando de la Rúa",
    "Eduardo Duhalde",
    "Néstor Kirchner",
    "Cristina Fernández I",
    "Cristina Fernández II",
    "Mauricio Macri",
    "Alberto Fernández",
    "Javier Milei",
]


def mandate_for(year: int, segment: str) -> tuple[str, str]:
    if segment == "historical":
        if year <= 1999:
            return "Carlos Menem", "serie disponible desde 1993"
        if year <= 2001:
            return "Fernando de la Rúa", "dato anual"
        if year == 2002:
            return "Eduardo Duhalde", "un único dato anual"
        if year <= 2007:
            return "Néstor Kirchner", "dato anual; 2003 y 2007 contienen transiciones"
    if 2016 <= year <= 2019:
        return "Mauricio Macri", "serie moderna desde 2016-T1"
    if 2020 <= year <= 2023:
        return "Alberto Fernández", "trimestres calendario; 2023-T4 contiene la transición"
    if year >= 2024:
        return "Javier Milei", "mandato en curso; último dato 2026-T1"
    return "Sin serie comparable", "corte metodológico 2008–2015"


def quarter_date(year: int, quarter: int) -> str:
    month = {1: 2, 2: 5, 3: 8, 4: 11}[quarter]
    return f"{year:04d}-{month:02d}-15"


def finite(value: float | None) -> bool:
    return value is not None and math.isfinite(value)


def build_rows(raw: dict) -> list[dict]:
    rows: list[dict] = []
    for item in raw["historical"]:
        universe = item["universe"]
        year = int(item["year"])
        president, coverage = mandate_for(year, "historical")
        rta = float(item["rta"])
        imb = float(item["imb"])
        eeb = float(item["eeb"])
        denominator = rta + imb + eeb
        rows.append(
            {
                "date": f"{year:04d}-07-01",
                "period": str(year),
                "year": year,
                "quarter": None,
                "frequency": "annual",
                "segment": "historical",
                "universe": universe,
                "president": president,
                "coverage_note": coverage,
                "vab": float(item["vab"]),
                "rta": rta,
                "imb": imb,
                "taxes_net": None,
                "eeb": eeb,
                "share_rta": rta / denominator * 100,
                "share_imb": imb / denominator * 100,
                "share_households": (rta + imb) / denominator * 100,
                "share_capital": eeb / denominator * 100,
                "pendulo": ((rta + imb) - eeb) / denominator * 100,
                "method_note": "CGI histórica: otros impuestos a la producción incluidos en IMB/EEB; no separables.",
            }
        )

    for item in raw["modern"]:
        year = int(item["year"])
        quarter = int(item["quarter"])
        president, coverage = mandate_for(year, "modern")
        for universe in ("private", "total"):
            source = item[universe]
            rta = float(source["rta"])
            imb = float(source["imb"])
            eeb = float(source["eeb"])
            taxes = float(source["taxes_net"])
            denominator = rta + imb + eeb
            rows.append(
                {
                    "date": quarter_date(year, quarter),
                    "period": f"{year}-T{quarter}",
                    "year": year,
                    "quarter": quarter,
                    "frequency": "quarterly",
                    "segment": "modern",
                    "universe": universe,
                    "president": president,
                    "coverage_note": coverage,
                    "vab": float(source["vab"]),
                    "rta": rta,
                    "imb": imb,
                    "taxes_net": taxes,
                    "eeb": eeb,
                    "share_rta": rta / denominator * 100,
                    "share_imb": imb / denominator * 100,
                    "share_households": (rta + imb) / denominator * 100,
                    "share_capital": eeb / denominator * 100,
                    "pendulo": ((rta + imb) - eeb) / denominator * 100,
                    "method_note": "CGI moderna: normalización solicitada excluye otros impuestos netos de subsidios.",
                }
            )

    rows.sort(key=lambda row: (row["universe"], row["date"]))
    first_by_mandate: dict[tuple[str, str], float] = {}
    for row in rows:
        key = (row["universe"], row["president"])
        if key not in first_by_mandate:
            first_by_mandate[key] = row["pendulo"]
        row["change_since_mandate_start"] = row["pendulo"] - first_by_mandate[key]
    return rows


def build_mandates(rows: list[dict]) -> list[dict]:
    result: list[dict] = []
    for universe in ("private", "total"):
        for mandate in MANDATE_ORDER:
            observed = [row for row in rows if row["universe"] == universe and row["president"] == mandate]
            if not observed:
                result.append(
                    {
                        "universe": universe,
                        "mandate": mandate,
                        "start_period": "",
                        "end_period": "",
                        "observations": 0,
                        "start": None,
                        "end": None,
                        "change": None,
                        "average": None,
                        "coverage_note": "sin serie comparable",
                    }
                )
                continue
            observed.sort(key=lambda row: row["date"])
            values = [row["pendulo"] for row in observed]
            result.append(
                {
                    "universe": universe,
                    "mandate": mandate,
                    "start_period": observed[0]["period"],
                    "end_period": observed[-1]["period"],
                    "observations": len(observed),
                    "start": values[0],
                    "end": values[-1],
                    "change": values[-1] - values[0],
                    "average": statistics.fmean(values),
                    "coverage_note": observed[0]["coverage_note"],
                }
            )
    return result


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def source_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def update_sources_registry() -> None:
    source_dir = ROOT / "data" / "fuentes" / "pendulo_distributivo"
    entries = [
        {
            "id": "indec_cgi_modern_2016_2026q1",
            "tema": "pendulo_distributivo",
            "institucion": "INDEC",
            "titulo": "Cuenta de generación del ingreso e insumo de mano de obra · serie 2016-T1/2026-T1",
            "url_original": "https://www.indec.gob.ar/ftp/cuadros/economia/serie_cgi_07_26.xls",
            "archivo_local": "/data/fuentes/pendulo_distributivo/indec/serie_cgi_07_26.xls",
            "fecha_descarga": "2026-08-21",
            "fecha_publicacion": "2026-07",
            "codigo_serie": "CGI · VAB_pb/RTA/IBM/T-S/EEB",
            "periodo_utilizado": "2016-T1/2026-T1",
            "tipo": "XLS oficial",
            "sha256": source_hash(source_dir / "indec" / "serie_cgi_07_26.xls"),
            "nota": "Serie trimestral moderna; sector total y total excluido sector público.",
        },
        {
            "id": "indec_cgi_historical_total_1993_2007",
            "tema": "pendulo_distributivo",
            "institucion": "INDEC",
            "titulo": "Generación del ingreso total de la economía · 1993-2007",
            "url_original": "https://www.indec.gob.ar/ftp/nuevaweb/cuadros/17/cgi_cuadro1.xls",
            "archivo_local": "/data/fuentes/pendulo_distributivo/indec/cgi_cuadro1_total_1993_2007.xls",
            "fecha_descarga": "2026-08-21",
            "fecha_publicacion": "",
            "codigo_serie": "CGI histórica · cuadro 1",
            "periodo_utilizado": "1993/2007",
            "tipo": "XLS oficial histórico",
            "sha256": source_hash(source_dir / "indec" / "cgi_cuadro1_total_1993_2007.xls"),
            "nota": "Otros impuestos a la producción incluidos en IMB/EEB; no se empalma con la serie moderna.",
        },
        {
            "id": "indec_cgi_historical_private_1993_2007",
            "tema": "pendulo_distributivo",
            "institucion": "INDEC",
            "titulo": "Generación del ingreso del sector privado · 1993-2007",
            "url_original": "https://www.indec.gob.ar/ftp/nuevaweb/cuadros/17/cgi_apendice4.xls",
            "archivo_local": "/data/fuentes/pendulo_distributivo/indec/cgi_apendice4_privado_1993_2007.xls",
            "fecha_descarga": "2026-08-21",
            "fecha_publicacion": "",
            "codigo_serie": "CGI histórica · apéndice 4",
            "periodo_utilizado": "1993/2007",
            "tipo": "XLS oficial histórico",
            "sha256": source_hash(source_dir / "indec" / "cgi_apendice4_privado_1993_2007.xls"),
            "nota": "Sector privado; otros impuestos a la producción incluidos en IMB/EEB.",
        },
        {
            "id": "indec_cgi_report_2026q1",
            "tema": "pendulo_distributivo",
            "institucion": "INDEC",
            "titulo": "Cuenta de generación del ingreso · primer trimestre de 2026",
            "url_original": "https://www.indec.gob.ar/uploads/informesdeprensa/cgi_07_26D31D16C00B.pdf",
            "archivo_local": "/data/fuentes/pendulo_distributivo/indec/cgi_07_26.pdf",
            "fecha_descarga": "2026-08-21",
            "fecha_publicacion": "2026-07",
            "codigo_serie": "Informe CGI 1T2026",
            "periodo_utilizado": "2026-T1",
            "tipo": "PDF oficial",
            "sha256": source_hash(source_dir / "indec" / "cgi_07_26.pdf"),
            "nota": "Control del último dato publicado.",
        },
        {
            "id": "indec_cgi_methodology_24",
            "tema": "pendulo_distributivo",
            "institucion": "INDEC",
            "titulo": "Metodología de las cuentas nacionales",
            "url_original": "https://www.indec.gob.ar/ftp/cuadros/economia/metodologia_24_cuentas_nacionales.pdf",
            "archivo_local": "/data/fuentes/pendulo_distributivo/metodologia/metodologia_24_cuentas_nacionales.pdf",
            "fecha_descarga": "2026-08-21",
            "fecha_publicacion": "",
            "codigo_serie": "Metodología INDEC 24",
            "periodo_utilizado": "metodología",
            "tipo": "PDF oficial",
            "sha256": source_hash(source_dir / "metodologia" / "metodologia_24_cuentas_nacionales.pdf"),
            "nota": "Definiciones de RTA, IMB, EEB y VAB.",
        },
    ]

    with SOURCES_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        existing = list(reader)
    entry_ids = {entry["id"] for entry in entries}
    existing = [row for row in existing if row.get("id") not in entry_ids]
    existing.extend(entries)
    with SOURCES_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(existing)


CSS = r"""
<style id="pendulo-distributivo-v137">
/* v137 · péndulo distributivo con lectura popular, stickers y flechas */
#tab-pendulo{padding-top:4px}
.pend-shell{display:grid;gap:16px;color:#5b4167}
.pend-card{min-width:0;padding:20px;border:1px solid #e4d4ed;border-radius:24px;background:rgba(255,255,255,.92);box-shadow:0 10px 24px rgba(90,57,112,.06);box-sizing:border-box}
.pend-hero{background:linear-gradient(135deg,rgba(255,249,253,.97),rgba(247,252,255,.97));border-color:#d9c8eb}
.pend-head{display:flex;align-items:flex-start;justify-content:space-between;gap:18px}
.pend-head h2,.pend-head h3{margin:0;color:#5a376b;line-height:1.18}.pend-head h2{font-size:27px}.pend-head h3{font-size:20px}
.pend-kicker{display:inline-flex;align-items:center;gap:6px;margin-bottom:8px;padding:5px 9px;border:1px solid #decceb;border-radius:999px;background:#fff;font-size:9px;font-weight:950;letter-spacing:.045em;text-transform:uppercase;color:#77558a}
.pend-sub{max-width:900px;margin:7px 0 0;font-size:11.5px;line-height:1.58;color:#725f78}
.pend-quote{margin:17px 0 0;padding:16px 18px;border-left:5px solid #b17ac7;border-radius:16px;background:#fbf7ff;color:#563a62;font-size:15px;line-height:1.55;font-weight:850}
.pend-quote small{display:block;margin-top:7px;color:#7b6a80;font-size:10px;font-weight:650}
.pend-controls{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(220px,.8fr);gap:12px;margin-top:16px}
.pend-control{padding:12px;border:1px solid #e1d4e9;border-radius:16px;background:#fff;box-sizing:border-box}
.pend-control>span{display:block;margin-bottom:7px;font-size:8.5px;font-weight:950;letter-spacing:.04em;text-transform:uppercase;color:#846a8e}
.pend-buttons{display:flex;flex-wrap:wrap;gap:7px}
.pend-btn{appearance:none;border:1px solid #d9c9e5;border-radius:999px;background:#fff;padding:8px 11px;color:#674a73;font:inherit;font-size:10px;font-weight:900;cursor:pointer;transition:.15s ease}
.pend-btn:hover,.pend-btn:focus-visible{border-color:#aa79bf;transform:translateY(-1px)}.pend-btn.active{border-color:#9a62b4;background:#f6ecfb;color:#5b376b;box-shadow:0 4px 10px rgba(112,62,136,.12)}
.pend-kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-top:14px}
.pend-kpi{padding:14px;border:1px solid #ded3e6;border-radius:16px;background:#fff;box-sizing:border-box}.pend-kpi.work{border-color:#b8dccb;background:#f6fff9}.pend-kpi.capital{border-color:#e5bfd0;background:#fff8fb}.pend-kpi.index{border-color:#cbbce8;background:#faf8ff}
.pend-kpi small{display:block;font-size:8px;font-weight:950;letter-spacing:.045em;text-transform:uppercase;color:#836d8b}.pend-kpi strong{display:block;margin:5px 0 3px;font-size:24px;line-height:1.05;color:#5a3d68}.pend-kpi.work strong{color:#2f8667}.pend-kpi.capital strong{color:#ae426d}.pend-kpi span{font-size:9.5px;line-height:1.4;color:#75647a}
.pend-reading{margin-top:12px;padding:12px 14px;border-left:5px solid #9b6db5;border-radius:14px;background:#fbf8ff;font-size:11px;line-height:1.55;color:#67526f}.pend-reading b{color:#553663}
.pend-everyday{position:relative;margin-top:14px;padding:17px;border:2px solid #d8c3e8;border-radius:20px;background:linear-gradient(135deg,#fff,#f9f5ff 54%,#f3fff8);overflow:hidden}
.pend-everyday::after{content:'$100';position:absolute;right:-6px;top:-16px;font-size:62px;font-weight:950;color:rgba(137,91,159,.055);transform:rotate(8deg);pointer-events:none}
.pend-everyday-head{position:relative;z-index:1;display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:12px}.pend-everyday-head h3{margin:0;font-size:17px;color:#593867}.pend-everyday-head p{margin:3px 0 0;font-size:9.5px;line-height:1.45;color:#75637a}
.pend-sticker{display:inline-flex;align-items:center;gap:5px;padding:6px 9px;border:2px solid #7e5590;border-radius:10px;background:#fff6c9;color:#5d4268;font-size:8.5px;font-weight:950;letter-spacing:.04em;text-transform:uppercase;box-shadow:3px 3px 0 rgba(112,75,128,.16);transform:rotate(-1.5deg)}
.pend-hundred-flow{position:relative;z-index:1;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:28px}.pend-hundred-piece{position:relative;min-width:0;padding:13px 14px;border:1px solid #ded1e6;border-radius:16px;background:rgba(255,255,255,.94)}.pend-hundred-piece:not(:last-child)::after{content:'➜';position:absolute;right:-24px;top:50%;transform:translateY(-50%);font-size:20px;color:#a16bb5}.pend-hundred-piece.rta{border-color:#c7bce8}.pend-hundred-piece.imb{border-color:#b9ddcd}.pend-hundred-piece.eeb{border-color:#e6bfd0}.pend-hundred-piece small{display:block;font-size:8px;font-weight:950;text-transform:uppercase;letter-spacing:.035em;color:#816b88}.pend-hundred-piece strong{display:block;margin:5px 0 3px;font-size:23px;color:#5b3d68}.pend-hundred-piece.rta strong{color:#6250ad}.pend-hundred-piece.imb strong{color:#2f8a69}.pend-hundred-piece.eeb strong{color:#b2456e}.pend-hundred-piece span{font-size:9.3px;line-height:1.4;color:#736176}
.pend-everyday-bottom{position:relative;z-index:1;margin-top:11px;padding:10px 12px;border-radius:12px;background:rgba(255,255,255,.76);font-size:10px;line-height:1.5;color:#67536e}.pend-everyday-bottom b{color:#50325e}
.pend-chart-stickers{display:flex;flex-wrap:wrap;gap:7px;margin:11px 0 2px}.pend-chart-sticker{display:inline-flex;align-items:center;gap:5px;padding:6px 9px;border:1px solid #d8c9e3;border-radius:999px;background:#fff;font-size:8.7px;font-weight:900;color:#694c75;box-shadow:0 3px 8px rgba(92,58,110,.07)}.pend-chart-sticker.up{border-color:#b6dccb;background:#f3fff8;color:#28775d}.pend-chart-sticker.down{border-color:#e5bacb;background:#fff6fa;color:#9e3d63}.pend-chart-sticker.warn{border-color:#ead79e;background:#fffdf1;color:#806629}
.pend-plain-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:13px}.pend-plain-card{position:relative;min-width:0;padding:13px 13px 12px 42px;border:1px solid #e1d4e8;border-radius:15px;background:#fff;font-size:9.8px;line-height:1.5;color:#6d5a72}.pend-plain-card .icon{position:absolute;left:12px;top:12px;font-size:21px}.pend-plain-card b{display:block;margin-bottom:3px;color:#593b67;font-size:10px}.pend-plain-card strong{color:#563963;font-weight:950}.pend-plain-card.up{border-color:#b8dccb;background:#f7fffa}.pend-plain-card.down{border-color:#e6bdce;background:#fff8fb}.pend-plain-card.warn{border-color:#ead9aa;background:#fffdf5}
.pend-component-guide{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px;margin-top:12px}.pend-component{padding:12px;border-radius:14px;border:1px solid #dfd3e6;background:#fff;font-size:9.4px;line-height:1.5;color:#6f5d74}.pend-component b{display:block;margin-bottom:4px;color:#5b3d68;font-size:10.5px}.pend-component .who{display:block;margin-top:5px;padding-top:5px;border-top:1px dashed #dfd4e5;color:#806b86}.pend-component .who strong{color:#4f3560}
.pend-chart-scroll{max-width:100%;overflow-x:auto;overflow-y:hidden;padding-bottom:4px;-webkit-overflow-scrolling:touch}.pend-chart{width:100%;min-width:820px;height:520px}.pend-chart.medium{height:440px}.pend-chart.compact{height:390px}
.pend-grid-2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}
.pend-note{margin:7px 0 0;font-size:10.5px;line-height:1.55;color:#76647b}
.pend-legend-note{margin-top:9px;padding:10px 12px;border:1px dashed #decee7;border-radius:13px;background:#fdfbff;font-size:9.5px;line-height:1.5;color:#746179}
.pend-table-wrap{max-width:100%;overflow:auto;margin-top:10px;border:1px solid #e4d7eb;border-radius:15px;background:#fff}
.pend-table-wrap table{width:100%;min-width:780px;border-collapse:collapse;font-size:9.5px}.pend-table-wrap th,.pend-table-wrap td{padding:9px 10px;border-bottom:1px solid #eee5f2;text-align:left;vertical-align:top}.pend-table-wrap th{position:sticky;top:0;background:#f7f1fb;color:#71527e;font-size:8px;text-transform:uppercase;letter-spacing:.035em}.pend-table-wrap td.num{text-align:right;font-variant-numeric:tabular-nums}.pend-table-wrap tr:last-child td{border-bottom:0}.pend-move-work{color:#2f8667;font-weight:900}.pend-move-capital{color:#ad426c;font-weight:900}.pend-no-data{color:#8a7b8f;font-style:italic}
.pend-verdict{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(0,.95fr);gap:14px;margin-top:14px}.pend-verdict>div{padding:15px;border:1px solid #e3d6ea;border-radius:17px;background:#fff}.pend-verdict h4{margin:0 0 8px;color:#5f416c;font-size:13px}.pend-verdict ul{margin:0;padding-left:18px;font-size:10.5px;line-height:1.6;color:#705d75}.pend-conclusion{margin-top:14px;padding:14px 16px;border:2px solid #cfbde2;border-radius:16px;background:linear-gradient(135deg,#fbf8ff,#f6fff9);font-size:12px;line-height:1.6;color:#5c4566}.pend-conclusion b{color:#51325f}
.pend-contrast-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:11px;margin-top:13px}.pend-contrast{padding:14px;border:1px solid #dfd3e7;border-radius:17px;background:#fff}.pend-contrast h4{margin:0 0 8px;font-size:14px;color:#5a3a68}.pend-contrast dl{display:grid;grid-template-columns:1fr auto;gap:7px 10px;margin:0;font-size:9.5px;line-height:1.4}.pend-contrast dt{color:#78677d}.pend-contrast dd{margin:0;text-align:right;font-weight:900;color:#5d4369}.pend-contrast .coverage{margin-top:9px;padding-top:8px;border-top:1px dashed #e2d7e8;font-size:8.8px;line-height:1.45;color:#84758a}
.pend-links{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}.pend-link{appearance:none;border:1px solid #d8cae3;border-radius:999px;background:#fff;padding:8px 11px;color:#654770;font:inherit;font-size:9.5px;font-weight:900;cursor:pointer}.pend-link:hover{border-color:#9d6eb3;background:#fbf7ff}
.pend-method details{border:1px solid #e2d7e8;border-radius:15px;background:#fff}.pend-method summary{cursor:pointer;padding:13px 15px;font-size:11px;font-weight:950;color:#654671}.pend-method details>div{padding:0 15px 15px;font-size:10px;line-height:1.6;color:#705f75}.pend-formula{margin:9px 0;padding:11px 12px;border-radius:12px;background:#f8f4fb;font-family:ui-monospace,SFMono-Regular,Consolas,monospace;color:#5a4165;overflow:auto}
.pend-source-grid{display:grid;grid-template-columns:1.1fr .9fr;gap:12px}.pend-source-box{padding:14px;border:1px solid #e1d5e8;border-radius:16px;background:#fff;font-size:9.5px;line-height:1.55;color:#6e5b73}.pend-source-box a{color:#7a4f91;font-weight:900}.pend-downloads{display:flex;flex-wrap:wrap;gap:8px;margin-top:9px}
@media(max-width:1050px){.pend-kpis{grid-template-columns:repeat(2,minmax(0,1fr))}.pend-grid-2,.pend-verdict,.pend-source-grid{grid-template-columns:1fr}.pend-contrast-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.pend-plain-grid{grid-template-columns:1fr}.pend-component-guide{grid-template-columns:1fr}}
@media(max-width:760px){.pend-card{padding:15px;border-radius:20px}.pend-head{display:block}.pend-head h2{font-size:23px}.pend-controls{grid-template-columns:1fr}.pend-contrast-grid{grid-template-columns:1fr}.pend-chart{min-width:760px;height:470px}.pend-chart.medium{height:410px}.pend-chart.compact{height:370px}.pend-quote{font-size:13px}.pend-btn{padding:8px 10px}.pend-kpi strong{font-size:22px}.pend-everyday-head{align-items:flex-start;flex-direction:column}.pend-hundred-flow{grid-template-columns:1fr;gap:23px}.pend-hundred-piece:not(:last-child)::after{content:'⬇';right:auto;left:50%;top:auto;bottom:-22px;transform:translateX(-50%);font-size:16px}}
@media(max-width:430px){.pend-card{padding:12px}.pend-kpis{grid-template-columns:1fr}.pend-chart{min-width:720px}.pend-sub,.pend-reading{font-size:10.5px}.pend-verdict>div{padding:12px}.pend-everyday{padding:13px}.pend-hundred-piece strong{font-size:21px}.pend-plain-card{padding-right:10px}}
@media(max-width:390px){.pend-card{padding:10px}.pend-control{padding:10px}.pend-chart{min-width:700px}.pend-kicker{white-space:normal}}
</style>
"""


SECTION = r"""
  <!-- PENDULO_DISTRIBUTIVO_TAB_VERSION:2 · lectura popular -->
  <section id="tab-pendulo" class="tab-panel">
    <div class="pend-shell">
      <section class="pend-card pend-hero">
        <div class="pend-head"><div><span class="pend-kicker">INDEC · Cuenta de Generación del Ingreso · 1993–2007 y 2016–2026-T1</span><h2>Péndulo distributivo ♡</h2><p class="pend-sub">Un instrumento para contrastar —no para dar por cierta— una hipótesis sobre cómo se reparte el ingreso generado entre trabajo/hogares y excedente societario.</p></div></div>
        <blockquote class="pend-quote">“El péndulo argentino es entre la gente que no quiere dejarse cagar por las corpos y la gente que no entiende que la están cagando.”<small>La frase es la hipótesis provocadora. Los datos no pueden probar intenciones de empresas ni de votantes.</small></blockquote>
        <div class="pend-controls">
          <div class="pend-control"><span>Ver como</span><div class="pend-buttons" id="pendPerspectiveButtons"><button class="pend-btn active" data-value="index">Índice del péndulo</button><button class="pend-btn" data-value="shares">Participación %</button><button class="pend-btn" data-value="change">Cambio desde inicio del mandato</button></div></div>
          <div class="pend-control"><span>Serie</span><div class="pend-buttons" id="pendUniverseButtons"><button class="pend-btn active" data-value="private">Sector privado</button><button class="pend-btn" data-value="total">Total economía</button></div></div>
        </div>
        <div class="pend-kpis">
          <div class="pend-kpi index"><small>Último péndulo</small><strong id="pendKpiIndex">—</strong><span id="pendKpiPeriod">—</span></div>
          <div class="pend-kpi work"><small>Trabajo / hogares</small><strong id="pendKpiHouseholds">—</strong><span>RTA + IMB · total normalizado</span></div>
          <div class="pend-kpi capital"><small>Excedente societario</small><strong id="pendKpiCapital">—</strong><span>EEB · total normalizado</span></div>
          <div class="pend-kpi"><small>Impuestos excluidos</small><strong id="pendKpiTaxes">—</strong><span>otros impuestos netos de subsidios</span></div>
        </div>
        <div class="pend-reading" id="pendQuickReading">Calculando la lectura desde los datos…</div>
        <div class="pend-everyday">
          <div class="pend-everyday-head"><div><span class="pend-sticker">🧁 La torta explicada</span><h3>Si el ingreso generado fueran $100…</h3><p>No son $100 de una familia: es una forma sencilla de traducir las participaciones de toda la economía seleccionada.</p></div><span class="pend-sticker" id="pendHundredUniverse">sector privado</span></div>
          <div class="pend-hundred-flow">
            <div class="pend-hundred-piece rta"><small>👷 Sueldos · RTA</small><strong id="pendHundredRta">—</strong><span>remuneración al trabajo asalariado</span></div>
            <div class="pend-hundred-piece imb"><small>🧰 Cuenta propia · IMB</small><strong id="pendHundredImb">—</strong><span>ingreso mixto de hogares y unidades no societarias</span></div>
            <div class="pend-hundred-piece eeb"><small>🏢 Excedente · EEB</small><strong id="pendHundredEeb">—</strong><span>excedente bruto de explotación; no es ganancia neta ni efectivo</span></div>
          </div>
          <div class="pend-everyday-bottom" id="pendHundredBottom"><b>La cuenta:</b> RTA + IMB + EEB = $100 normalizados.</div>
        </div>
      </section>

      <section class="pend-card">
        <div class="pend-head"><div><h3>El péndulo distributivo argentino</h3><p class="pend-note">+100 = todo hacia trabajo/hogares · 0 = empate distributivo · −100 = todo hacia excedente societario. Los umbrales descriptivos ±10 no son una clasificación científica.</p></div></div>
        <div class="pend-chart-stickers"><span class="pend-chart-sticker up">⬆️ sube = trabajo/hogares gana participación</span><span class="pend-chart-sticker down">⬇️ baja = EEB gana participación</span><span class="pend-chart-sticker warn">⚠️ participación ≠ plata en el bolsillo</span></div>
        <div class="pend-chart-scroll"><div id="pendMainChart" class="pend-chart"></div></div>
        <div class="pend-legend-note"><b>Corte visible:</b> 1993–2007 es una serie histórica anual; 2016–2026-T1 es trimestral y usa otra metodología. No se interpolan 2008–2015 ni se conectan ambos segmentos. En la serie histórica, otros impuestos a la producción están incluidos en IMB/EEB y no pueden separarse.</div>
        <div class="pend-plain-grid"><div class="pend-plain-card up"><span class="icon">↗️</span><b>Cuando la línea sube</b>Sueldos + trabajo por cuenta propia ocupan una porción mayor de la torta relativa.</div><div class="pend-plain-card down"><span class="icon">↘️</span><b>Cuando la línea baja</b>El excedente bruto de explotación ocupa una porción mayor de esa torta.</div><div class="pend-plain-card warn"><span class="icon">🧭</span><b id="pendPlainMovementTitle">Qué pasó últimamente</b><span id="pendPlainMovement">Calculando desde la serie…</span></div></div>
      </section>

      <section class="pend-card">
        <div class="pend-head"><div><h3>¿Quién se queda con el ingreso generado?</h3><p class="pend-note">Participaciones normalizadas para que RTA + IMB + EEB = 100. RTA son asalariados; IMB aproxima trabajo autónomo y unidades no constituidas en sociedad; EEB es el excedente bruto de explotación y no equivale a ganancia neta ni caja empresaria.</p></div></div>
        <div class="pend-chart-stickers"><span class="pend-chart-sticker">👷 violeta = asalariados</span><span class="pend-chart-sticker up">🧰 verde = cuenta propia / hogares</span><span class="pend-chart-sticker down">🏢 rosa = excedente bruto</span></div>
        <div class="pend-chart-scroll"><div id="pendSharesChart" class="pend-chart medium"></div></div>
        <div class="pend-component-guide"><div class="pend-component"><b>👷 RTA · el sueldo</b>Es lo que las cuentas nacionales registran como remuneración del trabajo asalariado.<span class="who"><strong>Si crece su porcentaje:</strong> mejora la porción relativa de quienes trabajan en relación de dependencia.</span></div><div class="pend-component"><b>🧰 IMB · dos cosas mezcladas</b>Combina remuneración del trabajo y retorno del pequeño capital en cuentapropistas, hogares y unidades no societarias.<span class="who"><strong>No es sólo salario:</strong> por eso lo mostramos separado de RTA.</span></div><div class="pend-component"><b>🏢 EEB · antes de muchos descuentos</b>Es excedente bruto: todavía no descuenta depreciación, intereses, impuestos sobre la renta ni distribuciones.<span class="who"><strong>Si crece su porcentaje:</strong> el excedente gana porción relativa; no prueba por sí solo abuso ni ganancia extraordinaria.</span></div></div>
      </section>

      <section class="pend-card">
        <div class="pend-head"><div><h3>¿Hacia dónde se movió el péndulo durante cada gobierno?</h3><p class="pend-note">Promedio y cambio entre el primer y el último dato observado dentro de cada gestión. Los datos anuales y trimestrales no permiten cortar exactamente el día de asunción.</p></div></div>
        <div class="pend-chart-stickers"><span class="pend-chart-sticker up">→ verde = se movió hacia trabajo/hogares</span><span class="pend-chart-sticker down">← rosa = se movió hacia EEB</span><span class="pend-chart-sticker warn">1 dato = no alcanza para dibujar una tendencia</span></div>
        <div class="pend-chart-scroll"><div id="pendMandateChart" class="pend-chart compact"></div></div>
        <div id="pendMandateTable" class="pend-table-wrap"></div>
        <div class="pend-legend-note">Una variación ocurrida durante un gobierno no implica que haya sido causada exclusivamente por sus políticas. También influyen ciclo económico, precios internacionales, productividad, crisis, pandemia, sequías y otras variables.</div>
      </section>

      <section class="pend-card">
        <div class="pend-head"><div><span class="pend-kicker">La hipótesis bajo prueba</span><h3>¿Cuánta verdad tiene la frase?</h3></div></div>
        <div class="pend-verdict">
          <div><h4>Lo que sí podemos medir</h4><ul><li>participación del trabajo asalariado;</li><li>participación del ingreso mixto;</li><li>excedente bruto de explotación;</li><li>evolución observada durante cada gobierno;</li><li>contraste con salarios reales, Gini y pobreza del dashboard.</li></ul></div>
          <div><h4>Lo que esta métrica no puede demostrar</h4><ul><li>que toda empresa perjudique a sus trabajadores;</li><li>que toda ganancia sea renta extraordinaria;</li><li>que más EEB implique por sí solo explotación;</li><li>que los votantes actúen contra sus intereses de forma consciente;</li><li>que el conflicto político se reduzca sólo a capital vs trabajo.</li></ul></div>
        </div>
        <div class="pend-conclusion" id="pendConclusion">La conclusión se construye desde la serie seleccionada.</div>
      </section>

      <section class="pend-card">
        <div class="pend-head"><div><h3>Discurso vs resultado</h3><p class="pend-note">No etiquetamos gobiernos como “pro-gente” o “pro-corpo”. Ponemos en la misma ficha cambios observados en distribución, salario real, Gini y pobreza; los períodos de cada fuente no siempre coinciden exactamente.</p></div></div>
        <div id="pendContrastGrid" class="pend-contrast-grid"></div>
        <div class="pend-legend-note"><b>Importante:</b> participación relativa no es bienestar absoluto. La porción del trabajo puede subir durante una recesión si el excedente cae más rápido, o bajar aunque ambos ingresos crezcan.</div>
        <div class="pend-links"><button class="pend-link" onclick="activateTab('tab-power')">→ Ver salarios reales</button><button class="pend-link" onclick="activateTab('tab-gini')">→ Ver Gini</button><button class="pend-link" onclick="activateTab('tab-poverty')">→ Ver pobreza</button><button class="pend-link" onclick="activateTab('tab-consumption')">→ Ver consumo</button><button class="pend-link" onclick="activateTab('tab-growth')">→ Ver crecimiento</button><button class="pend-link" onclick="activateTab('tab-debt-public')">→ Ver deuda</button><button class="pend-link" onclick="activateTab('tab-casta')">→ Ver La casta</button></div>
      </section>

      <section class="pend-card pend-method">
        <div class="pend-head"><div><h3>Cómo leer este gráfico</h3><p class="pend-note">Hacia arriba indica una mayor participación relativa de RTA + IMB; hacia abajo, mayor participación de EEB. No es una medida moral de bueno/malo ni una medición aislada de bienestar.</p></div></div>
        <details><summary>▸ ¿Cómo calculamos este indicador?</summary><div><p><b>Trabajo/hogares = RTA + IMB.</b> <b>Capital societario = EEB</b> como aproximación solicitada, con la cautela de que EEB es una categoría de cuentas nacionales, no ganancias netas de sociedades.</p><div class="pend-formula">share_hogares = (RTA + IMB) / (RTA + IMB + EEB)<br>share_capital = EEB / (RTA + IMB + EEB)<br>pendulo = ((RTA + IMB) − EEB) / (RTA + IMB + EEB) × 100</div><p>En la serie moderna excluimos del denominador otros impuestos netos de subsidios. En 1993–2007 esos impuestos están incluidos en IMB/EEB y el archivo no permite separarlos: por eso el tramo histórico se muestra como referencia separada, no como continuidad homogénea.</p><p>La asignación por gobierno usa años calendario en el tramo anual y trimestres calendario en el moderno. 2023-T4 se mantiene dentro de Alberto Fernández porque el trimestre no puede dividirse con la publicación CGI; Milei comienza en 2024-T1.</p></div></details>
      </section>

      <section class="pend-card">
        <div class="pend-head"><div><h3>Fuentes, datos y auditoría</h3><p class="pend-note">Fuente principal: INDEC — Cuenta de Generación del Ingreso e Insumo de Mano de Obra.</p></div></div>
        <div class="pend-source-grid">
          <div class="pend-source-box"><b>Serie moderna · 2016-T1 a 2026-T1</b><br><a href="https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-9-49" target="_blank" rel="noopener">Página oficial CGI</a> · <a href="https://www.indec.gob.ar/ftp/cuadros/economia/serie_cgi_07_26.xls" target="_blank" rel="noopener">XLS oficial</a> · <a href="https://www.indec.gob.ar/uploads/informesdeprensa/cgi_07_26D31D16C00B.pdf" target="_blank" rel="noopener">informe 2026-T1</a>.</div>
          <div class="pend-source-box"><b>Serie histórica · 1993–2007</b><br><a href="https://www.indec.gob.ar/Institucional/Indec/InformacionDeArchivo/5" target="_blank" rel="noopener">Archivo histórico INDEC</a> · cuadros total y sector privado. El propio archivo exige cautela con publicaciones del período intervenido y la metodología difiere de la vigente.</div>
        </div>
        <div class="pend-downloads"><button class="pend-link" onclick="downloadPendCsv('series')">Descargar serie derivada CSV</button><button class="pend-link" onclick="downloadPendCsv('mandates')">Descargar mandatos CSV</button><a class="pend-link" id="pendAuditLink" href="#" target="_blank">Abrir auditoría</a></div>
      </section>
    </div>
  </section>
"""


SCRIPT_TEMPLATE = r"""
<script id="pendulo-distributivo-script-v137">
const PEND_DATA=__PEND_DATA__;
const PEND_MANDATES=__PEND_MANDATES__;
const PEND_CSVS=__PEND_CSVS__;
let pendUniverse='private',pendPerspective='index',pendRendered=false;
const PEND_CONFIG={responsive:true,displaylogo:false,scrollZoom:false,modeBarButtonsToRemove:['lasso2d','select2d']};
const PEND_BANDS=[
 {name:'Menem',start:'1993-01-01',end:'1999-12-09',color:'rgba(246,224,185,.17)'},
 {name:'De la Rúa',start:'1999-12-10',end:'2002-01-01',color:'rgba(207,228,247,.16)'},
 {name:'Duhalde',start:'2002-01-02',end:'2003-05-24',color:'rgba(244,204,216,.16)'},
 {name:'N. Kirchner',start:'2003-05-25',end:'2007-12-09',color:'rgba(205,239,222,.16)'},
 {name:'CFK I',start:'2007-12-10',end:'2011-12-09',color:'rgba(223,210,247,.13)'},
 {name:'CFK II',start:'2011-12-10',end:'2015-12-09',color:'rgba(223,210,247,.13)'},
 {name:'Macri',start:'2015-12-10',end:'2019-12-09',color:'rgba(247,225,183,.16)'},
 {name:'A. Fernández',start:'2019-12-10',end:'2023-12-09',color:'rgba(201,229,247,.16)'},
 {name:'Milei',start:'2023-12-10',end:'2026-04-01',color:'rgba(251,203,219,.17)'}
];
function pendRows(){return PEND_DATA.filter(r=>r.universe===pendUniverse).sort((a,b)=>a.date.localeCompare(b.date))}
function pendStats(){return PEND_MANDATES.filter(r=>r.universe===pendUniverse)}
function pendFmt(v,d=1){return v==null||!Number.isFinite(Number(v))?'n.d.':Number(v).toLocaleString('es-AR',{minimumFractionDigits:d,maximumFractionDigits:d})}
function pendSigned(v,d=1){return v==null||!Number.isFinite(Number(v))?'n.d.':`${v>=0?'+':'−'}${pendFmt(Math.abs(v),d)}`}
function pendMoney(v){if(v==null||!Number.isFinite(Number(v)))return 'no separable';return Number(v).toLocaleString('es-AR',{maximumFractionDigits:1})}
function pendInterpret(v){return v>10?'Distribución relativamente inclinada hacia trabajo/hogares.':v<-10?'Distribución relativamente inclinada hacia excedente societario.':'Distribución relativamente equilibrada.'}
function pendLayout(title,yTitle,extra={}){const shapes=PEND_BANDS.map((b,i)=>({type:'rect',xref:'x',yref:'paper',x0:b.start,x1:b.end,y0:0,y1:1,fillcolor:b.color,line:{width:0},layer:'below'}));PEND_BANDS.slice(1).forEach(b=>shapes.push({type:'line',xref:'x',yref:'paper',x0:b.start,x1:b.start,y0:0,y1:1,line:{color:'rgba(115,83,130,.48)',width:1,dash:'dot'}}));shapes.push({type:'rect',xref:'x',yref:'paper',x0:'2008-01-01',x1:'2015-12-31',y0:0,y1:1,fillcolor:'rgba(229,222,236,.34)',line:{color:'rgba(130,105,143,.45)',width:1,dash:'dash'},layer:'below'});const annotations=PEND_BANDS.map(b=>({xref:'x',yref:'paper',x:b.start,y:1.045,text:b.name,showarrow:false,textangle:-35,xanchor:'left',font:{size:9,color:'#785e80'}}));annotations.push({xref:'x',yref:'paper',x:'2011-12-31',y:.52,text:'<b>Cambio / empalme<br>metodológico INDEC</b><br>sin serie comparable',showarrow:false,align:'center',font:{size:10,color:'#7a687e'},bgcolor:'rgba(255,255,255,.84)',bordercolor:'#d7c9df',borderpad:5});return Object.assign({title:{text:title,font:{size:13,color:'#5d4169'}},paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(255,255,255,.72)',font:{family:'Nunito, Arial, sans-serif',color:'#654f6c',size:10},margin:{l:62,r:24,t:68,b:55},hovermode:'closest',hoverlabel:{bgcolor:'#fff8fc',bordercolor:'#d8b7ca',font:{size:10,color:'#4f3d56'},align:'left'},xaxis:{type:'date',range:['1992-06-01','2026-07-01'],gridcolor:'#eee5f2',tickformat:'%Y',dtick:'M36',automargin:true},yaxis:{title:yTitle,gridcolor:'#eadff0',zeroline:true,zerolinecolor:'#8b7096',automargin:true},legend:{orientation:'h',y:1.13,x:0,font:{size:9}},shapes,annotations},extra)}
function pendCustom(r){return [r.period,r.president,pendMoney(r.rta),pendMoney(r.imb),pendMoney(r.eeb),pendFmt(r.share_households),pendFmt(r.share_capital),pendSigned(r.pendulo),pendInterpret(r.pendulo),r.segment==='historical'?'Histórico: impuestos a la producción incluidos en IMB/EEB.':'Moderno: impuestos netos excluidos del denominador.']}
function pendSegmentTrace(rows,segment,field,name,color,showLegend=true){const rr=rows.filter(r=>r.segment===segment);return{x:rr.map(r=>r.date),y:rr.map(r=>r[field]),customdata:rr.map(pendCustom),name,mode:'lines+markers',connectgaps:false,showlegend:showLegend,line:{color,width:3},marker:{size:segment==='historical'?6:5,color},hovertemplate:'<b>%{customdata[0]}</b> · %{customdata[1]}<br>RTA: %{customdata[2]} M$ corrientes<br>IMB: %{customdata[3]} M$ corrientes<br>EEB: %{customdata[4]} M$ corrientes<br>Trabajo/hogares: <b>%{customdata[5]}%</b><br>Capital societario: <b>%{customdata[6]}%</b><br>Péndulo: <b>%{customdata[7]}</b><br>%{customdata[8]}<br><span style="font-size:9px">%{customdata[9]}</span><extra></extra>'}}
function pendPopularAnnotations(rows){const modern=rows.filter(r=>r.segment==='modern'),latest=modern.at(-1),mileiStart=modern.find(r=>r.president==='Javier Milei'),albertoEnd=[...modern].reverse().find(r=>r.president==='Alberto Fernández'),crisis=rows.find(r=>r.segment==='historical'&&r.year===2002),movement=latest.pendulo-mileiStart.pendulo,color=movement>=0?'#2f8b69':'#b5426b';return{shapes:[{type:'line',xref:'x',yref:'y',x0:mileiStart.date,y0:mileiStart.pendulo,x1:latest.date,y1:latest.pendulo,line:{color,width:4,dash:'dot'},layer:'above'}],annotations:[{xref:'x',yref:'y',x:latest.date,y:latest.pendulo,ax:-102,ay:-64,text:`<b>${movement>=0?'↗':'↘'} ${pendSigned(movement)} puntos</b><br>${mileiStart.period} → ${latest.period}<br><span style="font-size:9px">${movement>=0?'más porción para RTA + IMB':'más porción para EEB'}</span>`,showarrow:true,arrowhead:3,arrowsize:1.15,arrowwidth:2.2,arrowcolor:color,bgcolor:'rgba(255,255,255,.95)',bordercolor:color,borderpad:6,font:{size:10,color:'#533d5d'},align:'left'},{xref:'x',yref:'y',x:albertoEnd.date,y:albertoEnd.pendulo,ax:-68,ay:62,text:`<b>⚖️ ${albertoEnd.period}</b><br>casi 50/50`,showarrow:true,arrowhead:2,arrowcolor:'#8c6f97',bgcolor:'rgba(255,255,255,.94)',bordercolor:'#cdbbd7',borderpad:5,font:{size:9,color:'#5e4867'}},{xref:'x',yref:'y',x:crisis.date,y:crisis.pendulo,ax:44,ay:70,text:`<b>⬇️ ${crisis.period}</b><br>EEB superó a<br>RTA + IMB`,showarrow:true,arrowhead:2,arrowcolor:'#b34a72',bgcolor:'rgba(255,250,252,.95)',bordercolor:'#e0b4c5',borderpad:5,font:{size:9,color:'#684452'}}]}}
function renderPendMain(){
 const rows=pendRows();let traces=[],layout;
 if(pendPerspective==='index'){
  traces=[pendSegmentTrace(rows,'historical','pendulo','Histórica anual 1993–2007','#a77ac1'),pendSegmentTrace(rows,'modern','pendulo','Moderna trimestral 2016–2026-T1','#5d43a4')];
  layout=pendLayout('Índice del péndulo · segmentos no empalmados','índice · −100 a +100',{yaxis:{title:'− capital societario · índice · trabajo/hogares +',range:[-100,100],dtick:20,gridcolor:'#eadff0',zeroline:true,zerolinecolor:'#765b81'}});
  const popular=pendPopularAnnotations(rows);layout.annotations.push(...popular.annotations);layout.shapes.push(...popular.shapes);
 }else if(pendPerspective==='shares'){
  ['historical','modern'].forEach((segment,idx)=>{traces.push(pendSegmentTrace(rows,segment,'share_households',idx?'Trabajo/hogares · moderno':'Trabajo/hogares · histórico','#328d70',idx===0));traces.push(pendSegmentTrace(rows,segment,'share_capital',idx?'EEB · moderno':'EEB · histórico','#c14d78',idx===0))});
  layout=pendLayout('Participación normalizada','% de RTA + IMB + EEB',{yaxis:{title:'porcentaje normalizado',range:[0,100],dtick:10,gridcolor:'#eadff0'}});
 }else{
  const groups=[...new Set(rows.map(r=>r.president))].filter(n=>n!=='Sin serie comparable');groups.forEach((name,idx)=>{const rr=rows.filter(r=>r.president===name);traces.push({x:rr.map(r=>r.date),y:rr.map(r=>r.change_since_mandate_start),customdata:rr.map(pendCustom),name,mode:'lines+markers',showlegend:false,connectgaps:false,line:{color:idx%2?'#b34f7a':'#5f48a4',width:2.6},marker:{size:5},hovertemplate:'<b>%{customdata[0]}</b> · %{customdata[1]}<br>Cambio desde primer dato del mandato: <b>%{y:+.1f}</b> puntos<br>Péndulo del período: <b>%{customdata[7]}</b><extra></extra>'})});
  layout=pendLayout('Cambio desde el primer dato observado de cada mandato','puntos del índice',{yaxis:{title:'cambio dentro del mandato',gridcolor:'#eadff0',zeroline:true,zerolinecolor:'#765b81'}});
 }
 Plotly.react('pendMainChart',traces,layout,PEND_CONFIG)
}
function renderPendShares(){const rows=pendRows(),x=[],rta=[],imb=[],eeb=[],custom=[];let lastSegment='';rows.forEach(r=>{if(lastSegment&&lastSegment!==r.segment){x.push('2011-12-31');rta.push(null);imb.push(null);eeb.push(null);custom.push(null)}lastSegment=r.segment;x.push(r.date);rta.push(r.share_rta);imb.push(r.share_imb);eeb.push(r.share_capital);custom.push(pendCustom(r))});const hover='<b>%{customdata[0]}</b> · %{customdata[1]}<br>%{fullData.name}: <b>%{y:.1f}%</b><extra></extra>';const traces=[{x,y:rta,customdata:custom,name:'Trabajo asalariado · RTA',stackgroup:'one',line:{color:'#6a59c2',width:2},hovertemplate:hover},{x,y:imb,customdata:custom,name:'Ingreso mixto · IMB',stackgroup:'one',line:{color:'#47a984',width:2},hovertemplate:hover},{x,y:eeb,customdata:custom,name:'Excedente bruto · EEB',stackgroup:'one',line:{color:'#d6537f',width:2},hovertemplate:hover}];Plotly.react('pendSharesChart',traces,pendLayout('Componentes del ingreso normalizado','% del total',{yaxis:{title:'porcentaje normalizado',range:[0,100],dtick:10,gridcolor:'#eadff0'},hovermode:'x unified'}),PEND_CONFIG)}
function renderPendMandates(){const stats=pendStats(),labels=stats.map(s=>s.mandate.replace('Cristina Fernández','CFK').replace('Fernando de la Rúa','De la Rúa').replace('Mauricio ','').replace('Alberto Fernández','Alberto').replace('Javier ','').replace('Carlos ',''));const avg={x:labels,y:stats.map(s=>s.average),name:'Promedio del índice',type:'bar',marker:{color:'#9d79be'},text:stats.map(s=>s.average==null?'':pendSigned(s.average)),textposition:'outside',cliponaxis:false,hovertemplate:'%{x}<br>promedio: <b>%{y:.1f}</b><extra></extra>'};const change={x:labels,y:stats.map(s=>s.change),name:'Cambio inicio → fin',type:'bar',marker:{color:stats.map(s=>s.change==null?'#d8d0dc':s.change>=0?'#45a27e':'#ca537c')},text:stats.map(s=>s.change==null?'':pendSigned(s.change)),textposition:'outside',cliponaxis:false,hovertemplate:'%{x}<br>cambio: <b>%{y:+.1f}</b><extra></extra>'};Plotly.react('pendMandateChart',[avg,change],{title:{text:'Promedio y movimiento observado por gestión',font:{size:13,color:'#5d4169'}},paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(255,255,255,.72)',font:{family:'Nunito, Arial, sans-serif',color:'#654f6c',size:9},margin:{l:55,r:18,t:65,b:85},barmode:'group',xaxis:{tickangle:-30,automargin:true,gridcolor:'#eee5f2'},yaxis:{title:'puntos del índice',gridcolor:'#eadff0',zeroline:true,zerolinecolor:'#765b81'},legend:{orientation:'h',y:1.13,x:0,font:{size:9}},hoverlabel:{bgcolor:'#fff8fc',font:{size:10}}},PEND_CONFIG);document.getElementById('pendMandateTable').innerHTML='<table><thead><tr><th>Gobierno</th><th>Período observado</th><th>Inicio</th><th>Final</th><th>Cambio</th><th>Promedio</th><th>Lectura</th></tr></thead><tbody>'+stats.map(s=>{if(!s.observations)return `<tr><td><b>${s.mandate}</b></td><td colspan="6" class="pend-no-data">Sin serie CGI comparable para 2008–2015.</td></tr>`;const cls=s.change>0?'pend-move-work':s.change<0?'pend-move-capital':'pend-no-data';const reading=s.observations===1?'Un solo dato: no permite inferir movimiento.':s.change>0?'→ hacia trabajo/hogares':s.change<0?'← hacia excedente societario':'sin cambio entre extremos';return `<tr><td><b>${s.mandate}</b><br><small>${s.coverage_note}</small></td><td>${s.start_period} → ${s.end_period}<br><small>${s.observations} observaciones</small></td><td class="num">${pendSigned(s.start)}</td><td class="num">${pendSigned(s.end)}</td><td class="num ${cls}">${pendSigned(s.change)}</td><td class="num">${pendSigned(s.average)}</td><td class="${cls}">${reading}</td></tr>`}).join('')+'</tbody></table>'}
function pendPowerChange(name){if(typeof powerTotalAllOfficial==='undefined')return null;const windows={Macri:['2017-01-01','2019-12-01','parcial: la serie salarial comienza en ene-2017'],Alberto:['2020-01-01','2023-11-01','ene-2020 → nov-2023'],Milei:['2023-11-01','2026-06-01','nov-2023 → jun-2026']}[name];if(!windows)return null;const i0=powerTotalAllOfficial.dates.indexOf(windows[0]),i1=powerTotalAllOfficial.dates.indexOf(windows[1]);if(i0<0||i1<0)return null;return{value:(powerTotalAllOfficial.yNov[i1]/powerTotalAllOfficial.yNov[i0]-1)*100,note:windows[2]}}
function pendGiniChange(name){if(typeof giniData==='undefined')return null;const windows={Macri:['2016-12-31','2019-12-31','4T2016 → 4T2019'],Alberto:['2019-12-31','2023-12-31','4T2019 → 4T2023'],Milei:['2023-12-31','2026-03-31','4T2023 → 1T2026']}[name];const i0=giniData.dates.indexOf(windows[0]),i1=giniData.dates.indexOf(windows[1]);return i0<0||i1<0?null:{value:giniData.values[i1]-giniData.values[i0],note:windows[2]}}
function pendPovertyChange(name){if(typeof povertyMandateChanges==='undefined')return null;const map={Macri:'Mauricio Macri',Alberto:'Alberto Fernández',Milei:'Javier Milei'};const r=povertyMandateChanges.find(x=>x.presidente===map[name]);return r?{value:r.cambio,note:`${r.base} → ${r.cierre}`} : null}
function renderPendContrast(){const names=[['Macri','Mauricio Macri'],['Alberto','Alberto Fernández'],['Milei','Javier Milei']],stats=pendStats();document.getElementById('pendContrastGrid').innerHTML=names.map(([key,label])=>{const p=stats.find(s=>s.mandate===label),sal=pendPowerChange(key),g=pendGiniChange(key),pov=pendPovertyChange(key),move=p&&p.change>=0?'hacia trabajo/hogares':'hacia excedente societario';return `<article class="pend-contrast"><h4>${label}</h4><dl><dt>Péndulo</dt><dd class="${p&&p.change>=0?'pend-move-work':'pend-move-capital'}">${p?pendSigned(p.change):'n.d.'} · ${move}</dd><dt>Salario real</dt><dd>${sal?pendSigned(sal.value)+'%':'n.d.'}</dd><dt>Gini</dt><dd>${g?pendSigned(g.value,3):'n.d.'}</dd><dt>Pobreza</dt><dd>${pov?pendSigned(pov.value)+' pp':'n.d.'}</dd></dl><div class="coverage">Péndulo: ${p?p.start_period+' → '+p.end_period:'n.d.'}. Salario: ${sal?sal.note:'n.d.'}. Gini: ${g?g.note:'n.d.'}. Pobreza: ${pov?pov.note:'n.d.'}.</div></article>`}).join('')}
function renderPendNarrative(){
 const rows=pendRows(),latest=rows.filter(r=>r.segment==='modern').at(-1),stats=pendStats(),milei=stats.find(s=>s.mandate==='Javier Milei'),alberto=stats.find(s=>s.mandate==='Alberto Fernández'),macri=stats.find(s=>s.mandate==='Mauricio Macri'),mileiStart=rows.find(r=>r.segment==='modern'&&r.president==='Javier Milei');
 document.getElementById('pendKpiIndex').textContent=pendSigned(latest.pendulo);document.getElementById('pendKpiPeriod').textContent=`${latest.period} · ${pendUniverse==='private'?'sin sector público':'economía total'}`;document.getElementById('pendKpiHouseholds').textContent=`${pendFmt(latest.share_households)}%`;document.getElementById('pendKpiCapital').textContent=`${pendFmt(latest.share_capital)}%`;document.getElementById('pendKpiTaxes').textContent=`${pendFmt(latest.taxes_net/latest.vab*100)}% del VAB`;
 document.getElementById('pendHundredRta').textContent=`$ ${pendFmt(latest.share_rta)}`;document.getElementById('pendHundredImb').textContent=`$ ${pendFmt(latest.share_imb)}`;document.getElementById('pendHundredEeb').textContent=`$ ${pendFmt(latest.share_capital)}`;document.getElementById('pendHundredUniverse').textContent=pendUniverse==='private'?'sector privado':'economía total';document.getElementById('pendHundredBottom').innerHTML=`<b>En criollo:</b> de cada $100 normalizados, $${pendFmt(latest.share_rta)} aparecen como sueldos y $${pendFmt(latest.share_imb)} como ingreso mixto: juntos suman $${pendFmt(latest.share_households)}. Los otros $${pendFmt(latest.share_capital)} quedan como EEB. La diferencia entre ambos bloques es el péndulo ${pendSigned(latest.pendulo)}.`;
 const mileiText=milei.change>0?`mejoró ${pendFmt(milei.change)} puntos hacia trabajo/hogares`:`se movió ${pendFmt(Math.abs(milei.change))} puntos hacia EEB`;document.getElementById('pendQuickReading').innerHTML=`<b>Respuesta corta:</b> en ${latest.period}, el reparto normalizado fue ${pendFmt(latest.share_households)}% para RTA + IMB y ${pendFmt(latest.share_capital)}% para EEB. En la ventana trimestral de Milei (${milei.start_period} → ${milei.end_period}) el índice ${mileiText}. Eso describe una participación relativa; no demuestra causalidad ni bienestar absoluto.`;
 document.getElementById('pendPlainMovementTitle').textContent=`Milei · ${milei.start_period} → ${milei.end_period}`;document.getElementById('pendPlainMovement').innerHTML=`El índice pasó de <strong>${pendSigned(mileiStart.pendulo)}</strong> a <strong>${pendSigned(latest.pendulo)}</strong>: ${milei.change>=0?'RTA + IMB ganaron':'EEB ganó'} <strong>${pendFmt(Math.abs(milei.change))} puntos</strong> de distancia relativa.`;
 document.getElementById('pendConclusion').innerHTML=`<b>Hay oscilaciones medibles, pero no un relato único.</b> En la serie ${pendUniverse==='private'?'privada':'de economía total'}, Macri cambió ${pendSigned(macri.change)} puntos y Alberto ${pendSigned(alberto.change)}; ambos movimientos fueron hacia el excedente societario. Milei cambió ${pendSigned(milei.change)} puntos hacia trabajo/hogares entre ${milei.start_period} y ${milei.end_period}: <b>la hipótesis de un desplazamiento necesariamente pro-empresa no se cumple en este período observado.</b> La existencia de oscilaciones da una base económica para hablar de “péndulo distributivo”; reducir el voto a personas que entienden o no entienden que las perjudican excede lo que la CGI puede demostrar.`
}
function renderPend(){renderPendMain();renderPendShares();renderPendMandates();renderPendContrast();renderPendNarrative();pendRendered=true}
function downloadPendCsv(key){const item=PEND_CSVS[key];if(!item)return;const blob=new Blob(['\ufeff'+item.content],{type:'text/csv;charset=utf-8'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=item.filename;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(a.href),800)}
function pendProjectAsset(relativePath){const inVersionFile=/\/data\/dashboard_/i.test(location.pathname);return new URL((inVersionFile?'derivados/pendulo_distributivo/':'data/derivados/pendulo_distributivo/')+relativePath,location.href).href}
document.getElementById('pendAuditLink')?.setAttribute('href',pendProjectAsset('AUDITORIA_PENDULO_DISTRIBUTIVO.md'));
document.getElementById('pendPerspectiveButtons')?.addEventListener('click',e=>{const b=e.target.closest('button[data-value]');if(!b)return;pendPerspective=b.dataset.value;document.querySelectorAll('#pendPerspectiveButtons .pend-btn').forEach(x=>x.classList.toggle('active',x===b));renderPendMain()});
document.getElementById('pendUniverseButtons')?.addEventListener('click',e=>{const b=e.target.closest('button[data-value]');if(!b)return;pendUniverse=b.dataset.value;document.querySelectorAll('#pendUniverseButtons .pend-btn').forEach(x=>x.classList.toggle('active',x===b));renderPend()});
document.querySelector('[data-tab="tab-pendulo"]')?.addEventListener('click',()=>requestAnimationFrame(renderPend));
window.addEventListener('resize',()=>{if(!pendRendered)return;['pendMainChart','pendSharesChart','pendMandateChart'].forEach(id=>{const el=document.getElementById(id);if(el&&window.Plotly)Plotly.Plots.resize(el)})});
</script>
"""


def make_audit(rows: list[dict], mandates: list[dict], raw: dict) -> tuple[str, dict]:
    modern_closure = []
    for item in raw["modern"]:
        for universe in ("private", "total"):
            source = item[universe]
            closure = source["rta"] + source["imb"] + source["taxes_net"] + source["eeb"]
            modern_closure.append(abs(closure - source["vab"]))
    historical_closure = [abs(row["rta"] + row["imb"] + row["eeb"] - row["vab"]) for row in rows if row["segment"] == "historical"]
    share_errors = [abs(row["share_rta"] + row["share_imb"] + row["share_capital"] - 100) for row in rows]
    identity_errors = [abs(row["pendulo"] - (row["share_households"] - row["share_capital"])) for row in rows]
    modern_periods = {row["period"] for row in rows if row["segment"] == "modern" and row["universe"] == "private"}
    historical_periods = {row["period"] for row in rows if row["segment"] == "historical" and row["universe"] == "private"}
    tests = {
        "modern_period_count_41": len(modern_periods) == 41,
        "historical_year_count_15": len(historical_periods) == 15,
        "no_observations_2008_2015": not any(2008 <= int(row["year"]) <= 2015 for row in rows),
        "modern_accounting_closure_max_abs_lt_1e_3_million_pesos": max(modern_closure) < 1e-3,
        "historical_accounting_closure_max_abs_lt_1e_5": max(historical_closure) < 1e-5,
        "normalized_shares_sum_100": max(share_errors) < 1e-9,
        "pendulum_equals_share_difference": max(identity_errors) < 1e-9,
        "all_values_finite": all(finite(row[key]) for row in rows for key in ("rta", "imb", "eeb", "share_households", "share_capital", "pendulo")),
        "mandates_computed_for_two_universes": len(mandates) == len(MANDATE_ORDER) * 2,
    }
    private_modern = [row for row in rows if row["universe"] == "private" and row["segment"] == "modern"]
    latest = private_modern[-1]
    milei = next(item for item in mandates if item["universe"] == "private" and item["mandate"] == "Javier Milei")
    md = f"""# Auditoría · Péndulo distributivo

Fecha de corte: 2026-08-21  
Fuente principal: INDEC — Cuenta de Generación del Ingreso e Insumo de Mano de Obra.

## Resultado reproducible

- Serie histórica: 1993–2007, anual, economía total y sector privado.
- Serie moderna: 2016-T1–2026-T1, trimestral, economía total y total excluido sector público.
- No hay observaciones ni interpolación para 2008–2015.
- Último dato privado normalizado ({latest['period']}): trabajo/hogares {latest['share_households']:.6f}%; EEB {latest['share_capital']:.6f}%; péndulo {latest['pendulo']:+.6f}.
- Ventana Milei observada ({milei['start_period']} → {milei['end_period']}): cambio {milei['change']:+.6f} puntos del índice.

## Fórmulas

```text
denominador = RTA + IMB + EEB
share_hogares = (RTA + IMB) / denominador × 100
share_capital = EEB / denominador × 100
pendulo = ((RTA + IMB) - EEB) / denominador × 100
```

En el tramo moderno, los otros impuestos netos de subsidios quedan fuera del denominador. En 1993–2007 el archivo indica que otros impuestos a la producción están incluidos en IMB/EEB; no se pueden retirar sin inventar una apertura. Por eso no se trata a ambos segmentos como una serie homogénea.

## Controles automáticos

| Control | Resultado |
|---|---:|
"""
    for name, passed in tests.items():
        md += f"| {name} | {'PASS' if passed else 'FAIL'} |\n"
    md += f"""

Máximo error absoluto de cierre contable moderno: {max(modern_closure):.12g}.  
Máximo error absoluto de cierre contable histórico: {max(historical_closure):.12g}.  
Máximo error de suma de participaciones: {max(share_errors):.12g} puntos porcentuales.

## Asignación por gobierno

- Serie histórica anual: 1993–1999 Menem; 2000–2001 De la Rúa; 2002 Duhalde; 2003–2007 Néstor Kirchner.
- 2002 tiene un único dato anual: no permite inferir movimiento dentro del mandato.
- 2008–2015: sin serie comparable; CFK I y II se muestran como “sin dato”.
- Serie moderna trimestral: 2016–2019 Macri; 2020–2023 Alberto Fernández; 2024–2026-T1 Milei.
- 2023-T4 no se divide por día: se asigna a Alberto Fernández y Milei comienza en 2024-T1.

## Fuentes archivadas

- `data/fuentes/pendulo_distributivo/indec/serie_cgi_07_26.xls`
- `data/fuentes/pendulo_distributivo/indec/cgi_cuadro1_total_1993_2007.xls`
- `data/fuentes/pendulo_distributivo/indec/cgi_apendice4_privado_1993_2007.xls`
- `data/fuentes/pendulo_distributivo/indec/cgi_07_26.pdf`
- `data/fuentes/pendulo_distributivo/metodologia/metodologia_24_cuentas_nacionales.pdf`

El JSON de extracción se genera con `extract_cgi_xls.ps1`. Los CSV, estadísticas por mandato, pruebas y HTML se regeneran con `build_pendulo_tab.py`.
"""
    return md, {"passed": all(tests.values()), "tests": tests, "max_errors": {"modern_closure": max(modern_closure), "historical_closure": max(historical_closure), "share_sum": max(share_errors), "pendulum_identity": max(identity_errors)}}


def main() -> None:
    raw = json.loads(RAW_JSON.read_text(encoding="utf-8"))
    rows = build_rows(raw)
    mandates = build_mandates(rows)
    series_fields = ["date", "period", "year", "quarter", "frequency", "segment", "universe", "president", "vab", "rta", "imb", "taxes_net", "eeb", "share_rta", "share_imb", "share_households", "share_capital", "pendulo", "change_since_mandate_start", "coverage_note", "method_note"]
    mandate_fields = ["universe", "mandate", "start_period", "end_period", "observations", "start", "end", "change", "average", "coverage_note"]
    write_csv(SERIES_CSV, rows, series_fields)
    write_csv(MANDATES_CSV, mandates, mandate_fields)
    audit_md, tests = make_audit(rows, mandates, raw)
    AUDIT_MD.write_text(audit_md, encoding="utf-8")
    TESTS_JSON.write_text(json.dumps(tests, ensure_ascii=False, indent=2), encoding="utf-8")
    update_sources_registry()

    html = SOURCE_HTML.read_text(encoding="utf-8")
    if "PENDULO_DISTRIBUTIVO_TAB_VERSION" in html:
        raise RuntimeError("Source HTML already contains the pendulum tab; build from v135.")
    html = html.replace("</head>", CSS + "\n</head>", 1)
    nav_marker = '    <button class="tab-btn" data-tab="tab-morosidad">Morosidad · ¿la gente puede pagar sus deudas?</button>'
    html = html.replace(nav_marker, nav_marker + '\n    <button class="tab-btn" data-tab="tab-pendulo">Péndulo distributivo</button>', 1)
    section_marker = '  <section id="tab-fiscal" class="tab-panel">'
    html = html.replace(section_marker, SECTION + "\n\n" + section_marker, 1)
    csv_payload = {
        "series": {"filename": SERIES_CSV.name, "content": SERIES_CSV.read_text(encoding="utf-8")},
        "mandates": {"filename": MANDATES_CSV.name, "content": MANDATES_CSV.read_text(encoding="utf-8")},
    }
    script = SCRIPT_TEMPLATE.replace("__PEND_DATA__", json.dumps(rows, ensure_ascii=False, separators=(",", ":"))).replace("__PEND_MANDATES__", json.dumps(mandates, ensure_ascii=False, separators=(",", ":"))).replace("__PEND_CSVS__", json.dumps(csv_payload, ensure_ascii=False, separators=(",", ":")))
    html = html.replace("</body>", script + "\n</body>", 1)
    html = html.replace("const DASHBOARD_SNAPSHOT_CUTOFF = '2026-08-20';", "const DASHBOARD_SNAPSHOT_CUTOFF = '2026-08-21';", 1)
    html = html.replace("cierre editorial · 20 ago 2026", "cierre editorial · 21 ago 2026", 1)
    html = html.replace("queda cerrada al <b>20/08/2026</b>", "queda cerrada al <b>21/08/2026</b>", 1)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(f"Built {OUTPUT_HTML.relative_to(ROOT)}")
    print(f"Rows: {len(rows)} · mandate rows: {len(mandates)} · tests passed: {tests['passed']}")


if __name__ == "__main__":
    main()
