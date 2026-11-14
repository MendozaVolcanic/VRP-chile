# -*- coding: utf-8 -*-
"""F3 S175: instrumento de rebajas no propagadas contra el codigo y los datos de UN commit.
Uso: python rebajas_vs_datos.py <commit>   (lee todo por git show; no toca el arbol)

Pregunta 1 (si lo medido estuviera roto, ¿lo veria?): solo para los dos patrones que codifica (frontera de regimen
escrita en documentos rectores y la nota A85 sobre el reproceso MODIS ene-jun 2026). Es un piso, no un barrido.
Pregunta 2 (si el instrumento estuviera muerto, ¿se veria distinto?): cada chequeo informa su denominador (lineas
leidas, records contados); con denominador 0 el veredicto es SIN DATO, nunca LIMPIO.
Lineas base rojas: 77e54e8e0^ debe dar A85=DESFASADA; d516b9d8c debe dar F281=DESFASADA (>=1 linea)."""
import io, json, re, subprocess, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
C = sys.argv[1]
def show(p):
    r = subprocess.run(["git", "show", f"{C}:{p}"], capture_output=True)
    return r.stdout.decode("utf-8", "replace") if r.returncode == 0 else None
DOCS = ["CLAUDE.md", "docs/MISSION.md", "docs/MIROVA_DIVERGENCES.md", "docs/SINTOMAS.md", "docs/CLAUDE_HISTORIA.md",
        "docs/FICHA_SDA_VRP_CHILE.md", "README.md"]
TIER_A = ["Lascar", "Lastarria", "Isluga", "NevadosDeChillan", "Llaima", "Villarrica", "Chaiten", "Tupungatito",
          "PlanchonPeteroa", "Copahue", "PuyehueCordonCaulle"]
MARCA = re.compile(r"⚠️|OBSOLET|rebaj|REBAJ|FALS[OA]|ya no|retirad", re.I)
out = {"commit": C}
# --- F281: frontera de regimen en documentos vs cambio_detector.js
js = show("frontend/cambio_detector.js") or ""
m = re.search(r'const DATOS_K_DESDE_UTC = "(\d{4}-\d{2}-\d{2})', js)
frontera = m.group(1) if m else None
pat = re.compile(r"C0 antes del (\d{4}-\d{2}-\d{2})|K (?:desde|despu[eé]s) del (\d{4}-\d{2}-\d{2})")
leidas, malas = 0, []
for d in DOCS:
    t = show(d)
    if t is None: continue
    ls = t.split("\n")
    for i, l in enumerate(ls, 1):
        leidas += 1
        # marcada si la linea o las 8 anteriores del mismo parrafo traen una marca que nombre #883 o el hallazgo 281
        vent = "\n".join(ls[max(0, i - 9):i])
        marcada = bool(re.search(r"#883|hallazgo 281|\b281\b", vent) and MARCA.search(vent))
        for mm in pat.finditer(l):
            f = mm.group(1) or mm.group(2)
            if frontera and f != frontera and not marcada and d != "docs/CLAUDE_HISTORIA.md":
                malas.append(f"{d}:{i}: {l.strip()[:220]}")
out["F281"] = {"frontera_datos_k": frontera, "lineas_leidas": leidas, "lineas_desfasadas": malas,
               "veredicto": "SIN DATO" if not frontera or leidas == 0 else ("DESFASADA" if malas else "LIMPIA")}
# --- A85: linea vigente de A85 en CLAUDE.md y lo que dicen los datos MODIS ene-jun 2026
cl = show("CLAUDE.md") or ""
a85 = next((l for l in cl.split("\n") if l.startswith("- **A85.**")), "")
hist = show("docs/CLAUDE_HISTORIA.md") or ""
afirma_sin_reproceso = bool(re.search(r"nunca se reprocesaron", hist))
vigente_marca_obsoleta = bool(re.search(r"OBSOLETA", a85)) and "#883" in a85
n, n_oct = 0, 0
meses = {}
for v in TIER_A:
    t = show(f"data/mirova_equivalent/{v}.json")
    if not t:
        out.setdefault("faltan_volcanes", []).append(v); continue
    for r in json.loads(t)["records"]:
        if not str(r.get("sensor", "")).startswith("MODIS"): continue
        dt = r.get("datetime_utc") or ""
        if not ("2026-01" <= dt[:7] <= "2026-06"): continue
        n += 1
        pm = (r.get("processed_utc") or "")[:7]
        meses[pm] = meses.get(pm, 0) + 1
out["A85"] = {"linea_vigente": a85[:400], "historia_dice_nunca_reprocesados": afirma_sin_reproceso,
              "vigente_marca_obsoleta_por_883": vigente_marca_obsoleta, "n_records_modis_ene_jun_2026": n,
              "processed_utc_por_mes": dict(sorted(meses.items()))}
reproc = n > 0 and sum(c for k, c in meses.items() if k >= "2026-07") == n
if n == 0: ver = "SIN DATO"
elif afirma_sin_reproceso and reproc and not vigente_marca_obsoleta: ver = "DESFASADA"
else: ver = "LIMPIA"
out["A85"]["veredicto"] = ver
# --- A85b (agregado tras leer SINTOMAS.md): la misma nota S153 en los OTROS documentos rectores (no la historia,
# que conserva texto viejo por A113), sin marca que nombre #883 en la linea o las 8 anteriores. Solo cuenta si los
# datos ya estan reprocesados (reproc), para que el veredicto dependa de los datos y no del texto.
pat85 = re.compile(r"gates intra-radio")
otras = []
for d in DOCS:
    if d in ("docs/CLAUDE_HISTORIA.md",): continue
    t = show(d)
    if t is None: continue
    ls = t.split("\n")
    for i, l in enumerate(ls, 1):
        if not pat85.search(l): continue
        vent = "\n".join(ls[max(0, i - 3):i + 2])
        if not re.search(r"(enero a junio|ene-jun) de 2026|2026-0[1-6]", vent): continue
        marc = "\n".join(ls[max(0, i - 9):i])
        if re.search(r"#883", marc) and MARCA.search(marc): continue
        otras.append(f"{d}:{i}: {l.strip()[:220]}")
out["A85b"] = {"lineas": otras, "datos_reprocesados": reproc,
               "veredicto": "SIN DATO" if n == 0 else ("DESFASADA" if (otras and reproc) else "LIMPIA")}
# --- MODK: documentos que describen el MODIS de produccion como K o con _interp_geo, sin marca S172 cerca, cuando los
# records MODIS desde el 2026-11-02T18 son de la via (via_codigo_mirova True). Piso: dos frases fijas.
patk = re.compile(r"producci[oó]n usa `?_interp_geo|R[eé]gimen vigente: el detector K est[aá] en producci[oó]n")
via_n = 0; via_tot = 0
for v in TIER_A:
    t = show(f"data/mirova_equivalent/{v}.json")
    if not t: continue
    for r in json.loads(t)["records"]:
        if str(r.get("sensor", "")).startswith("MODIS") and (r.get("datetime_utc") or "") >= "2026-11-02T18":
            via_tot += 1; via_n += r.get("via_codigo_mirova") is True
malk = []
for d in DOCS:
    if d == "docs/CLAUDE_HISTORIA.md": continue
    t = show(d)
    if t is None: continue
    ls = t.split("\n")
    for i, l in enumerate(ls, 1):
        if patk.search(l):
            marc = "\n".join(ls[max(0, i - 9):i])
            if re.search(r"S17[2-9]", marc) and MARCA.search(marc): continue
            malk.append(f"{d}:{i}: {l.strip()[:220]}")
out["MODK"] = {"modis_desde_corte_via": [via_n, via_tot], "lineas": malk,
               "veredicto": "SIN DATO" if via_tot == 0 else ("DESFASADA" if (malk and via_n == via_tot) else "LIMPIA")}
json.dump(out, open(f"rebajas_vs_datos_{C.replace('^','_padre')}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: (v if k == "commit" else {kk: vv for kk, vv in v.items() if kk != "linea_vigente"}) for k, v in out.items()}, ensure_ascii=False, indent=1))
