# -*- coding: utf-8 -*-
"""Barrido OpenAlex por autor del grupo MIROVA, publicaciones desde 2025-01-01.

Las dos preguntas del instrumento:
1. Si no existiera ningún paper 2025-2026 del grupo, el conteo por autor daría 0 y el
   control positivo (Coppola 2026 Scientific Data, DOI 10.1038/s41597-026-08100-7, que ya
   está en documentacion/) NO aparecería: esa ausencia delataría al instrumento.
2. Si la API estuviera muerta, el script aborta con el código HTTP; un 0 por autor nunca
   se confunde con "no hay": se imprime "SIN DATO" con el error.

Denominador: todos los works que OpenAlex atribuye al author.id elegido, filtrados por
from_publication_date=2025-01-01, hasta la fecha de corrida (2026-10-21).
Sin API key: presupuesto compartido $0.10/día por IP; list/filter cuesta $0.0001 por llamada,
search $0.001. Se usan <= 10 search y <= 30 list.
"""
import json, sys, time, io
import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = "https://api.openalex.org"
HDR = {"User-Agent": "vrp-chile-biblio-s159 (cvivallos@gmail.com)"}
OUT = r"C:\vrp-trabajo\s159-pruebas\experiments\_s159\biblio_2026"

AUTORES = {
    "Coppola": "Diego Coppola",
    "Laiolo": "Marco Laiolo",
    "Massimetti": "Francesco Massimetti",
    "Campus": "Adele Campus",
    "Aveni": "Sofia Aveni",
}
INST_OK = ("Torino", "Turin", "Firenze", "Florence", "Sapienza", "Roma", "Rome")
CONTROL_POSITIVO = "10.1038/s41597-026-08100-7"


def get(url, params):
    for i in range(3):
        r = requests.get(url, params=params, headers=HDR, timeout=40)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429:
            time.sleep(3)
            continue
        print(f"SIN DATO: HTTP {r.status_code} en {r.url[:120]}")
        return None
    return None


def elegir_autor(nombre):
    j = get(f"{BASE}/authors", {"search": nombre, "per-page": 10})
    if not j:
        return None
    cands = []
    for a in j["results"]:
        insts = [i.get("display_name", "") for i in a.get("affiliations", []) for i in [i["institution"]]]
        ok = any(any(k in s for k in INST_OK) for s in insts)
        cands.append((ok, a["works_count"], a["id"], a["display_name"], insts[:4]))
    cands.sort(key=lambda c: (c[0], c[1]), reverse=True)
    return cands


def works_de(author_id):
    res, cursor = [], "*"
    while cursor:
        j = get(f"{BASE}/works", {
            "filter": f"author.id:{author_id},from_publication_date:2025-01-01",
            "per-page": 50, "cursor": cursor,
            "select": "id,doi,title,publication_date,type,primary_location,authorships,open_access,biblio",
        })
        if not j:
            break
        res.extend(j["results"])
        cursor = j["meta"].get("next_cursor")
    return res


def main():
    inventario, autores_elegidos = {}, {}
    for clave, nombre in AUTORES.items():
        cands = elegir_autor(nombre)
        if not cands:
            print(f"{clave}: SIN DATO (búsqueda de autor falló)")
            continue
        for c in cands[:3]:
            print(f"  cand {clave}: ok_inst={c[0]} works={c[1]} {c[2]} {c[3]} {c[4]}")
        # puede haber más de un perfil del mismo autor; tomar todos los que tengan inst MIROVA
        elegidos = [c for c in cands if c[0]] or cands[:1]
        autores_elegidos[clave] = [(c[2], c[3]) for c in elegidos]
        n = 0
        for _ok, _n, aid, _nom, _ins in elegidos:
            for w in works_de(aid):
                n += 1
                k = (w.get("doi") or w["id"]).lower()
                e = inventario.setdefault(k, {
                    "doi": w.get("doi"), "titulo": w.get("title"), "fecha": w.get("publication_date"),
                    "tipo": w.get("type"),
                    "fuente": ((w.get("primary_location") or {}).get("source") or {}).get("display_name"),
                    "oa_url": (w.get("open_access") or {}).get("oa_url"),
                    "autores": [a["author"]["display_name"] for a in w.get("authorships", [])],
                    "instituciones": sorted({i["display_name"] for a in w.get("authorships", [])
                                             for i in a.get("institutions", [])}),
                    "por_autor": [],
                })
                e["por_autor"].append(clave)
        print(f"{clave}: {n} works desde 2025-01-01 (perfiles: {len(elegidos)})")
    lista = sorted(inventario.values(), key=lambda e: e["fecha"] or "", reverse=True)
    ctrl = any((e["doi"] or "").lower().endswith(CONTROL_POSITIVO) for e in lista)
    print(f"\nTOTAL únicos: {len(lista)}  control positivo (SciData 2026) presente: {ctrl}")
    with open(f"{OUT}\\openalex_2025_2026.json", "w", encoding="utf-8") as f:
        json.dump({"corrida": "2026-10-21", "autores": autores_elegidos, "control_positivo": ctrl,
                   "works": lista}, f, ensure_ascii=False, indent=1)
    with open(f"{OUT}\\openalex_2025_2026.md", "w", encoding="utf-8") as f:
        f.write("| fecha | tipo | título | fuente | DOI | autores MIROVA | OA |\n|---|---|---|---|---|---|---|\n")
        for e in lista:
            f.write(f"| {e['fecha']} | {e['tipo']} | {(e['titulo'] or '')[:110]} | {e['fuente']} | {e['doi']} | "
                    f"{','.join(sorted(set(e['por_autor'])))} | {e['oa_url'] or ''} |\n")


if __name__ == "__main__":
    main()
