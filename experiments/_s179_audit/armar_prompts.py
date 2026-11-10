"""Arma los prompts de la auditoría S179 desde el plan (docs/PLAN_AUDITORIA_S179.md §6).

POR QUÉ: el preámbulo se pega entero y los huecos se llenan por programa; un hueco sin llenar no da error, el agente
lo lee como texto y adivina. Este script falla (salida 1) si queda algún «HUECO» en un prompt armado.

Uso: python experiments/_s179_audit/armar_prompts.py   (desde la raíz del repo)
Salida: experiments/_s179_audit/prompts/{A,B,C,D}.txt y un resumen con el sha256 de cada uno.
"""
import hashlib
import io
import re
import subprocess
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

RAIZ = Path(__file__).resolve().parents[2]
PLAN = RAIZ / "docs" / "PLAN_AUDITORIA_S179.md"
GUIA_52 = Path(r"C:\Users\nmend\OneDrive\Escritorio\claude\GUIA_PROMPTING_prompting-claude-fable-5-2_ORIGINAL.md")
BASE_MAIN = "438a60a1e516fd04136e2144c797670c1cfdd46a"
SHA_PREAMBULO = "36a55c66d016afb3a28b2cdca446f19c32065c8c5b9e6affdfa1e31bb2cb6c1b"
SALIDA = RAIZ / "experiments" / "_s179_audit" / "prompts"
REPO_WIN = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile"

FRENTES = {
    "A": ("a", "401 a 449"),
    "B": ("b", "451 a 499"),
    "C": ("c", "501 a 549"),
    "D": ("d", "551 a 599"),
}


def bloques_codigo(texto):
    return re.findall(r"```text\n(.*?)\n```", texto, flags=re.S)


def preambulo():
    md = subprocess.run(
        ["git", "show", f"{BASE_MAIN}:docs/_prompts/PREAMBULO-AUDITOR.md"],
        cwd=RAIZ, capture_output=True, check=True,
    ).stdout.decode("utf-8")
    for b in bloques_codigo(md):
        if "<preambulo_auditor>" in b:
            # mismo recorte que el plan S175 §6: desde <preambulo_auditor> hasta </preambulo_auditor>, con fin de línea
            ini = b.index("<preambulo_auditor>")
            fin = b.index("</preambulo_auditor>") + len("</preambulo_auditor>")
            bloque = b[ini:fin]
            h = hashlib.sha256((bloque + "\n").encode("utf-8")).hexdigest()
            if h != SHA_PREAMBULO:
                sys.exit(f"sha256 del preámbulo distinto del sellado: {h}")
            return bloque
    sys.exit("no encontré <preambulo_auditor> en el preámbulo")


def seccion(texto, titulo_regex, nivel="###"):
    m = re.search(rf"^{nivel} {titulo_regex}.*?$(.*?)(?=^#{{2,3}} )", texto, flags=re.S | re.M)
    if not m:
        sys.exit(f"no encontré la sección {titulo_regex}")
    return m.group(0).strip()


def main():
    plan = PLAN.read_text(encoding="utf-8")
    pre = preambulo()

    huecos = bloques_codigo(seccion(plan, r"6\.1 Huecos comunes"))[0]
    m = re.search(r"«DEFINICIONES_DE_LA_VARA» =\n(.*?)\n«LIMITES_DE_RECURSOS» = (.*)", huecos, flags=re.S)
    definiciones, limites = m.group(1).strip(), m.group(2).strip()

    comunes = bloques_codigo(seccion(plan, r"6\.2 Líneas comunes"))[0].strip()
    autonomia = bloques_codigo(seccion(plan, r"6\.3 Bloque"))[0].strip()

    guia = GUIA_52.read_text(encoding="utf-8")
    m = re.search(r"```text wrap\n(# Communicating clearly.*?)\n```", guia, flags=re.S)
    comunicar = m.group(1).strip() + (
        "\n\nEscribe en español de Chile, con tú. Sin guiones largos ni medios: delatan texto generado y el informe "
        "puede salir a otras personas. Rutas absolutas completas, porque Nicolás las pega en el explorador."
    )

    SALIDA.mkdir(parents=True, exist_ok=True)
    resumen = []
    for letra, (carp, rango) in FRENTES.items():
        frente = seccion(plan, rf"{letra}\. ")
        carpeta = rf"{REPO_WIN}\experiments\_s179_audit\{carp}" + "\\"
        p = pre.replace("«DEFINICIONES_DE_LA_VARA»", definiciones)
        p = p.replace("«CARPETA»", carpeta).replace("«RANGO»", rango)
        a = autonomia.replace("«CARPETA»", carpeta).replace("«LIMITES_DE_RECURSOS»", limites)
        tarea = (
            f"<tarea>\nFrente {letra} de la auditoría S179 (plan: docs/PLAN_AUDITORIA_S179.md, commiteado en "
            f"loop/activo antes de lanzarte). Tu temporal: D:\\vrp-trabajo\\temporales\\s179-audit\\{carp}\\ .\n\n"
            f"{frente}\n\n{comunes}\n</tarea>"
        )
        prompt = f"{p}\n\n{tarea}\n\n<informe>\n{comunicar}\n</informe>\n\n{a}\n"
        restos = re.findall(r"«[A-Z_]+»", prompt)
        if restos:
            sys.exit(f"{letra}: quedan huecos {sorted(set(restos))}")
        ruta = SALIDA / f"{letra}.txt"
        ruta.write_text(prompt, encoding="utf-8", newline="\n")
        h = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        resumen.append(f"{letra}\t{len(prompt)} caracteres\tsha256 {h}")
    print("\n".join(resumen))
    (SALIDA / "SHA256.txt").write_text("\n".join(resumen) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
