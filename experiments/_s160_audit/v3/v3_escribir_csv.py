"""Escribe hallazgos.csv del verificador V3 con el módulo csv. Uso: python -I v3_escribir_csv.py"""
import csv
import os

C = os.path.dirname(os.path.abspath(__file__))
A = os.path.join("D:" + os.sep, "vrp-trabajo", "temporales", "s160_audit")
REPO = os.path.join("C:" + os.sep, "vrp-trabajo", "s159-pruebas")


def c(n):
    return os.path.join(C, n)


def a(*p):
    return os.path.join(A, *p)


MAIN = a("main")
DATA = a("main", "data", "mirova_equivalent")
rows = [
    ("241", "Plataforma o colección callada en CMR = Cobertura completa y código 0 (incluso estricto); todo vacío sí lo ve el healthcheck a 48 h",
     "pipeline/fetch.py:799-800, :1087-1088, :645-646; scripts/run_pipeline.py:416-417, :441", "CONFIRMADO EN PARTE", 4, "F3",
     f"python -I {c('v3_e2e_cmr_http.py')} {a('v3', 'arbol')} todo_vacio_http [--estricto]", c("v3_e2e_cmr_http_salida.txt")),
    ("242", "Arreglo del cese de Suomi NPP: ya subido (03:33:02 UTC) como PR #892, sin merge; su vigilante alarma por plataforma; el completa del NRT sigue",
     "origin/s159-cese-snpp f995d7101: scripts/vigilar_plataformas.py:84; nrt-healthcheck.yml +280-302", "CONFIRMADO EN PARTE (sin push REFUTADO)", 3, "F3",
     f"python -I {c('v3_vigilante_892.py')} {a('v3', 'rama892')} {DATA}", c("v3_vigilante_892_salida.txt")),
    ("243", "MODIS 6.1: decomiso anunciado para 2026-09-30 no ejecutado; Standard 6.1 sigue produciendo; nadie mide la proporción nrt; C7 sólo en LAADS",
     "pipeline/fetch.py:187-194; pipeline/store.py:683-684", "CONFIRMADO", 3, "F3",
     f"python -I {c('v3_proporcion_nrt_modis.py')} {DATA}", c("v3_cmr_granulos_modis_salida.txt")),
    ("245", "La copia horaria del consolidado acepta encogimientos: 6 de 7 pierden claves, 1.948 claves no vuelven (91 ALERTA, 14 de 1 MW o más); el tablero pierde alertas, el audit usa la unión histórica",
     "sync-mirova-csv.yml:75-80 contra :99-116", "CONFIRMADO EN PARTE", 3, "F3",
     f"python -I {c('v3_encogimientos_todos.py')} {REPO} d516b9d8c", c("v3_encogimientos_todos_salida.txt")),
    ("244", "PR #889: NO COMPLETA en toda corrida del NRT por dia_parcial; día cerrado todo vacío sale 0 también en estricto",
     "d0968e389: pipeline/fetch.py:745, :1119-1121; scripts/run_pipeline.py:459-460, :481-482", "CONFIRMADO", 2, "F3",
     f"V3_ARGS='--date 2026-10-10' python -I {c('v3_e2e_cmr_http.py')} {a('v3', 'arbol889')} todo_vacio_http --estricto", c("v3_e2e_cmr_http_889_salida.txt")),
    ("246", "Sync de la referencia: 5,17 corridas por día de 24, 8 de 50 canceladas, hueco máximo 22,3 h",
     "sync-mirova-csv.yml:42, :55; scripts/auto_audit_weekly.py:109", "CONFIRMADO", 2, "F3",
     "git log --format=%cI origin/main --since=2026-10-12T07:00:00Z -- latest_consolidado.csv", c("v3_cadencia_commits_consolidado_salida.txt")),
    ("247", "EARTHDATA_TOKEN: desconocido sin issue; nrt.yml sin guarda de token vacío: 8 logins y 1.300 s por job",
     "scripts/token_edad.py:43-50; nrt.yml:172-174; pipeline/fetch.py:318-345", "CONFIRMADO", 3, "F3",
     f"python -I {c('v3_token.py')} {MAIN}", c("v3_token_salida.txt")),
    ("248", "Cadencia del NRT depende de cron-job.org; el medidor ignora dispatch y nadie lee su JSON",
     "scripts/medir_cadencia_cron.py:63, :143-146; nrt-healthcheck.yml:301-305", "CONFIRMADO", 2, "F3",
     "conteo sobre insumos/runs_nrt.tsv (ver salida)", c("v3_cadencia_nrt_salida.txt")),
    ("252", "earthaccess sin fijar; el NRT instala hoy 0.17.0; el detector sobrevive a un cambio de envoltorio si el cuerpo nombra el token",
     "requirements.txt:1; nrt.yml:143; pipeline/fetch.py:430-452", "CONFIRMADO EN PARTE", 2, "F3",
     f"python -I {c('v3_credencial_envoltorio.py')} {MAIN}", c("v3_credencial_envoltorio_salida.txt")),
    ("V3-01", "Alerta protegida de MIROVA sin record nuestro (sin_record) no genera flag en el auto-audit",
     "scripts/auto_audit_weekly.py:796, :827", "CONFIRMADO", 4, "F3",
     f"python -I {c('v3_protegida_sin_record.py')} {MAIN}", c("v3_protegida_sin_record_salida.txt")),
    ("V3-02", "Medidor de cadencia ignora workflow_dispatch y su JSON no tiene consumidor",
     "scripts/medir_cadencia_cron.py:63; nrt-healthcheck.yml:304", "CONFIRMADO", 2, "F3",
     "grep -n event scripts/medir_cadencia_cron.py; grep -rn cadencia.json .github/workflows", c("v3_cadencia_nrt_salida.txt")),
    ("V3-03", "Token vacío: max-parallel 8 multiplica los logins con el par vencido (hasta 64 simultáneos, 88 por corrida)",
     "nrt.yml:80, :172-174; pipeline/fetch.py:318-345", "CONFIRMADO (efecto en la cuenta SOSPECHA)", 3, "F3",
     f"python -I {c('v3_token.py')} {MAIN}", c("v3_token_salida.txt")),
    ("V3-04", "El simulador de F3 no ejercita la búsqueda por ventana del NRT",
     "experiments/_s160_audit/f3/simular_dependencias.py; scripts/run_pipeline.py:537", "CONFIRMADO", 1, "instrumento",
     f"F3_TMP={a('v3', 'tmp_sim_f3')} python -I simular_dependencias.py {MAIN}", c("v3_rerun_scripts_auditor_salida.txt")),
]
with open(c("hallazgos.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "titulo", "archivo_linea", "confianza", "gravedad", "eje", "comando_reproduccion", "salida_cruda"])
    w.writerows(rows)
print(len(rows))
