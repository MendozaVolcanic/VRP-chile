# -*- coding: utf-8 -*-
"""S178 (P10): las cotas de investigación de VIIRS 375 de la regla de reversión, recalculadas con los casos de la
prueba retrospectiva leída con candado (F26-V, R25 y DM), con el MISMO método y el MISMO script que las vigentes.

POR QUÉ. La regla de reversión de las vías (`experiments/_s176_v375e_adopcion/REGLA_REVERSION_V375E_BORRADOR.md`
§4.4, decisión D1) investiga si la vía calla más alertas débiles de MIROVA (Muy Bajo, de 0,05 a 1 MW), o publica
en más negativos limpios, de lo que cabe esperar. Las cotas vigentes (más de 14 y más de 15 en 120 días) salen de
`experiments/_s176_v375e_adopcion/cotas_retrospectiva_v375.py` sobre la ventana O (2026-06-13 a 10-21) del A/B
V375-B y C, con el port y no con la vía de `pipeline/`. La retrospectiva (tag `s178-retro-lectura`) trae los records
reales de la vía y de K en febrero y marzo de 2026 (F26-V), 2025 (R25) y octubre de 2026 (DM).

QUÉ HACE, SIN RED Y SIN TOCAR NADA SELLADO.
  0. Candado: sha256 LF de cada archivo del lector extraído del tag contra `experiments/_s178_lectura/manifiesto.json`
     de la rama `claude/s178-retro-lectura`, y del OSF.
  1. Cotas vigentes: importa el script de S176 sin cambiarlo y repite su cuenta sobre su caché de filas.
  2. Filas de la retrospectiva: arma las pasadas con las funciones del lector (`armar_pasadas`, `etiquetar_tabla`,
     `tabla_publica`, `filas_v375e`), igual que su `main`, pero sólo pasa al predicado del tablero los records de
     VIIRS 375. Control de identidad: la regla de VIIRS 375 sobre F26-V tiene que dar lo mismo que `lectura.json`.
  3. Para cada tramo, las dos discordancias del script de S176 con su mismo predicado: (i) Muy Bajo (no protegida,
     VRP de MIROVA sobre 0,05 MW, clase pos_bajo) que K publica y la vía calla; (ii) neg_resto (negativo limpio que K
     calla) que la vía publica. Peso 1 (la retrospectiva es censo). Tasa por día, llevada a 120 días, cota Poisson con
     falsa alarma de 8 % o menos (funciones `p_mayor` y `cota` del script de S176, importadas).
  4. Las maneras de sumar los casos, cada una con su efecto. El método escrito no dice cómo sumar otra ventana;
     elegir una es de Nicolás.

R25: la tabla de MIROVA no cubre 2025 y el pre-registro dice que el OSF no sirve para contar publicaciones de más
(§4.2); (ii) no existe en R25. Para (i) el pre-registro sólo dice «Bajo 1 MW OSF: informa, con SN por analogía»
(§4.2), sin definición operativa: aquí se calcula UNA lectura posible, rotulada como OPCIÓN NO ESCRITA.

Uso (python -I; las rutas son de sólo lectura):
  python -I experiments/_s178_cotas_v375/cotas_v375_con_retro.py --arbol D:/vrp-trabajo/temporales/s178_cotas/arbol
      --manifiesto <manifiesto.json> --lectura <lectura.json> --via <dir> --k <dir> --osf <csv>
      --cache-s176 <carpeta con filas.json> [--json <salida.json>]
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import importlib.util
import json
import math
import sys
from datetime import date, datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
S176 = RAIZ / "experiments" / "_s176_v375e_adopcion" / "cotas_retrospectiva_v375.py"
PLAZO_FUENTE = "experiments/_s176_v375e_adopcion/cotas_retrospectiva_v375.py"


def sha256_lf(ruta):
    return hashlib.sha256(Path(ruta).read_bytes().replace(b"\r", b"")).hexdigest()


def importar(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = mod
    spec.loader.exec_module(mod)
    return mod


REF_LECTURA = "s178-retro-lectura"
# Lo que el lector necesita del tag: el manifiesto de la lectura no fija frontend/*.js, pero el predicado del tablero
# carga cambio_detector.js (banco_paridad, l. 148): sin él, los filtros de artefacto aplican la regla anterior a S173.
PATHSPECS_ARBOL = ("scripts", ":(glob)experiments/**/*.py", "experiments/_s159/portes", "experiments/_s178_lectura",
                   "pipeline", "frontend/index.html", ":(glob)frontend/*.js", "volcanoes.yaml",
                   "data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado_respaldo_20260408.csv",
                   "data/mirova_reference/union_historica")


def preparar_arbol(arbol, ref=REF_LECTURA):
    """Extrae del tag sólo lo que el lector importa o lee (unos 100 MB), si la carpeta no existe."""
    import subprocess
    import tarfile
    import io
    arbol = Path(arbol)
    if arbol.exists():
        return
    arbol.mkdir(parents=True)
    tar = subprocess.run(["git", "-C", str(RAIZ), "archive", ref, "--", *PATHSPECS_ARBOL], capture_output=True,
                         check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(tar)) as t:
        t.extractall(arbol, filter="data")


def igual_al_tag(arbol, rel, ref=REF_LECTURA):
    import subprocess
    blob = subprocess.run(["git", "-C", str(RAIZ), "show", f"{ref}:{rel}"], capture_output=True, check=True).stdout
    return hashlib.sha256(blob.replace(b"\r", b"")).hexdigest() == sha256_lf(Path(arbol) / rel)


def dias(ini, fin, excluir=()):
    a, b = date.fromisoformat(ini), date.fromisoformat(fin)
    return (b - a).days + 1 - len([d for d in excluir if ini <= d <= fin])


def discordancias(filas, brazo_pub, cond=lambda f: True):
    """Las dos cuentas del script de S176 (sus líneas `mb_base`, `mb`, `neg_base`, `neg`), con el brazo como función."""
    o = [f for f in filas if cond(f)]
    mb_base = [f for f in o if f["c"] == "pos_bajo" and not f["prot"] and f["mir"] > 0.05]
    mb = [f for f in mb_base if f["K"] and not brazo_pub(f)]
    neg_base = [f for f in o if f["c"] == "neg_resto"]
    neg = [f for f in neg_base if brazo_pub(f)]
    return {"i_num": len(mb), "i_den": len(mb_base), "i_w": sum(f["w"] for f in mb),
            "i_den_w": sum(f["w"] for f in mb_base),
            "ii_num": len(neg), "ii_den": len(neg_base), "ii_w": sum(f["w"] for f in neg),
            "ii_den_w": sum(f["w"] for f in neg_base),
            "i_lista": [(f["vol"], f["hora"], round(f["mir"], 3)) for f in mb],
            "ii_lista": [(f["vol"], f["hora"]) for f in neg]}


def linea_cota(S, etiqueta, w, d, plazo):
    lam = w * plazo / d if d else float("nan")
    c = S.cota(lam)
    return lam, c, S.p_mayor(lam, c), (f"{etiqueta}: ponderado {w:.1f} en {d} días; lambda {plazo} d = {lam:.2f}; "
                                       f"cota (falsa alarma <= {S.FALSA_ALARMA_MAX}) = {c} (falsa alarma {S.p_mayor(lam, c):.3f})")


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    ap = argparse.ArgumentParser()
    for x in ("--arbol", "--manifiesto", "--lectura", "--via", "--k", "--osf", "--cache-s176"):
        ap.add_argument(x, required=True)
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    arbol = Path(a.arbol)
    preparar_arbol(arbol)
    out = {}

    # ------------------------------------------------------------ 0. candado
    man = json.loads(Path(a.manifiesto).read_text(encoding="utf-8"))
    malos, vistos = {}, 0
    for rel, s in man.items():
        p = Path(a.osf) if rel.endswith("VRP_GLOBAL_ARCHIVE_2025.csv") else arbol / rel
        if not p.exists():
            malos[rel] = "falta"
            continue
        vistos += 1
        if sha256_lf(p) != s:
            malos[rel] = sha256_lf(p)
    print(f"== 0. candado: {vistos} de {len(man)} archivos del manifiesto de la lectura con su sha256 LF; distintos: "
          f"{malos or 'ninguno'}")
    js = ("frontend/cambio_detector.js", "frontend/cese_plataformas.js", "frontend/periodo.js")
    js_ok = {r: (arbol / r).exists() and igual_al_tag(arbol, r) for r in js}
    print(f"   fuera del manifiesto, iguales a {REF_LECTURA}: {js_ok}")
    if malos or not all(js_ok.values()):
        raise SystemExit("CANDADO ROJO")
    print(f"   script de S176: {PLAZO_FUENTE} sha256 LF {sha256_lf(S176)[:16]}; caché de filas "
          f"{sha256_lf(Path(a.cache_s176) / 'filas.json')[:16]}; lectura.json {sha256_lf(a.lectura)[:16]}")

    # ------------------------------------------------------------ 1. cotas vigentes (script de S176, sin cambio)
    sys.argv = [str(S176), a.cache_s176]
    S = importar("cotas_s176", S176)
    filas_o = S.filas_del_evaluador()           # lee la caché; no corre el evaluador
    dias_o = dias("2026-06-13", "2026-10-21") - 6   # la misma cuenta de S176 (6 días excluidos de evaluar.py)
    brazo_o = lambda f: f["brazo"]              # noqa: E731  (C13, «cercano»)
    sin_snpp = lambda f: "SNPP" not in (f.get("sat") or "")   # noqa: E731
    en_o = lambda f: f["tramo"] in ("O1", "O2")  # noqa: E731
    print(f"\n== 1. cotas vigentes (S176): filas {len(filas_o)}; ventana O {dias_o} días")
    viejas = {}
    for nom, cond in (("tres plataformas", en_o), ("NOAA-20 y NOAA-21", lambda f: en_o(f) and sin_snpp(f))):
        d = discordancias(filas_o, brazo_o, cond)
        li = linea_cota(S, "(i)", d["i_w"], dias_o, S.PLAZO)
        lii = linea_cota(S, "(ii)", d["ii_w"], dias_o, S.PLAZO)
        viejas[nom] = {"d": d, "i": li[:3], "ii": lii[:3]}
        print(f"  [{nom}] (i) Muy Bajo que K publica y C13 calla: crudo {d['i_num']} de {d['i_den']} "
              f"(denominador ponderado {d['i_den_w']:.1f}); {li[3]}")
        print(f"  [{nom}] (ii) neg_resto que C13 publica: crudo {d['ii_num']} de {d['ii_den']} "
              f"(denominador ponderado {d['ii_den_w']:.1f}); {lii[3]}")
    out["viejas"] = viejas

    # ------------------------------------------------------------ 2. filas de la retrospectiva (funciones del lector)
    sys.argv = ["leer_retro.py"]
    L = importar("leer_retro_s178", arbol / "experiments/_s172_retro_paquete/leer_retro.py")
    R = L.Reglas()                               # vuelve a comprobar el sha256 de las reglas selladas
    import banco_paridad as bp                   # el del árbol del tag (sys.path lo pone leer_retro)
    from referencia_mirova_unificada import cargar_referencia_unificada
    assert Path(bp.__file__).resolve().is_relative_to(arbol.resolve()), bp.__file__
    via, rep_v = L.cargar_carpeta(a.via)
    k, rep_k = L.cargar_carpeta(a.k)
    coords = bp._coords_por_volcan()
    inner = bp.inner_desde_html()
    es_noche = lambda vol, b, dt: not bp.es_pasada_diurna_descartada(b, coords[vol][0], coords[vol][1], dt)  # noqa: E731
    filas = L.armar_pasadas(via, k, None, es_noche, inner, [])
    no_r25 = [f for f in filas if f["tramo"] != "R25"]
    cons = arbol / "experiments/_s178_lectura/_congelado/registro_vrp_consolidado.csv"
    ocr = arbol / "experiments/_s178_lectura/_congelado/registro_vrp_ocr.csv"
    ref = cargar_referencia_unificada(cons, ocr)
    L.etiquetar_tabla(no_r25, ref, coords)       # sobre las pasadas de los tres sensores, como main (misma ventana)
    for f in filas:
        f.setdefault("lab", "sin_info")
        f.setdefault("vrp_mirova", None)
    v375 = [f for f in filas if f["b"] == "VIIRS375"]
    L.tabla_publica(R, v375, L._predicado_por_defecto(R))
    print(f"\n== 2. retrospectiva, VIIRS 375: {len(v375)} pasadas nocturnas en los tramos; repetidas via {len(rep_v)}, "
          f"K {len(rep_k)}; por tramo y estado: "
          f"{dict(collections.Counter((f['tramo'], f['estado'].split(':')[0]) for f in v375))}")

    # control de identidad: la regla de VIIRS 375 en F26-V tiene que ser la de lectura.json
    lec = json.loads(Path(a.lectura).read_text(encoding="utf-8"))["sensores"]["VIIRS375"]
    f26 = [f for f in v375 if f["tramo"] == "F26-V"]
    rg = L.regla_v375(R, f26, "V-cercano")
    mio = {kk: rg[kk] for kk in ("p2", "B", "neto", "p2_lejana", "silencio", "m", "m_n", "N_neg", "_fila_regla")}
    suyo = {kk: lec["regla"][kk] for kk in mio}
    et = dict(collections.Counter(f.get("lab") for f in L._ev(f26)))
    ok_id = (json.dumps(mio, sort_keys=True) == json.dumps(suyo, sort_keys=True) and et == lec["etiquetas"]
             and len(f26) == lec["n_pasadas"] and len(L._ev(f26)) == lec["n_evaluables"])
    print(f"   control de identidad contra lectura.json (regla V-cercano en F26-V, etiquetas, pasadas): "
          f"{'IGUAL' if ok_id else 'DISTINTO'}")
    print(f"     aquí {mio} etiquetas {et} pasadas {len(f26)} evaluables {len(L._ev(f26))}")
    print(f"     lectura {suyo} etiquetas {lec['etiquetas']} pasadas {lec['n_pasadas']} evaluables {lec['n_evaluables']}")
    if not ok_id:
        raise SystemExit("CONTROL DE IDENTIDAD ROJO: las filas no son las de la lectura")
    out["identidad"] = ok_id

    # ------------------------------------------------------------ 3. discordancias por tramo
    xs = {t: L.filas_v375e([f for f in v375 if f["tramo"] == t]) for t in ("F26-V", "DM")}
    dias_t = {"F26-V": dias(*L.TRAMOS["F26-V"][:2]), "DM": dias(*L.TRAMOS["DM"][:2], excluir=L.DM_SIN_VIIRS)}
    sats = (("tres plataformas", lambda f: True), ("NOAA-20 y NOAA-21", sin_snpp),
            ("sólo NOAA-20", lambda f: "NOAA20" in (f.get("sensor") or "")))
    for x in xs.values():
        for f in x:
            f["sat"] = f["sensor"]
    print("\n== 3. discordancias de la retrospectiva con el predicado de S176 (peso 1: censo)")
    nuevas = {}
    for t, x in xs.items():
        print(f"  {t}: {L.TRAMOS[t][0]} a {L.TRAMOS[t][1]}, {dias_t[t]} días; filas con clase {len(x)}; "
              f"por satélite {dict(collections.Counter(f['sensor'] for f in x))}")
        for brazo in ("V-cercano", "V"):
            for nom, cond in sats:
                d = discordancias(x, lambda f, b=brazo: f["X"][b], cond)
                li = linea_cota(S, "(i)", d["i_w"], dias_t[t], S.PLAZO)
                lii = linea_cota(S, "(ii)", d["ii_w"], dias_t[t], S.PLAZO)
                nuevas[(t, brazo, nom)] = {"d": d, "i": li[:3], "ii": lii[:3]}
                print(f"    [{brazo} | {nom}] (i) {d['i_num']} de {d['i_den']}; (ii) {d['ii_num']} de {d['ii_den']}; "
                      f"sola: (i) lambda {li[0]:.2f} cota {li[1]}; (ii) lambda {lii[0]:.2f} cota {lii[1]}")
                if brazo == "V-cercano" and nom == "tres plataformas":
                    print(f"      (i): {d['i_lista']}")
                    print(f"      (ii): {d['ii_lista']}")
    out["nuevas"] = {"|".join(kk): v for kk, v in nuevas.items()}
    # Control del instrumento (A110), el mismo de S176: K contra K da 0; un brazo que nunca publica pierde algo.
    x = xs["F26-V"]
    kk_ = discordancias(x, lambda f: f["K"])
    mudo = discordancias(x, lambda f: False)
    print(f"  control F26-V: K contra K (i) {kk_['i_num']} y (ii) {kk_['ii_num']} (tienen que ser 0); brazo mudo (i) "
          f"{mudo['i_num']} (tiene que ser mayor que 0)")
    if kk_["i_num"] or kk_["ii_num"] or not mudo["i_num"]:
        raise SystemExit("CONTROL DEL INSTRUMENTO ROJO")

    # R25: sólo (i), con una lectura NO ESCRITA del «Bajo 1 MW OSF»
    vol = {v["name"]: v for v in __import__("yaml").safe_load((arbol / "volcanoes.yaml").read_text(encoding="utf-8"))
           ["volcanoes"]}
    osf = [o for o in L.leer_osf(a.osf, vol, es_noche) if o["b"] == "VIIRS375"]
    r25 = [f for f in v375 if f["tramo"] == "R25" and f["estado"] != "sobra_en_via"]
    idx = collections.defaultdict(list)
    for f in r25:
        idx[f["vol"]].append(f)
    base, perd, sin_par, no_eval = [], [], 0, 0
    for o in osf:
        if not (o["noche"] and o["class"] == 1 and o["dist_crater_km"] <= o["inner"] and 0.05e6 < o["vrp_w"] < 1e6):
            continue
        cand = [f for f in idx.get(o["vol"], []) if abs((L._dt(f["dt"]) - o["dt"]).total_seconds()) <= L.VENTANA_S]
        if not cand:
            sin_par += 1
            continue
        f = cand[0]
        if not f.get("_evaluable"):
            no_eval += 1
            continue
        base.append((o, f))
        if L._pub(f, "K") and not L._pub(f, "V-cercano"):
            perd.append((o["vol"], o["dt"].strftime("%Y-%m-%d %H:%M"), round(o["vrp_w"] / 1e6, 3), f["sensor"]))
    d_r25 = dias(*L.TRAMOS["R25"][:2])
    lr = linea_cota(S, "(i) R25", len(perd), d_r25, S.PLAZO)
    print(f"\n  R25 (OPCIÓN NO ESCRITA: fila OSF nocturna, class 1, píxel más caliente dentro del radio interno, "
          f"0,05 MW < VRP < 1 MW, pareada a ±{L.VENTANA_S} s): {len(base)} con pasada evaluable "
          f"(sin pasada {sin_par}, no evaluables {no_eval}); K publica y la vía (cercano) calla: {len(perd)}; "
          f"{d_r25} días; sola: lambda {lr[0]:.2f} cota {lr[1]}")
    print(f"    por satélite de la base: {dict(collections.Counter(f['sensor'] for _, f in base))}; pérdidas: {perd[:15]}")
    print("    (ii) en R25: no existe (el OSF no trae negativos limpios, pre-registro §4.2)")
    out["r25"] = {"base": len(base), "perdidas": perd, "sin_par": sin_par, "no_eval": no_eval, "dias": d_r25,
                  "lambda": lr[0], "cota": lr[1]}

    # ------------------------------------------------------------ 4. maneras de sumar, con su efecto
    print("\n== 4. maneras de sumar los casos (ninguna está escrita; decide Nicolás). Plazo 120 días, falsa alarma "
          f"<= {S.FALSA_ALARMA_MAX}, régimen NOAA-20 y NOAA-21 salvo que se diga")
    vo = viejas["NOAA-20 y NOAA-21"]["d"]
    vo3 = viejas["tres plataformas"]["d"]
    f2 = nuevas[("F26-V", "V-cercano", "NOAA-20 y NOAA-21")]["d"]
    f3 = nuevas[("F26-V", "V-cercano", "tres plataformas")]["d"]
    dm = nuevas[("DM", "V-cercano", "NOAA-20 y NOAA-21")]["d"]
    op = {}

    def opcion(nombre, wi, wii, dd, nota, dd_ii=None):
        dd_ii = dd if dd_ii is None else dd_ii
        li = linea_cota(S, "(i)", wi, dd, S.PLAZO)
        lii = linea_cota(S, "(ii)", wii, dd_ii, S.PLAZO)
        op[nombre] = {"i": li[:3], "ii": lii[:3], "dias": dd, "dias_ii": dd_ii, "nota": nota}
        print(f"  {nombre}: (i) {li[3]}\n  {' ' * len(nombre)}  (ii) {lii[3]}\n  {' ' * len(nombre)}  {nota}")

    opcion("A. vigente (sólo O)", vo["i_w"], vo["ii_w"], dias_o, "lo sellable hoy en el borrador")
    opcion("B. O + F26-V por día", vo["i_w"] + f2["i_w"], vo["ii_w"] + f2["ii_w"], dias_o + dias_t["F26-V"],
           "suma conteos y días; F26-V aporta NOAA-20 (NOAA-21 queda sin_info antes de abril) y la tabla expone menos "
           "pasadas VIIRS por noche antes de abril (A119 b): baja la tasa por día")
    fr = nuevas[("F26-V", "V", "NOAA-20 y NOAA-21")]["d"]
    opcion("B-rad. como B, con F26-V en el brazo radiante", vo["i_w"] + fr["i_w"], vo["ii_w"] + fr["ii_w"],
           dias_o + dias_t["F26-V"], "el record de la vía publica hoy con radiante (pre-registro §5.1); O sigue en C13 "
           "cercano porque el port de V375-B y C no tiene ese brazo")
    opcion("B3. O + F26-V por día, tres plataformas", vo3["i_w"] + f3["i_w"], vo3["ii_w"] + f3["ii_w"],
           dias_o + dias_t["F26-V"], "como B con Suomi NPP (que terminó el 2026-11-02, A104)")
    # C: tasa por pasada de la clase (O ponderado + F26-V), llevada al número de pasadas de la clase que O espera por día
    for nom_c, a_i, a_ii in (("C. O + F26-V por pasada de la clase", f2, f2),):
        ti = (vo["i_w"] + a_i["i_num"]) / (vo["i_den_w"] + a_i["i_den"])
        tii = (vo["ii_w"] + a_ii["ii_num"]) / (vo["ii_den_w"] + a_ii["ii_den"])
        opcion(nom_c, ti * vo["i_den_w"], tii * vo["ii_den_w"], dias_o,
               f"tasa por pasada Muy Bajo {ti:.4f} y por neg_resto {tii:.4f} (O ponderado + F26-V crudo), por las "
               f"pasadas de cada clase que O tiene en sus {dias_o} días ({vo['i_den_w']:.1f} y {vo['ii_den_w']:.1f}): "
               "no depende de cuántas pasadas expone la tabla por noche")
    opcion("D. O + DM por día (DM está dentro de O)", vo["i_w"] + dm["i_w"], vo["ii_w"] + dm["ii_w"],
           dias_o + dias_t["DM"], "cuenta dos veces del 1 al 16 de octubre; el pre-registro dice que DM es control de "
           "montaje, no evidencia (§3.2)")
    perd_n20 = [p for p in perd if "SNPP" not in p[3]]
    opcion("E. B + R25 en (i) por día", vo["i_w"] + f2["i_w"] + len(perd_n20), vo["ii_w"] + f2["ii_w"],
           dias_o + dias_t["F26-V"] + d_r25,
           f"R25 entra sólo a (i), con la lectura NO ESCRITA del OSF (filtrado y reprocesado, A105), sólo NOAA-20 "
           f"({len(perd_n20)} de {len(perd)} pérdidas; el resto es Suomi NPP); (ii) queda como en B",
           dd_ii=dias_o + dias_t["F26-V"])
    out["opciones"] = op
    if a.json:
        Path(a.json).write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("\nsalida 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
