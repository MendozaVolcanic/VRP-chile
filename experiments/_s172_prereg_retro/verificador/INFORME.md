# Verificación del borrador de pre-registro de la prueba retrospectiva del paquete de las tres vías (VPR172)

## 1. Encabezado

- Fecha y hora del servidor: `date -u` = Mon Nov 2 01:43:39 UTC 2026 al empezar; header `Date` de la API de GitHub = Mon, 02 Nov 2026 01:43:38 GMT. Última comprobación al cerrar: 01:57:40 UTC.
- Objeto: `experiments/_s172_prereg_retro/PREREGISTRO_RETRO_PAQUETE.md` en `loop/activo`, commit `01be21ff5` (sha256 del archivo `45f48a930a6ab8060157003a97e4f7e91bfe40cdeb835c6a0ec1fd8e94b9a11c`). `loop/activo` avanzó después a `8f6e78e6d` sin tocar el borrador (`git diff --stat 01be21ff5 loop/activo -- experiments/_s172_prereg_retro` vacío). `origin/main` = `14fb62030a186fda02ce2ba172866cf01408eeb9`.
- Medí con los scripts, el predicado del tablero (`frontend/index.html`) y los records K de `origin/main`, exportados con `git archive` a `D:/vrp-trabajo/temporales/ver_s172_prereg_retro/export_main/`. La copia local de `loop/activo` tiene `data/mirova_equivalent/` atrasada respecto de `origin/main` (ver SEGUIMIENTOS S-1), así que no la usé.
- Copia de la referencia (la de `origin/main` hoy): `registro_vrp_consolidado.csv` sha256 `ab1a208c89b32df2fd5622c102ac2a984fa8a0102cfe0fe9f65cb8ff54b7d88f`; `registro_vrp_ocr.csv` sha256 `d4ad8c44d5112ca44751552d4aee6e920c20ac5dc0d73f4fc5d9f6594785026e`. OSF local `VRP_GLOBAL_ARCHIVE_2025.csv` sha256 `0863c2407eadd09722ccd98fd50c48eefdc871a4b68f843bd8478f94f5eb29da` (el mismo del borrador). El borrador recomienda congelar la referencia de MOD-D fase 4 (commits `cb91eb50…` y `cfc57c4d…`), que no es la de hoy: mis conteos de F26 pueden diferir en pocas filas de los que saldrán con la congelada.
- Modelo y esfuerzo: Sonnet 5.5 (`claude-sonnet-5-5`); esfuerzo bajo (el arnés no declara el nivel exacto).
- CARPETA: `D:/vrp-trabajo/temporales/ver_s172_prereg_retro/`. Antes de abrir ningún pre-registro sellado escribí `caminos.md` (sha256 y hora anotados al final de ese archivo: `391e868ede5698f74ff059bd2e29b3154fd37df5f78e4011060e31fc44fb75ba`, 01:44:08 UTC), como pide el bloque del verificador. Soy a la vez auditor y verificador de este borrador; no hay un auditor previo cuyo informe no deba abrir.
- Qué NO miré: (a) no rendericé el PDF de Coppola et al. 2026 (la semántica de `Dayflag` y `Satellite` la verifiqué sólo de forma empírica contra la elevación solar y la serie por año; la definición escrita sigue SIN VERIFICAR); (b) no ejecuté ninguna vía (no existe el perfil ni el workflow), así que todo número sobre la vía es una cota hecha con los errores de K; (c) no revisé las curvas de cenit de Chillán ni los números de MOD-D, V375-E y V750 port dentro de muestra que el borrador cita (0,983, 0,9996, 0,994 a 0,998); (d) no leí el plan completo `docs/superpowers/plans/2026-11-02-nrt-34-volcanes.md`, sólo las líneas de la Compuerta A; (e) no verifiqué el plan de la cuenta de GitHub (tope de 20 jobs); (f) no leí `leer_sombra_v375e.py` más allá de las dos líneas citadas; (g) no revisé el contenido de `_s162_v750b/PREREGISTRO_V750B.md` más allá de su §3.

## 2. En una pantalla

**Veredicto global: SELLABLE CON CAMBIOS** (11 grupos de cambios, todos de redacción, de regla de veredicto o de control; ninguno exige re-medir los números de referencia). Los números de referencia del borrador se sostienen: reproduje exacto 317 / 17 / 162 protegidas del OSF, el piso de 5,05 MW en 750, el costo de 2,39 min por volcán-día y los 6 jobs fallidos. Lo que no se sostiene es que F26 y R25 sean "fuera de muestra" en el sentido fuerte, y que un "se sostiene" pueda leerse como evidencia de paridad en los 11 volcanes: el P1 de F26 es Láscar (26 de 26 en VIIRS 375, 29 de 30 en 750, 9 de 9 en MODIS).
Los tres cambios que más importan: (1) el nombre y el texto del veredicto 6 y de la Compuerta A deben llevar el conteo de protegidas por volcán (VPR172-01); (2) el §3 debe sustituir "ninguna regla lo miró" por un inventario de exposiciones, que incluye las tres pasadas de Láscar de febrero que dejan a K sin publicar (VPR172-02); (3) el orden de las filas del §8 deja a una pérdida sólo OCR o a una curva que cae más que MIROVA bajo la etiqueta SIN PODER (VPR172-03).

## 3. Veredicto por afirmación (V-1 a V-5)

Escala: CONFIRMADO, CONFIRMADO EN PARTE, REFUTADO, SIN DATO. Gravedad propia 1-5.

| id | afirmación del borrador | veredicto | gravedad | evidencia |
|---|---|---|---|---|
| V-1a | Ventanas que usó cada regla sellada (tabla del §3 l. 96 a 107) | CONFIRMADO | 1 | `PREREGISTRO_E.md` l. 68 a 71 y 550 a 560 (tag `s170-v375e-lector`): marco S159 del 2026-04-01 al 2026-10-21 sin el 12, 13 y 17 a 20; `PREREGISTRO_V750B.md` l. 97 a 106 (tag `s167-v750b-adenda3-sellada`): T 04-01 a 06-12, O 06-13 a 11-02 12:59; `PREREGISTRO_MODD_F4.md` l. 94 a 121 (tag `s168-modd-f4-sellado`): C 03-01 a 10-16, E 10-17 a 10-26; `_s151_prereg_fk_11/PREREGISTRO.md` l. 90 a 102 (V1 08-29 a 10-08, V2 03-01 a 06-12, VIIRS desde 04-01) |
| V-1b | "Ninguna regla de las vías lo miró" para F26-V y R25 (l. 110 y 113) | CONFIRMADO EN PARTE: cierto para la selección de parámetros (ninguna ventana de elección de ROI, caja o posición toca febrero, marzo ni 2025), falso para los diagnósticos que motivaron las vías | 3 | VPR172-02 |
| V-1c | Febrero de MODIS es fuera de muestra (R-8) | REFUTADO para las tres pasadas donde K no publica | 3 | VPR172-02 |
| V-2a | Cada sensor aplica su regla sellada con un solo cambio (censo en lugar de pesos) | CONFIRMADO EN PARTE: hay otras diferencias que el borrador no declara en esa frase | 2 | VPR172-04, -06, -10 |
| V-2b | El censo no cambia lo que la regla puede decidir | CONFIRMADO EN PARTE: los umbrales no cambian, pero con censo B (bloques) crece, y el umbral "B de 4 o menos es SIN SUSTRATO" decide en más casos | 1 | `_evaluar_d25.py` `regla_signos_p2`, blob `1dbabf65` verificado |
| V-3a | La prueba puede perder (P1, P2, M) | CONFIRMADO para VIIRS 375 y 750 sobre Láscar; REFUTADO como lectura de los 11 volcanes | 4 | VPR172-01 |
| V-3b | Nulo y K-gemelo | REFUTADO como instrumento que pueda fallar | 3 | VPR172-05 |
| V-3c | Nombres de veredicto no prometen más que lo que la regla prueba | CONFIRMADO EN PARTE: el texto del veredicto 6 sí acota, pero el nombre y la Compuerta A no | 3 | VPR172-01, -03, -08 |
| V-4a | Conteos de protegidas del OSF (317 / 17 / 162; Láscar 273 / 17 / 155) | CONFIRMADO | 1 | `osf_protegidas_salida.txt` |
| V-4b | Piso de 0,011 / 0,176 / 5,05 MW por sensor en el OSF | CONFIRMADO (mínimos de Chile 2025: 0,0109 / 0,176 / 5,053; mínimos globales 2025: 0,0101 / 0,101 / 5,003) | 1 | `osf_cuentas_salida.txt` |
| V-4c | NOAA-21 sin referencia antes del 2026-04-09 y ausente del OSF | CONFIRMADO EN PARTE: en F26 es 895 de 895 y 889 de 889 `sin_info`; primer NOAA-21 etiquetado: 2026-04-03; el OSF sólo trae los códigos 3 y 4 en todos los años | 1 | VPR172-14 |
| V-4d | Conteos de F26 de la tabla (25 y 30; MODIS 7; bajo 1 MW 174 / 23 / 5) | CONFIRMADO EN PARTE: 26 y 30 (29 Láscar + 1 Isluga en 750), MODIS 9, bajo 1 MW 160 (después de SN) / 25 / 5 | 1 | VPR172-14 |
| V-4e | Referencia por tramo (A119, A105, D-9) | CONFIRMADO EN PARTE: hitos y reglas bien citados; el borrador revierte la regla A119(b) de K (VIIRS desde abril) sin medir lo que eso cambia | 3 | VPR172-07 |
| V-5a | `extends` resuelve un solo nivel y los flags se escriben en las secciones que el código lee | CONFIRMADO | 1 | `pipeline/profile.py` l. 46 a 67 (`origin/main`); flags en `_t` l. 902 a 933, `_cfg` l. 636, `_p` l. 175 |
| V-5b | Costo: 2,39 min por volcán-día, mediana 80 min, p95 160, máx 172, 6 de 176 fallaron, pared 32,3 h | CONFIRMADO (80,4 / 157,6 / 171,7; 2,39; 32,3 h; suma 254,2 h) | 1 | `costo_run_salida.txt` |
| V-5c | Con trozos de 20 días el p95 es de 95 a 115 min | CONFIRMADO EN PARTE: 92 a 108 min para el conjunto, pero los 6 fallidos son de Chillán y están censurados en 171 min | 2 | VPR172-11 |
| V-5d | Aritmética de despachos (825, 235, 3.520, 4.583 volcán-día; 44, 14, 176 jobs; 191 a 228 h) | CONFIRMADO (con la salvedad menor de Tupungatito, VPR172-14) | 1 | cálculo propio, ver §6 |

## 4. Hallazgos

### VPR172-01
- TÍTULO: El P1 fuera de muestra es Láscar, y ni el nombre del veredicto 6 ni la Compuerta A lo dicen
- ARCHIVO:LÍNEA: `experiments/_s172_prereg_retro/PREREGISTRO_RETRO_PAQUETE.md` l. 379 y 381 a 384 (veredicto 6 y "Qué abre cada uno"); l. 341 a 352 (poder); script `k_en_tramos.py` y `osf_protegidas.py`, salidas `k_en_tramos_salida.txt` y `osf_protegidas_salida.txt`
- QUÉ PASA: un cráter activo y brillante como el de Láscar se ve en cualquier detector; los volcanes de señal débil (Isluga, Lastarria, Puyehue, Planchón) son donde un detector pierde alertas. Medido: en F26 las protegidas de la tabla son 26 de 26 de Láscar en VIIRS 375, 29 de Láscar y 1 de Isluga en 750, y 9 de 9 de Láscar en MODIS de febrero. En R25 el OSF trae 273 de 317 (86 %) de Láscar en 375, 17 de 17 en 750 y 155 de 162 (96 %) en 1 km. El borrador lo admite en el §7 ("Casi toda la evidencia de P1 fuera de muestra es de Láscar") pero el nombre "LA ADOPCIÓN SE SOSTIENE FUERA DE MUESTRA" y la frase que abre la sombra de los 34 se leen sin ese límite. La regla de veto es "una pérdida", así que con 9 volcanes sin una sola protegida en F26 el veto no puede fallar ahí.
- CÓMO SE VE EN EL DASHBOARD: invisible hoy; la consecuencia llega después: se abriría la sombra de los 34 volcanes con una frase de paridad apoyada en un volcán.
- CÓMO REPRODUCIRLO: `python -I D:/vrp-trabajo/temporales/ver_s172_prereg_retro/k_en_tramos.py` (campo `prot` por tramo y sensor) y `python -I .../osf_protegidas.py` (tabla por volcán). Pasadas: 2026-02-01 a 2026-03-31 y 2025-02-15 a 2025-12-31 UTC.
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 4 (decide si se abre una sombra de 34 volcanes que no tienen grilla probada)
- Cambio pedido: (a) poner en la tabla del veredicto el conteo de protegidas por volcán y exigir un mínimo de volcanes distintos de Láscar con al menos una protegida para poder decir "se sostiene"; (b) renombrar el veredicto 6 a algo que contenga el alcance (por ejemplo "SIN PÉRDIDAS NI EXCESO EN LÁSCAR Y EN LOS VOLCANES CON SEÑAL, FEB-MAR 2026 Y 2025"); (c) en "Qué abre cada uno" escribir que ninguna lectura de esta prueba contiene evidencia de los 34 y que la Compuerta A es una decisión de Nicolás con esa limitación a la vista.

### VPR172-02
- TÍTULO: "Ninguna regla lo miró" es falso para los diagnósticos: tres pasadas de Láscar de febrero (las tres en que K no publica) y toda la ventana 2025-02-15 a 2026-10-21 de VIIRS 750 ya se examinaron por nombre
- ARCHIVO:LÍNEA: borrador l. 110 y 113; `experiments/_s159/mxd03_prereg/sustrato_mirova_modis_feb_salida.txt` l. 27 a 29; `experiments/_s159/m/INFORME.md` l. 52 y 58; `experiments/_s158_audit_r2/verificador/va/INFORME.md` l. 37; `experiments/_s158_audit_r2/ra1/contar_ceros_v750.txt` l. 1; `CLAUDE.md` del proyecto, regla A99 (pareo contra el OSF de 2025)
- QUÉ PASA: el borrador define "dentro de muestra" como "alguien la miró para escribir una regla de las vías o la de K". Febrero no entró a ninguna ventana de selección de parámetros (verificado en los cuatro pre-registros sellados), pero sí a análisis de casos que motivaron las vías. En MODIS de febrero hay 14 pasadas con alerta y K deja de publicar exactamente tres: Láscar 2026-02-11 01:20 Terra (bajo 1 MW), 2026-02-11 07:00 Aqua (bajo 1 MW) y 2026-02-16 01:20 Terra (protegida). Las tres figuran con su nombre en `sustrato_mirova_modis_feb_salida.txt` («K no publica: Lascar 2026-02-16 01:20 MODIS_TERRA protegida …», TEXTO, l. 29), la de 02-11 07:00 es el control positivo del etiquetado de MxD03 y de la sonda M, y la de 02-16 01:20 es el caso del verificador de la auditoría R2 sobre el segundo pase. Para VIIRS 750 la auditoría RA1 de S158 abrió con «records V750 con cumulo: 2733 ; ventana de observacion 2025-02-15 04:48 a 2026-10-21 05:48» (TEXTO, `contar_ceros_v750.txt` l. 1) y lista por nombre los ceros de K de febrero (Láscar 02-04, 02-05, 02-12, 02-21 con 2,39 MW, 02-25, 02-26; Isluga 02-26; Puyehue 02-01; Tupungatito 02-26). Y la regla A99 midió la razón de magnitud de K contra el OSF de 2025 (342 pares). La vía de 750 es un port literal del `.m` de MIROVA, no un ajuste a esos datos, así que el sesgo de selección de parámetros es débil; pero la prueba de K contra la vía en MODIS-febrero descansa en esas tres pasadas, y quitarlas deja a F26-M con 5 bloques donde K publica un negativo limpio y ninguno donde K pierde una alerta.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -I .../k_en_tramos.py`, línea `F26 pos MODIS` en `f26_sesgo_tabla_salida.txt`; `git show origin/main:experiments/_s159/mxd03_prereg/sustrato_mirova_modis_feb_salida.txt | sed -n 27,29p`.
- CONFIANZA: CONFIRMADO (las pasadas y sus apariciones); la influencia sobre el diseño de las vías es SOSPECHA
- GRAVEDAD: 3
- Cambio pedido: sustituir en el §3 "ninguna regla lo miró" por un inventario con los tres tipos de exposición (ventana de selección de parámetros: ninguna; casos mirados por nombre: las pasadas listadas; diagnóstico de K contra la referencia: RA1 y A99), y pedir al lector que informe P1, P2 y M de F26-M "con y sin" esas tres pasadas.

### VPR172-03
- TÍTULO: El orden de las filas 4 y 5 del §8 deja pérdidas sólo OCR, P1b y curva que cae más que MIROVA bajo la etiqueta SIN PODER
- ARCHIVO:LÍNEA: borrador l. 377 y 378; `PREREGISTRO_MODD_F4.md` l. 216 y 217 (tag `s168-modd-f4-sellado`)
- QUÉ PASA: una alerta de 1 MW o más que K publica y la vía pierde, aunque sea sólo del OCR, es el caso que el criterio de victoria no acepta perder en silencio. La fila 4 ("la regla da SIN SUSTRATO en F26 y R25 no tiene candidatas a veto") se evalúa antes que la fila 5 ("pérdida sólo OCR", "curva CAE MÁS QUE MIROVA", "candidatas a veto en P1-OSF" ya está excluida por la propia fila 4). Con SIN SUSTRATO en P2 (probable en MODIS, VPR172-09), una pérdida sólo OCR o un P1b quedan bajo "SIN PODER". En MOD-D sellado la fila 4 da INDECIDIBLE, que no promete nada; aquí SIN PODER dice "no dice que falle" y decide Nicolás "con la lectura B", que oculta la pérdida.
- CÓMO SE VE EN EL DASHBOARD: invisible; la pérdida sólo OCR se vería en una lista que el veredicto no señala.
- CÓMO REPRODUCIRLO: leer ambas tablas de veredicto; no hay comando.
- CONFIANZA: CONFIRMADO (lectura del texto)
- GRAVEDAD: 3
- Cambio pedido: la fila 4 debe decir "y ninguna de las condiciones de la fila 5", o subir la fila 5 sobre la 4.

### VPR172-04
- TÍTULO: C-via admite 99 % y el tratamiento de un record sin la marca es asimétrico (la regla sellada de MOD-D es 100 %)
- ARCHIVO:LÍNEA: borrador l. 316; `PREREGISTRO_MODD_F4.md` l. 271 y siguientes (tag `s168-modd-f4-sellado`) y §7 "Protocolo de fallo"; `PREREGISTRO_E.md` adenda 1 punto 4 (citado por el borrador)
- QUÉ PASA: MOD-D fase 4 dice que «Una vía que no corrió (record sin `via_codigo_mirova` True: `sin_mxd03`, `geo_distinta`, `sin_grilla`) o una falla del arnés deja el control en rojo» (TEXTO, l. 271 a 272, tag `s168-modd-f4-sellado`). El borrador acepta 99 % y añade "un record sin la marca no entra al brazo VIA". Si el record queda fuera del brazo VIA pero K sigue en su brazo con ese record, una protegida con record K-de-reserva (sin MxD03 en 2025, por ejemplo) se contaría como pérdida de la vía (falso veto) o desaparecería de un solo lado (reducción silenciosa del denominador); el texto no dice cuál. El borrador mismo duda de que el fetch de 2025 encuentre MxD03 en todos los días (Dudas abiertas 4).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: no aplica antes de correr; se prueba con el lector sintético.
- CONFIANZA: CONFIRMADO en la diferencia de umbral; SOSPECHA en el efecto (depende del dato de 2025)
- GRAVEDAD: 3
- Cambio pedido: declarar C-via como desviación de MOD-D en la tabla "Qué cambia", y decidir por escrito que un record sin marca sale de los dos brazos y va a SIN DATO con la misma regla "una protegida SIN DATO que K publica veta".

### VPR172-05
- TÍTULO: Los controles "nulo de runner" y C-K no pueden fallar con lo que aceptan, y cubren 2 de 11 volcanes con una tolerancia del tamaño del efecto
- ARCHIVO:LÍNEA: borrador l. 74, 318, 323; `PREREGISTRO_E.md` l. 66 a 68 (tag `s170-v375e-lector`); `k_shas_por_volcan_salida.txt`
- QUÉ PASA: (1) El nulo "P2 EMPATE o SIN SUSTRATO" acepta el resultado que da un instrumento muerto: con K-gemelo igual a K casi todos los bloques son cero, y SIN SUSTRATO (4 bloques o menos) es lo esperado; un control que pasa con SIN SUSTRATO no distingue "no hay diferencia" de "no medí" (pregunta 2 del instrumento). (2) C-K mide K-gemelo contra K de disco sólo en DM (16 días, 11 volcanes) y en Láscar-F26. Los records de K de F26 se escribieron con cuatro versiones de código (`3695f6758` 6.411, `57d18ad78` 429, `255e97e77` 10, `c408a909e` 6), y las 429 de `57d18ad78` y las 6 de `c408a909e` son todas de Chillán, que C-K no revisa en F26. (3) La tolerancia es 1 %, justo la que el verificador de V375-E rechazó para la publicación («tolerar 1 % de pasadas distintas, ~8 de 859, es del tamaño del efecto que B mide en negativos», TEXTO, l. 66 a 68): en F26-V de 375 hay 2.660 records y K yerra en 48 bloques; 1 % son 27 pasadas, comparable con 48 bloques.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -I .../k_en_tramos.py` (bloques donde K yerra); `python -I` del recuento por `codigo_sha` en `k_shas_por_volcan_salida.txt`.
- CONFIANZA: CONFIRMADO en (1) y (2); (3) es una comparación de magnitudes, CONFIRMADO
- GRAVEDAD: 3
- Cambio pedido: exigir en el nulo B de K-gemelo contra K igual a 0 salvo pasadas nombradas y explicadas; sin tolerancia del 1 % para la publicación (como V375-E); ampliar C-K al menos a un día por volcán de F26.

### VPR172-06
- TÍTULO: V750-A es un borrador sin verificador limpio y el borrador propone copiarlo y sellarlo aquí
- ARCHIVO:LÍNEA: borrador l. 232 y Dudas abiertas 2; `experiments/_s162_v750a/PREREGISTRO_V750A.md` §11 (rama `claude/s162-viirs750-2-918174`, `aa5583646`)
- QUÉ PASA: el §11 de V750-A dice que faltan «un verificador limpio de este agregado» (posición) y «su verificador limpio, junto con el del pre-registro», y que «El sello depende de la lectura de V750-B». Sellar su §6 en el pre-registro retrospectivo crea una regla sellada nueva que no pasó por ellos, con dos versiones del mismo texto (182 líneas en `main`, 341 en el borrador). La regla M de V750-A (razón entre 0,9 y 1,1 sobre las protegidas que la vía publica) pasaría a decidir sobre 30 pasadas de Láscar.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git show aa5583646:experiments/_s162_v750a/PREREGISTRO_V750A.md | sed -n 320,341p`.
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 3
- Cambio pedido: no copiar; condicionar el sello de este documento al sello de V750-A, o declarar el §6 como anexo "no verificado" y que el veredicto de 750 máximo es DECIDE NICOLÁS.

### VPR172-07
- TÍTULO: F26-V decide con la tabla en el tramo que A119(b) y el pre-registro de K sellado habían excluido, y la población etiquetada es casi sólo NOAA-20
- ARCHIVO:LÍNEA: borrador l. 109 a 110 y 130 a 134; `scripts/calidad_referencia_mirova.py` l. 27 (hito 2026-04-01); `_s151_prereg_fk_11/PREREGISTRO.md` l. 100; script `f26_sesgo_tabla.py`, salida `f26_sesgo_tabla_salida.txt`
- QUÉ PASA: el hito dice «una TASA POR PASADA de VIIRS anterior a abril no es comparable con una posterior» (TEXTO, l. 27) y K decidió «VIIRS desde el 2026-04-01» (TEXTO, l. 100). El borrador afirma que la menor exposición «baja el denominador, no lo sesga hacia la vía ni hacia K»; el contraste vía contra K sobre las mismas pasadas, sí. Pero medido, la población que decide no es una muestra al azar de las pasadas: en F26 de 375 hay 1.708 de 2.660 records (64 %) sin fila; NOAA-21 queda 895 de 895 sin etiquetar; Suomi NPP tiene sólo 163 de 895 etiquetadas y esas tienen cenit mediano 63,1° contra 44,9° las no etiquetadas (en 750: 62,6° contra 42,6°). O sea que la evidencia de F26-V es NOAA-20 más pasadas oblicuas de Suomi NPP. Además, una noche con una pasada con alerta que la tabla no expone contamina como "negativo limpio" a las otras pasadas de esa noche, y eso afecta la lectura B absoluta aunque no el contraste.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -I .../f26_sesgo_tabla.py` (líneas "VIIRS375 SNPP F26 etiquetadas…").
- CONFIANZA: CONFIRMADO (composición); la contaminación de negativos es SOSPECHA
- GRAVEDAD: 3
- Cambio pedido: declarar la desviación de A119(b) como tal, escribir en el §3 la composición por satélite y cenit (con estos números), y rotular el resultado de F26-V como "NOAA-20 y Suomi NPP oblicuo".

### VPR172-08
- TÍTULO: En VIIRS 375 decide el brazo "cercano", pero lo que publica el record de la vía es "radiante"
- ARCHIVO:LÍNEA: borrador l. 72 y 231 a 233; `PREREGISTRO_E.md` l. 703 a 716 (tag `s170-v375e-lector`)
- QUÉ PASA: V375-E §10 dice «la vía de `pipeline/` hoy publica con radiante, y el costo de cercano en las pasadas lejanas (104 de 329 contra 13 de radiante en la retrospectiva …) se sigue mirando» (TEXTO, l. 716). El borrador hace decidir a VIA-cercano, que es una variante calculada del record, y calla qué se adoptaría. Un "SE SOSTIENE" para 375 con cercano no es un "SE SOSTIENE" para el paquete que la sombra o producción publicarían mientras el record lleve radiante. Con 38 pasadas `far_ref` en F26 de 375 y K publicando 18, el costo de lejanas puede aparecer en P2'.
- CÓMO SE VE EN EL DASHBOARD: el operador vería (si se adopta radiante) los resultados de la columna que no decidió, o (si se adopta cercano) algo que requiere un cambio de código no probado por esta prueba.
- CÓMO REPRODUCIRLO: no hay comando; es un hueco de redacción.
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 3
- Cambio pedido: añadir a la fila de VIIRS 375 "el veredicto aplica al brazo cercano; para el paquete tal como lo publica el record hoy (radiante) se informa la misma regla y, si difiere, el veredicto máximo es DECIDE NICOLÁS".

### VPR172-09
- TÍTULO: MODIS no puede llegar al veredicto 6 con probabilidad razonable, y por la regla "los tres sensores o ninguno" la Compuerta A en verde es casi inalcanzable
- ARCHIVO:LÍNEA: borrador l. 358 a 364, 377, 383; `k_en_tramos_salida.txt` (F26-M); `leer_f4_salida.txt` de `e0bb1b150` (B 53 en el censo entero)
- QUÉ PASA: en F26-M K yerra en 6 bloques noche-volcán (5 negativos publicados, 2 bajo 1 MW sin publicar, 1 protegida sin publicar, repartidos en 6 bloques). La prueba D-45 es SIN SUSTRATO con B de 4 o menos, y GANA requiere que la vía arregle todos o casi todos los errores de K (con 6 bloques, 6 de 6 arreglados da p = 1/64; 5 arreglados y un sexto bloque empatado da 2/64; 5 arreglados y uno en contra da 7/64, que no llega a 5 %). En el censo de MOD-D el neto fue -44 con B = 53, o sea la vía arregló alrededor del 90 % de los errores de K; en febrero eso da B entre 3 y 7. Resultado más probable: SIN SUSTRATO o EMPATE. Con SIN SUSTRATO el veredicto es SIN PODER (fila 4); el borrador lo anticipa («MODIS sólo puede salir con P1 y con R25», l. 364) pero entonces el plan de "abrir la sombra si los tres sensores salen en verde" casi siempre termina en la decisión de Nicolás.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -I .../k_en_tramos.py` (F26-M `bloques_donde_K_yerra` = 6 en tabla y en unión).
- CONFIANZA: CONFIRMADO para el conteo de bloques de K; SOSPECHA para el B de la vía
- GRAVEDAD: 2
- Cambio pedido: escribir en el §0 que el resultado esperado de MODIS es SIN PODER y que la Compuerta A no puede ser automática.

### VPR172-10
- TÍTULO: Diferencias con las reglas selladas que la frase "un solo cambio declarado" no recoge
- ARCHIVO:LÍNEA: borrador l. 225 a 227 y 316 a 330; `PREREGISTRO_MODD_F4.md` l. 216, 251 a 262, 271 (tag `s168-modd-f4-sellado`)
- QUÉ PASA: (a) SIN SUSTRATO es INDECIDIBLE en MOD-D (fila 4) y SIN PODER en el borrador (VPR172-03); (b) el control de identidad de punta a punta, «la pieza nueva» de MOD-D (§8.2), se retira para MODIS ("sin las piezas que no aplican") y se reemplaza por C-montaje sólo en DM; en F26 y R25 la vía no se compara con el port pasada por pasada, de modo que una vía distinta del port solo se vería si cambia lo que publica; (c) V375-E §5.4 exige cumplir en la retrospectiva Y en la sombra; el borrador lee sólo la parte retrospectiva; (d) Tupungatito entra recién el 02-23, y NOAA-21 y Suomi NPP quedan casi todos `sin_info`; (e) censo en lugar de muestra cambia B (ver V-2b). Ninguna cambia un umbral, pero la frase del §0 «sin tocarla» y la del §5.1 («con un solo cambio declarado para los tres») sobreprometen.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: comparar las dos tablas de veredicto.
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 2
- Cambio pedido: tabla "Qué cambia respecto de las reglas selladas" como la de MOD-D fase 4 §6, con una fila por diferencia.

### VPR172-11
- TÍTULO: Los 6 trozos fallidos del precedente de K son todos de Chillán y están censurados en 171 min; el p95 de 20 días no los contiene
- ARCHIVO:LÍNEA: borrador l. 425 a 436; script `costo_run.py`, salida `costo_run_salida.txt`
- QUÉ PASA: la tasa mediana de Chillán es 4,41 min por volcán-día contra 1,76 a 2,64 de los otros diez volcanes (Chillán tiene más píxeles anómalos y más tiempo de proceso). Los 5 fallos de 171,4 a 171,7 min (Chillán 2025-07-13 a 08-18, 08-19 a 09-24, 09-25 a 10-31, 2026-02-20 a 03-28, 03-29 a 05-04) chocan con el paso de 170 min: su duración verdadera es mayor, y la tasa mínima compatible es 171,5 / 36 = 4,76 min por volcán-día. Con 20 días y factor 1,25 de la vía son al menos 119 min; con una tasa de 6 serían 150, a 20 min del límite. El p95 de "95 a 115" sale del conjunto en que esos 5 trozos cuentan como 171, no más. En F26 Chillán corre 59 días; en 2025 no hubo erupción y aun así falló.
- CÓMO SE VE EN EL DASHBOARD: invisible (si el trozo falla se repite y sube el costo).
- CÓMO REPRODUCIRLO: `python -I .../costo_run.py` (lista "no success").
- CONFIANZA: CONFIRMADO para lo medido; SOSPECHA para el margen
- GRAVEDAD: 2
- Cambio pedido: trozos de 10 días para Chillán, o declarar el costo de Chillán por separado.

### VPR172-12
- TÍTULO: El análogo del OSF a un falso positivo lejano está mal elegido: son las filas class 1 fuera del radio (49 de Chillán, 12 a 20 km), no las class 0
- ARCHIVO:LÍNEA: borrador l. 203 a 205; `osf_class0_salida.txt`
- QUÉ PASA: el borrador toma como análogo de `FALSO_POSITIVO` las 105 filas class 0 de 1 MW o más (375 m) y 9 (1 km). Medido: de las 105 de 375, sólo 13 caen dentro del `inner_radius_km` (9 de Láscar, 4 de Puyehue, cerca del cráter, luego probablemente señal volcánica que el filtro automático descartó), y 92 caen fuera. En cambio, hay 49 filas class 1 de 1 MW o más fuera del radio, todas en Chillán entre 2025-02-15 y 2025-03-05 (12,1 a 19,6 km del cráter, mediana de 17 MW), que son el calor lejano propiamente tal. El OSF mismo advierte que `class` es «a screening indicator rather than a definitive label» (TEXTO, `schema_osf_v25_texto.txt` l. 62).
- CÓMO SE VE EN EL DASHBOARD: si la vía publicara esos 49 como cumbre, el operador de OVDAS vería un foco a 12 a 20 km como actividad del cráter.
- CÓMO REPRODUCIRLO: `python -I D:/vrp-trabajo/temporales/ver_s172_prereg_retro/osf_protegidas.py` (genera `osf_w.pkl`) y después `python -I .../osf_class0.py`; salida en `osf_class0_salida.txt`.
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 2
- Cambio pedido: usar las filas class 1 fuera del radio como análogo de lejana en R25 (informa) y listar las 13 class 0 dentro del radio como "ambiguas".

### VPR172-13
- TÍTULO: La razón de magnitud contra el OSF queda truncada por el piso de cada sensor y no es comparable con la de F26
- ARCHIVO:LÍNEA: borrador l. 176 a 182 y 255 a 258; `osf_cuentas_salida.txt`
- QUÉ PASA: el OSF sólo contiene VRP de 5 MW o más en 750, de 0,10 MW o más en 1 km y de 0,01 MW o más en 375 (mínimos globales 2025: 5,003 / 0,101 / 0,010). Una razón vía/OSF calculada sobre las filas que el OSF conserva selecciona por el denominador: cuando el denominador es alto por azar la razón sale baja. En 750 el efecto es el más fuerte (todas las filas son de 5 MW o más, y las protegidas dentro del radio son 17, mínimo 5,05 MW). El borrador declara que la magnitud de R25 "informa", y eso protege el veredicto, pero la banda [0,9; 1,1] de V750-A y la comparación con F26 se leerían sobre una muestra truncada.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -I .../osf_cuentas.py`.
- CONFIANZA: CONFIRMADO para los pisos; SOSPECHA para la dirección y tamaño del sesgo
- GRAVEDAD: 2
- Cambio pedido: escribir que la razón de R25 se lee sólo como cota y no se compara con la de F26.

### VPR172-14
- TÍTULO: Cifras del borrador desactualizadas por poco (conteos, un hito y un volcán-día)
- ARCHIVO:LÍNEA: borrador l. 121, 185, 343 a 346, 110, 113; `cuentas_ref_salida.txt`, `f26_sesgo_tabla_salida.txt`, `osf_dayflag_salida.txt`
- QUÉ PASA: (a) protegidas de F26 en la tabla con regla SN y noche por elevación solar: 9 de MODIS-febrero (borrador 7; cota de pérdida 33 %, no 43 %), 26 de 375 (borrador 25), 30 de 750 (igual); bajo 1 MW: 160 en 375 después de SN, 25 en 750 (borrador 23), 5 en MODIS; (b) el primer NOAA-21 etiquetado en la tabla es 2026-04-03 (el hito del script dice 04-09 y su propia cifra "no reconstruida"); (c) 649 volcán-día de F26-V incluye a Tupungatito antes del 02-23 (son 627 sin él; 3.520 de R25 incluye a Tupungatito que no está en el OSF, 3.200 sin él); (d) `Dayflag` 0 en la ventana de 2025 son 2.528 filas con horas UTC de 01 a 20, no de 01 a 07 (cuatro filas fuera: horas 12, 13, 13 y 20; las cuatro, MODIS, son diurnas por la regla del proyecto, una con VRP de 1 MW o más), y `Dayflag` 1 son 49 filas, 49 de 49 diurnas por la regla del proyecto; (e) el control positivo de mi instrumento (ventana 2026-03-01 a 2026-10-16) reproduce exacto las etiquetas selladas de MOD-D (50 protegidas, 42 bajo 1 MW, 5.110 negativos limpios, 253 `sin_info`, 10 `far_ref`, 5.465 records).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -I .../cuentas_ref.py`, `.../k_en_tramos.py`, `.../f26_sesgo_tabla.py`, `.../osf_dayflag.py`.
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 1
- Cambio pedido: reemplazar por los números del §7 recalculados con la referencia congelada antes del sello (el propio borrador ya lo ordena).

### VPR172-15
- TÍTULO: El encabezado declara una ventana de escritura que termina después de la hora del commit
- ARCHIVO:LÍNEA: borrador l. 3 a 5; `git log -1 --format=%cI 01be21ff5` = 2026-11-01T22:42:57-03:00 (01:42:57 UTC)
- QUÉ PASA: «entre 01:00 y 02:30 UTC (hora del servidor de GitHub al empezar: 01:36:17 GMT)» no cuadra: el commit es de 01:42:57 UTC, antes de las 02:30, y el inicio declarado (01:00) es anterior a la hora del servidor "al empezar" (01:36). Es un defecto de trazabilidad de un documento que se sella.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git log -1 --format=%cI 01be21ff5`.
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 1

## 5. SEGUIMIENTOS (visto fuera de mi eje)

- S-1 (confianza CONFIRMADO, gravedad 2): el checkout de trabajo de `loop/activo` tiene `data/mirova_equivalent/*.json` atrasados respecto de `origin/main` (`git diff --stat origin/main HEAD -- data/mirova_equivalent volcanoes.yaml` muestra 11 archivos y 43.761 líneas menos en HEAD). El borrador ordena "recalcular con `banco_paridad`" en el §7; en ese checkout leería datos atrasados (regla A52).
- S-2 (CONFIRMADO, gravedad 1): en R25 K tiene 10.000 records NOAA-21 (5.008 y 4.982) que ninguna fila del OSF puede juzgar (el OSF no trae NOAA-21 en ningún año), y el precedente muestra que el cómputo de VIIRS es el grueso del costo. Si las vías se corren sobre NOAA-21 en R25 sólo sirven al costo.
- S-3 (SOSPECHA, gravedad 2): el recall de K contra las protegidas del OSF en R25 es 100 % (317 de 317, 17 de 17 y 160 de 160 con record; 2 MODIS sin record de K, `r25_k_salida.txt`). Eso hace de P1-OSF un control de "la vía no pierde las evidentes", no de recall en volcanes débiles.
- S-4 (CONFIRMADO, gravedad 2): el precedente de reproceso de K usa trozos de ~36 días con un paso de 170 min y 6 de 176 fallaron: el borrador pasa a 20 días pero no dice qué hace el lector si un trozo de Chillán falla dos veces (SIN DATO en la primera línea, l. 317, sólo para pasadas faltantes).
- S-5 (SOSPECHA, gravedad 2): la lógica "retrospectiva sobre los 11 abre la sombra de los 34" no tiene evidencia sobre las grillas ni la geometría de los 34. El `sombra_codigo_mirova.yaml` dice que con las vías encendidas los 11 Tier A tienen grilla de MIROVA, y que un volcán sin grilla cae a K (`via_codigo_mirova: "sin_grilla"`). Eso queda fuera de mi eje y es de la Compuerta A.
- S-6 (CONFIRMADO, gravedad 1): `scripts/calidad_referencia_mirova.py` l. 27 y 28 fija 2026-04-09 para NOAA-21 con una cifra de otra auditoría "no reconstruida" (AUDIT_S149:56); mi medida da 2026-04-03 (VPR172-14b). No lo corregí.

## 6. VERIFICADO LIMPIO

Cada ítem: qué miré, comando y contra qué vara. Todos los scripts y salidas están en CARPETA.

- Conteos de protegidas del OSF (317 / 17 / 162; Láscar 273 / 17 / 155; participación de Láscar 86 / 100 / 96 %): `python -I osf_protegidas.py`, contra el archivo OSF local con el sha del borrador, vara: la definición del §4.2 (nocturna por elevación solar, `class` = 1, VRP ≥ 1e6 W, píxel más caliente a ≤ `inner_radius_km` desde `vent_lat`/`vent_lon` de `volcanoes.yaml`). Control positivo: el mismo filtro sin distancia da 334 / 37 / 174 y baja a los valores del borrador al aplicarla; con la distancia a las coordenadas de cumbre del yaml o del OSF da lo mismo.
- 2.577 filas de Chile en la ventana, 10 volcanes, Tupungatito 0; 48.360 filas de Chile en todo el archivo (20.509 + 12.179 + 1.746 + 769 + 6.702 + 6.455): `osf_cuentas_salida.txt`.
- Piso de VRP por sensor: 375 → 0,0109 MW, 1 km → 0,176 MW, 750 → 5,053 MW (Chile 2025); globales 2025: 0,0101 / 0,101 / 5,003; `timeUTC` truncado al minuto (todas las pasadas pareadas con un record de K dan Δt = 0 s).
- `k = VRP / (Tot_Lmir_hot - Tot_Lmir_bk)` constante por resolución: 375 → 2,53125e6 (cv 1,07e-8), 750 → 1,10812e7 (5e-10), 1 km → 1,89e7 (9e-9), iguales a los coeficientes del `.m` y de S14: el argumento del §4.3 de independencia se sostiene (`osf_k_constante_salida.txt`).
- `Dayflag` 0 es noche en 2.524 de 2.528 filas y `Dayflag` 1 es día en 49 de 49 según la elevación solar del proyecto; `Satellite` 3 y 4 son VIIRS (4 desde 2018, NOAA-20), 1 y 2 son MODIS; no hay código de NOAA-21 en ningún año (`osf_dayflag_salida.txt`, `osf_cuentas_salida.txt`). Es verificación empírica, no la definición del paper.
- Instrumento de etiquetado: el control positivo (ventana 2026-03-01 a 2026-10-16, MODIS) reproduce exacto las etiquetas selladas de MOD-D (50 / 42 / 5.110 / 253 / 10 / 5.465); la alerta sin record V750 de Láscar 2026-03-11 06:18 (S158) aparece sólo en la unión (`f26_cobertura_salida.txt`). Vara: números selladas de `experiments/_s162_modis_paquete/PREREGISTRO.md` l. 54.
- Cobertura de K en F26 contra las alertas de la tabla: 2 alertas sin record (Lastarria y Puyehue, 375) y ninguna en febrero (`f26_cobertura_salida.txt`).
- Ventanas citadas de V375-E, V750-B, MOD-D fase 4 y K: verificadas contra el texto de cada tag o rama (véase V-1a). `evaluar.py` de V375-E sha256 LF `2126b7439809cc54…` (igual al citado); `evaluar_d25.py` blob `1dbabf65`; `UMBRAL_COBERTURA = 0.10` en `leer_sombra_v375e.py` l. 85.
- Hitos de `calidad_referencia_mirova.py` (02-14, 02-23, 03-01, 04-01) y la cobertura de la tabla de febrero (98,2 a 99,6 %).
- `pipeline/profile.py` l. 46 a 67: `extends` quita la clave del hijo, mezcla con el padre y deja una `extends` del padre como dato sin resolver (un nivel); los flags `enable_modis_geo_mxd03`, `enable_modis_crater_sin_dato` y `enable_modis_dist_desde_crater` se leen desde `thresholds:` (l. 923 a 925) y los de las vías también (l. 902, 909, 933); `enable_modis_b22_primary` se lee de la raíz (l. 636), `enable_test1_path` de `paths:` (l. 175).
- Costo y aritmética de los despachos: ver V-5b y V-5d; D2 = 3 trozos de 20 días por 11 volcanes + 1 trozo de DM por 11 = 44 jobs; D3 = 11 + 3 = 14; D4 = 16 trozos por 11 = 176; volcán-día 825 + 235 + 3.520 + 3 = 4.583; horas 191 a 228 con 2,5 a 3,0 min.
- Vencimiento del token de Earthdata (2026-12-07 18:03 UTC; rotar antes del 2026-11-27): `REGISTRO_CREDENCIALES.md` l. 28.
- K de disco publica 317 / 17 / 160 de las protegidas del OSF con record (R25) y no hay pares duplicados (C-pareo): `r25_k_salida.txt`.

## 7. SIN DATO

- Definición escrita de `Dayflag` y de la tabla de `Satellite` en Coppola et al. 2026 (no rendericé el PDF; sólo verificación empírica).
- Cualquier medida de la vía (P1, P2, M, curva): no existe el perfil, el workflow ni el lector. Mis cotas con los errores de K son de K, no de la vía.
- Poder real de P2 para MODIS y 750: depende de cuántos bloques discordantes aporte la vía (no medible hoy).
- Si el plan de la cuenta de GitHub limita a 20 jobs simultáneos y si NRT, sombra y experimental coinciden con D4.
- Factor de costo de la vía en VIIRS (el informe `_s172_capacidad_nrt` acota sólo la vía de MODIS, 1,06 a 1,25).
- Si el fetch de 2025 encuentra MxD03 en todos los días (Dudas abiertas 4 del borrador).
- Efecto real de los 429 records de Chillán de F26 con `codigo_sha` distinto sobre la equivalencia de K de disco con K de hoy.

## 8. FUERA DE ALCANCE

El plan de las cuatro compuertas, el diseño del lector `leer_retro.py`, el contenido de `grillas_mirova.yaml` de los 34, las cifras dentro de muestra de MOD-D, V375-E y V750, la regla de posición de MOD-D y de V750-A en sí, y la corrección del hito de NOAA-21 en el script de calidad de la referencia.

## 9. Cambios pedidos para sellar (resumen)

1. VPR172-01: conteo por volcán y mínimo de volcanes con evidencia en el veredicto 6; renombrar; texto de la Compuerta A.
2. VPR172-02: inventario de exposiciones en el §3; informar F26-M con y sin las tres pasadas.
3. VPR172-03: el orden de las filas 4 y 5.
4. VPR172-04: C-via 100 % como en MOD-D, o declarar la desviación; regla simétrica para records sin marca.
5. VPR172-05: nulo sin SIN SUSTRATO ni 1 %; C-K en más volcanes.
6. VPR172-06: no sellar V750-A aquí sin su verificador.
7. VPR172-07: declarar la desviación de A119(b) y la composición por satélite y cenit.
8. VPR172-08: qué brazo de posición se adopta, y qué se informa del otro.
9. VPR172-09 y -10: expectativa de MODIS y tabla de diferencias con las reglas selladas.
10. VPR172-11, -12, -13: trozos de Chillán, análogo de lejana, truncamiento del OSF.
11. VPR172-14 y -15: cifras y encabezado.
