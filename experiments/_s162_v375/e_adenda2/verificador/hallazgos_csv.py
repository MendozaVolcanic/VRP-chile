# Escribe hallazgos.csv con el modulo csv (campos con comas entre comillas).
import csv
from pathlib import Path
AQUI = Path(__file__).resolve().parent
rows = [
("VE2-01", "Veto de la RP determinado por perdidas ajenas a la posicion (3 protegidas OCR SNPP que K publica) => NINGUN BRAZO", "PREREGISTRO_E.md:264; e_adenda2/leer_posicion_v375e.py regla_posicion", "CONFIRMADO mecanismo / SOSPECHA en datos reales", 4, "RP", "python -I verificador/ve_veto_estructural.py", "verificador/ve_veto_estructural_salida.txt"),
("VE2-02", "Lista de lejanas depende de capa historica de filas perdidas no fijada (15 de 330)", "PREREGISTRO_E.md:226-227; scripts/referencia_mirova_unificada.py:160-178", "CONFIRMADO", 2, "lista", "python -I verificador/ve_far_capas.py", "verificador/ve_far_capas_salida.txt"),
("VE2-03", "Asercion main() sobre 5 grillas reales nunca se ejecuta (else muerto)", "e_adenda2/probar_adenda2.py:626-628", "CONFIRMADO", 2, "bateria", "grep -n \"main() sobre 5 grillas\" e_adenda2/probar_adenda2_salida.txt", "verificador/probar_repro_salida.txt"),
("VE2-04", "Mutaciones propias que sobreviven: pesos!=1, negativos en RP, cobertura 10%, C7 vivos, rango CTLF, ancla, pos_ref", "verificador/mutar_ve2.py", "CONFIRMADO", 3, "nulo", "python -I verificador/mutar_ve2.py", "verificador/mutar_ve2_salida.txt"),
("VE2-05", "Cableado de main() (C6, posicion/ref) sin test; falla en seguro salvo C6", "e_adenda2/leer_posicion_v375e.py main()", "CONFIRMADO", 2, "bateria", "python -I verificador/mutar_ve2.py (V15, V17)", "verificador/mutar_ve2_salida.txt"),
("VE2-06", "Sin veredicto por tramo (A104); solo conteo de bloques discordantes", "PREREGISTRO_E.md:273-275; leer_posicion_v375e.py p2_con", "CONFIRMADO", 2, "A104", "python -I verificador/ve_tramos.py", "verificador/ve_tramos_salida.txt"),
("VE2-07", "Las 4 protegidas motivadoras son solo-OCR; dos SNPP antes del 2026-10-09", "PREREGISTRO_E.md §8.1", "SOSPECHA", 3, "A119", "python -I verificador/ve_protegidas.py", "verificador/ve_protegidas_salida.txt"),
("VE2-08", "La variante cercano no es un record completo (lat/lon, n_pixels sin cambiar)", "e_adenda2/leer_posicion_v375e.py variante()", "SOSPECHA", 2, "instrumento", "lectura de codigo", "verificador/ve_almacen_variantes_salida.txt"),
("VE2-09", "decidir_brazo con ciclo devuelve texto vacio", "e_adenda2/leer_posicion_v375e.py decidir_brazo", "SOSPECHA", 1, "RP", "mutacion V55 sobrevive", "verificador/mutar_ve2_salida.txt"),
("VE2-10", "El lector lee artefactos reales por defecto", "e_adenda2/leer_posicion_v375e.py:73-76,558-560", "CONFIRMADO", 2, "lectura anticipada", "lectura de codigo (no corrido por restriccion)", "verificador/INFORME.md"),
("VE2-11", "Referencias internas erradas (§8.12 inexistente, §8.7 en yml, yml dice sellada)", "PREREGISTRO_E.md:359; probe-s166-v375e-far.yml:4,11", "CONFIRMADO", 1, "documentos", "grep -n \"8.12\" experiments/_s162_v375/PREREGISTRO_E.md", "verificador/INFORME.md"),
("VE2-12", "Alerta bajo 1 MW perdida pesa ~5x una protegida o una lejana en el error de posicion", "PREREGISTRO_E.md:265-268", "CONFIRMADO pesos / SOSPECHA efecto", 2, "RP", "python -I verificador/ve_pesos.py", "verificador/ve_pesos_salida.txt"),
("VE2-13", "La RP no exige poder estadistico en las lejanas (alertado en la caja)", "PREREGISTRO_E.md:271", "SOSPECHA", 2, "RP", "lectura del pre-registro", "verificador/INFORME.md"),
]
with open(AQUI / "hallazgos.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow("id,titulo,archivo_linea,confianza,gravedad,eje,comando_reproduccion,salida_cruda".split(","))
    w.writerows(rows)
print(len(rows), "filas")
