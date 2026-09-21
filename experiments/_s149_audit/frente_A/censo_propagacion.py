# -*- coding: utf-8 -*-
"""Frente A, auditoria S149. Mide DONDE vive cada forma de tres reglas del dueno.

Las dos preguntas del instrumento:
1. Si la propagacion estuviera rota (la regla deformada sigue viva, la decision nueva no llego), esta
   medicion lo ve? SI: cuenta lineas que calzan con cada forma, archivo por archivo.
2. Si el instrumento estuviera muerto, el resultado se veria distinto? SI: cada patron lleva un
   CONTROL POSITIVO (un archivo donde se sabe que debe calzar). Si el control da 0, el patron esta
   roto y la fila se rotula INSTRUMENTO MUERTO, no "limpio".

Limite declarado: busca por expresion regular, es un PISO (A89). Un cero con control positivo vivo
significa "esta forma textual no esta", no "la idea no esta".
Denominador: los archivos listados en VIGENTES. Ventana: el arbol de trabajo al 2026-09-21.
Solo lectura.
"""
import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[3]
MEM = Path("C:/Users/nmend/.claude/projects/"
           "C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile/memory")

VIGENTES = [
    REPO / "CLAUDE.md",
    REPO / "docs/MISSION.md",
    REPO / "docs/PLAN_AUDITORIA_S149.md",
    REPO / "tasks/BLOQUE_ARRANQUE_S150.md",
    REPO / "docs/PLAN_PARIDAD_POST_AUDITORIA_S146.md",
    REPO / "docs/S147_RESULTADO_AB_SIN_TEST1.md",
    REPO / "docs/s131/agentes/GROUND_TRUTH_ESPACIAL.md",
    REPO / "docs/audit_s143/BITACORA_S143.md",
    REPO / "docs/superpowers/specs/2026-09-13-plan-definitivo-paridad-design.md",
    REPO / "experiments/_s146_ab_sin_test1/PREREGISTRO.md",
    REPO / "experiments/_s146_ab_sin_test1/parametros.json",
    REPO / "experiments/_s146_ab_sin_test1/evaluar.py",
    REPO / "experiments/_s147_ab_conectiva/PREREGISTRO.md",
    REPO / "experiments/_s147_ab_conectiva/PREREGISTRO_CAJA.md",
    REPO / "experiments/_s149_prereg_invierno/PREREGISTRO_INVIERNO.md",
    MEM / "MEMORY.md",
    MEM / "feedback_mirova_equivalent_priorities.md",
    MEM / "feedback_s143_primero_igualar_a_mirova.md",
    MEM / "reference_paridad_mirova_umbrales.md",
]

PATRONES = {
    # forma deformada: corte de 0,5 MW como perdida aceptable sin decir "solo MODIS"
    "corte_0,5_como_criterio": (
        r"(0[,.]5 ?MW o m[aá]s|max_vrp_fn_aceptable_mw|bajo 0[,.]5 ?MW|<0[,.]5 ?MW|menos de 0[,.]5 ?MW)",
        REPO / "experiments/_s146_ab_sin_test1/PREREGISTRO.md"),
    # la correccion: el alcance por sensor
    "alcance_solo_MODIS": (
        r"(SOLO MODIS|s[oó]lo (vale )?para MODIS|solo vale para MODIS|queda s[oó]lo para MODIS|aplica SOLO a MODIS)",
        MEM / "feedback_mirova_equivalent_priorities.md"),
    # texto viejo: recall sobre precision
    "recall_sobre_precision": (
        r"(priorizamos recall|recall sobre precisi|prioriza recall)",
        REPO / "CLAUDE.md"),
    # decision S149: paridad en los dos sentidos
    "paridad_dos_sentidos": (
        r"(dos sentidos|callar donde|suma de los dos errores)",
        REPO / "docs/PLAN_AUDITORIA_S149.md"),
    # lectura asimetrica: cero perdidas manda sobre la sobre-publicacion
    "asimetria_recall_primero": (
        r"(prioridad es asim|manda sobre\s+la sobre|se optimizan \*\*despu)",
        MEM / "feedback_s143_primero_igualar_a_mirova.md"),
    # definicion de terminado congelada S141
    "definicion_de_terminado": (
        r"(Definici[oó]n de terminado|FALSAS_BANDA_TERMINADO|plan-definitivo-paridad)",
        REPO / "docs/superpowers/specs/2026-09-13-plan-definitivo-paridad-design.md"),
}


def contar(path, rx):
    try:
        txt = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None, []
    lineas = [i + 1 for i, l in enumerate(txt.splitlines()) if rx.search(l)]
    return len(lineas), lineas


def main():
    for nombre, (pat, control) in PATRONES.items():
        rx = re.compile(pat, re.IGNORECASE)
        n_ctrl, _ = contar(control, rx)
        estado = "VIVO" if n_ctrl else "INSTRUMENTO MUERTO"
        print(f"\n## {nombre}   [control positivo en {control.name}: {n_ctrl} lineas -> {estado}]")
        for p in VIGENTES:
            n, ls = contar(p, rx)
            if n is None:
                print(f"  SIN DATO (no se pudo leer)  {p.name}")
            elif n:
                rel = p.name if MEM in p.parents else p.relative_to(REPO).as_posix()
                print(f"  {n:3d}  {rel}  lineas {ls[:8]}")
        ceros = [p.name for p in VIGENTES if contar(p, rx)[0] == 0]
        print(f"  cero en: {', '.join(ceros)}")


if __name__ == "__main__":
    main()
