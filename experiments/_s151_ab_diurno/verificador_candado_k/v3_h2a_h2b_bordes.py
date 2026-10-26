# -*- coding: utf-8 -*-
"""Verificador del candado K (PR #858), parte 3: H2a sobre las raíces REALES de C0 y los bordes de H2b.

1. cableado_records sobre las 10 raíces reales (brazos C0, sha del tag s151-diurno-codigo): tiene que ver el Test 1
   (C0 lo tiene encendido) y los records de otros commits (sólo W6 y parte de W5a salieron del tag).
   Cuenta además cuántos records lee contra cuántos hay en los JSON de los brazos.
2. Bordes de H2a: un JSON que no es de volcán en el directorio del brazo; un JSON lista; triggered_test1 = 1 o "true".
3. Bordes de H2b: tabulador o salto de línea en --brazos; brazos K con --base c0 explícito; evaluar() con un
   Namespace sin `brazos` pero con base k.
Uso: python -I v3_h2a_h2b_bordes.py <directorio con W2a ... W6b>
"""
import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import evaluar_diurno as ED  # noqa: E402

SHA_TAG = "eb97779f4c0e1a40df20182a60921c1778bced1a"   # git rev-parse s151-diurno-codigo^{commit}


def main(base):
    raices = [str(Path(base) / w) for w in ("W2a", "W2b", "W3a", "W3b", "W4a", "W4b", "W5a", "W5b", "W6a", "W6b")]
    print("== 1. H2a sobre las raíces reales de C0, sha del tag %s" % SHA_TAG[:12])
    p = ED.cableado_records(raices, SHA_TAG)
    t1 = [x for x in p if "Test 1" in x]
    sha = [x for x in p if "codigo_sha" in x]
    print("   problemas %d (con Test 1 %d archivos, con otro sha %d archivos)" % (len(p), len(t1), len(sha)))
    for x in p[:4]:
        print("      " + x)
    raices_con_sha = sorted({x.split("/")[0] for x in sha})
    total = sum(len(json.loads(f.read_text(encoding="utf-8")).get("records", []))
                for r in raices for b in ED.BRAZOS.values() for f in (Path(r) / b).glob("*.json"))
    print("   records en los JSON de los dos brazos de las 10 raíces: %d" % total)
    por_raiz = {}
    for r in raices:
        q = ED.cableado_records([r], SHA_TAG)
        por_raiz[Path(r).name] = sum(1 for x in q if "codigo_sha" in x)
    print("   archivos con otro sha por raíz: %s" % por_raiz)
    # 1b. sólo el sha: ¿cuántos records de W6 pasan?
    print("   sobre W6a y W6b solos, archivos con otro sha: %d (tienen que ser 0: salieron del tag)" %
          sum(1 for x in ED.cableado_records(raices[-2:], SHA_TAG) if "codigo_sha" in x))

    print("\n== 2. bordes de H2a (directorio temporal)")
    tmp = Path(tempfile.mkdtemp(prefix="v3_h2a_"))
    brazos0 = dict(ED.BRAZOS)
    try:
        ED.BRAZOS.update({"control": "_s154_ab_diurno_k_control", "diurno": "_s154_ab_diurno_k_on"})
        bueno = {"datetime_utc": "2026-07-01 05:00", "sensor": "VIIRS_SNPP", "triggered_test1": False,
                 "final_hotspot_source": "ctx_cluster", "regimen": {"codigo_sha": "a" * 40}}
        for b in ED.BRAZOS.values():
            (tmp / b).mkdir(parents=True)
            (tmp / b / "Lascar.json").write_text(json.dumps({"records": [bueno]}), encoding="utf-8")
        print("   limpio: %s" % ED.cableado_records([str(tmp)], "a" * 40))
        for etq, valor in (("triggered_test1 = 1", 1), ("triggered_test1 = 'true'", "true"), ("triggered_test1 = numpy-like 1.0", 1.0)):
            (tmp / "_s154_ab_diurno_k_on" / "Lascar.json").write_text(json.dumps({"records": [dict(bueno, triggered_test1=valor)]}), encoding="utf-8")
            print("   %-34s -> %s" % (etq, ED.cableado_records([str(tmp)], "a" * 40) or "LIMPIO (no lo ve)"))
        (tmp / "_s154_ab_diurno_k_on" / "Lascar.json").write_text(json.dumps({"records": [bueno]}), encoding="utf-8")
        (tmp / "_s154_ab_diurno_k_on" / "sub").mkdir()
        (tmp / "_s154_ab_diurno_k_on" / "sub" / "Villarrica.json").write_text(json.dumps({"records": [dict(bueno, triggered_test1=True)]}), encoding="utf-8")
        print("   JSON con Test 1 en un subdirectorio del brazo -> %s" % (ED.cableado_records([str(tmp)], "a" * 40) or "LIMPIO (no lo ve; cargar_brazo tampoco lo lee)"))
        (tmp / "_s154_ab_diurno_k_on" / "notas.json").write_text(json.dumps({"x": 1}), encoding="utf-8")
        print("   JSON ajeno sin records en el brazo -> %s" % (ED.cableado_records([str(tmp)], "a" * 40) or "LIMPIO (se ignora)"))
        (tmp / "_s154_ab_diurno_k_on" / "lista.json").write_text(json.dumps([1, 2]), encoding="utf-8")
        try:
            print("   JSON lista en el brazo -> %s" % ED.cableado_records([str(tmp)], "a" * 40))
        except Exception as e:  # noqa: BLE001
            print("   JSON lista en el brazo -> se cae (%s: %s)" % (type(e).__name__, e))
        print("   sha abreviado (12) contra records de 40 -> %d problemas" % len(ED.cableado_records([str(tmp / "x")] + [str(tmp)], "a" * 12)) if False else
              "   sha abreviado (12) contra records de 40 -> %d problemas" % len([x for x in _sin_lista(tmp, "a" * 12)]))
    finally:
        ED.BRAZOS.clear(); ED.BRAZOS.update(brazos0)
        shutil.rmtree(tmp, ignore_errors=True)

    print("\n== 3. bordes de H2b")
    c0 = "_s151_ab_diurno_control,_s151_ab_diurno_on"
    k = "_s154_ab_diurno_k_control,_s154_ab_diurno_k_on"
    for etq, brazos, b in (("C0 con espacio", "_s151_ab_diurno_control, _s151_ab_diurno_on", None),
                           ("C0 con tabulador", "_s151_ab_diurno_control,\t_s151_ab_diurno_on", None),
                           ("K sin --base", k, None), ("K con tabulador sin --base", k.replace(",", ",\t"), None),
                           ("K con --base c0 explícito", k, "c0"), ("C0 con --base k explícito", c0, "k")):
        try:
            r = ED.resolver_base(brazos, b)
        except SystemExit as e:
            r = "SE NIEGA (%s)" % str(e)[:60]
        print("   %-28s -> %s" % (etq, r))
    # el camino de evaluar(): mismo reemplazo de espacios que hace evaluar()
    for etq, brazos in (("evaluar, K con tabulador", k.replace(",", ",\t")),):
        ns = ED.parser().parse_args(["--raiz", "x", "--brazos", brazos])
        try:
            ED.evaluar(ns)
            print("   %s -> corrió" % etq)
        except SystemExit as e:
            print("   %s -> SE NIEGA (%s)" % (etq, str(e)[:80]))
        except Exception as e:  # noqa: BLE001
            print("   %s -> %s: %s" % (etq, type(e).__name__, str(e)[:80]))
    # Namespace armado a mano, sin brazos, con base k
    ns = argparse.Namespace(raiz=["x"], logs=[], base="k", sha_codigo=None, repetidas="", out=None)
    estado0 = dict(ED.REGLA), dict(ED.BRAZOS)
    try:
        ED.evaluar(ns)
    except SystemExit as e:
        print("   evaluar(Namespace sin brazos, base k) -> SystemExit %s" % str(e)[:80])
    except Exception as e:  # noqa: BLE001
        print("   evaluar(Namespace sin brazos, base k) -> %s: %s | REGLA en ese momento %s | BRAZOS %s"
              % (type(e).__name__, str(e)[:70], dict(ED.REGLA), dict(ED.BRAZOS)))
    print("   (antes de llamar: REGLA %s)" % (estado0[0],))


def _sin_lista(tmp, sha):
    (tmp / "_s154_ab_diurno_k_on" / "lista.json").unlink(missing_ok=True)
    return ED.cableado_records([str(tmp)], sha)


if __name__ == "__main__":
    main(sys.argv[1])
