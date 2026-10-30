"""P2-05 / VC169-01. Pregunta 1: si el sha de la población en externos_referencia.json estuviera en CRLF, ¿se ve? Sí:
se compara contra sha LF y sha CRLF de los mismos bytes. Pregunta 2: si no leyera el archivo, daría excepción.
Control positivo: el sha LF debe coincidir con el del MANIFIESTO (e8315ba4...). Ventana: árbol 743e89c48."""
import hashlib, json
C = "D:/vrp-trabajo/temporales/s169_audit_patrones/f2_modis/arbol/experiments/_s166_modd_f4/"
b = open(C + "poblacion_f4.json", "rb").read()
lf = b.replace(b"\r\n", b"\n"); crlf = lf.replace(b"\n", b"\r\n")
h = lambda x: hashlib.sha256(x).hexdigest()
print("bytes en el árbol: n=", len(b), "tiene CRLF:", b"\r\n" in b, "n_lineas:", lf.count(b"\n"))
print("sha LF  :", h(lf)); print("sha CRLF:", h(crlf)); print("sha crudo árbol:", h(b))
m = json.load(open(C + "MANIFIESTO_CANDADO_F4.json", encoding="utf-8"))
print("manifiesto:", m["archivos"]["experiments/_s166_modd_f4/poblacion_f4.json"])
r = json.load(open(C + "externos_referencia.json", encoding="utf-8"))
print("externos_referencia.poblacion_sha256:", r.get("poblacion_sha256"), "checkout:", r.get("checkout"))
print("  == LF?", r.get("poblacion_sha256") == h(lf), " == CRLF?", r.get("poblacion_sha256") == h(crlf))
# ¿qué haría externos_f4.referencia_y_reetiquetado con una lectura LF (runner o checkout autocrlf=false)?
shas = {h(lf), h(lf)}  # en checkout LF, crudo == LF
print("lectura en checkout LF -> acepta?", r.get("poblacion_sha256") in shas)
shas_w = {h(crlf), h(lf)}
print("lectura en checkout CRLF -> acepta?", r.get("poblacion_sha256") in shas_w)
# el ensayo en seco escribe json.dumps(pob) en una sola línea: CRLF y LF dan los mismos bytes
toy = json.dumps({"pasadas": [{"a": 1}], "x": []}).encode()
print("ensayo: json compacto tiene saltos de línea?", b"\n" in toy, "-> LF==CRLF:", h(toy) == h(toy.replace(b"\n", b"\r\n")))
