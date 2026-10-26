# Verificación con contexto limpio de VE-01 (Tupungatito, 2026-09-29 04:54 UTC)

- Fecha y hora del servidor: 2026-10-23 18:11 UTC (header `Date` de la API de GitHub); `caminos.md` sellado a las 18:03:24 UTC.
- Commit medido: `3bbd18d2c` (igual a `origin/main` al empezar). Rama del hallazgo: `origin/claude/gracious-merkle-6447d8` (PR #898, abierto).
- Modelo: Claude Opus 5.5 (`claude-opus-5-5`), esfuerzo bajo. El hallazgo lo hizo otra sesión; no vi su razonamiento antes de escribir `caminos.md` (sha256 `cb91c692…828f`, al pie del archivo).
- CARPETA: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\frosty-lamport-3fef52\experiments\_s161_verif_ve01\`
- Qué NO miré: VE-02 (Cordón Caulle) ni el resto del PR #898 (mapa, persistencia, `01_` y `02_`); las otras cinco protegidas OCR de Tupungatito (sólo las listo, ver SEGUIMIENTOS); qué es físicamente la fuente (no tengo DEM ni otra imagen); el código del scraper Mirova-v1 (leí `volcanes.py` remoto y lo que cita `docs/audit_s139/EJE_1_semantica_etiquetas_referencia.md`).

## En una pantalla

**Veredicto: CONFIRMADO EN PARTE. La parte que serviría para decidir un cambio de radio está REFUTADA.**
1. Sí: MIROVA alertó a las 04:54 (1,86 MW, marco verde) y nosotros no publicamos esa pasada porque el píxel cae fuera de los 7 km. El predicado del tablero, ejecutado con node, lo confirma.
2. No está «en el cráter». El punto caliente de la miniatura de MIROVA está sobre nuestro píxel, a 9,4 km al E del cráter. Esto lo decía también el README de la otra sesión; el error está en el resumen que me pasaron.
3. No es una protegida perdida «por radio». La propia serie de distancia de MIROVA dibuja esa pasada a unos 9,6 km, con el color de «más de 7 km». La fila OCR quedó como ALERTA con 5,68 km porque leyó el marcador de la pasada de las 05:18. Con la distancia buena, la regla del scraper (`limite_km` 7) la habría dejado en FALSO_POSITIVO_OCR, y el banco de paridad la contaría `far_ref`, no protegida.
4. Nuestro «far» coincide con la clase que le da MIROVA. Por VE-01, Tupungatito no necesita cambio de radio. El defecto está en la referencia: está dentro del tramo de A119 que el propio banco anuncia.

---

## Hallazgos (lo peor primero)

### VE01-V01: VE-01 no es una protegida perdida por radio: su condición de protegida sale de una distancia OCR leída en el marcador de otra pasada
- SCRIPT:SALIDA: `05b_recorte_serie.py` : `05b_recorte_serie_salida.txt` y `05b_serie_dist_28_29sep_x8.png`; `04_etiqueta_banco.py` : `04_etiqueta_banco_salida.txt`; fila en `data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv` (Tupungatito, `2026-09-29 04:54:00`).
- QUÉ PASA: esa noche hubo dos focos. A las 04:54, Suomi NPP vio uno de 1,86 MW a ~9,5 km del centro de la grilla de MIROVA, que es el mismo píxel que el nuestro. A las 05:18, NOAA-20 vio el cráter con 0,04 MW a 5,41 km. Los dos marcadores quedan en la misma columna de la serie «Last Month» de la imagen Distance de MIROVA: el cuadrado negro (leyenda de MIROVA: «>7km») tiene el tope en y = 221, o sea unos 9,6 km con el centro del marcador a unos 9,5 km; el círculo rojo («<7km») tiene el tope en y = 252 a 253, con el centro a unos 5,3 km. La fila OCR dice «Grupo píxeles rojos Y=253 (… dist≈5.68 km …)»: el OCR midió el tope del círculo rojo, que es el de 05:18 (la tabla lo da a 5,41 km), y se lo puso a la pasada de 04:54. La propia fila OCR trae `Distancia_aprox_min_km` 5,41, `Distancia_aprox_max_km` 9,59 y método `ambiguo`, o sea los dos marcadores. Como la tabla `latest.php` no tiene fila a las 04:54, el canal OCR es la única fuente de esa pasada, y la memoria `reference_ocr_imagen_de_otra_pasada` dice que para esas filas el VRP sí es de su pasada pero la distancia puede ser de otra. Con la distancia correcta, el scraper (Mirova-v1 `volcanes.py` l. 37-38, `limite_km=7.0`, leído hoy por la API) la habría marcado FALSO_POSITIVO_OCR. Medido con `banco_paridad.etiquetar`: tal como está, la pasada sale `pos` (protegida, ≥ 1 MW) con la regla original y con la SN; con la fila a 9,59 km y tipo FALSO_POSITIVO_OCR sale `far_ref`. La lectura B, que sí la contaría, fue descartada (`docs/MISSION.md` l. 102 a 108, TEXTO: «La lectura B (toda pasada en que MIROVA ve 1 MW o más, a cualquier distancia, 992 pasadas) quedó descartada»).
- CÓMO SE VE EN EL DASHBOARD: el tablero no muestra la pasada de las 04:54; ese 29-sep muestra dos detecciones pequeñas en el cráter (05:18 y 06:00, que publican). Eso coincide con lo que MIROVA clasifica como cumbre. Lo que se tuerce es el evaluador: cuenta una protegida perdida que no existe, y en un A/B con regla de veto («ninguna protegida se puede perder») una sola de estas filas puede vetar una regla.
- CÓMO REPRODUCIRLO: `python -I experiments/_s161_verif_ve01/05b_recorte_serie.py <ruta>/evidencia_mirova/20261023_091135_VIIRS375_Dist.png` y `python -I experiments/_s161_verif_ve01/04_etiqueta_banco.py` desde la raíz del worktree. Volcán Tupungatito, pasadas 2026-09-29 04:54 (Suomi NPP) y 05:18 (NOAA-20) UTC.
- CONFIANZA: CONFIRMADO en la lectura de la imagen (dos marcadores con colores y alturas medidos por píxel) y en la etiqueta del banco. Hay una inferencia: atribuir el cuadrado negro a la pasada de 04:54. Se apoya en que es la única otra pasada con detección esa noche (06:00 y 06:36 son RUTINA con VRP 0 en la tabla) y en que nuestro píxel queda a 9,29 km de `mirova_center`, mientras nuestros píxeles de 05:18 en el cráter quedan a 5,0 a 5,4 km del mismo punto y MIROVA los da a 5,41.
- GRAVEDAD: 3. No cambia lo que ve el operador, pero sí cambia lo que se decidiría: sin esta verificación se habría pre-registrado un cambio de radio en Tupungatito para capturar un foco que MIROVA misma pone fuera de sus 7 km.

### VE01-V02: los hechos de base de VE-01 se confirman: MIROVA alertó a las 04:54 sobre nuestro mismo píxel, y lo que nos deja fuera es el radio de 7 km
- SCRIPT:SALIDA: `rerun/03_ve01_ve02_png.py` : `rerun/03_salida_rerun_datos_main.txt` (idéntica a la commiteada por la otra sesión); `02_mirar_miniaturas.py` : `02_mirar_miniaturas_salida.txt`, `02_miniatura_0454_marcas.png`; `06_nulo_georreferencia.py` : `06_nulo_georreferencia_salida.txt`; `03_predicado_y_etiqueta.py` : `03_predicado_y_etiqueta_salida.txt`; `01_records_29sep.py` : `01_records_29sep_salida.txt`.
- QUÉ PASA:
  - El panel «Latest Images» de MIROVA (captura 12:28:36 UTC, md5 `a4e7d743…e640`, copia en `evidencia_mirova/`) tiene una miniatura propia por pasada. La de 04:54 lleva el rótulo «29-Sep-2026 04:54:00», «VRP =1.86 MW», «ZEN =62°» y marco verde. Nuestro record de esa pasada (VIIRS_SNPP, gránulo `VNP02IMG.A2026272.0454.002.2026272125452.nc`) tiene cenit 62,41°: es la misma pasada, no una imagen de otra hora (camino C1 descartado).
  - En esa miniatura, nuestro píxel (-33,36927 / -69,72791; 302,41 K; 1,112 MW; 9,40 km de rumbo 77° desde el cráter) cae sobre un punto brillante. Con el instrumento de la otra sesión da z 21,3, el máximo de la imagen. Con mi lectura directa da 214 de gris contra una mediana de 104 (+2,8 MAD), y se ve en el recorte ampliado.
  - En las otras nueve miniaturas del panel ese mismo lugar da z 0,8 a 3,3. El cráter da z 6,7 a 10,9 en las cuatro miniaturas nocturnas despejadas (06:36, 06:00, 05:18 y 04:54), o sea que no es propio de la alerta de 04:54.
  - Nuestro record es `far`. El predicado del tablero con node da [summit 0, valid 1, artefacto 0, VRP mostrado 0, publica 0]. Para que publique hay que cambiar los dos cortes de 7 km: si sólo se pasa `distance_class` a `summit`, sigue sin publicar (VRP mostrado 0, porque el píxel queda fuera del radio interno del tablero); si sólo se sube el radio interno a 10 km con la clase `far`, tampoco; con los dos cambios publica 1,1115 MW. Control de identidad del predicado: ([0, 1, 1, 1, 0], [1, 0]), el esperado.
- CÓMO SE VE EN EL DASHBOARD: invisible. La pasada de 04:54 no aparece, y esa noche se publican las detecciones del cráter de 05:18 (0,028 MW) y 06:00 (0,037 MW).
- CÓMO REPRODUCIRLO: `python -I experiments/_s161_verif_ve01/03_predicado_y_etiqueta.py` y `python -I experiments/_s161_verif_ve01/06_nulo_georreferencia.py` desde la raíz y desde CARPETA respectivamente; Tupungatito, 2026-09-29 04:54 UTC.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1 como pérdida, porque MIROVA misma pone el foco en su clase de más de 7 km (VE01-V01).

### VE01-V03: la frase «está en el cráter según el panel» del encargo contradice la salida y el README de la otra sesión
- ARCHIVO:LÍNEA: `experiments/_s161_mapa_persistencia/README.md` l. 73 a 79 en `origin/claude/gracious-merkle-6447d8`, TEXTO: «Su punto más brillante (z 21,3) está a 0,02 km de nuestro píxel (302 K, 1,11 MW), a 9,40 km al E del cráter».
- QUÉ PASA: el README ubica la fuente donde está nuestro píxel. La afirmación que me pasaron dice «en el cráter». El README también menciona que «el cráter también se ve, débil (z 10,5)»; si alguien leyó esa frase como la ubicación de la alerta, se equivocó: el cráter aparece igual en pasadas RUTINA (z 9,6 a 10,9). Quien resume para decidir tiene que corregir la frase antes de que se use.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git show origin/claude/gracious-merkle-6447d8:experiments/_s161_mapa_persistencia/README.md | sed -n 73,83p`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2. Leída tal cual, la frase empuja a la conclusión equivocada (nuestro píxel mal ubicado), aunque los datos dicen otra cosa.

### VE01-V04: SOSPECHA: la fuente de 04:54 podría ser un artefacto de Suomi NPP, no calor
- SCRIPT:SALIDA: `01_records_29sep_salida.txt`; `06_nulo_georreferencia_salida.txt` (bloque de placebos); `rerun/03_salida_rerun_datos_main.txt` (recurrencia).
- QUÉ PASA: es un solo píxel de 302 K, de noche, a 9,4 km al E del cráter, en el borde del barrido (cenit 62°). NOAA-20 pasó 24 minutos después con mejor geometría (cenit 42°) y no lo ve: nuestro record de 05:18 no tiene píxel ahí, y en la miniatura de MIROVA de 05:18 ese lugar da z 1,0. NOAA-21, a las 06:00, tampoco. En todo nuestro corpus hay dos pasadas con un píxel a 1 km o menos de ese punto (2026-08-23 06:30 y 2026-09-29 04:54), y las dos son de Suomi NPP. Suomi NPP aporta 842 de 2.579 records I-band de Tupungatito, así que la probabilidad de que las dos caigan en esa plataforma por azar es de 0,33² ≈ 0,11: es una pista, no una prueba. Un foco real de 1 a 2 MW que se apaga en menos de 24 minutos no es imposible, pero tampoco es lo esperable. No tengo DEM ni imagen óptica del punto.
- CÓMO SE VE EN EL DASHBOARD: invisible hoy. Si alguien sube el radio, aparecería como un foco ENE aislado.
- CÓMO REPRODUCIRLO: `python -I experiments/_s161_verif_ve01/01_records_29sep.py`; mirar las columnas 2 y 3 del panel en `evidencia_mirova/`.
- CONFIANZA: SOSPECHA.
- GRAVEDAD: 2. Para la réplica no cambia nada, porque MIROVA alertó igual. Sí pesa si se piensa en el perfil `experimental` o en un cambio de radio.

---

## Caminos de `caminos.md` y cómo quedó cada uno

| camino | resultado | evidencia |
|---|---|---|
| C1, miniatura de otra pasada | descartado: el panel tiene una miniatura por pasada, con rótulo 04:54:00 y ZEN 62°, igual a nuestro cenit de 62,41° | panel en `evidencia_mirova/`, `01_…salida.txt` |
| C2, la correlación encaja por textura | descartado. Con espejos y rotación del mismo volcán (misma textura, geometría falsa), r máx 0,067 a 0,116 contra 0,711 del TIF correcto; para 05:18, 0,070 a 0,120 contra 0,857. Pico en (-1, 0); el segundo máximo está a 3 px en vertical (r 0,573), unos 1 km, muy lejos de los 9,4 km que importan | `06_…salida.txt` |
| C3, protegida sólo OCR de Suomi NPP con distancia de otra pasada | **confirmado: es el camino que tumba la conclusión** (VE01-V01) | `04_…salida.txt`, `05b_…salida.txt` |
| C4, nuestro record no es el que se cree | descartado: un solo record I-band de Suomi NPP a las 04:54, de 1 píxel, con `primary_cluster` igual al píxel (9,403 km, `geo_class` far); reprocesado el 2026-10-18 (K) | `01_…salida.txt` |
| C5, el radio no es el que se cree | descartado en lo mecánico: `inner_radius_km` 7 en `volcanoes.yaml` y 7,0 en `frontend/index.html`; hace falta cambiar los dos cortes para publicar. Pero el radio coincide con la clase «>7km» del propio MIROVA, que es lo que vuelve irrelevante la pérdida | `03_…salida.txt` |
| C6, escala de la miniatura | 1 px de miniatura son unos 0,34 km; el error de posición (pico ±1 a 3 px) es de 1 km o menos, contra 9,4 km | `06_…salida.txt` |
| C7, copia local atrasada | descartado: el worktree estaba en `origin/main` `3bbd18d2c` | `git log` |
| C8, el script no corre | corre. Con la copia de datos de S160 y con los datos de `main` de hoy, y con las PNG bajadas de nuevo, la salida es idéntica (diff sin diferencias salvo fin de línea) | `rerun/03_salida_rerun_*.txt` |

## SEGUIMIENTOS (fuera de mi eje)

- Las otras protegidas de Tupungatito también son sólo OCR, todas antes del 2026-10-09: 2026-04-13 18:24 V375 1,62 MW a 2,24 km; 08-01 05:00 V375 1,25 MW a 5,41; 08-20 17:30 V750 3,0 MW a 5,14; 09-14 06:18 V375 2,22 MW a 2,97; 09-28 05:18 V375 2,51 MW a 5,27 (`04_…salida.txt`). Las distancias de 2,24 y 2,97 km son raras, porque el cráter está a unos 5 km del centro de MIROVA. Habría que revisar cada una contra su serie Dist.png, igual que aquí. SOSPECHA de la misma familia que VE01-V01.
- `banco_paridad.etiquetar` imprime el aviso A119 («la distancia y la clase pueden ser de OTRA pasada») pero igual etiqueta esas filas como `pos`. Se podría crear un estrato «protegida OCR de Suomi NPP antes del 2026-10-09, sin verificar su distancia» y tratarlo como sin geometría. Lo decide quien orquesta.
- El parser de marcadores `05_serie_dist_mirova.py` no encontró marcadores (salida vacía, guardada en `05_serie_dist_mirova_salida.txt`): los marcadores son huecos y el filtro por tamaño de componente no los aísla. Por eso usé `05b_recorte_serie.py`, que lee por columna. Lo dejo como instrumento fallido, no como evidencia.

## VERIFICADO LIMPIO

- El script `03_ve01_ve02_png.py` de la otra sesión reproduce su salida exacta con los datos de hoy y las PNG bajadas de nuevo. Vara: diff textual contra la salida commiteada en la rama del PR.
- El predicado del tablero sobre el record de 04:54: no publica, y la causa son los dos cortes de 7 km. Vara: `frontend/index.html` de `main` ejecutado con node vía `banco_paridad.correr_node`, con control de identidad y una mutación que sí lo hace publicar.
- La georreferencia de la miniatura con la identidad «interior = bounds del TIF», corregida en 1 px. Vara: placebos del mismo volcán. El nulo de otro volcán (Isluga) que usó la otra sesión era demasiado fácil, pero el resultado se sostiene con el nulo más duro.

## SIN DATO

- Qué es la fuente ENE (calor real o artefacto de Suomi NPP): sin DEM, sin imagen óptica, sin TIF después del 22-sep.
- Si MIROVA, internamente, cuenta la alerta de 04:54 como de cumbre: sólo tengo su color en la serie Dist (negro, «>7km») y el marco verde del panel, que marca alerta en el ROI y no distingue cumbre.

## FUERA DE ALCANCE

- VE-02 (Cordón Caulle) y la pregunta del radio de 20 km de PCC: VE-01 no dice nada sobre ellos.
- Arreglos en el scraper, en el banco o en el pipeline.
