# -*- coding: utf-8 -*-
"""Prueba que el brazo A1 difiere de produccion SOLO en lo declarado, leyendo pipeline.profile (A89), no el YAML.

Reusa el volcado de experiments/_s146_ab_sin_test1/diff_perfiles.py (cada perfil en su subproceso, porque
pipeline.profile lee VRP_PROFILE una sola vez). Control: el control del A/B contra produccion da 0 diferencias;
el brazo tiene que mostrar exactamente ENABLE_VENT_ANCHORED_CLUSTERING True -> False. Si el brazo diera 0
diferencias, el instrumento no estaria leyendo el perfil y el script falla.

Uso: python experiments/_s151_ab_vrp_max/diff_perfiles.py  ->  diff_perfiles_salida.txt
"""
import importlib.util
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
_spec = importlib.util.spec_from_file_location("dp146", ROOT / "experiments" / "_s146_ab_sin_test1" / "diff_perfiles.py")
dp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dp)

BASE = "mirova_equivalent"
DECLARADO = {"_s146_ab_control": set(), "_s151_ab_vrp_max": {"ENABLE_VENT_ANCHORED_CLUSTERING"}}


def main():
    out = io.StringIO()
    base = dp.volcar(BASE)
    ok = True
    for perfil, esperado in DECLARADO.items():
        d = dp.volcar(perfil)
        difs = {k: [base.get(k), d.get(k)] for k in sorted(set(base) | set(d))
                if base.get(k) != d.get(k) and k not in dp.IDENTIDAD}
        aislado = d.get("DATA_SUBDIR") == perfil
        bien = set(difs) == esperado and aislado
        ok &= bien
        print(f"[{'OK' if bien else 'REVISAR'}] {perfil}: data_subdir {d.get('DATA_SUBDIR')} (aislado {aislado}); "
              f"diferencias contra {BASE}: {json.dumps(difs, sort_keys=True) if difs else 'ninguna'}", file=out)
    print("VEREDICTO:", "cada brazo difiere solo en lo declarado" if ok else "HAY ALGO SIN DECLARAR", file=out)
    txt = out.getvalue()
    print(txt)
    (HERE / "diff_perfiles_salida.txt").write_text(txt, encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
