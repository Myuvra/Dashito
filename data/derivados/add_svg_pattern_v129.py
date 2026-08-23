#!/usr/bin/env python3
"""Agrega el patrón SVG provisto por la usuaria a todas las pestañas del dashboard.

La imagen queda embebida en el HTML para conservar el carácter autocontenido del
dashboard. La v128 permanece intacta y se genera una nueva v129.
"""

from __future__ import annotations

import base64
import hashlib
import re
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parents[1]
INPUT_HTML = DATA_DIR / "dashboard_kawaii_128_pinza_financiera_auditada.html"
OUTPUT_HTML = DATA_DIR / "dashboard_kawaii_129_fondo_patron_svg.html"
SOURCE_SVG = Path(
    r"C:\Users\miyur\Downloads\95046d2f-9772-4a81-b56f-be50c35b9823.svg"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean_svg(source: str) -> str:
    lowered = source.lower()
    forbidden = ("<script", "<foreignobject", "onload=", "onclick=", "<image")
    if any(token in lowered for token in forbidden):
        raise RuntimeError("El SVG contiene elementos activos o embebidos no admitidos")
    if re.search(r"\b(?:href|xlink:href)\s*=", source, flags=re.I):
        raise RuntimeError("El SVG contiene referencias externas no admitidas")

    cleaned = re.sub(r"^\s*<\?xml.*?\?>\s*", "", source, count=1, flags=re.S)
    cleaned = re.sub(r"^\s*<!DOCTYPE.*?>\s*", "", cleaned, count=1, flags=re.S)
    cleaned = cleaned.strip()
    if cleaned.count("<svg") != 1 or not cleaned.endswith("</svg>"):
        raise RuntimeError("No se pudo validar la estructura del SVG")
    return cleaned.replace(
        "<svg ",
        '<svg opacity="0.18" aria-hidden="true" focusable="false" ',
        1,
    )


def main() -> None:
    if not INPUT_HTML.exists():
        raise RuntimeError(f"No existe el HTML de entrada: {INPUT_HTML}")
    if not SOURCE_SVG.exists():
        raise RuntimeError(f"No existe el SVG provisto: {SOURCE_SVG}")
    if OUTPUT_HTML.exists():
        raise RuntimeError(f"La salida ya existe y no se sobrescribirá: {OUTPUT_HTML}")

    html = INPUT_HTML.read_text(encoding="utf-8")
    svg = clean_svg(SOURCE_SVG.read_text(encoding="utf-8"))
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    source_hash = sha256(SOURCE_SVG)

    css = f'''\n<style id="global-tab-svg-pattern-v129">
/* Patrón provisto por la usuaria · SHA-256 {source_hash} */
.tab-panel{{
  background-image:url("data:image/svg+xml;base64,{encoded}");
  background-repeat:repeat;
  background-position:12px 16px;
  background-size:clamp(320px,32vw,470px) auto;
}}
@media(max-width:720px){{
  .tab-panel{{background-position:0 12px;background-size:300px 300px}}
}}
</style>
'''

    if html.count("</head>") != 1:
        raise RuntimeError("No se encontró un cierre único de <head>")
    output = html.replace("</head>", css + "</head>", 1)
    if output.count("global-tab-svg-pattern-v129") != 1:
        raise RuntimeError("El bloque del patrón no quedó insertado una sola vez")
    if output.count('class="tab-panel') < 20:
        raise RuntimeError("No se reconoció la estructura esperada de pestañas")

    OUTPUT_HTML.write_text(output, encoding="utf-8", newline="\n")
    print(f"Creado: {OUTPUT_HTML}")
    print(f"Patrón SVG: {SOURCE_SVG}")
    print(f"SHA-256: {source_hash}")


if __name__ == "__main__":
    main()
