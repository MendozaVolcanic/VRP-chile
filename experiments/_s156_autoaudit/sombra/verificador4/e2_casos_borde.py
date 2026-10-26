# E2: casos borde de las decisiones (d) y (e) sobre disparadores() y leer_juzgadas(), sin tocar el worktree.
import json, os, sys, tempfile
W = sys.argv[1]
sys.path[:0] = [W, os.path.join(W, "scripts")]
import scripts.vigilancia_sombra as vs
ADOP = "2026-10-18 09:57:30"

def P(vol, b, fecha, prot, prod, sombra, minima=False):
    return {"volcano": vol, "sensor": b, "fecha_utc": fecha[:16], "instante_utc": fecha[:16] + ":00",
            "vrp_mirova_mw": 2.0 if prot else 0.3, "protegida": prot, "minima": minima,
            "referencia_sospechosa": False, "prod_pub": prod, "sombra_pub": sombra}

def D(pas, hoy="2026-10-25", juz=None):
    return vs.disparadores(pas, [], hoy=hoy, adopcion=ADOP, juzgadas=juz or {})

print("== 1. formato de fecha distinto en el archivo de juzgadas")
base = P("PuyehueCordonCaulle", "VIIRS750", "2026-10-20 05:54", True, False, True)
for fmt in ("2026-10-20 05:54", "2026-10-20 05:54:00", "2026-10-20T05:54", "2026-10-20T05:54:00Z", "2026-10-20 5:54"):
    tmp = os.path.join(sys.argv[2], "juz.json")
    json.dump({"pasadas": [{"volcano": "PuyehueCordonCaulle", "sensor": "VIIRS750", "fecha_utc": fmt}]},
              open(tmp, "w", encoding="utf-8"))
    j = vs.leer_juzgadas(tmp)
    d = D([dict(base)], juz=j)
    print(f"   {fmt!r:26} -> veredicto {d['veredicto']}, juzgadas reconocidas {len(d['juzgadas'])}")
tmp = os.path.join(sys.argv[2], "juz.json")
json.dump({"pasadas": [{"volcano": "Puyehue-Cordon Caulle", "sensor": "VIIRS750", "fecha_utc": "2026-10-20 05:54"}]},
          open(tmp, "w", encoding="utf-8"))
print("   variante de nombre 'Puyehue-Cordon Caulle' ->", D([dict(base)], juz=vs.leer_juzgadas(tmp))["veredicto"],
      "(¿avisa que la entrada no calza con ninguna pasada? salida no tiene campo para eso)")

print("== 2. pasada juzgada posterior a la adopción: efecto sobre persistencia y Muy Bajo")
pas = [P("V", "VIIRS375", "2026-10-20 05:00", False, False, True),
       P("V", "VIIRS375", "2026-10-21 05:00", False, False, True),
       P("V", "VIIRS375", "2026-10-22 05:00", False, False, True)]
j = {("V", "VIIRS375", "2026-10-20 05:00"): {"decision": "x"}}
print("   sin juzgada: persistencia", D(pas)["persistencia"], "veredicto", D(pas)["veredicto"])
print("   con la 1.a noche juzgada: persistencia", D(pas, juz=j)["persistencia"], "veredicto", D(pas, juz=j)["veredicto"])
print("   Muy Bajo sin / con juzgada:", D(pas)["muy_bajo"]["V|VIIRS375"]["k"], D(pas)["muy_bajo"]["V|VIIRS375"]["n"], "/",
      D(pas, juz=j)["muy_bajo"]["V|VIIRS375"]["k"], D(pas, juz=j)["muy_bajo"]["V|VIIRS375"]["n"])

print("== 3. juzgada anterior a la adopción: ¿sale del retrospectivo?")
r = [P("PCC", "VIIRS750", "2026-10-10 05:54", True, False, True), P("L", "MODIS", "2026-10-11 05:54", True, True, True)]
jr = {("PCC", "VIIRS750", "2026-10-10 05:54"): {"decision": "x"}}
for nombre, jj in (("sin", None), ("con", jr)):
    rr = D([dict(x) for x in r], juz=jj)["retrospectivo"]
    print(f"   {nombre} juzgada: n_pasadas {rr['n_pasadas']}, protegidas vistas {rr['protegidas_vistas_en_sombra']}, "
          f"perdidas {len(rr['protegidas_que_la_sombra_publica_y_k_calla'])}")

print("== 4. plazo: la candidata ES la protegida número 29")
pas = [P(f"V{i}", "MODIS", f"2026-10-{19 + i // 10:02d} 0{i % 10}:00", True, True, True) for i in range(28)]
pas.append(P("X", "MODIS", "2026-10-25 07:20", True, False, True))
d = D(pas, hoy="2026-10-26")
print("   vistas", d["duracion"]["protegidas_vistas_en_sombra"], "cumplida", d["duracion"]["cumplida"], "veredicto", d["veredicto"])
d = D(pas[:20] + pas[-1:], hoy="2026-10-26")
print("   misma candidata con 20 vistas antes: veredicto", d["veredicto"])

print("== 5. plazo por fecha: candidata del día 119, vista por primera vez el día 121 (retraso del OCR o workflow caído)")
c = [P("X", "MODIS", "2027-02-14 07:20", True, False, True)]
print("   evaluada 2027-02-14:", D(c, hoy="2027-02-14")["veredicto"], "| evaluada 2027-02-16:", D(c, hoy="2027-02-16")["veredicto"])

print("== 6. juzgada posterior + plazo cumplido: la juzgada no dispara y sí cuenta")
pas = [P(f"V{i}", "MODIS", f"2026-10-{19 + i // 10:02d} 0{i % 10}:00", True, True, True) for i in range(28)]
pj = P("X", "MODIS", "2026-10-25 07:20", True, False, True)
d = D(pas + [pj], hoy="2026-10-26", juz={("X", "MODIS", "2026-10-25 07:20"): {"decision": "x"}})
print("   veredicto", d["veredicto"], "vistas", d["duracion"]["protegidas_vistas_en_sombra"], "cumplida", d["duracion"]["cumplida"])

print("== 7. prefijos de título del workflow")
pref = ["Sombra de K: candidata a reversion", "Sombra de K: candidata fuera de plazo", "Sombra de K: investigar",
        "Sombra de K: vigilancia ciega", "Vigilancia de la sombra de K: el script fallo"]
for a in pref:
    for b in pref:
        if a != b and (b + ": 2026-10-20").startswith(a):
            print("   CHOQUE:", a, "captura", b)
print("   (sin líneas CHOQUE: ningún prefijo captura el título de otra clase)")
