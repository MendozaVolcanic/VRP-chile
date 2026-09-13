"""S138 eje 5 - intenta ROMPER la bateria del Apendice A sobre los JSON ya commiteados (sin reprocesar).

POR QUE. La bateria (experiments/_s136/conformidad_apendice.py, evaluar_caso) declara "conforme" un
positivo si CUALQUIER pasada nocturna de esa fecha publica un cumulo con VRP > 0 a <= 5 km de la
coordenada GVP. Tres cosas que esa regla no mira y que aca se miden:
  (a) OBJETO: si el cumulo que publicamos es el que el autor marco (posicion medida en la figura,
      experiments/_s138_audit/eje5/out/figuras_9.json), o algo distinto dentro de la caja.
  (b) PASADA: el autor muestra UNA pasada (titulo de la figura). La bateria mezcla todas las
      nocturnas de la fecha (2 a 4 por caso). Un "conforme" en otra pasada no confirma nada; un
      "falso positivo" en otra pasada no contradice al autor.
  (c) SENSIBILIDAD: el conteo 6/6 y 3/3 con INNER_KM 3, 5 y 8 km, y con la referencia en GVP o en el
      centro de la grilla de MIROVA (Volc_LAT/LON del archivo global).

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) Si la bateria midiera otra cosa que el objeto del autor, esto
lo ve: compara posiciones, no distancias, en los brazos que persisten pc_lat/pc_lon; y donde no hay
posicion (brazos de S136 y los dos B22 con compuerta) usa la COTA INFERIOR |d_autor - d_nuestro|
(A93: la diferencia de dos radios acota por abajo la distancia entre los puntos) y lo declara.
(2) Si el instrumento estuviera muerto: la reevaluacion con INNER_KM = 5 y referencia GVP debe
reproducir EXACTAMENTE el veredicto commiteado de cada caso (control de identidad); si no lo hace, el
reimplementador esta mal y nada de lo demas vale.

READ-ONLY: lee JSON commiteados; escribe solo en experiments/_s138_audit/eje5/out/.
"""
import io
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAIZ = HERE.parents[2]
OUT = HERE / "out"
sys.path.insert(0, str(HERE))
from medir_9_figuras import hav, punto_desde, rumbo, CENTRO_MIROVA  # noqa: E402

BRAZOS = [
    ("_s136/out_apendice", "B21 min (hoy)"),
    ("_s136/out_apendice_prosa", "B21 max"),
    ("_s137/out_apendice_b22", "B22 min"),
    ("_s137/out_apendice_b22_prosa", "B22 max"),
    ("_s137/out_apendice_b22_sincompuerta", "B22 min sinBT"),
    ("_s137/out_apendice_b22_sincompuerta_prosa", "B22 max sinBT"),
    ("_s137/out_apendice_b22_sincompuerta_fondolocal", "B22 min sinBT loc"),
    ("_s137/out_apendice_b22_sincompuerta_fondolocal_prosa", "B22 max sinBT loc"),
]
TOL_NTI = 0.06
RADIO_MISMO_OBJETO_KM = 2.0   # un pixel MODIS remuestreado es 1 km; 2 km = vecino inmediato


def evaluar(caso, pasadas, inner_km, ref, solo_pasada=None):
    """Reimplementacion parametrica de evaluar_caso. ref = (lat, lon) de referencia. Si el brazo no
    persiste pc_lat, usa dist_crater_km (que es a la GVP) y solo vale con ref = GVP."""
    if solo_pasada is not None:
        pasadas = [p for p in pasadas if p["inicio"] == solo_pasada]
    if not pasadas:
        return "INDETERMINADO"
    npap = caso.get("nti_paper")
    if npap is not None:
        pasadas = [p for p in pasadas if isinstance(p["nti_max"], (int, float))
                   and abs(p["nti_max"] - npap) <= TOL_NTI]
        if not pasadas:
            return "INDETERMINADO"
    publica = []
    for p in pasadas:
        if not ((p.get("vrp_pc_mw") or 0) > 0):
            continue
        if p.get("pc_lat") is not None:
            d = hav(p["pc_lat"], p["pc_lon"], ref[0], ref[1])
        else:
            d = p.get("dist_crater_km")
        if d is not None and d <= inner_km:
            publica.append(p)
    if caso["veredicto_paper"] == "detecta":
        return "CONFORME" if publica else "FN"
    return "FP" if publica else "CONFORME"


def main():
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    import yaml
    fig = json.loads((OUT / "figuras_9.json").read_text(encoding="utf-8"))
    figs = {f["caso"]: f for f in fig["figuras"]}
    yml = {c["caso"]: c for c in yaml.safe_load(
        (RAIZ / "experiments/_s136/apendice_a.yaml").read_text(encoding="utf-8"))["casos"]}
    datos = {}
    for d, n in BRAZOS:
        p = RAIZ / "experiments" / d / "resultado_apendice.json"
        datos[n] = {c["caso"]: c for c in json.loads(p.read_text(encoding="utf-8"))}
    orden = sorted(yml)

    # ---------- control de identidad: la reimplementacion reproduce el JSON commiteado ----------
    print("=== CONTROL DE IDENTIDAD (INNER 5 km, ref GVP, todas las pasadas) ===")
    fallas = 0
    for n in datos:
        for k in orden:
            c = datos[n][k]
            mio = evaluar(c, c["pasadas"], 5.0, (yml[k]["lat"], yml[k]["lon"]))
            suyo = ("CONFORME" if c["resultado"] == "CONFORME" else
                    "FN" if "falso negativo" in c["resultado"] else
                    "FP" if "falso positivo" in c["resultado"] else "INDETERMINADO")
            if mio != suyo:
                fallas += 1
                print(f"  DISCREPA {n} {k}: reimplementado {mio} vs commiteado {suyo}")
    print(f"discrepancias: {fallas} de {len(datos) * len(orden)}  -> "
          f"{'la reimplementacion es fiel' if fallas == 0 else 'NO USAR lo que sigue'}")
    # control positivo del reimplementador: con INNER 0.01 km todos los positivos deben caer a FN
    fn0 = sum(1 for n in datos for k in orden if yml[k]["veredicto"] == "detecta"
              and evaluar(datos[n][k], datos[n][k]["pasadas"], 0.01, (yml[k]["lat"], yml[k]["lon"])) == "FN")
    print(f"control positivo (INNER 0,01 km): positivos que caen a FN = {fn0} de "
          f"{len(datos) * 6} (esperado {len(datos) * 6})")

    # ---------- (a) OBJETO: posicion del autor vs cumulo nuestro, brazo por brazo ----------
    print("\n=== (a) MISMO OBJETO QUE EL AUTOR? positivos, por brazo ===")
    tabla_a = []
    for n in datos:
        for k in orden:
            if yml[k]["veredicto"] != "detecta":
                continue
            c, f = datos[n][k], figs[k]
            m = f["medicion"]
            pas_fig = f["pasada_figura_utc"]
            gvp = (yml[k]["lat"], yml[k]["lon"])
            # posicion del autor en lat/lon: centro MIROVA si existe, si no GVP
            if f.get("autor_latlon_centro_mirova"):
                pa = tuple(f["autor_latlon_centro_mirova"])
                centro = "mirova"
            else:
                pa = tuple(f["autor_latlon_centro_gvp"])
                centro = "gvp"
            d_autor_gvp = hav(pa[0], pa[1], gvp[0], gvp[1])
            fila = {"brazo": n, "caso": k, "name": yml[k]["name"], "resultado_commiteado": c["resultado"],
                    "pasada_figura": pas_fig, "autor_dist_gvp_km": round(d_autor_gvp, 2),
                    "autor_rumbo_desde_centro": m["rumbo_deg"], "autor_dist_desde_centro_km": m["dist_km"],
                    "centro_usado": centro}
            # cumulos publicados (VRP>0) en la pasada de la figura y en las demas
            pub = [p for p in c["pasadas"] if (p.get("vrp_pc_mw") or 0) > 0]
            en_fig = [p for p in pub if p["inicio"] == pas_fig]
            fila["n_pasadas_publican"] = len(pub)
            fila["publica_en_pasada_figura"] = bool(en_fig)
            tiene_pos = any(p.get("pc_lat") is not None for p in pub)
            fila["json_tiene_posicion"] = tiene_pos
            veredicto = "sin cumulo"
            detalle = []
            if pub:
                if tiene_pos:
                    # separacion real cumulo-autor, minima sobre las pasadas que publican
                    seps = []
                    for p in pub:
                        s = hav(p["pc_lat"], p["pc_lon"], pa[0], pa[1])
                        seps.append((s, p["inicio"], p["vrp_pc_mw"], p["dist_crater_km"],
                                     rumbo(gvp[0], gvp[1], p["pc_lat"], p["pc_lon"])))
                    seps.sort()
                    fila["sep_min_km"] = round(seps[0][0], 2)
                    fila["sep_min_pasada"] = seps[0][1]
                    ef = [s for s in seps if s[1] == pas_fig]
                    fila["sep_en_pasada_figura_km"] = round(ef[0][0], 2) if ef else None
                    fila["nuestro_rumbo_dist_en_pasada_figura"] = (
                        [round(ef[0][4], 1), round(ef[0][3], 2)] if ef else None)
                    ref_sep = ef[0][0] if ef else seps[0][0]
                    veredicto = "mismo objeto" if ref_sep <= RADIO_MISMO_OBJETO_KM else "otro objeto"
                    detalle = [f"{s[1][11:16]} sep={s[0]:.2f} km d_gvp={s[3]:.2f} vrp={s[2]}" for s in seps]
                else:
                    # cota inferior A93: |d_autor - d_nuestro|
                    cotas = [(abs(d_autor_gvp - p["dist_crater_km"]), p["inicio"], p["vrp_pc_mw"], p["dist_crater_km"])
                             for p in pub if p.get("dist_crater_km") is not None]
                    cotas.sort()
                    ef = [x for x in cotas if x[1] == pas_fig]
                    ref = ef[0] if ef else cotas[0]
                    fila["cota_inferior_sep_km"] = round(ref[0], 2)
                    fila["cota_en_pasada_figura"] = bool(ef)
                    fila["nuestro_d_gvp_en_pasada_figura_km"] = round(ef[0][3], 2) if ef else None
                    veredicto = ("otro objeto (cota)" if ref[0] > RADIO_MISMO_OBJETO_KM
                                 else "indeterminable (sin posicion en el JSON)")
                    detalle = [f"{x[1][11:16]} cota>={x[0]:.2f} km d_gvp={x[3]:.2f} vrp={x[2]}" for x in cotas]
            fila["veredicto_objeto"] = veredicto
            fila["detalle"] = detalle
            tabla_a.append(fila)
    for n in datos:
        print(f"\n-- {n}")
        for r in [r for r in tabla_a if r["brazo"] == n]:
            print(f"  {r['caso']} {r['name'][:12]:12} commit={r['resultado_commiteado'][:12]:12} "
                  f"autor@{r['autor_dist_gvp_km']}km  publica_en_fig={r['publica_en_pasada_figura']!s:5} "
                  f"pos={r['json_tiene_posicion']!s:5} -> {r['veredicto_objeto']}  | " + "; ".join(r["detalle"]))
    resumen_a = {}
    for n in datos:
        rs = [r for r in tabla_a if r["brazo"] == n and r["resultado_commiteado"] == "CONFORME"]
        resumen_a[n] = {"conformes": len(rs),
                        "mismo_objeto": sum(1 for r in rs if r["veredicto_objeto"] == "mismo objeto"),
                        "otro_objeto": sum(1 for r in rs if r["veredicto_objeto"].startswith("otro objeto")),
                        "indeterminable": sum(1 for r in rs if r["veredicto_objeto"].startswith("indeterminable"))}
    print("\nRESUMEN (a): de los positivos CONFORMES de cada brazo, cuantos son el objeto del autor")
    for n, r in resumen_a.items():
        print(f"  {n:20} conformes {r['conformes']}  mismo objeto {r['mismo_objeto']}  otro objeto {r['otro_objeto']}  indeterminable {r['indeterminable']}")

    # ---------- (b) SENSIBILIDAD ----------
    print("\n=== (b) SENSIBILIDAD: INNER_KM x referencia x pasada ===")
    configs = []
    for inner in (3.0, 5.0, 8.0):
        for refn in ("gvp", "mirova", "autor"):
            for pas in ("todas", "figura"):
                configs.append((inner, refn, pas))
    tabla_b = {}
    for n in datos:
        tabla_b[n] = {}
        for inner, refn, pas in configs:
            vs = {}
            for k in orden:
                c, f = datos[n][k], figs[k]
                if refn == "gvp":
                    ref = (yml[k]["lat"], yml[k]["lon"])
                elif refn == "mirova":
                    ref = CENTRO_MIROVA.get(k) or (yml[k]["lat"], yml[k]["lon"])
                else:  # posicion del autor (solo positivos); negativos: centro mirova o gvp
                    if f.get("autor_latlon_centro_mirova"):
                        ref = tuple(f["autor_latlon_centro_mirova"])
                    elif f.get("autor_latlon_centro_gvp"):
                        ref = tuple(f["autor_latlon_centro_gvp"])
                    else:
                        ref = CENTRO_MIROVA.get(k) or (yml[k]["lat"], yml[k]["lon"])
                tiene_pos = any(p.get("pc_lat") is not None for p in c["pasadas"])
                if refn != "gvp" and not tiene_pos and any((p.get("vrp_pc_mw") or 0) > 0 for p in c["pasadas"]):
                    vs[k] = "n/d"   # sin posicion no se puede mover la referencia
                    continue
                vs[k] = evaluar(c, c["pasadas"], inner, ref,
                                solo_pasada=(f["pasada_figura_utc"] if pas == "figura" else None))
            pos = [vs[k] for k in orden if yml[k]["veredicto"] == "detecta"]
            neg = [vs[k] for k in orden if yml[k]["veredicto"] != "detecta"]
            tabla_b[n][f"inner{inner:g}_{refn}_{pas}"] = {
                "casos": vs, "pos_ok": pos.count("CONFORME"), "neg_ok": neg.count("CONFORME"),
                "nd": (pos + neg).count("n/d"), "indet": (pos + neg).count("INDETERMINADO")}
    print(f"{'brazo':20} " + " ".join(f"{i:g}{r[0]}{p[0]}" .rjust(7) for i, r, p in configs))
    print(" " * 21 + "(inner km, ref g=gvp m=centro mirova a=posicion autor, pasada t=todas f=la de la figura; celda = pos_ok/neg_ok, * = hay n/d)")
    for n in datos:
        celdas = []
        for inner, refn, pas in configs:
            r = tabla_b[n][f"inner{inner:g}_{refn}_{pas}"]
            celdas.append(f"{r['pos_ok']}/{r['neg_ok']}{'*' if r['nd'] else ''}".rjust(7))
        print(f"{n:20} " + " ".join(celdas))
    (OUT / "romper_bateria.json").write_text(json.dumps(
        {"identidad_discrepancias": fallas, "objeto": tabla_a, "resumen_objeto": resumen_a,
         "sensibilidad": tabla_b, "radio_mismo_objeto_km": RADIO_MISMO_OBJETO_KM},
        indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\nescrito {OUT / 'romper_bateria.json'}")


if __name__ == "__main__":
    main()
