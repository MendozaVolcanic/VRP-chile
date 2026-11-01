# -*- coding: utf-8 -*-
"""Censo F2 (S158): dónde vive cada afirmación sobre MIROVA que el código de VIIRS 750 toca.

Pregunta 1 (¿vería la rotura?): si una afirmación vive en un archivo que NO aparece acá, el censo
no la ve: es un censo por palabras clave, un PISO, no un techo. Pregunta 2 (¿instrumento vivo?):
el control positivo es P1 en CLAUDE.md (se sabe que la l. 142 dice «kernel 8-vec»); si P1 no
encuentra CLAUDE.md, el censo está muerto.

Salida: por patrón, archivo:línea del hit, y si el ARCHIVO tiene alguna marca «S158» (flag de
archivo, no de pasaje: que el archivo tenga una marca no prueba que el pasaje esté marcado).
Uso: python -B experiments/_s158_audit/f2/censo_afirmaciones.py > experiments/_s158_audit/f2/censo_salida.txt
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

PATRONES = {
    "P1_kernel_8_vecinos": r"8.vecinos|8-vec|ocho vecinos|eight neighbo|8-neighbo|_KERNEL_8N|_FOOTPRINT_8N",
    "P2_clusters_n_hotspots": r"n_hotspots|regiones (espacialmente )?contiguas|reporta el n[uú]mero de clusters",
    "P3_fondo_vrp": r"mediana del anillo|vecinos no alertados|media de los vecinos|mean\(8 vecinos|L1129",
    "P4_recorte_cero": r"recort[ae]\w* a (0|cero)|ΔL ≥ 0|clip ΔL|np\.maximum\(L_hot",
    "P5_K1_menos_0_8": r"K1\s*=\s*-0[.,]8|NTI\s*>\s*-0[.,]8|nti_k1.*-0\.8|-0[.,]8 noche",
    "P6_c1_scene_0_010": r"0[.,]010 scene|C1_SCENE|scene\s*=\s*0[.,]010|0[.,]010 (a|de)?fuera",
    "P7_segundo_pase_condicionado": r"(segundo pase|second.pass|second run).{0,80}(condicionad|only if one|adyacent|adjacent)|(condicionad|only if one|adjacent).{0,80}(segundo pase|second.pass|second run)",
    "P8_mascaras_geograficas": r"m[aá]scaras geogr[aá]ficas|exclude_zones",
    "P9_test1_mascara_saturacion": r"RETIRE_FROM_HOT_MASK|retire_from_hot_mask|M[AÁ]SCARA DE SATURACI[OÓ]N",
    "P10_grilla_51": r"51\s*[x×]\s*51",
    "P11_conectiva_min": r"min\(C1|rama OR completa|OR l[oó]gico",
    "P12_dia_K1_menos_0_6": r"K1\s*=\s*-0[.,]6|-0[.,]6 d[ií]a|noche -0,8 / d[ií]a -0,6",
    "P13_tabla1_para_viirs": r"Tabla 1 (por|para) (dual-ROI|VIIRS)|VIIRS.{0,40}Tabla 1|Tabla 1.{0,40}VIIRS",
}

GLOBS = [
    "docs/*.md", "docs/**/*.md", "CLAUDE.md", "tests/*.py", "pipeline/*.py", "pipeline/profiles/*.yaml",
    "experiments/_s157_prereg_d25/*.md", "experiments/_s151_prereg_fk_11/*.md",
    "experiments/_s151_prereg_caja/*.md", "experiments/_s153_fk_v2/*.md",
    "documentacion/BIBLIOGRAPHY_SYNTHESIS.md",
]


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    archivos = []
    for g in GLOBS:
        archivos.extend(sorted(ROOT.glob(g)))
    vistos = []
    for a in archivos:
        if a not in vistos and a.is_file():
            vistos.append(a)
    print("archivos barridos:", len(vistos))
    for nombre, pat in PATRONES.items():
        rx = re.compile(pat, re.IGNORECASE)
        print("\n####", nombre, "::", pat)
        n = 0
        por_archivo = {}
        for a in vistos:
            try:
                texto = a.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            tiene_s158 = "S158" in texto
            for i, linea in enumerate(texto.splitlines(), 1):
                if rx.search(linea):
                    n += 1
                    rel = a.relative_to(ROOT).as_posix()
                    por_archivo.setdefault(rel, []).append(i)
        for rel, lineas in por_archivo.items():
            texto = (ROOT / rel).read_text(encoding="utf-8", errors="replace")
            marca = "S158 en archivo" if "S158" in texto else "SIN S158"
            print(f"  {rel}  [{marca}]  líneas: {lineas[:12]}{' ...' if len(lineas) > 12 else ''}")
        print("  total hits:", n, "| archivos:", len(por_archivo))


if __name__ == "__main__":
    main()
