# -*- coding: utf-8 -*-
"""VD1 (verificador frente D, S179). Afirmaciones 551 y DEC-14: con la vía «código MIROVA» en VIIRS 375, ¿cuántas
protegidas de MIROVA que K publica deja de publicar la vía con la posición que escribe producción («radiante»,
pipeline/mirova_v750_codigo.py::_cumulo_del_mas_radiante) y cuántas con la posición que decidió la retrospectiva
(«cercano», experiments/_s172_retro_paquete/leer_retro.py l. 1274)?

Camino propio, distinto del auditor: (1) no uso su unión, leo los records de la vía directo de los trozos D2 y D4
(intento más alto, records dentro de la ventana del trozo); (2) aplico la variante «cercano» con la función del lector
sellado (reglas/leer_posicion_v375e.py::variante, copia de 438a60a1e); (3) separo cada protegida por fuente (tabla u
OCR) y por la marca `referencia_sospechosa` de vigilancia_sombra.pasadas_de_alerta (OCR de Suomi NPP antes del hito).

Las dos preguntas del instrumento:
1. Si la vía callara protegidas, ¿lo vería? Sí, en F26 (2026-02-01 a 03-31) y DM (2026-10-01 a 10-16), las ventanas
   con artefacto. No ve abril a septiembre ni desde el 10-17.
2. Si el instrumento estuviera muerto, ¿se vería distinto? Control placebo: la variante «radiante» aplicada con la misma
   función tiene que dar exactamente lo mismo que el record crudo. Control positivo: tengo que reproducir el 5 del
   auditor con radiante, y el conteo de protegidas de K tiene que ser > 0.

Vara: «publica» = predicado del tablero con node (bp.correr_node vía bp.cargar_nuestros) sobre frontend/index.html de
la instantánea de 438a60a1e; «protegida» = cm.alerta_protegida dentro de vs.pasadas_de_alerta, referencia de
438a60a1e (latest_consolidado.csv sha256 40b1b928..., OCR 7e54155a...).

Uso: python vd1_cercano_vs_radiante.py <instantanea main> <base con data/ de 438a60a1e> <D2> <D4> <temporal> <salida.json>
"""
import sys, io, os, json, re, copy, collections, importlib.util
from datetime import date, timedelta
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
MAIN, BASE, D2, D4, TMP, OUT = sys.argv[1:7]
OUT = os.path.abspath(OUT)
TMP = os.path.abspath(TMP)
sys.path.insert(0, MAIN)
sys.path.insert(0, os.path.join(MAIN, "scripts"))
os.chdir(MAIN)
import banco_paridad as bp
import vigilancia_sombra as vs
import referencia_mirova_unificada as rmu
aa = vs.aa
spec = importlib.util.spec_from_file_location("lp_vd", os.path.join(TMP, "lp.py"))
# lp.py importa cosas pesadas; sólo necesito variante y distancias_desde_record: las copio por texto
src = open(os.path.join(TMP, "lp.py"), encoding="utf-8").read()
ns = {"copy": copy}
for nombre in ("distancias_desde_record", "clase_dc", "variante"):
    m = re.search(r"^def %s\(.*?(?=^def |\Z)" % nombre, src, re.S | re.M)
    exec(m.group(0), ns)
distancias_desde_record, variante = ns["distancias_desde_record"], ns["variante"]

PAT = re.compile(r"^trozo-(?P<v>[A-Za-z]+)-(?P<i>\d+)-(?P<a>\d{4}-\d\d-\d\d)_(?P<b>\d{4}-\d\d-\d\d)-intento-(?P<n>\d+)$")
VENT = {"F26": ("2026-02-01", "2026-03-31"), "DM": ("2026-10-01", "2026-10-16")}
inner = bp.inner_desde_html()

trozos = collections.defaultdict(dict)
for carpeta in (D2, D4):
    for p in Path(carpeta).iterdir():
        m = PAT.match(p.name)
        if m and (m["a"] >= "2026-01-01"):
            trozos[(m["v"], m["a"], m["b"])][int(m["n"])] = p / (m["v"] + ".json")
via = collections.defaultdict(dict)
dias = collections.defaultdict(set)
for (v, a, b), ints in trozos.items():
    d0, d1 = date.fromisoformat(a), date.fromisoformat(b)
    dias[v] |= {(d0 + timedelta(n)).isoformat() for n in range((d1 - d0).days + 1)}
    for r in json.loads(ints[max(ints)].read_text(encoding="utf-8"))["records"]:
        if a <= (r.get("datetime_utc") or "")[:10] <= b and bp.bucket(r.get("sensor")) == "VIIRS375":
            via[v][(r["datetime_utc"], r["sensor"])] = r
print("trozos 2026 leídos:", len(trozos), "; records VIIRS 375 de la vía:", sum(len(x) for x in via.values()))

brazos = {}
sin_dist = 0
for brazo in ("crudo", "radiante", "cercano"):
    d = os.path.join(TMP, "via_" + brazo)
    os.makedirs(d, exist_ok=True)
    for v in bp.VOLS:
        out = []
        for r in sorted(via.get(v, {}).values(), key=lambda r: r["datetime_utc"]):
            if brazo == "crudo" or not r.get("primary_cluster"):
                out.append(r)
                continue
            dd = distancias_desde_record(r)
            if dd is None:
                sin_dist += brazo == "cercano"
                out.append(r)
                continue
            out.append(variante(r, dd[brazo], inner[v]))
        with open(os.path.join(d, v + ".json"), "w", encoding="utf-8") as fh:
            json.dump({"volcano": v, "records": out}, fh)
    brazos[brazo] = d
print("records con cúmulo sin distancias para la variante (quedan crudos):", sin_dist)

filas = rmu.cargar_referencia_unificada(
    aa.CONS if False else os.path.join(BASE, "latest_consolidado.csv"),
    os.path.join(BASE, "data", "mirova_reference", "mirova_v1_snapshot", "registro_vrp_ocr.csv"),
    respaldo_path=Path(BASE) / "data" / "mirova_reference" / "mirova_v1_snapshot" / "registro_vrp_consolidado_respaldo_20260408.csv",
    historico_path=Path(BASE) / "data" / "mirova_reference" / "union_historica" / "consolidado_filas_perdidas.csv")
coords = aa._coords_por_volcan()
bp.DATA = Path(BASE) / "data" / "mirova_equivalent"
fuentes = collections.defaultdict(set)
import clase_mirova as cm
for f in filas:
    if f.get("tipo") in cm.TIPOS_ALERTA and cm.alerta_protegida(f):
        fuentes[cm.clave_pasada(f)].add(f.get("source"))

res = {}
for nombre, win in VENT.items():
    prod = [r for r in bp.cargar_nuestros(coords, inner, win) if r["b"] == "VIIRS375" and r["noche"] in dias[r["vol"]]]
    res[nombre] = {}
    for brazo, d in brazos.items():
        vrec = [r for r in bp.cargar_nuestros(coords, inner, win, data=d) if r["b"] == "VIIRS375"]
        pas = [p for p in vs.pasadas_de_alerta(filas, prod, vrec, win) if p["sensor"] == "VIIRS375"
               and p["fecha_utc"][:10] in dias[p["volcano"]]]
        prot = [p for p in pas if p["protegida"]]
        perd = [p for p in prot if p["prod_pub"] is True and p["sombra_pub"] is not True]
        det = []
        for p in perd:
            fu = sorted(x for x in fuentes.get((p["volcano"], "VIIRS375", p["fecha_utc"]), set()) if x)
            det.append([p["volcano"], p["fecha_utc"], p["vrp_mirova_mw"], "sin record" if p["sombra_pub"] is None else "calla",
                        "+".join(fu) or "?", "sospechosa" if p["referencia_sospechosa"] else ""])
        res[nombre][brazo] = {"protegidas": len(prot), "K_publica": sum(p["prod_pub"] is True for p in prot),
                              "via_publica": sum(p["sombra_pub"] is True for p in prot),
                              "K_publica_y_via_no": len(perd), "detalle": det,
                              "con_fila_de_tabla": sum(1 for p in prot if "CONS" in fuentes.get((p["volcano"], "VIIRS375", p["fecha_utc"]), set())),
                              "perdidas_con_fila_de_tabla": sum(1 for x in det if "CONS" in x[4])}
        r = res[nombre][brazo]
        print(f"{nombre} {brazo}: protegidas {r['protegidas']} (con fila de la tabla {r['con_fila_de_tabla']}); K publica {r['K_publica']}; "
              f"vía publica {r['via_publica']}; K publica y la vía no {r['K_publica_y_via_no']} (con fila de la tabla {r['perdidas_con_fila_de_tabla']})")
        for x in det:
            print("    ", x)

placebo_ok = all(res[n]["crudo"]["detalle"] == res[n]["radiante"]["detalle"] for n in res)
total_rad = sum(res[n]["radiante"]["K_publica_y_via_no"] for n in res)
print("\nCONTROL PLACEBO (radiante por la función == crudo):", "OK" if placebo_ok else "FALLA")
print("CONTROL POSITIVO (radiante reproduce el 5 del auditor):", total_rad, "OK" if total_rad == 5 else "DISTINTO")
res["controles"] = {"placebo_ok": placebo_ok, "total_radiante": total_rad}
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(res, fh, indent=1, ensure_ascii=False, default=str)
