"""Arma el prompt del verificador de un frente de la auditoría S179 (plan docs/PLAN_AUDITORIA_S179.md §4 y §6.4).

POR QUÉ: el verificador no debe heredar el razonamiento del auditor. Recibe sólo título, archivo:línea o script:salida y
gravedad de cada afirmación (la lista la escribe el orquestador en lista_v<x>.txt, aplicando el corte del plan §3), más
el preámbulo, el bloque <verificador> de docs/_prompts/PREAMBULO-AUDITOR.md en la base y el mismo <autonomia> de los
auditores. Falla (salida 1) si queda un hueco «NOMBRE» sin llenar o si la lista trae una línea de razonamiento larga.

Uso, desde la raíz del repo: python experiments/_s179_audit/armar_verificadores.py A
Entrada: experiments/_s179_audit/lista_va.txt (una afirmación por línea: «ID | título | archivo:línea o script:salida |
gravedad»). Salida: experiments/_s179_audit/prompts/VA.txt y su sha256 agregado a prompts/SHA256_VERIFICADORES.txt.
"""
import hashlib

import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import armar_prompts as ap  # noqa: E402  (ya envuelve sys.stdout en utf-8; envolverlo dos veces lo cierra)


def bloque_verificador():
    md = subprocess.run(["git", "show", f"{ap.BASE_MAIN}:docs/_prompts/PREAMBULO-AUDITOR.md"],
                        cwd=ap.RAIZ, capture_output=True, check=True).stdout.decode("utf-8")
    for b in ap.bloques_codigo(md):
        if b.lstrip().startswith("<verificador>"):
            return b.strip()
    sys.exit("no encontré <verificador> en el preámbulo")


def main():
    letra = sys.argv[1].upper()
    carp, _ = ap.FRENTES[letra]
    v = f"v{carp}"
    lista_p = ap.RAIZ / "experiments" / "_s179_audit" / f"lista_{v}.txt"
    lista = lista_p.read_text(encoding="utf-8").strip()
    for linea in lista.splitlines():
        if len(linea) > 400:
            sys.exit(f"línea de la lista demasiado larga (¿razonamiento del auditor?): {linea[:80]}")

    plan = ap.PLAN.read_text(encoding="utf-8")
    huecos = ap.bloques_codigo(ap.seccion(plan, r"6\.1 Huecos comunes"))[0]
    m = re.search(r"«DEFINICIONES_DE_LA_VARA» =\n(.*?)\n«LIMITES_DE_RECURSOS» = (.*)", huecos, flags=re.S)
    definiciones = m.group(1).strip()
    limites = m.group(2).strip().replace("Hasta 10 llamadas a la\nAPI de GitHub (verificador: 5)",
                                         "Hasta 5 llamadas a la\nAPI de GitHub")
    autonomia = ap.bloques_codigo(ap.seccion(plan, r"6\.3 Bloque"))[0].strip()
    guia = ap.GUIA_52.read_text(encoding="utf-8")
    comunicar = re.search(r"```text wrap\n(# Communicating clearly.*?)\n```", guia, flags=re.S).group(1).strip() + (
        "\n\nEscribe en español de Chile, con tú. Sin guiones largos ni medios: delatan texto generado y el informe "
        "puede salir a otras personas. Rutas absolutas completas, porque Nicolás las pega en el explorador.")

    carpeta = rf"{ap.REPO_WIN}\experiments\_s179_audit\{v}" + "\\"
    carpeta_aud = rf"{ap.REPO_WIN}\experiments\_s179_audit\{carp}" + "\\"
    rango = f"V{letra}-01 en adelante"
    pre = ap.preambulo().replace("«DEFINICIONES_DE_LA_VARA»", definiciones)
    pre = pre.replace("«CARPETA»", carpeta).replace("«RANGO»", rango)
    ver = bloque_verificador().replace("«CARPETA»", carpeta).replace("«RANGO»", rango)
    aut = autonomia.replace("«CARPETA»", carpeta).replace("«LIMITES_DE_RECURSOS»", limites)
    tarea = (
        f"<lista>\nVerificador del frente {letra} de la auditoría S179. Tu temporal: "
        f"D:\\vrp-trabajo\\temporales\\s179-audit\\{v}\\ .\n"
        f"Base: código en main 438a60a1e (instantánea en D:\\vrp-trabajo\\temporales\\s179-audit\\main\\), documentos "
        f"del loop en 0472cd95e (D:\\vrp-trabajo\\temporales\\s179-audit\\loop\\), insumos de GitHub en "
        f"D:\\vrp-trabajo\\temporales\\s179-audit\\insumos\\; datos y experimentos con git show <ref>:<ruta> y "
        f"export MSYS_NO_PATHCONV=1.\n"
        f"De la carpeta del auditor ({carpeta_aud}) puedes leer y re-correr sus scripts y sus salidas, pero no abras "
        f"su informe (INFORME*.md) ni hallazgos.csv. Tampoco abras docs/PLAN_AUDITORIA_S179.md ni otra carpeta "
        f"experiments/_s179_*: traen el control de esta auditoría y mediciones sin verificar. Es un obstáculo "
        f"deliberado. No lances subagentes.\n"
        f"Afirmaciones a verificar (ID | título | archivo:línea o script:salida | gravedad del auditor):\n{lista}\n"
        f"</lista>"
    )
    prompt = f"{pre}\n\n{ver}\n\n{tarea}\n\n<informe>\n{comunicar}\n</informe>\n\n{aut}\n"
    restos = re.findall(r"«[A-Z_]+»", prompt)
    if restos:
        sys.exit(f"{v}: quedan huecos {sorted(set(restos))}")
    ruta = ap.SALIDA / f"V{letra}.txt"
    ruta.write_text(prompt, encoding="utf-8", newline="\n")
    h = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    linea = f"V{letra}\t{len(prompt)} caracteres\tsha256 {h}"
    print(linea)
    with open(ap.SALIDA / "SHA256_VERIFICADORES.txt", "a", encoding="utf-8", newline="\n") as f:
        f.write(linea + "\n")


if __name__ == "__main__":
    main()
