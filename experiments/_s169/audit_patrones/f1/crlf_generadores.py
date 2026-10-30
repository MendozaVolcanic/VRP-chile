# Auditoría S169 f1 (P-A): ¿los archivos que escribe el generador en Windows llevan CRLF, y cuáles se hashean?
# Replica EXACTAMENTE las dos llamadas de escritura: objetivos_v750b.py l.117-118 (json.dumps sin indent + write_text) y
# 01_poblacion.py l.143-147 (json.dumps indent=0 + write_text). Control positivo: el de indent=0 DEBE traer CR.
# Pregunta 2: si Path.write_text no tradujera, ambos darían 0 CR; el control positivo lo distingue.
import json, hashlib, tempfile, shutil
from pathlib import Path
d = Path(tempfile.mkdtemp(dir="D:/vrp-trabajo/temporales/s169_audit_patrones/f1_v750"))
pob = [{"volcan": "Lascar", "hora_utc": "2026-10-01 05:00", "mirova": [{"tipo": "ALERTA", "x": "a\nb\r\nc"}]}] * 3
texto = json.dumps(pob, ensure_ascii=False, default=str)                    # objetivos_v750b.py l.117
(d / "objetivos.json").write_text(texto, encoding="utf-8")                   # l.118
poblacion = json.dumps({"meta": {}, "pasadas": pob}, ensure_ascii=False, indent=0, default=str)   # 01_poblacion.py l.143-147
(d / "poblacion.json").write_text(poblacion, encoding="utf-8")
for n in ("objetivos.json", "poblacion.json"):
    b = (d / n).read_bytes()
    print(f"{n:16s} CR={b.count(b'\r')} LF={b.count(b'\n')} sha256(bytes)={hashlib.sha256(b).hexdigest()[:12]} "
          f"sha256(texto LF)={hashlib.sha256((texto if n=='objetivos.json' else poblacion).encode('utf-8')).hexdigest()[:12]}")
shutil.rmtree(d)
