# -*- coding: utf-8 -*-
"""Frente C, auditoria S179. Instrumento c11: candado, reproduccion de la lectura y sensibilidad al frontend.

(1) Recalcula el sha256 (LF y en bruto) de los 16 archivos del manifiesto de la lectura sobre el worktree de la ref
    de lectura (D:/vrp-trabajo/worktrees/s178-lectura, commit ff8a39972) y lo compara con manifiesto.json.
(2) Compara el JSON de la lectura commiteada (rama claude/s178-retro-lectura, experiments/_s178_lectura/lectura.json)
    con el que da el lector re-corrido en esta sesion sobre los insumos aplanados por c01 (relectura/lectura_c.json).
(3) Compara lo que publica el tablero con el frontend del tag de despacho, con el de main 438a60a1e y con el del tag
    SIN cambio_detector.js (tablas de c02).

LAS DOS PREGUNTAS. (1) Si un archivo del manifiesto difiriera, o la lectura no fuera reproducible, o el frontend de hoy
publicara distinto, esto lo ve y lo lista. (2) Instrumento muerto: control positivo, el sha256 en bruto de los archivos
con CRLF TIENE que diferir del LF (se cuenta), y el run sin modulo TIENE que haber emitido el aviso de node (se cuenta
en su stderr).
Uso: python c11_candado_y_reproduccion.py
"""
import hashlib, json, os, sys
sys.stdout.reconfigure(encoding="utf-8")
W = "D:/vrp-trabajo/worktrees/s178-lectura"
T = "D:/vrp-trabajo/temporales/s179-audit/c"
m = json.load(open(T + "/lectura/manifiesto.json"))
ok = dist = crlf = 0
for r, s in m.items():
    b = open(os.path.join(W, r), "rb").read()
    lf = hashlib.sha256(b.replace(b"\r", b"")).hexdigest()
    raw = hashlib.sha256(b).hexdigest()
    ok += lf == s; dist += lf != s; crlf += raw != lf
    if r.endswith("VRP_GLOBAL_ARCHIVE_2025.csv"):
        print("OSF: sha256 en bruto", raw, "| LF", lf, "| el pre-registro (§4.2) declara 0863c2407eadd09722ccd98fd50c48eefdc871a4b68f843bd8478f94f5eb29da:",
              raw == "0863c2407eadd09722ccd98fd50c48eefdc871a4b68f843bd8478f94f5eb29da")
print(f"(1) manifiesto: {len(m)} archivos; sha256 LF igual al manifiesto en {ok}; distintos {dist}; control: archivos cuyo sha256 en bruto difiere del LF {crlf}")
a = json.load(open(T + "/lectura/lectura.json", encoding="utf-8"))
b = json.load(open(T + "/relectura/lectura_c.json", encoding="utf-8"))
print("(2) lectura re-corrida con insumos propios, JSON identico al commiteado:", a == b)
t = {n: json.load(open(f"{T}/tabla_{n}.json", encoding="utf-8")) for n in ("tag", "main", "sin_modulo")}
for n in ("main", "sin_modulo"):
    for brazo in ("K", "V", "KG", "PL"):
        c = dp = dm = 0
        for x, y in zip(t["tag"], t[n]):
            if "pub_" + brazo in x:
                c += 1
                dp += x["pub_" + brazo] != y["pub_" + brazo]
                dm += abs(x["mag_" + brazo] - y["mag_" + brazo]) > 1e-9
        print(f"(3) frontend del tag contra {n}, brazo {brazo}: casos {c}; publicacion distinta {dp}; magnitud distinta {dm}")
    print("    etiquetas distintas:", sum(1 for x, y in zip(t["tag"], t[n]) if x["lab"] != y["lab"]))
for n in ("tag", "main", "sin_modulo"):
    e = open(f"{T}/c02_{n}_stderr.txt", encoding="utf-8", errors="replace").read()
    print(f"    avisos «no cargo cambio_detector.js» en el stderr del run {n}: {e.count('aviso banco_paridad')}")
