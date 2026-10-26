# -*- coding: utf-8 -*-
"""Pruebas extra de la segunda vuelta del verificador del candado MOD-D (adenda 4). Solo lectura sobre el candado:
reusa fila/base/correr de probar_evaluar_paquete.py y carga evaluar_paquete.py tal como esta en el arbol.
Uso: python -I -B pruebas_extra_r2.py [--modulo ../evaluar_vacio.py]
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
import traceback
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CANDADO = AQUI.parent
RAIZ = CANDADO.parents[1]
sys.path.insert(0, str(CANDADO))
import probar_evaluar_paquete as T  # noqa: E402  (fila, base, correr, g, port, k_slim, Falla, exige)

fila, base, correr, g, port, exige = T.fila, T.base, T.correr, T.g, T.port, T.exige


def res_sintetico(p1="SIN PERDIDA", p2="GANA", p1b=None, m="MEJORA", prot=None, controles_ok=True):
    ok = {"estado": "OK"}
    cob = dict(ok, protegidas_fuera_del_denominador=prot or [])
    ctl = {"k_produccion": dict(ok), "port_s159": dict(ok), "placebo": dict(ok), "contador": dict(ok),
           "cobertura": cob, "blobs": "OK", "manifiesto": dict(ok), "procedencia": dict(ok)}
    if not controles_ok:
        ctl["manifiesto"] = {"estado": "INDECIDIBLE"}
    return {"controles": ctl, "brazos": {"PM": {"p1": {"estado": p1}, "p2": {"estado": p2},
                                                "p1b": {"decide": p1b or []}, "m": {"regla": m}}}}


PK = [{"vol": "Lascar", "dt": "x", "motivo": "volcan_fuera_del_granulo", "k_publica": 1}]
P0 = [{"vol": "Lascar", "dt": "x", "motivo": "escena_invalida", "k_publica": 0}]


# ---------------------------------------------------------------- veredicto() directo: precedencia de la regla (b)
def r01_veredicto_precedencia(E):
    V = E.veredicto
    exige(V(res_sintetico(p1="VETADO", prot=PK)) == "NO CANDIDATO", "P1 veto + protegida fuera debe ser NO CANDIDATO")
    exige(V(res_sintetico(p2="PIERDE", prot=PK)) == "NO CANDIDATO", "P2 PIERDE + protegida fuera debe ser NO CANDIDATO")
    exige(V(res_sintetico(p2="SIN SUSTRATO", prot=PK)) == "INDECIDIBLE", "SIN SUSTRATO + protegida fuera debe ser INDECIDIBLE")
    exige(V(res_sintetico(controles_ok=False, prot=PK)) == "INDECIDIBLE", "control rojo + protegida fuera debe ser INDECIDIBLE")
    for p2 in ("GANA", "EMPATE", "BLOQUEA"):
        exige(V(res_sintetico(p2=p2, prot=PK)) == "DECIDE NICOLÁS", "P2 %s + protegida fuera (K publica) debe ser DECIDE NICOLÁS" % p2)
    exige(V(res_sintetico(p2="GANA", prot=P0)) == "CANDIDATO", "protegida fuera con K callado no decide")
    exige(V(res_sintetico(p2="GANA", prot=[])) == "CANDIDATO", "sin protegidas fuera: CANDIDATO")


# ---------------------------------------------------------------- escenarios completos (node) alrededor de la adenda 4
def r02_p1_veto_y_protegida_fuera(E):
    fs = base() + [fila("Lascar", T.dia(300), "protegida", k=3.0, pm=None, geo5=None, sens=3.0, mirova=3.0),
                   fila("Lascar", T.dia(320), "protegida", k=3.0, pm=None, mirova=3.0,
                        port_estado="volcan_fuera_del_granulo", port=None)]
    r = correr(E, fs)
    exige(r["veredicto"] == "NO CANDIDATO", "P1 veto + protegida fuera: %s" % r["veredicto"])
    exige(len(g(r, "controles", "cobertura", "protegidas_fuera_del_denominador", defecto=[])) == 1, "la fuera no se listo")


def r03_bajo1_fuera_no_decide(E):
    fs = base() + [fila("Lascar", T.dia(321), "bajo1", k=0.5, pm=None, mirova=0.5,
                        port_estado="volcan_fuera_del_granulo", port=None)]
    r = correr(E, fs)
    exige(r["veredicto"] == "CANDIDATO", "bajo1 fuera del denominador no debe decidir: %s" % r["veredicto"])
    exige(g(r, "controles", "cobertura", "protegidas_fuera_del_denominador") == [], "bajo1 entro a la lista de protegidas")
    exige(g(r, "controles", "cobertura", "fuera_del_denominador", "volcan_fuera_del_granulo") == 1, "no se conto el motivo")


def r04_neg_limpio_escena_invalida_k_publica(E):
    fs = base() + [fila("Lascar", T.dia(322), "neg_limpio", k=0.4, pm=None,
                        port={"fisica": dict(port(None), motivo_vacio="escena_invalida")})]
    r = correr(E, fs)
    exige(r["veredicto"] == "CANDIDATO" and g(r, "controles", "cobertura", "protegidas_fuera_del_denominador") == [],
          "negativo con escena invalida y K publicando no debe decidir: %s" % r["veredicto"])


def r05_port_ok_sin_port_es_falla(E):
    fs = base() + [fila("Lascar", T.dia(323), "neg_limpio", port_estado="ok", port=None)]
    r = correr(E, fs)
    c = g(r, "controles", "cobertura", defecto={})
    exige(c.get("estado") == "INDECIDIBLE" and c.get("n_fallas_del_instrumento") == 1
          and c.get("fallas_del_instrumento", [{}])[0].get("motivo") == "falla_port_ok",
          "port vacio con estado ok debe ser falla del instrumento: %s" % {k: c.get(k) for k in ("estado", "fallas_del_instrumento")})


def r06_falla_del_arnes_es_roja(E):
    fs = base() + [dict(fila("Lascar", T.dia(324), "protegida", k=3.0, pm=3.0, mirova=3.0), estado="error")]
    r = correr(E, fs)
    c = g(r, "controles", "cobertura", defecto={})
    exige(c.get("estado") == "INDECIDIBLE" and c.get("n_fallas_del_instrumento") == 1 and r["veredicto"] == "INDECIDIBLE",
          "falla del arnes: %s %s" % (c.get("estado"), r["veredicto"]))
    fs2 = base() + [dict(fila("Lascar", T.dia(325), "protegida", k=3.0, pm=3.0, mirova=3.0), estado="no_bajado")]
    r2 = correr(E, fs2)
    exige(g(r2, "controles", "cobertura", "estado") == "INDECIDIBLE", "no_bajado no puso rojo")


def r07_grilla_incompleta_negativo_cuenta(E):
    fs = base() + [fila("Copahue", T.dia(150), "neg_limpio", pm=0.2, port_grilla="grilla_incompleta")]
    r = correr(E, fs)
    exige(g(r, "brazos", "PM", "p2", "s_b") == 1 and g(r, "controles", "cobertura", "n_evaluables") == len(fs),
          "grilla incompleta en un negativo: s_b %s evaluables %s" % (g(r, "brazos", "PM", "p2", "s_b"),
                                                                   g(r, "controles", "cobertura", "n_evaluables")))


def r08_protegida_fuera_y_p2_pierde(E):
    fs = [x for x in base() if x["vol"] != "Llaima"]
    fs += [fila("Copahue", T.dia(150 + i), "neg_limpio", pm=0.2) for i in range(6)]
    fs += [fila("Lascar", T.dia(326), "protegida", k=3.0, pm=None, mirova=3.0, port_estado="volcan_fuera_del_granulo", port=None)]
    r = correr(E, fs)
    exige(r["veredicto"] == "NO CANDIDATO", "P2 PIERDE + protegida fuera: %s" % r["veredicto"])


def r09_k_publica_de_la_fuera_es_del_runner(E):
    """Documenta de donde sale k_publica en la lista: del runner (pub.K), no del predicado del evaluador."""
    fs = base() + [fila("Lascar", T.dia(327), "protegida", k=3.0, pm=None, mirova=3.0,
                        port_estado="volcan_fuera_del_granulo", port=None, pub={"K": 0, "K33": 0})]
    r = correr(E, fs)
    pf = g(r, "controles", "cobertura", "protegidas_fuera_del_denominador", defecto=[])
    exige(len(pf) == 1 and pf[0].get("k_publica") == 0 and r["veredicto"] == "CANDIDATO",
          "k_publica no es el pub.K del runner (%s, %s)" % (pf, r["veredicto"]))
    exige(g(r, "controles", "k_produccion", "estado") == "OK", "el control 1 no mira esa fila (es lo esperado, documentado)")


# ---------------------------------------------------------------- procedencia y manifiesto (fuera de la bateria)
def _cab(commit):
    sha_html = hashlib.sha256((RAIZ / "frontend/index.html").read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    return {"tipo": "cabecera", "parte": 0, "commit": commit, "blobs": dict(E_BLOBS), "sha256_frontend_index": sha_html}


E_BLOBS = {}


def r10_procedencia(E):
    E_BLOBS.update(E.BLOBS_SELLADOS)
    full = "ff2ced5319e1e40e665e3acda60ca0a4ab041cc5"
    casos = {
        "commit exacto": ([_cab(full)], full, "OK"),
        "sin --commit": ([_cab(full)], None, "INDECIDIBLE"),
        "--commit vacio": ([_cab(full)], "", "INDECIDIBLE"),
        "otro commit": ([_cab(full)], "0" * 40, "INDECIDIBLE"),
        "dos commits": ([_cab(full), _cab("1" * 40)], full, "INDECIDIBLE"),
        "cabecera sin commit": ([_cab(None)], full, "INDECIDIBLE"),
        "prefijo de 7 (documenta: pasa)": ([_cab(full)], full[:7], "OK"),
        "prefijo de 1 (documenta: pasa)": ([_cab(full)], "f", "OK"),
    }
    malos = []
    for nombre, (cab, commit, esperado) in casos.items():
        ext = E.externos_de_entrada({}, cab, [], None, commit)
        est = ext["procedencia"]["estado"]
        print("    procedencia %-34s -> %-12s (esperado %s) %s" % (nombre, est, esperado, "" if est == esperado else "<<"))
        if est != esperado:
            malos.append(nombre)
        if nombre == "commit exacto":
            exige(ext["manifiesto"]["estado"] == "OK" and ext["blobs"]["estado"] == "OK" and ext["predicado"]["estado"] == "OK",
                  "con cabecera buena, manifiesto/blobs/predicado deben dar OK: %s" % {k: ext[k]["estado"] for k in ("manifiesto", "blobs", "predicado")})
    exige(not malos, "procedencia distinta de lo esperado en: %s" % malos)


def r11_manifiesto_ve_una_alteracion(E):
    import manifiesto_candado as MC
    m = json.loads(MC.MANIFIESTO.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as td:
        raiz = Path(td)
        for a in m:
            dst = raiz / a
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(RAIZ / a, dst)
        exige(MC.comprobar(MC.MANIFIESTO, raiz=raiz)["estado"] == "OK", "copia fiel del arbol no da OK")
        # LF puro: el hash tiene que ser el mismo (normaliza)
        p = raiz / "experiments/_s162_modis_paquete/probe_paquete.py"
        p.write_bytes(p.read_bytes().replace(b"\r\n", b"\n"))
        exige(MC.comprobar(MC.MANIFIESTO, raiz=raiz)["estado"] == "OK", "pasar a LF cambio el hash")
        # un byte cambiado en el arnes
        p.write_bytes(p.read_bytes().replace(b"K33", b"K34", 1))
        r = MC.comprobar(MC.MANIFIESTO, raiz=raiz)
        exige(r["estado"] == "INDECIDIBLE" and "experiments/_s162_modis_paquete/probe_paquete.py" in r["distintos"],
              "un byte cambiado en probe_paquete.py no se vio: %s" % r)
        shutil.copy2(RAIZ / "experiments/_s162_modis_paquete/probe_paquete.py", p)
        # un archivo que falta
        (raiz / "experiments/_s162_modis_paquete/grillas.json").unlink()
        r = MC.comprobar(MC.MANIFIESTO, raiz=raiz)
        exige(r["estado"] == "INDECIDIBLE" and r["faltan"] == ["experiments/_s162_modis_paquete/grillas.json"],
              "archivo faltante no se vio: %s" % r)
        # un modulo de otra carpeta (MOD-B) alterado
        shutil.copy2(RAIZ / "experiments/_s162_modis_paquete/grillas.json", raiz / "experiments/_s162_modis_paquete/grillas.json")
        q = raiz / "experiments/_s162_mxd03/probe_mxd03_ab.py"
        q.write_bytes(q.read_bytes() + b"\n# x\n")
        r = MC.comprobar(MC.MANIFIESTO, raiz=raiz)
        exige(r["estado"] == "INDECIDIBLE" and list(r["distintos"]) == ["experiments/_s162_mxd03/probe_mxd03_ab.py"],
              "probe_mxd03_ab.py alterado no se vio: %s" % r)


def r12_manifiesto_rojo_tumba_el_veredicto(E):
    """Un manifiesto INDECIDIBLE en los externos tiene que dar veredicto INDECIDIBLE (via _rojo)."""
    r = correr(E, base(), ext=dict(T.OK_EXT, manifiesto={"estado": "INDECIDIBLE", "distintos": {"x": "y"}}))
    exige(r["veredicto"] == "INDECIDIBLE", "manifiesto rojo no tumbo el veredicto: %s" % r["veredicto"])
    r2 = correr(E, base(), ext=dict(T.OK_EXT, procedencia={"estado": "INDECIDIBLE"}))
    exige(r2["veredicto"] == "INDECIDIBLE", "procedencia roja no tumbo el veredicto: %s" % r2["veredicto"])


def r13_evaluador_usa_el_manifiesto(E):
    """Cableado: externos_de_entrada tiene que tomar el estado de manifiesto_candado.comprobar (si lo ignorara, nada
    del candado lo veria: la bateria no pasa por externos y el ensayo exige manifiesto OK)."""
    import manifiesto_candado as MC
    E_BLOBS.update(E.BLOBS_SELLADOS)
    orig = MC.comprobar
    try:
        MC.comprobar = lambda *a, **k: {"estado": "INDECIDIBLE", "distintos": {"x": "y"}}
        ext = E.externos_de_entrada({}, [_cab("f" * 40)], [], None, "f" * 40)
    finally:
        MC.comprobar = orig
    exige(ext["manifiesto"]["estado"] == "INDECIDIBLE", "el evaluador no toma el estado del manifiesto: %s" % ext["manifiesto"])


PRUEBAS = [v for k, v in sorted(globals().items()) if k.startswith("r") and k[1:3].isdigit()]


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--modulo", default=str(CANDADO / "evaluar_paquete.py"))
    a = ap.parse_args(argv)
    E = T.cargar(a.modulo)
    res = {}
    for t in PRUEBAS:
        try:
            t(E)
            res[t.__name__] = "pasa"
            print("  PASA %s" % t.__name__)
        except T.Falla as e:
            res[t.__name__] = "falla"
            print("  FALLA %s: %s" % (t.__name__, e))
        except Exception as e:  # noqa: BLE001
            res[t.__name__] = "cae"
            print("  CAE %s: %s: %s" % (t.__name__, type(e).__name__, str(e)[:300]))
            print("    " + traceback.format_exc().splitlines()[-3][:300])
    n = {s: sum(1 for v in res.values() if v == s) for s in ("pasa", "falla", "cae")}
    print("%s: pasan %d, fallan %d, caen %d (de %d)" % (Path(a.modulo).name, n["pasa"], n["falla"], n["cae"], len(res)))
    return 0 if n["pasa"] == len(res) else 1


if __name__ == "__main__":
    sys.exit(main())
