"""S146 - arma docs/audit_s146/A2_RESULTADO_VARA_CORREGIDA.md pegando la salida cruda del
evaluador dentro de la prosa, para que ningun numero del informe se transcriba a mano (S91).
Tambien verifica que el pre-registro no cambio desde que se anoto su hash."""
import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAIZ = HERE.parents[1]
pre = RAIZ / "docs/audit_s146/A2_CRITERIO_PRE_REGISTRADO.md"
h_ahora = hashlib.sha256(pre.read_bytes()).hexdigest()
h_anotado = (HERE / "HASH_PRE_REGISTRO.txt").read_text(encoding="utf-8").split()[0]
estado = "COINCIDE" if h_ahora == h_anotado else "NO COINCIDE: PRE-REGISTRO INVALIDADO"
cruda = (HERE / "out/salida_cruda.txt").read_text(encoding="utf-8")
prosa = (HERE / "informe_prosa.md").read_text(encoding="utf-8")
txt = (prosa.replace("{{HASH_ANOTADO}}", h_anotado).replace("{{HASH_AHORA}}", h_ahora)
       .replace("{{HASH_ESTADO}}", estado).replace("{{SALIDA_CRUDA}}", cruda.rstrip()))
dest = RAIZ / "docs/audit_s146/A2_RESULTADO_VARA_CORREGIDA.md"
dest.write_text(txt, encoding="utf-8", newline="\n")
print(estado, h_ahora)
print("escrito", dest)
