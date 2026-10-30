# Auditoría S169 f1 (P-A): las 5 constantes sha256 que los lectores exigen, contra los blobs de los tags.
# Solo lee el repositorio (git show). Cuenta los CR de cada blob en bytes (los LF y CR no pasan por ningún filtro).
# Pregunta 1: si una constante estuviera mal, ¿se vería? Sí: el control negativo (otro archivo) tiene que dar DISTINTO.
import hashlib, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
REPO = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
CASOS = [
    ("s162-v750b-sellado:experiments/_s162_v750b/analizar_v750b.py", "83b7159bd0666871b2e88a48c23feba4900ae28c24abd76b6cb3abf7b2593392"),
    ("s162-v750b-adenda2-sellada:experiments/_s162_v750b/adenda1/leer_v750b.py", "11e0ee91fe77d6685e2fd3ac06ffbe18cb237fadae8d5d7e73759199689b52e2"),
    ("s162-v750b-adenda2-sellada:experiments/_s162_v750b/adenda1/cobertura_cajas_v750b.py", "f250a926ae26435ba5101566b4f90abcf9a1e98d23de4f7a94ba95992fb1d70d"),
    ("s167-v750b-adenda3-sellada:experiments/_s162_v750b/adenda3/leer_n3_v750b.py", "fa6d61a7d1fd4bebbfe27f61ec81c925b4d1380aeef6bf38a9bb938dcb930d5e"),
    ("s161-d25-lectura:experiments/_s157_prereg_d25/evaluar_d25.py", "2e5576973ef1df6969f517c40bedc271f76db8a8b4756613e5004fc05d976747"),
    ("s162-v750b-sellado:experiments/_s162_v750b/probe_v750b.py", "83b7159bd0666871b2e88a48c23feba4900ae28c24abd76b6cb3abf7b2593392"),  # CONTROL NEGATIVO
]
for k, esp in CASOS:
    b = subprocess.run(["git", "-C", REPO, "show", k], capture_output=True, check=True).stdout
    h = hashlib.sha256(b).hexdigest()
    hl = hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest()
    print(("OK       " if h == esp else "DISTINTO ") + f"bytes={len(b)} CR={b.count(b'\r')} LF={b.count(b'\n')} sha_crudo==sha_LF:{h == hl}  {k}")
