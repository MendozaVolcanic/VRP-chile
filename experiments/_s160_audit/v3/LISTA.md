# Lista que verificas (de F3: 9 de 15 hallazgos; gravedad 3 o más)

Sólo título, ubicación, gravedad y comando del auditor. No abras C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\f3\INFORME.md; sí puedes correr sus scripts (están en C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\f3).

## 241 (gravedad 5, CONFIRMADO)
- TÍTULO: Toda plataforma o colección que calle en CMR se lee como «no hubo pasada»: cobertura «completa», código 0, sin falla; vale para Suomi NPP, NOAA-20, NOAA-21 (sólo versión 2.1), MODIS 6.1 entera y «todo vacío»
- UBICACIÓN: pipeline/fetch.py:770-800 (search_granules devuelve [] sin registrar); :1087-1088 (continue sin _registrar_falla); :218-225 (NOAA-21 sólo \"2.1\"); scripts/run_pipeline.py:402-418
- COMANDO DEL AUDITOR: cd C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\f3 && PYTHONIOENCODING=utf-8 python -I simular_dependencias.py D:\vrp-trabajo\temporales\s160_audit\main (escenarios snpp_vacio, noaa20_vacio, noaa21_version_cambia, modis61_y_nrt_vacios, todo_vacio; Villarrica 2026-11-05)
- SALIDA CRUDA: C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\f3\simular_dependencias_salida.txt

## 242 (gravedad 4, CONFIRMADO)
- TÍTULO: El arreglo del cese de Suomi NPP vive en una rama local sin push a 11 días del cese; cubre la ausencia por plataforma a 72 h y el aviso del tablero, y deja fuera el mensaje «completa» del NRT, la versión de colección y la referencia
- UBICACIÓN: C:\vrp-trabajo\s159-instrumentos (rama s159-cese-snpp; scripts/vigilar_plataformas.py:84 VENTANA_H=72; nrt-healthcheck.yml +280-302; frontend/cese_plataformas.js:30-33; scripts/ceses_esperados.json)
- COMANDO DEL AUDITOR: git -C C:\vrp-trabajo\s159-instrumentos status --short; git -C C:\vrp-trabajo\s159-instrumentos diff d516b9d8c --stat; git -C C:\vrp-trabajo\s159-pruebas ls-remote origin s159-cese-snpp
- SALIDA CRUDA: C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\f3\INFORME.md (§3, 242; estado visto 2026-10-22 03:08 UTC)

## 243 (gravedad 4, CONFIRMADO)
- TÍTULO: MODIS Colección 6.1 con decomiso anunciado (2026-09-30, no ejecutado): el Standard cae al NRT 6.1 en silencio y nadie mide la proporción de records NRT; si LANCE 6.1 también cierra, MODIS entero calla sin falla; la Colección 7 existe sólo en Standard y el pipeline no la pide
- UBICACIÓN: pipeline/fetch.py:187-194; pipeline/store.py (auto-upgrade NRT a Standard que nunca ocurriría); cmr_estado_colecciones_salida.txt filas MOD021KM y MYD021KM
- COMANDO DEL AUDITOR: python -I simular_dependencias.py D:\vrp-trabajo\temporales\s160_audit\main (escenarios modis61_decomiso y modis61_y_nrt_vacios); python -I cmr_estado_colecciones.py
- SALIDA CRUDA: C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\f3\simular_dependencias_salida.txt; C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\f3\cmr_estado_colecciones_salida.txt

## 245 (gravedad 4, CONFIRMADO)
- TÍTULO: La copia horaria de la tabla de MIROVA acepta copias que se encogen: 7 encogimientos en 64 días (hasta 659 líneas), sin validar tamaño ni cabecera, y los propaga al tablero; el canal OCR sí tiene esa defensa
- UBICACIÓN: .github/workflows/sync-mirova-csv.yml:65-84 (consolidado: curl + cmp + mv) contra :110-112 y :199-205 (OCR: no encogerse; rojo); :139-172 (rebuild por volcán con WARN continuing); frontend/diario.html:209
- COMANDO DEL AUDITOR: cd C:\vrp-trabajo\s159-pruebas && git log --format='%h %cI' -n 400 -- latest_consolidado.csv > D:\vrp-trabajo\temporales\s160_audit\f3\consolidado_commits.txt && python -I experiments\_s160_audit\f3\medir_encogimientos_consolidado.py . D:\vrp-trabajo\temporales\s160_audit\f3\consolidado_commits.txt
- SALIDA CRUDA: C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\f3\medir_encogimientos_consolidado_salida.txt

## 244 (gravedad 3, CONFIRMADO)
- TÍTULO: PR #889 cambia «completa» por «NO COMPLETA» pero el código sigue 0 y el encabezado se satura: toda corrida del NRT lleva la incidencia «dia_parcial», así que el resumen dice NO COMPLETA siempre; «sin_granulos» no cuenta ni en modo estricto
- UBICACIÓN: origin/s159-instrumentos d0968e389: pipeline/fetch.py (TIPOS_INCIDENCIA sin_granulos False; dia_incompleto); scripts/run_pipeline.py (informar_cobertura: cuenta_estricto)
- COMANDO DEL AUDITOR: python -I simular_dependencias.py D:\vrp-trabajo\temporales\s160_audit\f3\arbol_889 (escenario vivo: 1 incidencia dia_parcial, «Cobertura NO COMPLETA»)
- SALIDA CRUDA: C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\f3\simular_dependencias_salida.txt

## 246 (gravedad 3, CONFIRMADO)
- TÍTULO: La sincronización horaria de la referencia corre 5,2 veces por día de 24 y pierde 8 de 50 corridas desplazadas por el grupo push-main; hueco máximo 22,7 h entre dos sincronizaciones buenas, invisible bajo 7 días
- UBICACIÓN: .github/workflows/sync-mirova-csv.yml:42 y :45-55; insumos runs_sync-mirova-csv.tsv
- COMANDO DEL AUDITOR: python -I medir_cadencia_insumos.py ..\insumos\runs_nrt.tsv ..\insumos\runs_sync-mirova-csv.tsv
- SALIDA CRUDA: C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\f3\medir_cadencia_insumos_salida.txt

## 247 (gravedad 3, CONFIRMADO)
- TÍTULO: EARTHDATA_TOKEN: el vigilante funciona (issue a 10 días; vence 2026-12-07 18:03 UTC, issue desde 2026-11-27), pero un secret ausente o ilegible da «desconocido» sin issue, y nrt.yml no tiene la guarda de token vacío: con token vacío hace 8 logins con el par vencido (1.300 s) y bloquea la cuenta (A71)
- UBICACIÓN: nrt-healthcheck.yml:320-400; scripts/token_edad.py:27 y :43-50; nrt.yml:172-174 (sin guarda) contra experimental-diario.yml:63-64; pipeline/fetch.py:318-345
- COMANDO DEL AUDITOR: python -I probar_token_edad.py D:\vrp-trabajo\temporales\s160_audit\main; python -I simular_dependencias.py D:\vrp-trabajo\temporales\s160_audit\main (escenario token_vacio)
- SALIDA CRUDA: C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\f3\probar_token_edad_salida.txt; C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\f3\simular_dependencias_salida.txt

## 248 (gravedad 3, CONFIRMADO)
- TÍTULO: La cadencia del NRT depende de un disparador de tercero (cron-job.org con PAT sin vencimiento declarado): GitHub entrega 4,7 de 12 corridas schedule por día con atraso mediano de 68 min; si el externo muere, la cadencia vuelve a eso y nadie abre issue (medir_cadencia sólo alerta con cero corridas y nunca sale != 0)
- UBICACIÓN: scripts/medir_cadencia_cron.py:36-44 y :144; nrt-healthcheck.yml:297-305; REGISTRO_CREDENCIALES.md §2 fila 31; docs/audit_s142/CRON_EXTERNO_PASO_A_PASO.md:19
- COMANDO DEL AUDITOR: python -I medir_cadencia_insumos.py ..\insumos\runs_nrt.tsv ..\insumos\runs_sync-mirova-csv.tsv
- SALIDA CRUDA: C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\f3\medir_cadencia_insumos_salida.txt

## 252 (gravedad 3, SOSPECHA)
- TÍTULO: Bibliotecas sin fijar: el pipeline codifica supuestos de earthaccess 0.17 (bypass del token, envoltorio del 401 en __cause__.response, formato temporal) sin pin ni test de versión; si cambia el envoltorio, la credencial muerta vuelve a degradar a WARN (el zombie de S123)
- UBICACIÓN: requirements.txt:1 (>=0.9.0); nrt.yml:143 (sin versión); pipeline/fetch.py:418-452 (_is_credential_dead)
- COMANDO DEL AUDITOR: grep -n earthaccess requirements.txt .github/workflows/nrt.yml; grep -n '__cause__' pipeline/fetch.py
- SALIDA CRUDA: C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\f3\INFORME.md (§3, 252)
