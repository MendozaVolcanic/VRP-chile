# -*- coding: utf-8 -*-
"""S126 — veredicto del A/B de la máscara de nube. Escrito ANTES del resultado (A16).

⚠️ Este A/B **no decide si apagarla: valida algo que ya está vivo**. El PR #535 la
apagó en producción el 2026-08-28 creyendo que era no-op (el YAML dice 0.0 desde S29 y
el comentario afirmaba 260.0). Ver docs/S126_CLOUDMASK_YA_ESTA_VIVA.md.

Así que la pregunta no es "¿la apagamos?" sino **"¿cuánto cuesta tenerla apagada, y ese
costo justifica revertir?"**.

    brazo ON  (_s125_cloudmask_on,  260 K) = como era ANTES del merge
    brazo OFF (_s125_cloudmask_off, 0.0)   = como está HOY en producción

LO QUE HAY QUE MEDIR — las dos caras, escritas en la cabecera de los propios perfiles:

  (+) **Recupera noches ciegas.** Con la máscara, en noches de nieve a altura el filtro
      descartaba el ROI entero y no quedaba ni el t_max del cráter: el record decía "sin
      señal" cuando en realidad no se miró. Medido en producción: 82 de 420 pasadas en
      18 días.
  (−) **Puede meter topes de nube fríos en el anillo de fondo**, bajando `t_bg` e
      inflando la magnitud. Ésta es la cara que hay que cuantificar, porque es la razón
      por la que la máscara existía.

Criterios, estratificados POR VOLCÁN (lección central de S126):

  1. Noches ciegas recuperadas: cuántas, y si en ellas hay señal real o nada.
  2. Magnitud contra MIROVA por volcán: OFF no debe sacar a nadie de banda.
  3. `t_bg` en las noches donde la máscara SÍ descartaba: cuánto baja.
  4. Detecciones sin contraparte MIROVA: cuántas agrega OFF (no son "FP" sin más — A54
     —, pero el delta importa).
  5. Recall sobre noches que MIROVA confirma.

Persiste en 02_veredicto.json.
"""
import io
import json
import os
import statistics as st
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _s126_lib import (ROOT, BANDA, bucket, cargar_brazo, cargar_mirova,   # noqa: E402
                       en_banda, ic95, interseccion, marca, pares_por_noche, resumen)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

VENTANA = ("2026-06-25", "2026-08-24")
BRAZOS = {"ON_260K": "_s125_cloudmask_on", "OFF_hoy": "_s125_cloudmask_off"}
VOLS = ["NevadosDeChillan", "Villarrica", "Lascar"]

mir, diurnas = cargar_mirova(VENTANA)
disp = {n: s for n, s in BRAZOS.items() if os.path.isdir(os.path.join(ROOT, "data", s))}
if len(disp) < 2:
    print("faltan brazos (%s). Nada que evaluar todavia." % ", ".join(disp) or "ninguno")
    sys.exit(0)

print("VEREDICTO DEL A/B DE LA MASCARA DE NUBE — %s a %s" % VENTANA)
print("ON = 260 K (como antes del merge de #535) · OFF = 0.0 (como esta HOY en produccion)")
print("alertas diurnas de MIROVA descartadas (A76): %d\n" % diurnas)

datos, pasadas = {}, {}
for nom, sub in disp.items():
    datos[nom], pasadas[nom] = {}, {}
    for vol in VOLS:
        d = cargar_brazo(sub, vol, VENTANA)
        if d is not None:
            datos[nom][vol], pasadas[nom][vol] = d, set(d)
comunes = {vol: interseccion([pasadas[n].get(vol) for n in disp]) for vol in VOLS}

res = {"ventana": list(VENTANA), "brazos": list(disp), "por_volcan": {}, "criterios": {}}

# ── 1. noches ciegas ─────────────────────────────────────────────────────────
print("1. NOCHES CIEGAS (fondo = 0 pixeles: el record dice 'sin senal' sin haber mirado)")
print("%-22s %10s %10s %14s %16s" %
      ("volcan", "pasadas", "ciegas ON", "ciegas OFF", "recuperadas"))
tot_rec = 0
for vol in VOLS:
    if vol not in datos.get("ON_260K", {}):
        continue
    ci = {n: 0 for n in disp}
    recuperadas_con_senal = 0
    for k in comunes[vol]:
        for n in disp:
            nbg = datos[n][vol][k].get("diag_n_bg_used_first_pass")
            if nbg is not None and nbg == 0:
                ci[n] += 1
        on_ciega = (datos["ON_260K"][vol][k].get("diag_n_bg_used_first_pass") == 0)
        off_ve = (datos["OFF_hoy"][vol][k].get("diag_n_bg_used_first_pass") or 0) > 0
        if on_ciega and off_ve:
            if (datos["OFF_hoy"][vol][k].get("primary_cluster") or {}).get("vrp_mw"):
                recuperadas_con_senal += 1
    rec = ci["ON_260K"] - ci["OFF_hoy"]
    tot_rec += rec
    res.setdefault("por_volcan", {}).setdefault(vol, {})["ciegas"] = {
        "pasadas": len(comunes[vol]), "ON": ci["ON_260K"], "OFF": ci["OFF_hoy"],
        "recuperadas": rec, "recuperadas_con_deteccion": recuperadas_con_senal}
    print("%-22s %10d %10d %14d %10d (%d con deteccion)"
          % (vol, len(comunes[vol]), ci["ON_260K"], ci["OFF_hoy"], rec, recuperadas_con_senal))
res["criterios"]["1_noches_ciegas_recuperadas"] = tot_rec

# ── 2. magnitud por volcan ───────────────────────────────────────────────────
print("\n2. MAGNITUD CONTRA MIROVA (VIIRS375), POR VOLCAN — banda [%.1f-%.1f]" % BANDA)
print("%-22s %6s %14s %14s" % ("volcan", "n", "ON (antes)", "OFF (hoy)"))
salidos = []
for vol in VOLS:
    if vol not in datos.get("ON_260K", {}):
        continue
    fila = {}
    for n in disp:
        pares = pares_por_noche(datos[n][vol], comunes[vol], mir.get(vol), "v375")
        if len(pares) < 3:
            continue
        rs = sorted(a / b for _, a, b in pares)
        fila[n] = {"n": len(rs), "mediana": round(st.median(rs), 3), "ic95": ic95(rs)}
        fila[n]["en_banda"] = en_banda(fila[n]["mediana"])
    if len(fila) < 2:
        print("%-22s %6s   (muestra insuficiente)" % (vol, "-"))
        continue
    res["por_volcan"][vol]["magnitud"] = fila
    if fila["ON_260K"]["en_banda"] and not fila["OFF_hoy"]["en_banda"]:
        salidos.append(vol)
    print("%-22s %6d %12.3f %s %12.3f %s"
          % (vol, fila["ON_260K"]["n"],
             fila["ON_260K"]["mediana"], "✓" if fila["ON_260K"]["en_banda"] else "✗",
             fila["OFF_hoy"]["mediana"], "✓" if fila["OFF_hoy"]["en_banda"] else "✗"))
res["criterios"]["2_salieron_de_banda_con_OFF"] = {"volcanes": salidos,
                                                   "cumple": not salidos}

# ── 3. t_bg en las noches donde la mascara SI filtraba ───────────────────────
print("\n3. LA CARA NEGATIVA: ?cuanto baja el fondo al dejar entrar topes de nube?")
print("   (solo pasadas donde la mascara ON descarto pixeles del ROI)")
print("%-22s %8s %12s %12s %12s" % ("volcan", "pasadas", "t_bg ON", "t_bg OFF", "delta"))
for vol in VOLS:
    if vol not in datos.get("ON_260K", {}):
        continue
    deltas, on_v, off_v = [], [], []
    for k in comunes[vol]:
        a, b = datos["ON_260K"][vol][k], datos["OFF_hoy"][vol][k]
        na = a.get("diag_n_bg_used_first_pass")
        nb = b.get("diag_n_bg_used_first_pass")
        if na is None or nb is None or nb <= na:
            continue           # la mascara no filtro nada en esa pasada
        ta, tb = a.get("t_bg_k"), b.get("t_bg_k")
        if ta and tb:
            on_v.append(ta); off_v.append(tb); deltas.append(tb - ta)
    if len(deltas) < 3:
        print("%-22s %8d   (pocas pasadas filtradas)" % (vol, len(deltas)))
        continue
    res["por_volcan"][vol]["t_bg_en_pasadas_filtradas"] = {
        "n": len(deltas), "ON": round(st.median(on_v), 2), "OFF": round(st.median(off_v), 2),
        "delta": resumen(deltas, 2)}
    print("%-22s %8d %12.2f %12.2f %+12.2f"
          % (vol, len(deltas), st.median(on_v), st.median(off_v), st.median(deltas)))

# ── 4 y 5. detecciones sin contraparte, y recall ─────────────────────────────
print("\n4-5. DETECCIONES Y RECALL")
print("%-22s %14s %14s %16s %16s" %
      ("volcan", "det ON", "det OFF", "sin MIROVA (d)", "recall ON->OFF"))
for vol in VOLS:
    if vol not in datos.get("ON_260K", {}):
        continue
    det, sinmir, rec_ = {}, {}, {}
    noches_mir = {f for (f, b) in (mir.get(vol) or {}) if b == "v375"}
    for n in disp:
        ks = [k for k in comunes[vol] if bucket(k[1]) == "v375"
              and (datos[n][vol][k].get("primary_cluster") or {}).get("vrp_mw")]
        det[n] = len(ks)
        noches_det = {k[0][:10] for k in ks}
        sinmir[n] = len(noches_det - noches_mir)
        rec_[n] = len(noches_det & noches_mir)
    res["por_volcan"][vol]["deteccion"] = {
        "det": det, "sin_contraparte_mirova": sinmir, "recall_noches": rec_,
        "noches_mirova": len(noches_mir)}
    print("%-22s %14d %14d %13d (%+d) %8d -> %-6d"
          % (vol, det["ON_260K"], det["OFF_hoy"], sinmir["OFF_hoy"],
             sinmir["OFF_hoy"] - sinmir["ON_260K"], rec_["ON_260K"], rec_["OFF_hoy"]))

print("\n" + "=" * 78)
print("LECTURA")
print("  noches ciegas recuperadas en total: %d" % tot_rec)
print("  volcanes que OFF saca de banda: %s" % (", ".join(salidos) if salidos else "ninguno"))
print("\n  Recordar que OFF es lo que YA esta corriendo en produccion desde el 28-ago.")
print("  Si OFF saca volcanes de banda o infla la magnitud de forma clara, la accion")
print("  no es 'no adoptar' sino REVERTIR (poner cloud_mask_bt_k: 260.0 en el perfil")
print("  operacional), y eso pasa por el ciclo A45.")

dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), "02_veredicto.json")
json.dump(res, open(dest, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("\npersistido en", dest)
