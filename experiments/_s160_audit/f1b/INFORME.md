# F1b (S160): los instrumentos de prioridad B y C, S125 a S151. ¿Cuáles podían dar su veredicto sin importar el efecto real?

## 1. Encabezado

- Fecha y hora del servidor al empezar: `Date: Thu, 22 Oct 2026 04:02:54 GMT` (cabecera de `gh api -i repos/MendozaVolcanic/VRP-chile`, una llamada de las diez permitidas; la de los insumos decía 03:11:55 GMT). Última medición de este informe: 04:28 UTC (`date -u`).
- Commit auditado: `origin/main` = `d516b9d8c0fad5b0ca458b9fb57cdf5e6f75f956`; instantánea en `D:\vrp-trabajo\temporales\s160_audit\main\`. Los instrumentos se leyeron del worktree `C:\vrp-trabajo\s159-pruebas` (HEAD `2b50c8a4a`, rama `loop/activo`); donde un script o un documento difiere entre ese HEAD y `d516b9d8c` lo digo. Los datos de brazos salieron del repo (`data/_s125_*`, `data/_s126_*`, `experiments/_s143_evaluador/artefactos_fusionados_s143.zip`) o de `git archive origin/s146-ab/35548121381 experiments/_s146_ab_sin_test1/salidas/35548121381` (nunca `checkout` ni `pull`).
- Referencia de MIROVA usada en toda re-ejecución: la copia congelada de `d516b9d8c`, sha256 en `referencia_sha256.txt`: `latest_consolidado.csv` bc1522c24c924cb5…, `mirova_v1_snapshot/registro_vrp_ocr.csv` 94679246acbd0db5…, `mirova_v1_snapshot/registro_vrp_consolidado.csv` 2e2c268e8811cdc1….
- Modelo y esfuerzo: Fable 5.1 (claude-fable-5-1), esfuerzo `high` según el plan §3 F1 (lo declaro como me lo pasaron; no lo puedo verificar desde adentro).
- CARPETA: `C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\f1b\` (este informe, `matriz_instrumentos.csv`, `hallazgos.csv`, scripts `placebo.py`, `correr_evaluador_raiz.py`, `r3_censo_vs_ponderado.py`, `r7_barajado_s126.py`, `r8_consumidores.py`, y las salidas en `s125/`, `s126/`, `s143/`, `s148/` y `*_salida.txt`). Datos extraídos: `D:\vrp-trabajo\temporales\s160_audit\f1b\` (346 MB; disco D con 9,2 GB libres al cerrar, C con 13 GB).
- Criterio: tabla R1 a R17 de `docs/PLAN_AUDITORIA_S160.md` §3 F1 (l. 100 a 120), con R7 reemplazada por §11.2b (l. 720 a 728) y el §11 completo. Sellado en `60762a939`; no lo cambié.
- Censo inicial de los 25 instrumentos: tres subagentes Explore (sólo lectura) me devolvieron veredicto, frente, evaluador, ventana, vara, controles y cambios de criterio con `archivo:línea`. Comando con que se completó el inventario del plan: `find experiments scripts -iname "evaluar*.py"` (16 evaluadores, 7 con `banco_paridad`, igual que el plan) más `ls` de cada carpeta de la lista del plan y `git log --diff-filter=A --format='%h %ci' -- <pre-registro>` para R1 (salida en el §4 de este informe). Lo que del censo entra a un hallazgo lo verifiqué contra el archivo (está citado con línea); lo que no verifiqué va marcado SOSPECHA.
- Qué NO miré: el veredicto del A/B de D25 (`experiments/_s157_prereg_d25/` resultados y PR #890), por instrucción; la regla de adopción de K y los bancos compartidos (`banco_paridad`, `clase_mirova`, `calidad_referencia_mirova`, `libro_de_cuentas`, auto-audit: F1a); el código del scraper Mirova-v1; ningún L1B ni workflow (no reprocesé ni despaché nada). No medí placebo ni barajado en los instrumentos cuyos datos de brazos no están ni en el repo ni en una rama `origin/s146-ab/<run>` (S130, S135, S149, MxD03: dicho en SIN DATO). No corrí R7 sobre S143 ni S148 (exige ejecutar el predicado del tablero con node mil veces; no cabía en el presupuesto): SIN DATO, no OK.

## 2. En una pantalla

1. **Ningún instrumento de prioridad B con evaluador en código aprueba un placebo** (control por 1,10, por 1,2, desplazado): medido en S125, S126, S143 y S146/S148; los cuatro los rechazan porque exigen un beneficio que una copia del control no puede dar (criterio 2 en S143, criterio 2 en S126, más volcanes en banda en S125, el nulo barajado C8 en S146/S148).
2. **Dos frentes que siguen cerrados lo están sobre un instrumento que no podía ver el efecto**: D18 (S130: Test 1 integrado encendido y la caja sin llegar al segundo pase, hallazgo 180) y D22 (S143: ventana que cruza #535 sin tramo, pisa tres hitos de la referencia y Test 1 encendido, hallazgo 182). D18 hoy cuelga de S151, que es otro instrumento y otra premisa; D22 cuelga sólo de S143 más la suspensión de S150.
3. **La conectiva `max`, que está en producción con K, se declaró CONFIRMADA en S148 mientras el evaluador que corrió imprimía INDECIDIBLE** (control positivo calibrado para producción con Test 1); el CONFIRMADA salió de otro script y hoy los dos instrumentos dan recalls distintos para el mismo control (133 contra 137 de 143) (hallazgos 181 y 196). La adopción en producción la sostiene `_s151_prereg_fk_11` (F1a), no S148.
4. **Los evaluadores viejos (S125, S126) son ciegos a la cobertura** (R2 FALLA medido: un día borrado y el criterio «cero pérdidas» cumple) y **seis instrumentos leyeron la referencia viva sin hash** (R14); nada de eso cambió un veredicto real porque todos eran NO ADOPTAR por falta de beneficio, pero los mismos evaluadores aprobarían a un brazo que se cae justo las noches en que pierde.
5. Los dos controles positivos del barrido salieron con mi propio instrumento: (c) R3 ponderado 152,33 sobre un techo contable de 119, ΔE +104 contra +12 del censo; (d) R8 la caja decide cumbre sin la máscara en 6 sitios del código del run de S148, el segundo pase incluido (l. 1313). R7 sobre S126: 0 de 1.000 barajados aprueban (Wilson [0,000, 0,004], OK).

## 3. Hallazgos (IDs 180 a 196; `hallazgos.csv` tiene la fila de cada uno)

### 180. El NO ADOPTAR de D18 en S130 salió de un instrumento que no podía ver la caja

- ARCHIVO:LÍNEA: `docs/s130/VEREDICTO_AB_D18.md:3` («**No adoptar.** No por daño», y sigue «sino por ausencia de beneficio», TEXTO; entre las dos partes hay un inciso que no copio); `origin/s146-ab/35572961810:pipeline/process_viirs.py:1313` (`is_summit_mask = vent_dist_per_pixel <= inner_radius_km`, sin `_roi1_mask`, TEXTO); `CLAUDE.md` A114 y A118; `docs/MIROVA_DIVERGENCES.md:2385-2393`.
- QUÉ PASA: el volcán no cambia con el instrumento: la caja de 5 × 5 km sólo puede actuar si el píxel tibio del flanco se evalúa con el umbral estricto en los dos pases. En S130 el Test 1 integrado estaba encendido (publica por su cuenta, A114) y el segundo pase recibía el círculo, no la caja (A118). Mi script `r8_consumidores.py` sobre el código del run de la caja de S148 cuenta 6 sitios que deciden cumbre por `inner_radius_km` y ninguno con la máscara en su contexto; en `d516b9d8c` quedan 4 (l. 1774, 1838, 2134 y el docstring l. 725), pero los dos pases ya la reciben (l. 1206 y 1346, `roi1_summit_mask`). Para el código exacto de S130 no lo medí (SOSPECHA, como ya lo era en A118).
- CÓMO SE VE EN EL DASHBOARD: invisible hoy (la caja está apagada); lo que torció fue un cierre.
- CÓMO REPRODUCIRLO: `python -B experiments/_s160_audit/f1b/r8_consumidores.py D:/vrp-trabajo/temporales/s160_audit/f1b/process_viirs_ramaG.py` (archivo = `git show origin/s146-ab/35572961810:pipeline/process_viirs.py`).
- CONFIANZA: CONFIRMADO para el código del run de S148; SOSPECHA para el código de S130.
- GRAVEDAD 4: cerró un frente (D18) que sigue cerrado; hoy el cierre vale por S151 (veto), que depende de la geolocalización MODIS (`docs/MIROVA_DIVERGENCES.md:2387-2393`), o sea que si D-19 se corrige, D18 vuelve a quedar sin ningún instrumento válido detrás.

### 181. La conectiva se declaró CONFIRMADA mientras su evaluador imprimía INDECIDIBLE

- ARCHIVO:LÍNEA: `docs/S148_RESULTADO_AB_CONECTIVA.md:64-70` («⚠️ **El evaluador imprime INDECIDIBLE, y hay que decir por qué.** Su control positivo incluye una banda para la tasa de publicación del control (80 a 92 % en VIIRS 375) que está calibrada para el control de **producción**», TEXTO) y `:87` («**Hipótesis CONFIRMADA en VIIRS 375**», TEXTO); `experiments/_s146_ab_sin_test1/evaluar.py:757-775` (argumentos).
- QUÉ PASA: el evaluador pre-registrado de S146 se reusó para S148 con otro control (B, sin Test 1). Su control positivo no aplica a ese control, así que el instrumento, tal como corrió, no emite veredicto. Lo reproduje hoy con los brazos del run 35548121381: `=== _s147_ab_sin_test1_max -> INDECIDIBLE (el control positivo del brazo de control no se cumple)` y criterios C4, C6 y C7 falsos (`s148/real_stdout.txt:8` y `:21`). El CONFIRMADA salió de `experiments/_s147_lectura/lectura_por_tramo.py` (P1 a P4), un instrumento sin esa banda. Y los dos cuentan distinto el recall del control: 133 de 143 (`real_stdout.txt:12`) contra 137 de 143 (`S148_RESULTADO:79`); la causa no la tracé (hallazgo 196).
- CÓMO SE VE EN EL DASHBOARD: la conectiva `max` está en producción con K (#850); lo que publica hoy el operador lo decide K. El instrumento de adopción fue `_s151_prereg_fk_11` (F1a); éste fue el que dijo «merece el gate completo».
- CÓMO REPRODUCIRLO: `python -B experiments/_s146_ab_sin_test1/evaluar.py --control <S>/_s146_ab_sin_test1 --brazo <S>/_s147_ab_sin_test1_max --out experiments/_s160_audit/f1b/s148/real.json`, con `<S>` = `D:/vrp-trabajo/temporales/s160_audit/f1b/s148/experiments/_s146_ab_sin_test1/salidas/35548121381`.
- CONFIANZA: CONFIRMADO (el 133 contra 137: CONFIRMADO el número, SOSPECHA la causa).
- GRAVEDAD 4.

### 182. El A/B de D22 y D25 (S143) decidió sobre una ventana que cruza #535, pisa tres hitos de la referencia y corrió con el Test 1 integrado encendido

- ARCHIVO:LÍNEA: `experiments/_s143_evaluador/parametros.json` («"ventana": ["2026-06-01", "2026-08-31"]», TEXTO); `experiments/_s143_evaluador/evaluar.py` (`grep -c 535` = 0); `docs/MIROVA_DIVERGENCES.md:2734` (D22 ABIERTA); `experiments/_s150_ab_d22/PREREGISTRO.md:3` («NO se rehace como A/B en GitHub», TEXTO, citado por el censo y leído por mí en la salida del grep).
- QUÉ PASA: con la máscara de nube de 260 K (hasta #535) las pasadas de invierno quedaban sin fondo y eso se leía como precisión (A104); la ventana jun-ago es justo ese tramo. Además el Test 1 integrado publicaba por su cuenta (A114), y cualquier «pérdida» del literal se mide contra un control saturado. Al re-correr hoy con la copia congelada, el evaluador de hoy avisa solo que la ventana «pisa 5 tramos con defectos conocidos» (`s143/base_stdout.txt:2`); en S143 esa alarma no existía (A119 es de S149). El veredicto se reproduce (272 noches, 5 pérdidas del literal, negativos 1.184 contra 1.170 publicados: la referencia se movió entre S143 y hoy sin cambiar nada).
- CÓMO SE VE EN EL DASHBOARD: invisible; D22 (la compuerta de 3 K) sigue encendida en producción con K (`CLAUDE.md:908`, según el censo; no lo re-verifiqué: SOSPECHA en esa línea), y el frente no se rehace.
- CÓMO REPRODUCIRLO: `python -B experiments/_s143_evaluador/evaluar.py --dir D:/vrp-trabajo/temporales/s160_audit/f1b/s143/s143_ab --ref-cons <main>/latest_consolidado.csv --ref-ocr <main>/data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv --B 1000 --out-json … --out-md …` (unos 8 minutos con node).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD 4: D22 sigue cerrada sobre este instrumento. (D25 no: su A/B de S157 está pendiente y no lo abrí.)

### 183. El nulo de S143 es el control contra sí mismo

- ARCHIVO:LÍNEA: `experiments/_s160_audit/f1b/s143/base.json` → `controles_instrumento.control_contra_si_mismo` (pérdidas 0, dif_neg_limpio 0); `experiments/_s143_evaluador/MUTACIONES.md:3` (25 de 27 mutaciones mueren, según el censo; leído por mí sólo el conteo).
- QUÉ PASA: un «nulo» que corre el mismo brazo contra sí mismo da cero por construcción (es la forma «gemelo que es identidad» de la tarea). Lo que sí vigila al evaluador son las mutaciones. No cambia el veredicto.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -c "import json;print(json.load(open('experiments/_s160_audit/f1b/s143/base.json'))['controles_instrumento'])"`.
- CONFIANZA: CONFIRMADO. GRAVEDAD 2.

### 184. Los evaluadores de S125 y S126 son ciegos a la cobertura

- ARCHIVO:LÍNEA: `experiments/_s126_lib.py:166-170` (`interseccion`: «Pasadas presentes en TODOS los brazos», TEXTO); `experiments/_s125_magnitud/02_veredicto_ab.py:137` (`comunes = pasadas["control"] & pasadas["C"]`).
- QUÉ PASA: si a un brazo le falta un día (un job caído, un gránulo que NASA no sirvió), la intersección lo saca de la comparación sin avisar. Medido: brazo = copia del control sin el 2026-07-15 (40 records en S126, 32 en S125). S126: el criterio 5 «cero detecciones perdidas en total» pasa a CUMPLE y el veredicto sigue NO ADOPTAR por el criterio 2 (`s126/sin_dia.txt`); S125: Láscar baja de n 55 a 53 sin ninguna marca (`s125/sin_dia.txt`). En S143 el mismo experimento excluye al volcán por «cobertura dispareja» y deja 0 noches (`s143/placebo.md:63-77`): ese evaluador sí lo ve.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -B experiments/_s160_audit/f1b/placebo.py data/_s126_corona_off <raiz>/data/_pl_corona_sin_dia sin_dia:2026-07-15` y después `correr_evaluador_raiz.py experiments/_s126_corona/01_veredicto.py <raiz> s126/sin_dia.json corona=_pl_corona_sin_dia ctx_off=_no_existe corona+ctx_off=_no_existe`.
- CONFIANZA: CONFIRMADO. GRAVEDAD 2 (no podía cambiar los veredictos reales, que fallan por falta de beneficio; sí aprobaría a un brazo que se cae en las noches en que pierde).

### 185. Seis instrumentos leyeron la referencia viva sin hash y sus ventanas pisan los hitos del OCR

- ARCHIVO:LÍNEA: `experiments/_s126_lib.py:68-69` (`FUENTES_GT = ("latest_consolidado.csv", "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv")`); `experiments/_s125_magnitud/02_veredicto_ab.py:58-59`; `experiments/_s135_ab_d1d2/evaluar_ab.py:181-182` (`load_mirova_alertas` sobre `SNAP`, el snapshot vivo); `experiments/_s129_ab_fondos/veredicto.py:31` y `:86`, `experiments/_s130_d18/veredicto_d18.py:33` y `:115` (`cargar_mirova` de `_s126_lib`, sobre 2026 entero).
- QUÉ PASA: la tabla pierde filas y el OCR reescribe alertas (plan §11.1.1); un veredicto leído contra la copia que había ese día no se puede volver a obtener. Hoy S125 y S126 reproducen el mismo veredicto con la copia congelada de `d516b9d8c` (`s125/real.txt`, `s126/real.txt`), así que en estos dos no cambió nada; en S135 no lo pude medir (brazos fuera del repo). Las ventanas (jun-ago) pisan 06-11, 06-13 y 08-06 (hitos de `calidad_referencia_mirova`, A119) sin separar.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `sha256sum` en `referencia_sha256.txt` y las corridas `real` de `s125/` y `s126/`.
- CONFIANZA: CONFIRMADO en los seis (la reproducción del veredicto sólo en S125 y S126). GRAVEDAD 2.

### 186. El pre-registro de S125 exige los 11 Tier A o no emitir veredicto, y el evaluador decide con 4

- ARCHIVO:LÍNEA: `docs/S125_AB_MAGNITUD_PREREGISTRO.md:81` («**Los 11 Tier A se listan explícitamente**, PCC incluido, o el veredicto no se emite», TEXTO, l. 81-82); `experiments/_s125_magnitud/02_veredicto_ab.py:28` (`VOLS = ["Villarrica", "PlanchonPeteroa", "Lascar", "PuyehueCordonCaulle"]`).
- QUÉ PASA: el criterio 2 del pre-registro se escribió para que ningún volcán en banda pudiera salirse sin que se viera; el evaluador sólo mira cuatro. El veredicto NO ADOPTAR no cambia (los cuatro brazos dan 3 de 4 en banda e IC solapados), pero el instrumento prometió una cobertura que no tiene.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `sed -n 28p experiments/_s125_magnitud/02_veredicto_ab.py`.
- CONFIANZA: CONFIRMADO. GRAVEDAD 2.

### 187. La prueba de Nevados de Chillán aprueba por construcción a un brazo igual al control, y su autoprueba no corre hoy

- ARCHIVO:LÍNEA: `experiments/_s150_ndc/resultado_38560317428/verificador/INFORME.md:17` («**P5_T0 CUMPLE es vacuo.** El tope no toca la etiqueta `far`, así que T0 no podía cambiar ninguna decisión», TEXTO) y `:18` («**P4 no prueba la etiqueta.**», TEXTO); `experiments/_s150_ndc/probar_medir_ndc.py:97` (`StopIteration` sobre `data/mirova_equivalent/NevadosDeChillan.json` del worktree).
- QUÉ PASA: el criterio «cero pérdidas de 1 MW o más» lo cumple cualquier brazo que no cambie nada; el pre-registro lo sabe («Nada se adopta con esta prueba», `PREREGISTRO_NDC.md:132`), y el verificador ya había dicho que P5_T0 es vacuo. Lo nuevo: la autoprueba del evaluador busca en la producción viva un record `d9_capped` y `far`, que en el worktree de hoy no existe, así que la autoprueba se cae antes de probar nada (`ndc_autoprueba_salida.txt`). Un instrumento cuya prueba depende de un dato que la producción puede dejar de tener pierde su control positivo sin avisar.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -B experiments/_s150_ndc/probar_medir_ndc.py D:/vrp-trabajo/temporales/s160_audit/f1b/tmp_ndc`.
- CONFIANZA: CONFIRMADO. GRAVEDAD 2.

### 188. El A/B diurno sobre C0: un G1 que empata con su propio p95 y una ventana que cruza #535 sin partir

- ARCHIVO:LÍNEA: `origin/loop/activo:experiments/_s151_ab_diurno/salidas/W2_W6_s154/evaluar_salida.txt:323` («G1 W3 a W6 (sin W2, decide)   M1  85.0 % - q_neg  62.0 % = +0.2303 | p95 del nulo barajado +0.2303 (mediana +0.1297) | 20 positivos, 3587 negativos procesados -> FALLA», TEXTO) y `:322` (W2 a W6: +0,1816 contra p95 +0,2446, FALLA), `:326-327` (G2: VIIRS 375 publica 2236 de 2511 diurnas, VIIRS 750 766 de 2466); `experiments/_s151_ab_diurno/PREREGISTRO.md:62-67` (W4 = 08-13 a 08-31, según el censo).
- QUÉ PASA: en W3 a W6 el estadístico observado es exactamente el p95 del nulo (con 20 positivos, M1 = 17 de 20, el soporte del nulo es discreto): decide el signo estricto de la desigualdad. No cambia el NO ADOPTAR, porque W2 a W6 falla con margen y G2 falla por saturación (el brazo diurno publica en el 89 % de las pasadas diurnas de la tabla). Y W4 cruza #535 sin partirse (R10). Este mismo evaluador decide el A/B pendiente sobre K (adenda sellada el 2026-10-18).
- CÓMO SE VE EN EL DASHBOARD: en producción sigue sólo la noche (D27 DELIBERADA); nada cambia hoy.
- CÓMO REPRODUCIRLO: `git show origin/loop/activo:experiments/_s151_ab_diurno/salidas/W2_W6_s154/evaluar_salida.txt | sed -n 322,327p`.
- CONFIANZA: CONFIRMADO. GRAVEDAD 3 (sostiene un A/B pendiente).

### 189. Los tres probes MxD03 decidieron bajo C0 sobre una ventana que cruza #535 sin tramo, con artefactos fuera del repo

- ARCHIVO:LÍNEA: `experiments/_s151_mxd03_etiquetas/README.md:68` («Records MODIS de los 11 Tier A entre el **2026-03-01 y el 2026-10-12**», TEXTO); `experiments/_s159/mxd03_prereg/PREREGISTRO_MXD03.md:3` (borrador v2 para el sello, según el censo).
- QUÉ PASA: la ventana mezcla los dos regímenes de la máscara de nube (A104) y los veredictos (PIERDE PROTEGIDA, EMPEORA, MEDIDO) salieron bajo C0, antes de K; los artefactos están en `%TEMP%` (censo), así que hoy no se pueden volver a evaluar. Está previsto repetirlos sobre K.
- CÓMO SE VE EN EL DASHBOARD: invisible (la geolocalización MODIS sigue siendo `_interp_geo`).
- CÓMO REPRODUCIRLO: `ls experiments/_s151_mxd03_*` (no hay salidas en `main`).
- CONFIANZA: SOSPECHA (veredictos y ubicación de artefactos vienen del censo de un subagente; la ventana la leí yo). GRAVEDAD 3.

### 190. El pre-registro de invierno (S149) cambió después del despacho y enmendó el recall después de evaluar mayo; sus congelados no están en el repo

- ARCHIVO:LÍNEA: `experiments/_s149_prereg_invierno/PREREGISTRO_INVIERNO.md:151` («**Enmienda del recall (2026-09-21, DESPUES de evaluar mayo; declarada como tal).**», TEXTO); `git log`: `86121536c 08:59`, `5ed619261 10:52` (A119), `4ead8b744 12:00` (v3), `1dba6c5f9 14:56` (-0300), con el despacho de mayo a las 12:30 UTC según el censo (SOSPECHA en la hora del despacho); `docs/S150_RESULTADO_MESES.md:192` («J publica al menos la mitad de las positivas: 68 de 73», TEXTO) contra el «15 de 27» del pre-registro (censo, SOSPECHA).
- QUÉ PASA: los cambios están declarados (no es un cambio escondido), pero el criterio que decidió los meses no es el que estaba sellado cuando se despachó el primero. Y los CSV congelados por mes sólo existen como `MANIFIESTO.json` (`.gitignore:40` ignora `*.csv`, censo): no se puede volver a correr el evaluador sobre la referencia que vio. La adopción en producción no se apoyó en este instrumento (fue `_s151_prereg_fk_11`).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git log --format='%h %ci %s' -- experiments/_s149_prereg_invierno/PREREGISTRO_INVIERNO.md`; `ls experiments/_s149_prereg_invierno/_congelado/mayo`.
- CONFIANZA: CONFIRMADO lo leído; SOSPECHA el «15 de 27» y la hora del despacho. GRAVEDAD 2.

### 191. La conectiva se cerró en S136 con un criterio escrito después de conocer el resultado de la fórmula

- ARCHIVO:LÍNEA: `experiments/_s136/LA_CONECTIVA_DE_LOS_TESTS_23.md:90` («Un brazo con `max` es conforme si y sólo si mantiene los **6 positivos** y cura los **3 negativos**.», TEXTO), commit `811c4a99d` del 2026-09-09 00:57 contra `91569a996` del 2026-09-08 19:18 con el 0 de 3 de la fórmula (fechas del censo, verificadas sólo la primera por mí: SOSPECHA en la segunda).
- QUÉ PASA: con n = 9 escenas del paper y el criterio escrito en medio, el «cierra la conectiva como frente» (`VEREDICTO_CONECTIVA.md:45`, censo) era un cierre sobre la lectura `min`; K adoptó `max` y A95 lo tumbó. No sigue cerrado: lo anoto porque es la forma de instrumento que el plan busca (criterio después del dato), no porque hoy decida.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git log --format='%h %ci' -- experiments/_s136/LA_CONECTIVA_DE_LOS_TESTS_23.md`.
- CONFIANZA: CONFIRMADO la línea 90 y el commit que la trae; SOSPECHA el orden contra el 0 de 3. GRAVEDAD 2.

### 192. El probe de 3 brazos (S136) cambió el evaluador después del dato

- ARCHIVO:LÍNEA: `git log -- experiments/_s136/evaluar_3brazos.py`: `135eabd9b 2026-09-08 17:27` (pre-registro y probe) y `17c4c6235 2026-09-08 17:55` (mensaje: «resultado del probe de 3 brazos», y sigue «el control de validez falla, no hay veredicto»); `experiments/_s136/RESULTADO_PROBE.md:83-87` (pasada útil, «Ambigüedad que decide Nicolás», censo).
- QUÉ PASA: el evaluador se tocó en el mismo commit que trae el resultado. El desenlace fue «indeterminado por falta de sustrato», así que no cerró nada; vale como forma.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git log --format='%h %ci %s' -- experiments/_s136/evaluar_3brazos.py`.
- CONFIANZA: CONFIRMADO el git log; SOSPECHA el contenido del cambio (no abrí el diff). GRAVEDAD 2.

### 193. El pre-registro de keep_peak (S144) entró en git en el mismo commit que el cierre

- ARCHIVO:LÍNEA: `docs/CIERRE_FRENTE_KEEP_PEAK_S144.md:3-5» («**Estado: frente CERRADO el 2026-09-19 por decisión de Nicolás.** La medida pre-registrada (…) **nunca se corrió sobre su muestra**», TEXTO); `git log --diff-filter=A -- docs/PREREGISTRO_KEEP_PEAK_DIRECCION_S144.md` = `efe644e30 2026-09-19 22:52`, un solo commit.
- QUÉ PASA: v1 a v7 y el cierre llegaron juntos; git no prueba que el criterio precediera a los controles que se midieron. El documento es honesto en que no se corrió. D19 sigue abierta y con K `keep_peak` no actúa (`CLAUDE.md` A100).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: el `git log` de arriba.
- CONFIANZA: CONFIRMADO. GRAVEDAD 1.

### 194. El presupuesto de magnitud (S151) y A2 (S146) entraron con criterio y resultado en un solo commit, y lo declaran

- ARCHIVO:LÍNEA: `experiments/_s151_presupuesto_magnitud/PREREGISTRO.md:4` («git no prueba el orden», TEXTO); `docs/audit_s146/A2_RESULTADO_VARA_CORREGIDA.md:277` («**El pre-registro no era ciego.**», TEXTO).
- QUÉ PASA: no son cierres (son estudios), pero D17 cita al presupuesto para dejar la dependencia angular SIN ATRIBUIR y A2 levantó el bloqueo formal de D21 y D22 (censo). Un insumo sin orden probado sostiene menos de lo que se le cita.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `sed -n 4p experiments/_s151_presupuesto_magnitud/PREREGISTRO.md`.
- CONFIANZA: CONFIRMADO. GRAVEDAD 1.

### 195. La autoprueba de `recuperacion_d22` (S150) es F contra F

- ARCHIVO:LÍNEA: `experiments/_s150_ab_d22/recuperacion_d22_prueba_salida.txt` («P1 (camino D22, etiqueta confiable): F2 publica 0 de 14 (umbral: 7 de 14; en las tablas 14) | FALLA», TEXTO), con F2 = F.
- QUÉ PASA: la única corrida del evaluador es la identidad; da «0 de 14» por construcción y no muestra que pueda dar distinto de cero. El A/B quedó SUSPENDIDO, así que no decidió nada; pero D22 queda cerrada sin que exista un instrumento probado para reabrirla.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `cat experiments/_s150_ab_d22/recuperacion_d22_prueba_salida.txt`.
- CONFIANZA: CONFIRMADO. GRAVEDAD 1.

### 196. Dos instrumentos dan dos recalls para el mismo control de S148 (133 contra 137 de 143)

- ARCHIVO:LÍNEA: `experiments/_s160_audit/f1b/s148/real_stdout.txt:12` («"VIIRS375": {"control_publicadas": 133, "brazo_publicadas": 135, "piso_conteo": 118, "cumple": true, "n": 143», TEXTO); `docs/S148_RESULTADO_AB_CONECTIVA.md:79» («| **P4** recall por pasada | 118 o más, ninguna pérdida de 0,5 MW o más | 137 de 143 | **135 de 143**, ninguna grande | sí |», TEXTO).
- QUÉ PASA: el brazo coincide (135) y el control no (133 contra 137): o la referencia congelada difiere entre los dos (la mía es la de `_congelado/`, la del documento también según el censo), o `lectura_por_tramo.py` y `evaluar.py` parean distinto. No lo tracé. P4 (≥ 118) se cumple con los dos números, así que no cambia el veredicto; lo que cambia es que «perdidas_contra_control» pasa de +2 a −2 según el instrumento.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: el comando de 181.
- CONFIANZA: CONFIRMADO el número; SOSPECHA la causa. GRAVEDAD 2.

## 4. La matriz (`matriz_instrumentos.csv`) y cómo se llenó

Una fila por instrumento (25, más los controles del barrido), columnas: instrumento, ruta, qué decidió, si el frente sigue cerrado, R1 a R17 y el script de cada celda medida. Las celdas medidas son las de S125, S126, S143 y S146/S148 (R2, R6; R7 en S126) y los dos controles (R3, R8); el resto es lectura, con SIN DATO donde no había datos de brazos. R1 sale de `git log --diff-filter=A --format='%h %ci' -- <pre-registro>` sobre los 21 pre-registros (salida transcrita abajo); R10 y R14 de la ventana declarada en cada pre-registro contra 2026-08-28 23:00 UTC, 2026-10-18 y los hitos de `calidad_referencia_mirova` (06-11, 06-13, 08-06, 10-09, 10-10).

Fechas R1 (primer commit del pre-registro; si cambió después, la última):
S125 79a90d026 2026-08-28 · S126 024f9f057 08-29 (adenda 08-30) · S129 262b1d644 08-30 · S130 d6d9b8e05 08-31 · S135 994c9f842 09-07 (cambios 09-07 21:45 y marca S158 10-21) · S136 A6 53f2e2708 09-08 · S136 probe 135eabd9b 09-08 · S143 cefeaeb00 09-17 (v2 aadd1766b, probe f031e13b2, decisión 1b 3ee3d15be 09-18 02:37) · S144 efe644e30 09-19 · S146 sin Test 1 3f3fb55c3 09-20 (adenda 3dfa8e974) · S146 batería fb45ec4d9 09-20 · S146 A2 61cc94e3a 09-20 · S147 conectiva 198228ef9 09-20 · S147 caja 85d8be05e 09-20 (adenda 24d10a546 09-21) · S149 invierno 86121536c 09-21 (3 commits más el mismo día) · S150 D22 70006e364 10-09 (89077f5ae 10-14) · S150 NdC 5c540b066 10-08 (3d6c6a067) · S151 diurno 0b61158fb 10-15 (hasta 2766c1980 10-17) · S151 vrp_max 1795676b8 10-14 · S151 caja d5bc604fd 10-14 (5170f9539 10-15) · S151 presupuesto 33c42ab50 10-14.

## 5. Mediciones, con las dos preguntas del instrumento en cada una

### 5.1 Control positivo (c), R3: `r3_censo_vs_ponderado.py` → `r3_censo_vs_ponderado_salida.txt`

Pregunta 1: si el ponderado excediera el techo, ¿se ve? Sí: compara `neg_encendidos` de `resumen.json` contra el conteo de negativos limpios no publicados con píxel alertado en `poblacion_completa.json`. Pregunta 2: si el script estuviera muerto, falla por `assert` al no hallar el censo. Resultado: población 5.819 pasadas (2026-04-01 a 2026-10-21, regla SN, tol 120 s); subconjunto donde F puede actuar 120 (119 sin el 18 y 19 de octubre); ponderado 152,33 encendidos > techo 119; censo 60 de 119; ΔE +104 ponderado contra +12 censado. **ENCONTRADO**. R3 FALLA del estimador ponderado; el propio frente N lo corrigió (`INFORME.md` §1 viñeta 1).

### 5.2 Control positivo (d), R8: `r8_consumidores.py` → `r8_ramaG_salida.txt`, `r8_main_salida.txt`

Pregunta 1: si la máscara no llegara al segundo pase, ¿se ve? Sí: el sitio `is_summit_mask = … <= inner_radius_km` aparece sin máscara en su contexto. Pregunta 2: si el script estuviera muerto, falla por `assert` si no halla consumidores o si el archivo no tiene `_roi1_mask`. Resultado en el código del run de la caja (`origin/s146-ab/35572961810`): 6 sitios por radio, 0 con máscara, incluido l. 1313 (segundo pase). **ENCONTRADO**. En `d516b9d8c`: 6 sitios, 2 con máscara (l. 1206 primer pase, l. 1346 segundo pase, los dos con `roi1_summit_mask`) y 4 sin (l. 725 docstring, l. 1774 `test1_hotspot_dist_km`, l. 1838 y l. 2134 `distance_class`). Los últimos tres son la etiqueta summit/far del tablero (el círculo deliberado de S14), no umbrales; `experiments/_s151_prereg_caja/cableado_salida.txt` traza por AST 8 llamadas que reciben la caja y no lista esos tres sitios porque no son consumidores de umbral. Mi instrumento es más grueso que `cableado.py` (cuenta todo lo que decide cumbre por radio); lo dejo como SEGUIMIENTO, no como hallazgo.

### 5.3 R6 y R2 por placebo: `placebo.py` + `correr_evaluador_raiz.py` (S125, S126), `evaluar.py` de S143 y de S146 (S148)

Pregunta 1: si el evaluador aprobara cualquier cosa, ¿se ve? Sí: un brazo que es el control por 1,10, por 1,2 o con la magnitud rotada entre pasadas no puede ser mejor por ninguna razón física. Pregunta 2: el generador cuenta los valores que tocó (69.967 en S126, 52.859 en S125, 37.517 en S148; 0 en `id`, declarado) y falla si no toca nada; cada harness reproduce primero el veredicto real (control positivo del harness): S126 NO ADOPTAR con 2 y 5 (igual que `S127_CORONA_RESULTADO.md:26`), S125 3 de 4 en banda e IC solapados (igual que `S125_AB_MAGNITUD_RESULTADO.md:14-16`, censo), S143 272 noches y 5/8/25/5/1 pérdidas (igual que `RESULTADO_AB_S143.md`), S148 INDECIDIBLE (igual que `S148_RESULTADO:64`).

| instrumento | id | ×1,10 | ×1,2 | desplazada | sin un día (R2) |
|---|---|---|---|---|---|
| S126 corona | NO ADOPTAR (falla 2) | NO ADOPTAR (2, 6) | NO ADOPTAR (2, 6) | NO ADOPTAR (1, 5, 6) | NO ADOPTAR (2); criterio 5 CUMPLE: **R2 FALLA** |
| S125 magnitud | 3/4 en banda, IC solapan | 3/4, solapan | 3/4, solapan | 1/4, FN nuevos | 3/4; Láscar n 53 sin aviso: **R2 FALLA** |
| S143 D22/D25 | no (criterio 2: dif 0, IC [0,0]) | no (2; 3 empeora PCC) | no (2; 3) | no (2; 3 en 6 volcanes) | volcán excluido por cobertura, 0 noches: **R2 OK** |
| S146/S148 (evaluar.py) | INDECIDIBLE; C8 y C8b falsos | ídem más C4 falso | ídem | C1 C2 C4 C6 C8b falsos | C0 cobertura falso: **R2 OK** |

R6 OK en los cuatro. Lo que frena al placebo: en S126 el criterio 2 (Villarrica tiene que BAJAR), en S125 «más volcanes en banda», en S143 el criterio 2 (publicación en negativos entera bajo cero), en S146 el nulo barajado C8 (un brazo igual al control cae dentro de su nulo, que es [0, 0]). Salidas: `s126/*.txt`, `s125/*.txt`, `s143/placebo4.md`, `s143/placebo.md` (la corrida con `sin_dia` junto a los otros cuatro excluyó a los 9 volcanes para todos: por eso hay dos corridas), `s148/placebo_stdout.txt`, `s148/sin_dia_stdout.txt`.

### 5.4 R7 por barajado, S126: `r7_barajado_s126.py` → `s126/r7_barajado_200_salida.txt`, `s126/r7_barajado_salida.txt`

Semilla 20261022, sellada en este informe a las 04:14:36 UTC antes de la primera ejecución (está en la versión anterior de este archivo y en el docstring del script). Barajado dentro de estrato volcán × sensor: los VRP de MIROVA de ese estrato se reparten al azar entre las noches que el control procesó, con el mismo número de alertas. Pregunta 1: si el instrumento aprobara con etiquetas al azar, la fracción de ADOPTAR subiría sobre 5 %. Pregunta 2: se imprime el veredicto sin barajar (NO ADOPTAR, 2 y 5: reproduce) y cuántos barajados quedaron idénticos al original (0). Resultado con 1.000 barajados (terminado a las 04:28 UTC): ADOPTAR en 0 (0,000), Wilson 95 % [0,000, 0,004], **OK**; el criterio 5 (cero pérdidas) falla en los 1.000, el 1 en 388, el 2 en 42, el 3 en 24. La corrida de respaldo con 200 dio lo mismo ([0,000, 0,019]). Lectura: con etiquetas al azar el brazo corona pierde siempre alguna detección que el control reproduce, así que este evaluador no aprueba por azar.

### 5.5 Autopruebas que no corrieron

- `experiments/_s151_prereg_caja/probar_evaluar_caja.py` pide `<TMP> <DIR_NDC>` con los `logs/` del run 38560317428, que no están en la rama (`caja_autoprueba_salida.txt`). R6 de la caja queda OK por lectura (`PREREGISTRO.md:196-197`: un CUMPLE sin huella del mecanismo es INDECIDIBLE), no por medición.
- `experiments/_s150_ndc/probar_medir_ndc.py`: hallazgo 187.

## 6. Frentes cerrados cuyo instrumento falla una fila que podía cambiar el veredicto

| frente | instrumento | fila que falla | ¿podía cambiar el veredicto? | hallazgo |
|---|---|---|---|---|
| D18 (caja de 5 × 5 km), NO ADOPTAR S130 | `docs/s130/PREREGISTRO_AB_D18.md` | R8, R9 | sí: el brazo no podía actuar; el cierre de hoy es S151 sobre otra premisa | 180 |
| D22 (compuerta de 3 K), NO ADOPTAR S143 y «no se rehace» S150 | `experiments/_s143_evaluador/evaluar.py` | R9, R10, R14 parcial | sí: la pérdida de 5 noches del literal se midió contra un control saturado en el tramo de la máscara de 260 K | 182 |
| conectiva `max` «merece el gate completo» S148 (adoptada en K) | `evaluar.py` de S146 reusado | R16 (INDECIDIBLE), R5 | no sobre la adopción (la sostiene fk_11, F1a); sí sobre lo que S148 dijo que probó | 181, 196 |
| corona Eq. 6 NO ADOPTAR S126; R1 y R2 NO ADOPTAR S125 | `01_veredicto.py`, `02_veredicto_ab.py` | R2, R14, R9 literal | no: ambos fallan por falta de beneficio y eso un placebo no lo arregla; R2 aprobaría a un brazo que se cae donde pierde | 184, 185, 186 |
| keep_peak (D19) cerrado sin medir S144 | documento | R1 | no se puede saber: no se midió | 193 |

No falla ninguna fila que pudiera cambiar el veredicto en: S135 (NO ADOPTAR, sin datos para medir; R9 y R14 fallan pero el veredicto es «sin beneficio»), S151 caja (veto; el instrumento tiene mecanismo y repetición), S151 diurno sobre C0 (G2 falla por saturación con cualquier lectura), NdC (no decidió nada).

## 7. SEGUIMIENTOS (fuera de mi eje; no los perseguí)

- **F5-03 (regla SN)**: NO resuelto por S159. `experiments/_s159/n/PREREGISTRO_N.md:20-23` sigue etiquetando con «la regla D-9 en modo SN» y dice que «PR #889 documenta que hay otras tres». Es de F1a (`clase_mirova.py`).
- **F5-04 (tres caminos al 0,0)**: NO resuelto; nadie lo cita en `experiments/_s159/` (grep «tres caminos», «negativo limpio» con 0,0: sólo `negativo_crater/`, que es otra pregunta). F1a.
- **F5-05 (`libro_de_cuentas.py` fuera de banda, noche de Terra)**: NO resuelto; 0 menciones en `experiments/_s159/` y en `tasks/BLOQUE_ARRANQUE_S160.md`. F1a lo tiene por nombre.
- **F5-06 (halo más tibio)**: resuelto EN PARTE por S159: `experiments/_s159/p3/INFORME.md:35-49` establece que ningún paper de MODIS describe halo ni interpolación y pide «un brazo con la media de vecinos y otro con el halo» (`:174`); el signo en los volcanes chilenos sigue sin medir.
- **F5-07 (filtros de artefacto sin sustrato)**: NO resuelto; sin menciones en `experiments/_s159/` (grep `isThermalArtifact`, `isCirrusArtifact`: 0 fuera de imágenes).
- **S148, recall del control 133 contra 137** (hallazgo 196): trazar si `lectura_por_tramo.py` y `evaluar.py` parean distinto o leen referencias distintas.
- **`r8_consumidores.py` en `d516b9d8c`**: l. 1774, 1838 y 2134 deciden summit/far por círculo sin la caja; `cableado.py` no los lista. Si alguna vez la caja se adopta, decidir por escrito si la etiqueta del tablero sigue el círculo (deliberado) o la caja.
- **`experiments/_s150_ndc/probar_medir_ndc.py:97`** depende de que la producción viva tenga un record `d9_capped` y `far`: la autoprueba de ese evaluador muere cuando ese dato no está.
- **PREREGISTRO_AB_D1_D2_S135.md** tiene un commit del 2026-10-21 (`09f484aa2`, marcas A113 de S158 R2): no toca aserciones según el mensaje; no abrí el diff.
- **Fila R9 del plan**: tomada al pie de la letra marca FALLA a todo A/B corrido con el Test 1 integrado encendido (S125, S126, S129, S130, S135, S136 probe, S143). Para los de magnitud (S125, S126) no está medido que la saturación de publicación afecte la magnitud; lo marco FALLA (literal) y lo digo aquí. Si la fila quería decir «el camino saturante actúa sobre la métrica que decide», S125 y S126 pasarían a SIN DATO.

## 8. VERIFICADO LIMPIO (contra qué vara)

- S126 reproduce hoy NO ADOPTAR con los criterios 2 y 5 fallando, con la referencia congelada de `d516b9d8c` (vara: `docs/S127_CORONA_RESULTADO.md:26`; comando: `s126/real.txt`).
- S125 reproduce 3 de 4 en banda e IC solapados en los 4 volcanes (vara: `docs/S125_AB_MAGNITUD_RESULTADO.md:14-16` según censo; `s125/real.txt`).
- S143 reproduce 272 noches confirmadas y las pérdidas 5/8/25/5/1 de los cinco brazos (vara: `RESULTADO_AB_S143.md`; `s143/base.md`); la cobertura dispareja sí se detecta (R2 OK).
- S148: el evaluador de S146 reproduce INDECIDIBLE y rechaza los 4 placebos por C8 (vara: `S148_RESULTADO:64-70`; `s148/real_stdout.txt`, `placebo_stdout.txt`); con un día borrado, C0 falso (R2 OK).
- R7 S126 con 1.000 barajados, semilla 20261022: 0 ADOPTAR, Wilson [0,000, 0,004] (vara: §11.2b).
- `experiments/_s146_bateria`: hash del criterio sellado 09-20 11:01 UTC antes del primer run 11:56 UTC (censo; `HASH_CRITERIO_NULO.txt:1-2`): R1 OK.
- `experiments/_s151_prereg_caja/cableado_salida.txt`: K contra KC difieren sólo en `ENABLE_ROI1_BOX_PAPER` y los dos pases reciben la caja (vara: A118): R8 OK para S151.

## 9. SIN DATO

- R6, R7 y R2 en S130, S135, S149, MxD03 (brazos fuera del repo o CSV congelados ausentes) y en S151 vrp_max (sin despachar).
- R7 en S143 y S148 (exige node mil veces).
- La autoprueba de la caja (pide `logs/` del run de NdC) y la de NdC (muere sobre la producción de hoy).
- R17 en todos los que usan `banco_paridad` (S143, S146/S148, S151 diurno, caja, NdC, saturación): F1a.
- Esfuerzo con que corrí: declarado, no verificable desde adentro.

## 10. FUERA DE ALCANCE

El veredicto de D25 (S157, PR #890); la regla de adopción de K; los bancos compartidos; el scraper; cualquier arreglo. No modifiqué nada fuera de CARPETA y `D:\vrp-trabajo\temporales\s160_audit\f1b\`; no hice commit, push ni merge; no despaché workflows; una sola llamada a la API de GitHub (la hora).
