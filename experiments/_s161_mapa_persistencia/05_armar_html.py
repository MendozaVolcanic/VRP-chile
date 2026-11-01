# -*- coding: utf-8 -*-
"""S161: arma artefacto/mapa_persistencia.html desde artefacto_plantilla.html, con el CSS de Leaflet 1.9.4 (cdnjs)
y los datos de 04 incrustados. El visor de Artifacts sólo admite hojas de estilo de Google Fonts, por eso el CSS va
dentro. Las imágenes satelitales quedan como archivos al lado (artefacto/sat_*.jpg).
Uso: python -I 05_armar_html.py
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comun161 as C  # noqa: E402

AQ = Path(__file__).resolve().parent
css = C.SCRATCH / "leaflet" / "leaflet.css"
if not css.exists():
    css.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["curl", "-sSf", "-o", str(css), "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css"], check=True)
html = (AQ / "artefacto_plantilla.html").read_text(encoding="utf-8")
html = html.replace("/*LEAFLET_CSS*/", css.read_text(encoding="utf-8"))
html = html.replace("/*DATOS*/", (AQ / "artefacto" / "datos_mapa.js").read_text(encoding="utf-8"))
out = AQ / "artefacto" / "mapa_persistencia.html"
out.write_text(html, encoding="utf-8")
print(out, f"{out.stat().st_size / 1e6:.2f} MB")
