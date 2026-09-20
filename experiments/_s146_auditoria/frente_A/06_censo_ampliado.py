# -*- coding: utf-8 -*-
"""S146 frente A, paso 6: ampliacion del censo de cierres de S145 (que se declara un PISO).
Mismos 5 documentos rectores. Tres capas, para que se vea de donde viene el crecimiento:
  capa 0 = patrones ORIGINALES del censo (leidos de censo.py, sin copiar a mano);
  capa 1 = las MISMAS palabras pero sin distinguir mayusculas y con flexiones (el censo original es
           sensible a mayusculas: "NO REABRIR", "REFUTADO", "cerrada", "resuelto" se le escapan);
  capa 2 = OTRAS redacciones de cierre (descartado, no aplica, ya hecho, superado, no vale el ROI, inmune,
           sano, obsoleto, no es bug, no amerita, rechazado, vetado, curado, marginal, inerte, etc.).
NO juzga ninguna afirmacion: inventaria. La capa 2 tiene falsos positivos (una palabra no es un cierre);
por eso se reporta el conteo bruto Y una lista priorizada, y se declara que es un TECHO blando.

Las dos preguntas del instrumento:
 1. Si el patron estuviera roto, fallaria? PARCIAL: control positivo abajo (4 frases de cierre conocidas
    que el censo original NO ve deben aparecer en la ampliacion; si alguna falta, aborta). No protege
    contra redacciones que ni yo imagine: sigue siendo busqueda por palabras.
 2. Instrumento muerto? SI se veria: la capa 0 debe reproducir el censo S145 (89 filas, tolerancia 5 por
    ediciones posteriores de los documentos); si no, aborta.
Salida: JSON y MD chicos dentro de esta carpeta.
"""
import collections
import io
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
src = (ROOT / "experiments/_s145_censo_cierres/censo.py").read_text(encoding="utf-8")
ns = {}
exec(src[src.index("DOCS = ["):src.index("def contexto")], ns)
DOCS, P0, RESP = ns["DOCS"], ns["PATRONES"], ns["RESPALDOS"]

P1 = [("cerrada_ci", r"\bcerrad[oa]s?\b|\bse cierra\b|\bcierre formal\b|\bcerrar el frente\b"),
      ("resuelta_ci", r"\bresuelt[oa]s?\b"), ("agotado_ci", r"\bagotad[oa]s?\b"),
      ("no_reabrir_ci", r"\bno (se )?reabr\w+|\bno volver a plantear\w*|\banti-A8\b"),
      ("efecto_nulo_ci", r"\befecto nulo\b|\bnulo hoy\b|\bes nul[oa]\b|\bsin efecto\b"),
      ("irreducible_ci", r"\birreducibles?\b"),
      ("es_fiel_ci", r"\b(es|ya es|son) fiel(es)?\b|\bfidelidad confirmada\b"),
      ("despreciable_ci", r"\bdespreciables?\b|\binvisible hoy\b|\bnegligible\b"),
      ("menor_ci", r"\bprioridad baja\b|\bimpacto menor\b|\babierta, menor\b"),
      ("no_adoptar_ci", r"\bno adoptar\b|\bno se adopta\b"), ("refutada_ci", r"\brefutad[oa]s?\b")]
P2 = [("descartado", r"\bdescartad[oa]s?\b|\bdescart[oó]\b|\bse descarta\b"),
      ("no_aplica", r"\bno aplica\b|\bno aplicar[ií]a\b"),
      ("ya_hecho", r"\bya (est[aá] )?(hech[oa]|resuelt[oa]|decidid[oa]|implementad[oa]|correct[oa]|[oó]ptim[oa]|cubiert[oa])\b"),
      ("superado", r"\bsuperad[oa]s?\b|\bobsolet[oa]s?\b|\bsubsumid[oa]s?\b"),
      ("no_vale_roi", r"\bno vale el ROI\b|\bno vale la pena\b|\bno amerita\b|\bno urgente\b|\bnice-to-have\b"),
      ("inmune", r"\binmunes?\b"), ("sano", r"\bsan[oa]s?\b|\bcalibrad[oa] natural\w*"),
      ("no_es_bug", r"\bno es (un )?bug\b|\bno es error\b|\bno es (un )?frente\b|\bno es gap\b|\bno interpretar como bug\b"),
      ("rechazado", r"\brechazad[oa]s?\b|\bvetad[oa]s?\b"),
      ("curado", r"\bcurad[oa]s?\b|\bmitigad[oa]s?\b"),
      ("marginal_inerte", r"\bmarginal(es)?\b|\binerte\b|\bcosm[eé]tic[oa]\b|\bredundantes?\b"),
      ("no_tocar", r"\bno (se )?toca\w*\b|\bno modificar\b|\bno cambiar\b|\bno revertir\b|\bno implementar\b|\bsin acci[oó]n\b|\bno quedan acciones\b|\bno se propone cambio\b"),
      ("no_bloquea", r"\bno bloque\w+|\bno afecta\b|\bsin da[nñ]o\b|\bsin p[eé]rdida\b"),
      ("confirmada", r"\bCONFIRMAD[OA]\b"),
      ("aplazado", r"\baplazad[oa]\b|\bcongelad[oa]s?\b|\bdiferid[oa]\b"),
      ("unico_que", r"\bel [uú]nico que\b|\b[uú]nica validaci[oó]n\b")]


def barrer(patrones, flags):
    out = {}
    for rel in DOCS:
        L = (ROOT / rel).read_text(encoding="utf-8", errors="replace").split("\n")
        for i, l in enumerate(L):
            t = [n for n, rx in patrones if re.search(rx, l, flags if n != "confirmada" else 0)]
            if t:
                v = "\n".join(L[max(0, i - 1):i + 4])
                resp = sorted({n for n, rx in RESP if re.search(rx, v)})
                out[(rel, i + 1)] = {"tipos": t, "resp": resp, "sin": resp in ([], ["sesion"]),
                                     "texto": l.strip()[:220]}
    return out


c0 = barrer(P0, 0)
ref = json.loads((ROOT / "experiments/_s145_censo_cierres/censo_cierres.json").read_text(encoding="utf-8"))
print("capa 0 (patrones originales, hoy):", len(c0), "| censo S145 guardado:", ref["n_afirmaciones"],
      "| sin respaldo hoy:", sum(v["sin"] for v in c0.values()))
assert abs(len(c0) - ref["n_afirmaciones"]) <= 5, "la capa 0 no reproduce el censo: instrumento roto"
c1 = barrer(P1, re.I)
c2 = barrer(P2, re.I)
u1 = set(c0) | set(c1)
u2 = u1 | set(c2)
CONTROL = [("docs/MIROVA_DIVERGENCES.md", "**NO REABRIR** como"),
           ("docs/MIROVA_DIVERGENCES.md", "cap de magnitud REFUTADO"),
           ("docs/HYPOTHESIS_LOG.md", "original (DESCARTADA)"),
           ("CLAUDE.md", "MIROVA es inmune porque detecta por NTI")]
for rel, frag in CONTROL:
    L = (ROOT / rel).read_text(encoding="utf-8").split("\n")
    idx = [k + 1 for k, l in enumerate(L) if frag in l]
    assert idx, "control positivo: no encuentro la frase %r en %s" % (frag, rel)
    assert all((rel, k) not in c0 for k in idx), "el censo original SI la veia: %r" % frag
    assert all((rel, k) in u2 for k in idx), "control positivo falla: %r" % frag
print("control positivo: 4 de 4 frases de cierre que el censo original NO ve aparecen en la ampliacion")
print("capa 1 (mismas palabras, sin mayusculas, con flexiones): universo %d (+%d)" % (len(u1), len(u1) - len(c0)))
print("capa 2 (otras redacciones): universo %d (+%d sobre capa 1; x%.1f sobre el censo)"
      % (len(u2), len(u2) - len(u1), len(u2) / len(c0)))
allr = {}
for k in u2:
    e = {"tipos": [], "resp": [], "sin": True, "texto": ""}
    for c in (c0, c1, c2):
        if k in c:
            e["tipos"] += [t for t in c[k]["tipos"] if t not in e["tipos"]]
            e["resp"], e["sin"], e["texto"] = c[k]["resp"], c[k]["sin"], c[k]["texto"]
    e["capa"] = 0 if k in c0 else (1 if k in c1 else 2)
    allr[k] = e
nuevos = {k: v for k, v in allr.items() if v["capa"] > 0}
print("nuevos:", len(nuevos), "| nuevos sin respaldo citable (misma regla del censo):",
      sum(v["sin"] for v in nuevos.values()))
print("por capa:", dict(collections.Counter(v["capa"] for v in nuevos.values())))
print("por documento (nuevos):", dict(collections.Counter(k[0] for k in nuevos)))
print("por tipo (nuevos):", collections.Counter(t for v in nuevos.values() for t in v["tipos"]).most_common())
APAGA = ("no_reabrir_ci", "no_tocar", "irreducible_ci", "agotado_ci", "descartado", "rechazado", "no_vale_roi",
         "cerrada_ci", "inmune", "no_adoptar_ci")
prio = sorted([(k, v) for k, v in nuevos.items() if any(t in APAGA for t in v["tipos"])],
              key=lambda kv: (not kv[1]["sin"], kv[0]))
print("nuevos que apagan trabajo:", len(prio), "| de ellos sin respaldo citable:", sum(v["sin"] for _, v in prio))
(HERE / "06_censo_ampliado.json").write_text(json.dumps(
    {"n_capa0": len(c0), "n_capa1": len(u1), "n_capa2": len(u2),
     "nuevos": [{"archivo": k[0], "linea": k[1], **v} for k, v in sorted(nuevos.items())]},
    ensure_ascii=False, indent=1), encoding="utf-8")
md = ["# Censo ampliado S146 (frente A): cierres nuevos que APAGAN trabajo", "",
      "| archivo:linea | tipos | sin respaldo citable | texto |", "|---|---|---|---|"]
for k, v in prio:
    md.append("| `%s:%d` | %s | %s | %s |" % (k[0], k[1], ", ".join(v["tipos"]), "SI" if v["sin"] else "no",
                                           v["texto"][:170].replace("|", " ")))
(HERE / "06_censo_ampliado_prioritarios.md").write_text("\n".join(md) + "\n", encoding="utf-8")
