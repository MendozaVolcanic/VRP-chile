# -*- coding: utf-8 -*-
"""F4T (S175): escribe hallazgos.csv con el módulo csv (campos con comas quedan entre comillas)."""
import csv
from pathlib import Path

CARPETA = Path(__file__).resolve().parent
C = r"experiments\_s175_audit\f4t"
FILAS = [
    (381, "El clasificador de credencial muerta nunca lee el status HTTP: un 401 con texto fuera del regex deja el NRT verde sin datos",
     "pipeline/fetch.py:467-471", "CONFIRMADO (exposicion SOSPECHA)", 5, "token",
     f"python {C}\\f4t_01_formas_error_credencial.py; python {C}\\f4t_03_pipeline_simulado.py (cmr401_noexist)",
     f"{C}\\f4t_01_formas_error_credencial_salida.txt; {C}\\f4t_03_pipeline_simulado_salida.txt"),
    (382, "El guard de descarga (S124) esta ciego a la forma real DownloadFailure de earthaccess: 401/403 en la descarga termina en WARN y nrt.yml verde sin records",
     "pipeline/fetch.py:1111-1120; tests/test_fetch_credential_dead_s123.py (bloque S124)", "CONFIRMADO (exposicion SOSPECHA)", 4, "token",
     f"python {C}\\f4t_03_pipeline_simulado.py (descarga401, descarga403)",
     f"{C}\\f4t_03_pipeline_simulado_salida.txt"),
    (383, "Los avisos van a un repositorio sin lectores: 0 suscriptores, sin asignado ni otro canal (A-1 de S150 sin cambios)",
     ".github/workflows/nrt-healthcheck.yml:413-414", "CONFIRMADO", 5, "token",
     "gh api repos/MendozaVolcanic/VRP-chile --jq .subscribers_count",
     f"{C}\\api_repo.json; {C}\\api_issues_token.json"),
    (384, "gh label create sin --force falla si la etiqueta existe: el primer issue de cada incidente deja el healthcheck ROJO con FAIL aunque el issue se creo",
     ".github/workflows/nrt-healthcheck.yml:247-248,411-412", "CONFIRMADO", 3, "token",
     f"gh run view 37215535362 --repo MendozaVolcanic/VRP-chile --log-failed; python {C}\\f4t_04_healthcheck_token_issue.py",
     f"{C}\\api_run_healthcheck_20261004_logfailed_full.txt; {C}\\f4t_04_healthcheck_token_issue_salida.txt"),
    (385, "nrt.yml no exige que la corrida escriba algo: unico productor con cron que puede quedar verde sin producir (guardia y sombras no)",
     ".github/workflows/nrt.yml:292-337,339-371,382-384", "CONFIRMADO", 4, "token",
     f"python {C}\\f4t_03_pipeline_simulado.py (tabla final)",
     f"{C}\\f4t_03_pipeline_simulado_salida.txt; {C}\\inventario_workflows_token.tsv"),
    (386, "21 workflows de despacho manual llevan USERNAME/PASSWORD sin guarda de token vacio: 8 logins por job con el par vencido (A71)",
     "dispatch_sin_guarda_con_usuario.txt; reproc-chunked.yml:136-137; tests/test_guard_token_vacio_cron_s160.py", "CONFIRMADO", 3, "token",
     f"awk -F'\\t' 'NR>1 && $2==0 && $5>0 && $6==0' {C}\\inventario_workflows_token.tsv; python {C}\\f4t_03_pipeline_simulado.py (token_vacio_pre894)",
     f"{C}\\inventario_workflows_token.tsv; {C}\\f4t_03_pipeline_simulado_salida.txt"),
    (387, "Token desconocido (vacio o no JWT) no abre issue; con pipeline verde nadie recibe nada hasta el staleness a 48 a 72 h (linea base 2, hallazgo 124 F0)",
     ".github/workflows/nrt-healthcheck.yml:385-387; scripts/token_edad.py:44-45", "CONFIRMADO", 3, "token",
     f"python {C}\\f4t_04_healthcheck_token_issue.py",
     f"{C}\\f4t_04_healthcheck_token_issue_salida.txt"),
    (388, "El pipeline nunca mira exp del JWT: JWT vencido y texto cualquiera se comportan igual; el unico lector de exp es token_edad una vez al dia",
     "pipeline/fetch.py:343-350; earthaccess auth.py _get_credentials (0.17.0 y 0.19.0)", "CONFIRMADO", 2, "token",
     f"python {C}\\f4t_03_pipeline_simulado.py (descarga401_jwt_vencido)",
     f"{C}\\f4t_03_pipeline_simulado_salida.txt"),
    (389, "earthaccess sin pin: el CI instala 0.19.0 y los tests locales corren 0.17.0; la deteccion depende de textos de error que cada version puede cambiar",
     ".github/workflows/nrt.yml:143; requirements.txt:1", "CONFIRMADO (deriva futura SOSPECHA)", 2, "token",
     "pip index versions earthaccess; git show 752d348bc:.github/workflows/nrt.yml | grep -n 'pip install earthaccess'",
     f"{C}\\f4t_01_formas_error_credencial_salida.txt"),
    (390, "El primer aviso de renovar sale el 2026-11-28 12:00 UTC (9,25 dias de margen), un dia despues de la fecha de rotacion a los 50 dias (2026-11-27)",
     "scripts/token_edad.py:27; .github/workflows/nrt-healthcheck.yml:21", "CONFIRMADO", 1, "token",
     f"python {C}\\f4t_04_healthcheck_token_issue.py (seccion B)",
     f"{C}\\f4t_04_healthcheck_token_issue_salida.txt"),
]

with open(CARPETA / "hallazgos.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "titulo", "archivo_linea", "confianza", "gravedad", "eje", "comando_reproduccion", "salida_cruda"])
    for fila in FILAS:
        w.writerow(fila)
print(f"{len(FILAS)} filas en {CARPETA / 'hallazgos.csv'}")
