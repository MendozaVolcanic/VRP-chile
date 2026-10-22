# -*- coding: utf-8 -*-
"""S160 (hallazgo 245 de docs/AUDIT_S160.md): la copia horaria del consolidado de MIROVA avisa cuando la copia
nueva perdió llaves de la vigente, y el workflow deja la corrida en rojo sin dejar de commitear la copia.

POR QUE: 7 encogimientos en 64 dias, 1.948 filas que no volvieron, 14 protegidas, y nadie se entero. Contar
filas no basta: se comparan llaves (Volcan, Sensor, Fecha_Satelite_UTC). Avisa y no rechaza (decision de
Nicolas): rechazar puede congelar la referencia.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "avisar_llaves_perdidas_consolidado.py"
CAB = ("timestamp,Fecha_Satelite_UTC,Fecha_Captura_Chile,Volcan,Sensor,VRP_MW,Distancia_km,Tipo_Registro,"
       "Clasificacion Mirova")


def _csv(ruta, filas):
    lineas = [CAB] + [f"t,{fecha},c,{vol},{sen},{vrp},1.0,{tipo},x" for fecha, vol, sen, vrp, tipo in filas]
    ruta.write_text("\n".join(lineas) + "\n", encoding="utf-8")


BASE = [("2026-10-01 05:00:00", "Lascar", "MODIS", "2.5", "ALERTA_TERMICA"),
        ("2026-10-01 06:00:00", "Lascar", "VIIRS375", "0.0", "RUTINA"),
        ("2026-10-02 05:00:00", "Villarrica", "VIIRS750", "0.3", "ALERTA_TERMICA_OCR")]


def _correr(tmp_path, vieja, nueva):
    v, n, out = tmp_path / "v.csv", tmp_path / "n.csv", tmp_path / "out.txt"
    _csv(v, vieja)
    _csv(n, nueva)
    r = subprocess.run([sys.executable, str(SCRIPT), str(v), str(n)], capture_output=True, text=True,
                       encoding="utf-8", env={"GITHUB_OUTPUT": str(out), "PYTHONIOENCODING": "utf-8",
                                              "SYSTEMROOT": __import__("os").environ.get("SYSTEMROOT", "")})
    return r, out.read_text(encoding="utf-8") if out.exists() else ""


def test_copia_que_crece_no_pierde_nada(tmp_path):
    r, out = _correr(tmp_path, BASE, BASE + [("2026-10-03 05:00:00", "Isluga", "MODIS", "0.1", "RUTINA")])
    assert r.returncode == 0 and "llaves_perdidas=0" in out


def test_copia_que_pierde_una_protegida_y_una_rutina_lo_cuenta(tmp_path):
    r, out = _correr(tmp_path, BASE, BASE[2:])
    assert r.returncode == 0, "avisa, no rechaza: el rojo lo pone el workflow"
    assert "llaves_perdidas=2" in out
    assert "1 alertas, 1 protegidas" in r.stdout and "Lascar MODIS 2026-10-01 05:00:00" in r.stdout


def test_reordenar_y_quitar_duplicados_no_es_perder(tmp_path):
    """El caso de los siete encogimientos que no perdio filas: menos lineas, mismas llaves."""
    r, out = _correr(tmp_path, BASE + [BASE[0]], list(reversed(BASE)))
    assert "llaves_perdidas=0" in out


def test_el_sync_compara_antes_de_reemplazar_y_el_workflow_pone_el_rojo():
    sh = (ROOT / "scripts" / "sync_mirova_csv.sh").read_text(encoding="utf-8")
    llamada = re.search(r"(?<![A-Za-z0-9_])avisar_llaves_perdidas_consolidado\.py\s+latest_consolidado\.csv\s+"
                        r"latest_consolidado\.csv\.new", sh)
    reemplazo = sh.index("mv latest_consolidado.csv.new latest_consolidado.csv")
    assert llamada and llamada.start() < reemplazo, "la comparacion tiene que ir antes de reemplazar la copia"
    yml = (ROOT / ".github" / "workflows" / "sync-mirova-csv.yml").read_text(encoding="utf-8")
    assert re.search(r"steps\.bajar\.outputs\.llaves_perdidas", yml)
    assert re.search(r"steps\.push\.outputs\.llaves_perdidas", yml), "el bucle de push vuelve a bajar"
