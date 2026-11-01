# M1, meta-auditor del método de la primera ronda S158

Auditor M1, 2026-10-21 (hora del servidor 17:17 UTC al cerrar). Worktree
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s158-audit-r2-0eeee2`,
HEAD `e81bfadd5`. Todo lo que escribí está en `experiments/_s158_audit_r2/m1/` (scripts `t*.py` con su `*_salida.txt` al
lado). No toqué `pipeline/`, `data/`, `frontend/` ni `docs/`. No hice commit ni push. No corrí el evaluador de D25 ni abrí
salidas del A/B (no leí su veredicto).

Una sesión hermana (`a113`) está editando en paralelo `CLAUDE.md`, `docs/MISSION.md`, `docs/MIROVA_DIVERGENCES.md`,
`docs/HYPOTHESIS_LOG.md`, varias pruebas y otros archivos del mismo árbol sin commit. Por eso la propagación A113 la mido
en dos columnas: HEAD (lo que dejó la primera ronda, `git show HEAD:archivo`) y TRAB (el árbol de hoy, que sigue
cambiando). Mis citas de línea son de HEAD salvo que diga TRAB.

Lo que NO leí, por las reglas de este alcance: el veredicto del A/B de D25. Lo que sí leí: `docs/PLAN_AUDITORIA_S158.md`,
`docs/AUDIT_S158.md`, los nueve informes `f1` a `f6` y `v1` a `v3` con sus scripts, el oráculo, su prueba, el brief. De
`docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md` (no está en mi lista) sólo hice `grep` de líneas citadas por otros frentes.

## 0. En una pantalla

1. **Los números de la primera ronda aguantan.** Reconstruí por un camino propio seis de ellos (pareo del OSF 2025, curva
   con el cenit, escalón de 50° del OSF V750, corte de 30 km, cúmulos de VIIRS 750 en cero, fracción del mínimo de
   escena) y reproduje todos exactos (§3). El pareo de F3, que V3 había "verificado" regenerándolo con el mismo script,
   también sale igual cuando lo escribo desde cero exigiendo el mismo satélite.
2. **Lo que no aguanta es la lectura de causa y la propagación.** (a) El AUDIT §0 convierte condiciones necesarias en
   causas (compuerta de 3 K, "la brecha entera es el fondo") y presenta la causa del hueco del A/B de D25 como si fuera de
   la NASA, cuando los records de producción la contradicen (H2). (b) Los límites que F6 le puso al código ("compacto",
   escalón de 50°, corte de 30 km, umbrales sin contraste) no bajaron a ninguno de los documentos que dicen "el código
   manda" (H1). (c) El censo de F2 se dejó D18, D8 y D27 sin marcar y no entró a la memoria del agente (H5, §5).
3. **Instrumentos que no podían fallar**: los controles de Etna para K1, mínimo de dNTI, media de 3 × 3, `max` contra
   `min` y recorte (ya declarado por la ronda 1, lo confirmé); el control "0 de 48" de V1 sobre la compuerta; el "todos
   los píxeles con `bt <= t_bg`" de los cúmulos en cero (identidad del recorte); la igualdad de k y área del VRP como
   prueba de que "toda la brecha es el fondo" (sustituir el fondo del oráculo en la fórmula da, por construcción, el VRP
   del oráculo).
4. **El oráculo valida el fondo sólo a ±1,4 %**, no a 0,09 %: el desempate de la triangulación de `griddata` mueve el VRP
   de Etna entre -1,37 % y +1,44 % contra el OSF (30 desempates al azar). El 0,09 % es la convención elegida mirando ese
   mismo caso (H3).
5. **Ventana K**: la primera ronda restringe mediciones a desde el 2026-09-18 "porque los datos cambian de detector". En
   el árbol de hoy, los 71.968 records de los 11 Tier A desde 2025-02 descienden de K y de #535 (37 de 37 `codigo_sha`), y
   el perfil del reproceso histórico difiere del de producción sólo en su nombre y su carpeta (2 de 146 claves). La
   restricción cuesta potencia (Muy Bajo 8 de 19: IC95 23 a 64 %) sin comprar pureza (H7).

## 1. Tabla de instrumentos

Veredicto: PUEDE FALLAR (lo probé o lo leí y el instrumento tiene poder, aunque el resultado haya salido bien), NO PODÍA
FALLAR (por construcción o por no ejercitar lo que dice medir), NO PUDE PROBARLO (razón en la última columna).

| # | instrumento | dónde | qué podía fallar | prueba que hice | veredicto |
|---|---|---|---|---|---|
| 1 | Control de Etna del oráculo: 5 píxeles, VRP -0,09 % contra OSF | `experiments/_s158_oraculo_mirova/README.md`, `tests/test_oraculo_mirova_v750_s158.py` | detección de cumbre, fondo, fórmula | `pytest` 6 passed (`t17_pytest_oraculo_salida.txt`) | PUEDE FALLAR para detección de cumbre y fórmula |
| 1b | Mismo control, el fondo | idem | el fondo interpolado (`fillmissing2`) | `t19_oraculo_empates.py`: columna/fila -0,09 %, fila/columna -0,85 %, 30 desempates al azar de 1e-9: -1,37 % a +1,44 % | PUEDE FALLAR sólo a ±1,4 %; el 0,09 % es de una convención ajustada a un caso (H3) |
| 2 | Mismo control, K1, mínimo de dNTI fuera, 3 × 3 con central, `max`/`min`, recorte | idem, `mutar_oraculo.py` | umbrales y conectiva | re-corrí las mutaciones (`t21_mutaciones_oraculo_rerun_salida.txt`): 5 de 8 dan "igual" | NO PODÍA FALLAR (la ronda 1 lo declaró; confirmado) |
| 3 | "Con nuestro k y el fondo de MIROVA da 9,8809 MW, así que toda la brecha es el fondo" | `v1/h1_fondo_etna.py`, AUDIT §0.1 | k, área | k nuestro = 19,7 × 562.500 = k del `.m` por aritmética; reemplazar el fondo del oráculo en la fórmula da el VRP del oráculo | NO PODÍA FALLAR como control de identidad. La evidencia real es el 0,09 % contra el OSF, un caso |
| 4 | "Nosotros 2,748 MW" en Etna (F1, V1) | `f1/nuestro_k_en_grilla.py`, `v1/h1_fondo_etna.py` | que sea producción | es nuestra fórmula sobre la grilla remuestreada de MIROVA, con anillo de 5 a 25 km tomado de esa grilla; producción corre en barrido nativo | NO PUDE PROBARLO (no hay L1B); el supuesto está declarado en V1 y omitido en AUDIT §0.1 |
| 5 | Predicado del tablero ejecutado con node | `f1/predicado_tablero.js`, usado por F1 y V1 | divergencia con `index.html` | leído; F5 lo cruzó con una réplica en Python (0 discordancias en 3.573 records). No lo re-corrí | PUEDE FALLAR; dependencia común de F1 y V1 |
| 6 | `diag_n_first_pass_pixels == 0` y `diag_n_second_pass_recapture > 0` | `pipeline/process_viirs_mod.py:1474-1487`, `pipeline/detection_context.py:501-512`, `process_viirs_mod.py:904-916` | confundir "primer pase vacío" con "primer pase no corrió" | lectura: con `fp_diag is None` el segundo pase no corre (`eti_for_second_pass` queda sin definir). Entonces primer pase 0 y segundo > 0 implica que el primero corrió | PUEDE FALLAR; es válido |
| 6b | Control "0 de 48 sin primer pase vacío con píxel sobre la compuerta" (V1) | `v1/h5_compuerta.py` | atribución a la compuerta | un primer pase no vacío exige `bt > t_bg + 3 K` (`detection_context.py:546`), así que el control es cierto por definición | NO PODÍA FALLAR |
| 6c | Atribución de los 19 de 67 a la compuerta | AUDIT §0.3, F1-H5, V1 | que el segundo pase sea sólo más permisivo | "0 píxeles sobre la compuerta" prueba necesidad. La suficiencia (que sin compuerta el primer pase los detecte) sólo se probó en Etna | NO PUDE PROBARLO en Chile (sin dNTI por píxel ni L1B) |
| 7 | Cúmulos de VIIRS 750 en 0 MW | `v3/h1_recorte_v750.py`, `f3/recorte_todos.py` | conteo | recuento propio `t13_recorte_v750_independiente.py`: 855 records, 235 cúmulos de cumbre en 0, 54 coinciden con alerta de la tabla; V3: 855, 235, 55 | PUEDE FALLAR, pasó |
| 7b | "Todos sus píxeles con `bt <= t_bg`" en esos cúmulos | idem | mecanismo del recorte | es la identidad del recorte (cúmulo en 0 si y sólo si ningún píxel supera el fondo): 234 de 235 en mi recuento | NO PODÍA FALLAR |
| 8 | Pareo OSF 2025 ↔ records y tabla del cenit (F3-H2) | `f3/descomp_osf2025.py`, `v3/h2_cenit.py` | pasadas distintas, satélites cruzados | `t11_pareo_independiente.py` (desde cero, exige mismo satélite): 1.652 pares, conteo 0,902 / 0,649 / 0,422, energía 0,979 / 0,716 / 0,481, Spearman de N_M con cenit 0,042 | PUEDE FALLAR, pasó. V3 sólo lo había reusado |
| 9 | Fondo por píxel MIROVA contra nuestro (F3-H4) | `v3/h4_fondo.py` | sesgo de selección del OSF | no re-medido. Control natural: los volcanes con kernel local dan 1,03 a 1,08 | NO PUDE PROBARLO yo; PUEDE FALLAR en V3 |
| 10 | Identidad del VRP del OSF y escalón de 50° (F6-1) | `f6/m1`, `m16`, `v1/f6_1_cenit.py` | tolerancia, k, definición de ΔL | `t5_osf_identidad_750.py`: 8.239 de 34.250 sobre 50°, 0 de 66.391 en o bajo 50°, igual con tolerancias de 1e-6 a 1e-2; 375 y MODIS 0 fuera; k de 750 sobre 375 falla 252.374 de 252.374 | PUEDE FALLAR, pasó |
| 11 | Corte de `Max_Dist` a 30 km (F6-H2) | `f6/m10` | artefacto de un sensor | `t20_osf_corte_30km.py`: 0 filas sobre 30.000 m en 615.470, caída gradual hasta el corte | PUEDE FALLAR, pasó |
| 12 | Fracción de pasadas con `μ + 10σ` bajo el mínimo (F4-H1, V3) | `f4/04_*`, `v3/h5_minimo_escena.py` | σ que no es el del umbral | `t16_minimo_escena_independiente.py`: V750 5,7 / 84,5 %, V375 10,0 / 96,3 %, MODIS 7,5 / 63,5 % (< 0,010 / < 0,0225). Límite: σ del barrido nativo, no de la grilla de MIROVA | PUEDE FALLAR, pasó |
| 13 | Cota de K1 con `diag_nti_max` de los negativos limpios (F4-H2) | `f4/04_*` | dominio del máximo | `process_viirs_mod.py:538,596`: `roi_mask` es la caja de 50 × 50 km, el mismo dominio que la ventana de MIROVA | NO PODÍA distinguir -0,7 de -0,8 (lo declara F4); el dominio es válido |
| 14 | Alertas de la tabla en VIIRS 750 | `latest_consolidado.csv`, `Sensor == "VIIRS"` | rótulo de sensor | `t3_alertas_definiciones.py`: 51 en la ventana K, igual a F1. Mi propio control de cuantización de distancias salió mal por mi tolerancia (86 % contra 53 %); me apoyo en el de F6 (M12), que leí | PUEDE FALLAR; el control es de F6, no mío |
| 15 | Premisa de V1: la `Distancia_km` de Cordón Caulle se mide desde `mirova_center` | `v1/h3_caja.py`, F1-H3 | acimut ausente (A93) | `t4_distancia_origen.py`: |Dist MIROVA - distancia de nuestro cúmulo a `mirova_center`| mediana 0,27 km (p90 0,68) en 33 pares V750 desde 2026-03; contra el cráter 7,55 km | PUEDE FALLAR, pasó |
| 16 | "MIROVA nunca publicó a más de 8,55 km" (V1) | idem | que la lectura A oculte alertas lejanas | `t14_pcc_lejanas.py`: Cordón Caulle tiene 0 filas FALSO_POSITIVO en 1.294 de V750; Láscar, Chillán e Isluga sí las tienen (6, 17, 8) | PUEDE FALLAR, pasó |
| 17 | Pareo con tolerancias distintas: F1 20 min, V1 8 min, F3 5 min, V2 minuto exacto | `f1/alertas_mirova_perdidas.py:49`, `f1/cruce_referencia.py:56` | cruzar satélites | `t15_separacion_satelites.py`: 2.188 de 9.275 pares consecutivos de satélites distintos están a 18 min; de 279 alertas V750 de la tabla (desde marzo), 275 tienen record a menos de 1 min y 4 no tienen a menos de 20 | PUEDE FALLAR; con V750 no hubo ambigüedad. Riesgo latente con 20 min |
| 18 | Reparto por día de la búsqueda por ventana | `pipeline/fetch.py:554-583` (`_repartir_por_dia`) | perder el último día | `t12c_repartir_por_dia.py` (extraída por AST): granules de las 05:06 y 05:42 del 18-oct caen en el día 18; el de medianoche da días 17 y 18 | PUEDE FALLAR; no es la causa del hueco |
| 19 | Cobertura del A/B de D25 | `v2/f501_cobertura.py` | causa del hueco | `t12_cobertura_dias.py` sobre producción: los 86 records VIIRS del 18-oct existen y son `standard`; los granules traen hora de proceso del 18-oct 10:38 y 12:18 UTC | PUEDE FALLAR el conteo; la CAUSA la contradicen los datos (H2) |
| 20 | Métrica M del A/B (placebo) | `v2/v2_m1_rerun.py` | que M premie cualquier subida | V2 re-corrió el script de F5 sin cambios. Mi chequeo es algebraico: si `c·K ≤ M`, `d = -log10(c)` exacto. No re-medí la fracción de pares con `K/M ≤ 1/1,10` | NO PUDE PROBARLO por otro camino (no corro el evaluador); el álgebra sí vale |
| 21 | Censo de afirmaciones de F2 | `f2/censo_afirmaciones.py` | frases con otras palabras | `t9b_propagacion_curada.py`: D18 "igual para todos", D8, D27 y la memoria del agente quedaron fuera (H5) | PUEDE FALLAR, falló |
| 22 | Marcas A113 del AUDIT §3 | `docs/` | que existan y digan lo verificado | HEAD: existen en D1, D17, D19, D22, D23, D25, D26, D29, D32, D34, glosario, A76, MISSION; no llevan los límites de F6 ni F4-H6 (H1, U1) | PUEDE FALLAR, falló parcialmente |
| 23 | Ventana K como límite de pureza | todos los frentes | mezcla de detectores | `t2b_regimen_tierA.py`: 37 de 37 `codigo_sha` descienden de #850 y #535; `t2d_diff_perfiles.py`: el perfil histórico difiere en 2 de 146 claves (nombre y carpeta) | PUEDE FALLAR, pasó. La restricción es innecesaria |
| 24 | Ejecución real del `.m` de MIROVA | todo el AUDIT | que el port no sea el `.m` | no hay MATLAB ni Octave en el computador; el port está validado en una pasada | NO PUDE PROBARLO |

## 2. Afirmaciones del método de la primera ronda

| afirmación | veredicto | evidencia |
|---|---|---|
| "Lo que este documento llama CONFIRMADO lo confirmó un verificador que no vio el trabajo del auditor" (AUDIT, encabezado) | CON MATIZ | No vieron los informes, pero reusaron instrumentos: V1 usó `f1/predicado_tablero.js` y el oráculo; V2 re-corrió `f5/m1` sin cambios para F5-02; V3 regeneró el pareo con `f3/descomp_osf2025.py` (idéntico celda a celda) antes de medir. En F3-H2 el pareo era un punto único de falla; mi reconstrucción (§1 fila 8) lo cierra |
| "Gravedad final = la del verificador" (AUDIT §1) | CON MATIZ | Se cumple fila por fila, pero la misma raíz queda con gravedades distintas: F1-H1 en 4 (V1) y F3-H1 / F3-H4 en 3 (V3), con 0 noches y 0 alertas protegidas perdidas en V3. No es un error, pero un lector toma el 4 |
| "Cero gránulos se registra como cobertura completa, y por eso al A/B le falta el 18-oct" (AUDIT §0.6) | CON MATIZ | El mensaje y los `n=0` son ciertos. "Por eso" no: el mensaje explica que nadie lo viera, no que faltaran (H2) |
| "La brecha entera es el fondo" (AUDIT §0.1) | CON MATIZ | Cierto en Etna (28 % contra ±1,4 % de incertidumbre numérica), un caso; en Chile V1 lo marca SOSPECHA y V3 mide Chillán en dirección contraria (fondo de MIROVA 1,17 veces el nuestro) y Láscar sin cambio |
| "Con el fondo de MIROVA el déficit a nadir desaparece en Copahue e Isluga" (AUDIT §0.1) | CON MATIZ | Son medianas a cenit ≤ 40° (no nadir); en sumas, Isluga 1,09 y Copahue 1,37 con n = 18 (V3) |
| "La compuerta vacía el primer pase en cumbres frías" (AUDIT §0.3) | CON MATIZ | Necesidad medida en Chile (0 píxeles sobre la compuerta), suficiencia sólo en Etna (§1, filas 6b y 6c) |
| "Las cuatro [afirmaciones del AUDIT] quedaron marcadas en sus documentos" (AUDIT §2) | CON MATIZ | Tres sí en HEAD (oráculo README, `DISENO_D17` §3.6, `S158_CODIGO` l. 170). La de D17 sigue diciendo "pendiente del verificador" aunque V3 la confirmó (`DISENO_D17_REMUESTREO_UTM.md:282`) |
| Números del AUDIT con ventana y denominador (regla A90) | REFUTADA en parte | Faltan en el texto del AUDIT: "235 de 855" (2026-03-01 a 2026-10-20, noche), "19 de 67" (ventana K), "0,98 a 0,72 a 0,48" (V375, 2025, clase 1, un solo tipo de pasada), "~79 %" (marzo a octubre, 10.755 pasadas), "8 publicados de PCC", "24 %, mediana 0,51" (OSF 2012 a 2025). Están en los informes, no en el documento que se lee primero |

## 3. Hallazgos nuevos

### H1. Los límites que F6 le puso al código no bajaron a ningún documento que dice "el código manda en VIIRS 750"
- ARCHIVO:LÍNEA: HEAD `CLAUDE.md:117-120` (TRAB 123), `docs/MISSION.md:124-130`, `docs/MIROVA_DIVERGENCES.md:3265` (título de D34, "difiere de producción en 10 de 13") y `:3279` (Alcance), memoria `MEMORY.md:122`. Fuente de los límites: `experiments/_s158_audit/f6/INFORME.md` H1, H2, H3; mi recuento `t5_osf_identidad_750_salida.txt` y `t20_osf_corte_30km_salida.txt`.
- QUÉ PASA: el repositorio publicado se declara compacto (README, "Scope"), el OSF muestra que sobre 50° de cenit el VRP de VIIRS 750 no sigue el código en 8.239 de 34.250 filas (0 de 66.391 en o bajo 50°), ninguna alerta del OSF pasa de 30 km de la cumbre aunque la grilla llegaría a 33,9 km, y el único caso reproducido (Etna) no ejercita K1, mínimos, 3 × 3 ni recorte (§1 fila 2). Los pasajes que fundan "para VIIRS 750 manda el código" dicen "código operacional" sin esos límites. Quien lea CLAUDE.md o MISSION adoptaría K1 de -0,7 y mínimo de 0,02 "porque lo dice el código" sin saber que ninguno de los dos tiene contraste con un resultado publicado.
- CÓMO SE VE EN EL DASHBOARD: invisible hoy; es una puerta a un cambio de umbrales de producción sin medición.
- CÓMO REPRODUCIRLO: `grep -n -E "sobre 50° de cenit|escalón|compacto|30 km de la cumbre" CLAUDE.md docs/MISSION.md docs/MIROVA_DIVERGENCES.md` da 0 resultados relevantes (TRAB y HEAD); `python -B experiments/_s158_audit_r2/m1/t5_osf_identidad_750.py`.
- CONFIANZA: CONFIRMADO (grep y recuento propios).
- GRAVEDAD: 3.

### H2. La causa del hueco del 18-oct se escribió como hecho de la NASA y los records de producción la contradicen
- ARCHIVO:LÍNEA: `experiments/_s158_audit/v2/INFORME.md` F5-01 "QUÉ PASA" (afirma que el Standard "todavía no los traía y el NRT ya no"; su propia CONFIANZA dice SOSPECHA), AUDIT §0.6 y §4 decisión 1. Evidencia mía: `t12_cobertura_dias.py` y `t12b_processed_salida.txt`.
- QUÉ PASA: en `data/mirova_equivalent/NevadosDeChillan.json` los records VIIRS del 2026-10-18 son `standard` y sus granules llevan hora de proceso del propio 18-oct (`VJ202IMG.A2026291.0506.021.2026291103813.nc`, proceso 10:38 UTC; `VNP02IMG.A2026291.0542.002.2026291121847.nc`, 12:18 UTC). Los 86 records VIIRS de los 11 Tier A de ese día existen en producción (primer proceso 06:44 a 09:20 UTC y última actualización 11:03 a 13:59 UTC del propio 18-oct). O sea que el Standard de ese día existía tres días antes del reproceso del 21-oct. "No estaba en la NASA" no es compatible con eso. Tampoco es el reparto por día (`_repartir_por_dia` asigna bien el último día, `t12c`). La causa queda sin identificar (¿índice de CMR, búsqueda por ventana de S157, caché?).
- CÓMO SE VE EN EL DASHBOARD: invisible. Importa porque la decisión 1 del AUDIT ("reponer el 18-oct") y la 2 ("cero gránulos es falla") asumen que reponer es posible y que el defecto es sólo de aviso. Si el defecto es de la búsqueda, un reproceso idéntico vuelve a perder el día y el aviso sólo lo hace fallar.
- CÓMO REPRODUCIRLO: `python -B experiments/_s158_audit_r2/m1/t12_cobertura_dias.py`. Prueba que falta (la propone esta auditoría, no la hice porque exige red de NASA): repetir un día corto con `VRP_BUSQUEDA_VENTANA=0` (búsqueda por día) y comparar `n_l1b` del 18-oct.
- CONFIANZA: CONFIRMADO que la explicación del informe está contradicha por los datos de producción; SOSPECHA para la causa real.
- GRAVEDAD: 3.

### H3. El oráculo valida el fondo a ±1,4 %, no a 0,09 %
- ARCHIVO:LÍNEA: `experiments/_s158_oraculo_mirova/mirova_v750.py:187-200` (`_fillmissing2_linear`, comentario "comprobado contra UN solo caso"); `t19_oraculo_empates_salida.txt`.
- QUÉ PASA: `fillmissing2` de MATLAB no se puede ejecutar; el port usa `griddata` lineal, y en una grilla regular los empates de la triangulación cambian el resultado. Con la convención del port el VRP de Etna queda -0,087 % del OSF; con fila y columna, -0,85 %; con 30 desempates al azar de 1e-9, entre -1,37 % y +1,44 %. La convención se eligió mirando este caso, de modo que el 0,09 % no es una validación independiente del fondo.
- Consecuencia: la mutación "sin dilatación" (+0,76 %) no se distingue del ruido, y el brazo D25 del oráculo (+2,65 %) queda a 1,9 veces la amplitud. F5-06 ("el halo no está más tibio, D sube 2,7 %") conserva el signo pero con poco margen. No afecta la conclusión de Etna (el fondo escalar da 28 % del VRP de MIROVA).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -B experiments/_s158_audit_r2/m1/t19_oraculo_empates.py` (trabaja sobre una copia del módulo en `m1/_copia/`).
- CONFIANZA: CONFIRMADO (medido).
- GRAVEDAD: 2.

### H4. El AUDIT §0 convierte condiciones necesarias en causas
Cuatro casos, todos con la evidencia dentro de los propios informes:
- Compuerta de 3 K: "0 píxeles sobre la compuerta" en los 19 es necesario, no suficiente (§1 filas 6b y 6c). El control "0 de 48" es cierto por definición.
- "La brecha entera es el fondo": N = 1 (Etna), con nuestra fórmula aplicada sobre la grilla de MIROVA, no producción (§1 filas 3 y 4); en Chile, Chillán (el volcán en erupción) tiene el fondo de MIROVA 1,17 veces el nuestro, o sea al revés, y Láscar no cambia (V3 H4).
- "Todos los píxeles con `bt <= t_bg`" en los 235 cúmulos en cero es la definición del recorte (234 de 235 en mi recuento; el restante no tiene `bt` en la lista).
- Causa del hueco del A/B: H2.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 3 (el AUDIT es el documento que se lee primero y alimenta las decisiones 1, 3 y 4).

### H5. El censo de F2 dejó fuera D18 "igual para todos", D8 y D27, y no entró a la memoria del agente
- ARCHIVO:LÍNEA: HEAD `docs/MIROVA_DIVERGENCES.md:2358` (título de D18: "una CAJA de 5 km igual para todos") y `:2442` ("brazo fiel es una caja de 5 × 5 km uniforme"); `:1315` (D8 "Coppola 2024 L1129 literal"); `:2848` y `:2856` (D27, K1 diurno de -0,6). Memoria `reference_mirova_daytime_cloud_artifact.md:29` y `feedback_mirova_no_human_supervision.md:37` (A76 "supervisión MANUAL").
- QUÉ PASA: el código dice que las ROI "can be shifted, reshaped or resized" por volcán (`MIROVA_VIIRS750_hotspot_detection.m` l. 120-125) y V1 lo comprobó en Cordón Caulle (también `t4` y `t14`: las alertas de MIROVA caen a 7,8 km del centro de su grilla, o sea en el cráter, fuera de la caja de 7 × 7). F2 dio la fila 22 (D18, caja de celdas) y la fila 19 ("uniforme entre volcanes") por CONFIRMADAS sin ver que el título de D18 dice lo contrario. D27 y D8 estaban en la tabla de F2 (filas 6 y 5) pero el AUDIT §3 no las lista entre las marcas puestas. A76 en la memoria sigue diciendo que MIROVA no filtra de día por gate, cuando el código rechaza la escena con reflejo solar bajo 12° (F6-m9, F5).
- CÓMO SE VE EN EL DASHBOARD: invisible. Pesa en la decisión 7 (D-10, A/B diurno con K1 de -0,6 mientras el código usa -0,5) y en cualquier A/B de la caja (D18).
- CÓMO REPRODUCIRLO: `python -B experiments/_s158_audit_r2/m1/t9b_propagacion_curada.py` (filas 5, 6, 13, 14).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### H6. Propagación A113 pendiente (lista completa en §5)
Catorce grupos de pasajes (U1 a U14 del §5) siguen sin marca o con una marca incompleta en HEAD; la sesión hermana ya marca varios en TRAB, pero sin commit. CONFIANZA: CONFIRMADO. GRAVEDAD: 2.

### H7. La ventana K del 2026-09-18 es más estrecha de lo necesario
- ARCHIVO:SALIDA: `t2b_regimen_tierA_salida.txt`, `t2d_diff_perfiles_salida.txt`, `t2c_perfil_salida.txt`, `t18_wilson_salida.txt`.
- QUÉ PASA: 68.072 de los 71.968 records de los 11 Tier A (2025-02 a hoy) llevan `perfil = _s154_reproc_k_historico` y los 3.896 restantes `mirova_equivalent`; los dos perfiles difieren sólo en `PROFILE_NAME` y `DATA_SUBDIR` (2 de 146 claves; el control `experimental` difiere en 5). Los 37 `codigo_sha` presentes descienden de #850 y de #535; no hay un solo record `preK` ni sin régimen. La pureza que justificaba cortar en 2026-09-18 ya existe en toda la historia. El corte deja cifras de potencia baja: Muy Bajo 8 de 19 (IC95 de Wilson 23 a 64 %), cumbre en cero 7 de 51 (7 a 26 %), PCC fuera de la caja 15 de 67 (14 a 34 %).
- CÓMO SE VE EN EL DASHBOARD: invisible. Los frentes que no cortaron en K (F3, F4, V3) quedaron bien parados; los que sí (F1, V1, V2) podrían reportar con 2026-03-01 en adelante (A119 limita por el lado de la referencia, no por el del detector).
- CONFIANZA: CONFIRMADO. GRAVEDAD: 2.

### H8. "Alerta de MIROVA" tiene al menos cuatro definiciones en la primera ronda y el AUDIT no las nombra
- F1: sólo la tabla (`ALERTA_TERMICA`, `Sensor == "VIIRS"`, 51 en la ventana K; reproducido en `t3`). V1: tabla más OCR sin duplicar (62; 58 nocturnas y 4 diurnas). V3, F3, F4: `banco_paridad` (tabla ∪ OCR, regla SN, "304 pasadas V750 con alerta de MIROVA"). F5: la referencia congelada de V1 del pre-registro de D25. Pareo: 20 min (F1), 8 min (V1), 5 min (F3), minuto exacto (V2).
- Efecto medido sobre las alertas V750 de la tabla: ninguno (§1 fila 17). Pero "7 alertas de MIROVA" (V1-1), "55 de 304" (V3), "26 de 136" (F1) no son comparables entre sí y el AUDIT las mezcla en §0.1.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 1.

### H9. Una marca de la primera ronda quedó desactualizada
- `docs/DISENO_D17_REMUESTREO_UTM.md:282`: "pendiente del verificador" para la rebaja de F3, que V3 ya confirmó. CONFIANZA: CONFIRMADO. GRAVEDAD: 1.

## 4. VERIFICADO LIMPIO

Cada ítem dice contra qué vara y con qué comando.

| qué | vara | comando |
|---|---|---|
| Todos los records de los 11 Tier A descienden de K (#850) y de #535 | `git merge-base --is-ancestor` sobre cada `regimen.codigo_sha`; control: K no es ancestro de #535 y #535 sí lo es de K | `python -B experiments/_s158_audit_r2/m1/t2b_regimen_tierA.py`, `t2c_perfil.py` |
| El perfil del reproceso histórico es el de producción | `pipeline.profile` con `VRP_PROFILE` (regla A89), 146 claves; control: `experimental` difiere en 5 | `python -B experiments/_s158_audit_r2/m1/t2d_diff_perfiles.py` |
| Escalón de 50° del OSF V750 (F6-1) | OSF v2.5 completo, 615.470 filas; controles en 375, MODIS y k cruzado | `python -B experiments/_s158_audit_r2/m1/t5_osf_identidad_750.py` |
| Corte de 30 km (F6-H2) | OSF v2.5 completo | `python -B experiments/_s158_audit_r2/m1/t20_osf_corte_30km.py` |
| Curva del cenit de F3-H2, con pareo propio y mismo satélite | OSF v2.5, records de hoy | `python -B experiments/_s158_audit_r2/m1/t11_pareo_independiente.py` |
| 235 cúmulos de cumbre de VIIRS 750 en cero de 855 | records de hoy, tabla | `python -B experiments/_s158_audit_r2/m1/t13_recorte_v750_independiente.py` |
| Fracción de pasadas bajo el mínimo de escena (V750 84,5 % bajo 0,0225) | records de hoy, perfil efectivo | `python -B experiments/_s158_audit_r2/m1/t16_minimo_escena_independiente.py` |
| Premisa de V1 sobre Cordón Caulle (la `Distancia_km` de MIROVA es desde el centro de su grilla; MIROVA no publicó lejos) | tabla y nuestras posiciones | `t4_distancia_origen.py`, `t14_pcc_lejanas.py` |
| Reparto por día de la búsqueda por ventana | `pipeline/fetch.py` extraído por AST, granules sintéticos | `t12c_repartir_por_dia.py` |
| Alertas V750 de la tabla: 51 en la ventana K; ninguna pareada ambiguamente | `latest_consolidado.csv` | `t3_alertas_definiciones.py`, `t15_separacion_satelites.py` |
| Pruebas del oráculo | `tests/test_oraculo_mirova_v750_s158.py` | `python -B -m pytest tests/test_oraculo_mirova_v750_s158.py -q -p no:cacheprovider` (6 passed) |
| `nti_max` es del dominio de 50 × 50 km | `pipeline/process_viirs_mod.py:538,596` | lectura |
| Un segundo pase sin primer pase no puede ocurrir con `fp_diag` nulo | `pipeline/process_viirs_mod.py:904-916`, `detection_context.py:501-512` | lectura |

## 5. Propagaciones A113 pendientes, con archivo y línea

Comandos de búsqueda (para auditar mi cobertura): `python -B experiments/_s158_audit_r2/m1/t9_propagacion_A113.py`
(regex amplios, 20 afirmaciones, ventana de ±6 líneas; es un piso con falsos positivos, por eso lo curé a mano) y
`python -B experiments/_s158_audit_r2/m1/t9b_propagacion_curada.py` (51 anclas verificadas, ventana [-8, +12], columnas HEAD
y TRAB; ojo: una marca puesta al inicio de una sección, como la de D19, queda fuera de la ventana y sale "0/1": en esos
casos revisé a mano). Archivos buscados: `CLAUDE.md`, `docs/MISSION.md`, `docs/MIROVA_DIVERGENCES.md`, `docs/SINTOMAS.md`,
`docs/META_RULES_S80.md`, `docs/FICHA_SDA_VRP_CHILE.md`, `pipeline/profiles/mirova_equivalent.yaml`, `pipeline/*.py`,
`tests/*.py`, los pre-registros D25 y D1/D2, y en la memoria del agente `MEMORY.md`, `project_s157_estado.md`, `feedback_*.md`,
`reference_*.md`. No entré a `documentacion/` salvo `BIBLIOGRAPHY_SYNTHESIS.md`.

Estado a las 17:20 UTC. "Sin marca" = no hay "S158" en ±8/+12 líneas en TRAB.

| # | pasaje | de qué conclusión de la primera ronda | HEAD | TRAB | nota |
|---|---|---|---|---|---|
| U1 | `docs/MIROVA_DIVERGENCES.md:3279` (D34, Alcance: "La estructura se puede trasladar a MODIS y VIIRS 375 con cita"); TRAB l. 3314 | F4-H6, confirmado y reforzado por V3 | sin marca | sin marca | la misma frase está en `docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md` l. 191, 211 y 281 |
| U2 | `CLAUDE.md:117-120` (TRAB 123), `docs/MISSION.md:124-130`, D34 título `:3265`, memoria `MEMORY.md:122` | F6-H1, H2, H3 (límites del código) | marca sin límites | marca sin límites | H1 |
| U3 | `docs/MIROVA_DIVERGENCES.md:2358` (D18, "igual para todos") y `:2442` | H:120-125, F1-H3 / V1 (Cordón Caulle) | sin marca | sin marca | H5 |
| U4 | `docs/MIROVA_DIVERGENCES.md:2848, 2856` (D27); `tests/test_rama_diurna_viirs_s151.py:114-118`; `experiments/_s151_ab_diurno/PREREGISTRO.md:18`; `pipeline/diurno.py:128` | F2-H6, F4-H7, V1-3 (K1 diurno -0,5 y reflejo bajo 12°) | sin marca | D27 sin marca | decisión 7 |
| U5 | `docs/MIROVA_DIVERGENCES.md:1315` (D8, "L1129 literal"); `pipeline/profiles/mirova_equivalent.yaml:449`; `tests/test_local_kernel_background.py:1-6` | F2-H5 | sin marca | D8 y yaml sin marca | en VIIRS 750 el kernel ni existe (`process_viirs_mod.py:461-468`) |
| U6 | `pipeline/profiles/mirova_equivalent.yaml:47` (K1 -0,8), `:114-124` y `:253` (8 vecinos, "Coppola 2016a Table 2"), `:292` (sin máscaras), `:440` (condicionado), `:465` (recorte) | D34, F2-H3, H2, H7, F2 filas 8, 9, 11 | sin marca | sin marca | comentarios que se leen al editar el perfil |
| U7 | `pipeline/detection_context.py:883-898` ("DOS condiciones") y `:977` (comentario "MÁSCARA DE SATURACIÓN") | F2-H2, H8 | sin marca | sin marca | código: marca como comentario, sin tocar lógica (A45) |
| U8 | `docs/MIROVA_DIVERGENCES.md:1089` (TRAB 1104, "scene=0.010 Table 2"); `CLAUDE.md:142` (TRAB 148, "kernel 8-vec aritmético"); `docs/MISSION.md:266` (TRAB 271, filtros no aptos) | F2 filas 7, 8, 12 | sin marca | sin marca | el kernel de 3 × 3 con central y el piso de -0,1 sólo en dNTI |
| U9 | `experiments/_s157_prereg_d25/RESUMEN_SELLO.md:3` y `PREREGISTRO.md:34-35` ("lo que hace MIROVA") | F5-02, F5-06 | sin marca | sin marca | sellado: corresponde una adenda, no editar |
| U10 | `experiments/50_FACTOR_42_HALLAZGO.md:1, 42-50` | F2-H1 | sin marca | sin marca | HYPOTHESIS_LOG, `tests/test_cluster_hotspots.py` y MISSION l. 297 ya marcados en TRAB |
| U11 | `documentacion/BIBLIOGRAPHY_SYNTHESIS.md:142, 248, 249` (fuera de git, 12σ y 8σ de Di Bella como "canónico" de VIIRS) | F2-H4 | sin marca | sin marca | `CLAUDE.md` lo manda leer primero |
| U12 | memoria `reference_mirova_daytime_cloud_artifact.md:29`, `feedback_mirova_no_human_supervision.md:37` ("supervisión MANUAL") | F5 / F6-m9 (rechazo automático por reflejo bajo 12°) | sin marca | sin marca | fuera del repo; el censo de F2 declaró no entrar |
| U13 | `docs/DISENO_D17_REMUESTREO_UTM.md:282` ("pendiente del verificador") | V3 confirmó la rebaja | desactualizada | desactualizada | H9 |
| U14 | `scripts/run_pipeline.py:417` y `pipeline/fetch.py:622-643` | V2-1 | sin cambio | sin cambio | arreglo de código: decide Nicolás (A45); mientras, un aviso en SINTOMAS |

Ya marcados en TRAB por la sesión hermana y por tanto fuera de esta lista: `docs/MISSION.md:297`, `CLAUDE.md` A4 y A12,
`docs/HYPOTHESIS_LOG.md:812`, la mayoría de las pruebas de F2-H9. Los reviso al final: si algún cambio de ellos se pierde
(sin commit), vuelven a la lista.

## 6. Fuera de alcance

- Mecanismo del escalón de 50° (F6-H1): lo comprobé como hecho (§3), no lo expliqué. De las filas sobre 50° con ΔL·k > 100 MW, 8.145 de 11.563 (70 %) se desvían; con Satellite 3 el 70 %, con Satellite 4 el 71 %; 4.626 son de noche y 3.613 de día (`t5_osf_identidad_750_salida.txt`).
- `f5/m5` y el libro de cuentas: el recall V750 del tablero cae a 75,44 % hoy (F5-05); no verifiqué su causa.
- El sibling `a113` modifica pruebas y documentos mientras yo audito: el estado de §5 es de las 17:20 UTC.

## 7. Lo que no pude medir

- **La causa del hueco del 18-oct** (H2): exige consultar CMR y reproducir una búsqueda con y sin ventana; tengo prohibido bajar gránulos y usar Earthdata.
- **La fracción de pares con `K/M ≤ 1/1,10`** de F5-02 por otro camino: pasa por `banco_paridad` y el evaluador de D25, y no corro ese evaluador sobre los datos del A/B. Sólo verifiqué el álgebra del placebo.
- **La suficiencia de la compuerta de 3 K en Chile**: no se persiste el dNTI por píxel y no hay L1B.
- **La ejecución real del `.m` de MIROVA**: no hay MATLAB ni Octave; todo "MIROVA hace X" es lectura del código más un port validado en una pasada, con la incertidumbre de H3.
- **El control de poder de F3-H4** (fondo por píxel de MIROVA contra el nuestro): lo leí, no lo reconstruí; me apoyo en su control natural (volcanes con kernel: 1,03 a 1,08).
- **El predicado del tablero (`predicado_tablero.js`)**: lo leí y leí la validación de F5; no lo re-corrí.
- **El cuarto control del evaluador de cobertura del A/B** (umbral del 5 %): requiere las salidas del A/B, vetadas.
- **El censo completo de propagación**: es un piso. No busqué en `docs/audit_s*` ni en `experiments/` salvo los pre-registros nombrados, ni en memoria fuera de `MEMORY.md`, `project_s157_estado.md`, `feedback_*` y `reference_*`.
- **`docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md` completo**: no está en la lista de lectura de mi alcance; sólo `grep`.
