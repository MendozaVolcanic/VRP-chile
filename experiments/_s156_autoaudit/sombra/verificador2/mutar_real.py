"""C5 complemento: efecto de las mutaciones sobrevivientes sobre la corrida REAL (referencia del 2026-10-19).
Aplica cada mutación en la copia, corre correr.py, resume y restaura. Uso: python mutar_real.py <copia> <ref> <out>"""
import json
import os
import subprocess
import sys
from pathlib import Path

copia, ref, out = sys.argv[1:4]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mutar_propio_defs as defs  # noqa: E402

p = Path(copia) / "scripts" / "vigilancia_sombra.py"
orig = p.read_text(encoding="utf-8")
aqui = os.path.dirname(os.path.abspath(__file__))


def correr(nombre):
    o = os.path.join(out, nombre)
    os.makedirs(o, exist_ok=True)
    r = subprocess.run([sys.executable, os.path.join(aqui, "correr.py"), copia, ref, o], capture_output=True,
                       text=True, encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    if r.returncode:
        return f"CAE rc={r.returncode}: {r.stderr.strip().splitlines()[-1][:150]}"
    d = json.load(open(os.path.join(o, "sombra_latest.json"), encoding="utf-8"))
    ret = d.get("retrospectivo") or {}
    return (f"veredicto={d['veredicto']} reversion={[(x['volcano'], x['sensor'], x['fecha_utc']) for x in d.get('reversion', [])]} "
            f"retro_vistas={ret.get('protegidas_vistas_en_sombra')} retro_calla={[(x['volcano'], x['sensor'], x['fecha_utc']) for x in ret.get('protegidas_que_la_sombra_publica_y_k_calla', [])]} "
            f"retro_muybajo={ret.get('muy_bajo_que_la_sombra_publica_y_k_calla')} n_pasadas={d.get('n_pasadas_alerta')} "
            f"con_sombra={d.get('n_pasadas_alerta_con_sombra')} neg={(d.get('negativos_VIIRS375') or {}).get('n')} "
            f"avisos={len(d.get('avisos', []))} {[a[:60] for a in d.get('avisos', [])]}")


try:
    print("ORIGINAL", correr("original"))
    for nombre in sys.argv[4:] or defs.MUT:
        txt = orig
        for a, b in defs.MUT[nombre]:
            assert txt.count(a) == 1, (nombre, a)
            txt = txt.replace(a, b)
        p.write_text(txt, encoding="utf-8", newline="\n")
        print(nombre, correr(nombre))
finally:
    p.write_text(orig, encoding="utf-8", newline="\n")
