# -*- coding: utf-8 -*-
"""Escribe hallazgos.csv del verificador de D-45 con el modulo csv (campos con comas quedan entre comillas)."""
import csv
from pathlib import Path

AQUI = Path(__file__).resolve().parent
C = "experiments/_s159/instrumentos/verificador_d45/"
S = "experiments/_s159/instrumentos/signos_p2/"
FILAS = [
    ("V45-01", "El parentesis de la adenda §6 describe una accion comun por noche, pero el nulo de §2.3 exige signo comun; el placebo (c) sigue el signo",
     "experiments/_s157_prereg_d25/ADENDA_SIGNOS_P2.md:123-125; " + S + "placebo_signos.py:14-16,253-273", "CONFIRMADO", 2, "regla (adenda §6)",
     "python " + C + "verif_placebos.py", C + "verif_placebos_salida.txt"),
    ("V45-02", "El valor-p por sorteos (B >= 21) depende del orden de los bloques; la adenda no lo fija y el JSON guarda las sumas ordenadas (no re-decidible); SOSPECHA de dependencia de la version de numpy",
     "experiments/_s157_prereg_d25/evaluar_d25.py:618,542-549,621; ADENDA_SIGNOS_P2.md:53-57", "CONFIRMADO (i) / SOSPECHA (ii)", 2, "regla y detalle del JSON",
     "python " + C + "verif_matematica.py", C + "verif_matematica_salida.txt"),
    ("V45-03", "Escenario sintetico A (nulo iid, 500 semillas): D-45 PIERDE 6,0 % contra 3,68 % exacto; es la muestra de semillas, no la regla",
     S + "medir_escenarios_A_B_B2.txt; " + S + "medir_esperado_escenarios.txt", "CONFIRMADO", 1, "mediciones §7",
     "python " + S + "medir_signos_p2.py escenarios 500 A", C + "verif_extras_salida.txt"),
    ("V45-04", "Los verdes se midieron sobre 8642543ec, no sobre 7eb91eb5e; los 8 archivos medidos son identicos (sha256)",
     S + "status_antes.txt:2; " + S + "sha_antes.txt", "CONFIRMADO", 1, "verdes A8",
     "sha256sum experiments/_s157_prereg_d25/evaluar_d25.py tests/test_evaluar_d25_signos_p2_s161.py", S + "sha_despues.txt"),
    ("V45-05", "57 de las 58 mutaciones corrieron con las pruebas anteriores a ac6eab47b; solo s12a2 con las finales",
     S + "mutaciones_salida.json; " + S + "mutaciones_s12a2_salida.json", "CONFIRMADO", 1, "candados A4",
     "git show ac6eab47b --stat", S + "mutaciones_parcial.jsonl"),
    ("V45-06", "El placebo (c) al 50 % no alcanza el objetivo de pasadas tocadas en VIIRS 750 (y en VIIRS 375 de V2): el punto es mas chico de lo que dice su nombre",
     S + "placebo_signos.py:260-274", "CONFIRMADO", 1, "placebos A6",
     "python " + C + "verif_extras (ver verif_extras_salida.txt)", C + "verif_extras_salida.txt"),
    ("V45-07", "Dos corridas de placebo cayeron por el reinicio y quedaron junto a su repeticion con la misma semilla; los dos recuentos las descartan",
     S + "placebo_a_V1.jsonl (V1 a 0.5 semilla 8); " + S + "placebo_c_V1.jsonl (V1 c 0.5 semilla 3)", "CONFIRMADO", 1, "placebos A6",
     "python " + C + "verif_placebos.py", C + "verif_placebos_salida.txt"),
]
with open(AQUI / "hallazgos.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "titulo", "archivo_linea", "confianza", "gravedad", "eje", "comando_reproduccion", "salida_cruda"])
    for f in FILAS:
        w.writerow(f)
print("hallazgos.csv:", len(FILAS), "filas")
