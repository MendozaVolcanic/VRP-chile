# S159: arreglo de los instrumentos que rompió la auditoría S158 (segunda ronda)

> ⚠️ **S163**: lo que todavía aporta este trabajo se reescribió sobre `main` (`691e4d588`) en la rama `s163-instrumentos` (PR #909), que reemplaza a #889. I1, I3 y A se conservan, fusionados con #897; I2 ya había salido a #890 y D25 se decidió NO ADOPTAR (D-48). Lo que quedó y por qué: `experiments/_s163_rebase_889/NOTAS.md`. La rama de S159 está en el tag `pre-s163-rebase-889`. Las rutas `C:\vrp-trabajo\...` de abajo son del worktree de S159. Texto de S159 conservado por historia.

Worktree `C:\vrp-trabajo\s159-instrumentos`, rama `s159-instrumentos`, cortada de `origin/main` en `ac60cc9f2`.
No toca el detector: ni `pipeline/process_*.py`, ni `pipeline/store.py`, ni ningún perfil. Hallazgos de origen en
`docs/AUDIT_S158_R2.md` (rama de `C:\vrp-trabajo\s159-pruebas`): R2-7, R2-8, R2-9, VB-1, VB-2 y la nota H8 del
meta-auditor. Cada salida citada vive en esta carpeta, `C:\vrp-trabajo\s159-instrumentos\experiments\_s159\instrumentos\`.

Método por arreglo (guía de auditorías §6): prueba que falla por la razón que dice, arreglo mínimo, prueba en verde,
y mutaciones que reintroducen el defecto y tienen que volver a ponerla roja **por aserción** (A116; el script
`mutar.py` cuenta una mutación como atrapada sólo si alguna prueba cae con `AssertionError`, restaura el archivo y
compara su sha256).

## I1. Cero gránulos, L1B sin geolocalización y día parcial salían como «Cobertura: completa» (R2-9, VB-1)

**El fenómeno.** El satélite pasa o no pasa sobre el volcán; el catálogo de NASA (CMR) puede tener el gránulo o
todavía no; y el archivo de geolocalización (MOD03, VNP03) a veces llega horas después que el L1B, o no llega. El
resumen de cobertura sólo contaba búsquedas y descargas que **fallaron**, así que una búsqueda que respondía vacía (el
18-oct CMR devolvía cero gránulos de todo el día, R2-13), un L1B al que le faltaba su geolocalización (el 20-oct había
72 MOD021KM NRT contra 68 MOD03) y el día en curso, que el NRT procesa siempre aunque no haya terminado, terminaban en
«Cobertura: completa».

**¿Puede el código saber si cero gránulos era normal?** No. `pipeline/fetch.py` no tiene un modelo de órbita (el que
existe vive en `Sat_Tracker`, otro proyecto, y la regla 4 del mapa prohíbe leerlo por disco). Lo que sí sabe es si la
búsqueda **falló** (cortacircuito de CMR o excepción, ya registrado como falla) o **respondió vacía**. Por eso:

| tipo de incidencia | cuándo | cuenta en `--estricto-cobertura` | NRT (sin estricto) |
|---|---|---|---|
| `sin_granulos` | la búsqueda del L1B respondió vacía y no hubo falla en esa plataforma | **no** (sin juicio) | código 0 |
| `sin_geolocalizacion` | L1B en el catálogo sin su geolocalización (`fetch.py`), o en disco sin su archivo de geolocalización (`run_pipeline.py`, los tres procesadores) | sí, código 3 | código 0 |
| `dia_parcial` | al buscar, el día UTC no había terminado más la latencia mínima de LANCE (3 h, la que da el CLAUDE.md del proyecto, «NASA LANCE NRT ~3h latencia») | sí, código 3 | código 0 |

Un día más viejo que eso puede seguir incompleto en el catálogo (Standard publicado a medias, gránulos tardíos) y el
código no tiene cómo saberlo: el «día parcial» se marca sólo donde es seguro. El filtro nocturno que deja cero
gránulos no es incidencia: ahí el código sabe por qué no hay nada.

**Salida roja** (`i1_rojo.txt`): 10 fallas, 3 pasan (el control del día limpio, en sus dos modos, y el de la búsqueda
caída). Las fallas de comportamiento son por aserción («cero gránulos se informó como cobertura completa (R2-9)», «un
L1B sin geolocalización se descartó en silencio (VB-1)», «el día en curso se informó como cobertura completa»); la de
la función nueva `fetch.dia_incompleto` cae por `AttributeError`, que es lo esperable para una función que no existe,
y su comportamiento ya lo atrapan por aserción las pruebas de `main()`.

**Arreglo.**
- `pipeline/fetch.py`: registro aparte `_INCIDENCIAS` con `registrar_incidencia`, `incidencias_de_cobertura` y
  `dia_incompleto`; `limpiar_fallas()` limpia las dos listas. En `fetch_for_volcano`: `dia_parcial` una vez por volcán y
  día; `sin_granulos` sólo si la plataforma no registró falla (no duplica una búsqueda caída); `sin_geolocalizacion`
  cuando `_match_granules` descarta L1B. Parámetro nuevo opcional `ahora` (por defecto la hora UTC del proceso).
- `scripts/run_pipeline.py`: las tres copias de «No geolocation match» (MODIS, VIIRS 375, VIIRS 750) llaman a
  `_sin_geolocalizacion`, que imprime lo mismo y registra la incidencia (A102); `informar_cobertura(..., incidencias=...)` escribe `incidencias` en el JSON, imprime cada tipo con
  su título y deja de decir «completa»; el código 3 sólo con `--estricto-cobertura` y sólo por fallas o incidencias
  que cuentan. No emite `::warning` por incidencias: el NRT procesa siempre el día en curso y vería un aviso por volcán
  en cada corrida; van al stdout y al resumen del job.
- `scripts/reproc_brazos.py`: lee `incidencias` de cada brazo, las agrega al JSON de cobertura y, en modo estricto,
  sale con 3 también por las que cuentan.

**Salida verde** (`i1_verde.txt`): 61 de 61 en el archivo nuevo y en los dos de cobertura de S157
(`test_reproc_brazos_s157.py`, `test_busqueda_ventana_s157.py`).

**Mutaciones** (`i1_mutaciones.txt`): **9 de 9 atrapadas por aserción**: no registrar `sin_granulos`; registrarlo
aunque la búsqueda haya fallado; no registrar el L1B sin geolocalización en el catálogo; no registrarlo en disco; día
parcial nunca detectado; modo estricto que ignora las incidencias; resumen que vuelve a decir «completa»; `sin_granulos`
que pasa a contar en modo estricto (un NRT o reproceso que sale con 3 sin juicio); `reproc_brazos` que ignora las
incidencias.

**Efecto en el NRT.** `nrt.yml` no pasa `--estricto-cobertura` (verificado en sus dos llamadas a `run_pipeline.py`),
así que su código de salida no cambia en ningún caso (lo fijan las pruebas parametrizadas con `estricto=False`). Lo que
sí cambia: el resumen de cada corrida deja de decir «completa» (el día en curso siempre es parcial) y el resumen del
job gana una sección «Incidencias de cobertura». Ningún workflow lee ese texto (`grep` de «Cobertura: completa» y
«Cobertura INCOMPLETA» en `.github/` y `scripts/`). En los reprocesos con `--estricto-cobertura` (`reproc-chunked.yml`,
`reproc_brazos.py`) un L1B sin geolocalización o un día sin terminar ahora ponen el job rojo: es el cambio buscado
(A108), pero es un cambio de comportamiento.

**Lo que no cubre.** Un L1B que no llegó al disco con su geolocalización sí presente queda en silencio (habría que
cruzar en sentido contrario); y un día que el catálogo tiene a medias después de las 3 h no se puede ver desde acá.


## I2. El evaluador de D25: calibración por defecto (VB-2) y control placebo obligatorio (R2-8)

**(a) El defecto.** El sello vive en `experiments/_s157_prereg_d25/ADENDA_CALIBRACION.md:3-8`: «SELLADA por Nicolás el
2026-10-20 (D-27) ... Rige: §2 entero ... y §3 opción A ... El evaluador corre con `--calibracion simetrica`.» El
evaluador tenía `CALIB_MODO = "sellada"` (l. 79 en `origin/main`) y su mensaje decía que la simétrica «requiere el sello
de Nicolás». Ahora `CALIB_MODO = "simetrica"`, con la cita del sello en el comentario; `--calibracion sellada` sigue
disponible para reproducir lo medido antes del sello, y el mensaje lo dice.

**(b) Por qué un placebo.** M pregunta si D queda más cerca del VRP de MIROVA que K. Pero K queda **bajo** MIROVA (razón
mediana 0,52 a 0,66 en los estratos que deciden), así que cualquier brazo que sólo suba la magnitud se acerca, sea o no
un mecanismo fiel. Si M aprueba un brazo que multiplica por 1,2, no distingue a D25 de una ganancia cualquiera. El
evaluador ahora corre, antes de dar veredicto, la **misma** decisión de cada estrato que decide o bloquea (regla,
calibración y opción A, función `decidir_estrato`, extraída sin cambios de `contar`) sobre K×1,2 y K×0,8, con los
controles dados por buenos (se prueba la métrica, no la corrida). Si alguna da MEJORA, el veredicto de la ventana es
`INVALIDO POR INSTRUMENTO (motivo) | sin el placebo: <lo que habría dado>`, el más estricto del orden, y `combinar` lo
trata como malo. La regla de decisión sellada no se tocó.

**Salida roja** (`i2_rojo.txt`): 9 fallas, 1 pasa (la del texto del sello). El defecto cae por aserción
(`assert 'sellada' == 'simetrica'`); el veredicto y `combinar` por aserción («MEJORA», `assert False`); las del placebo
por `AttributeError` (la función `evaluar_m` no existía).

**Salida verde** (`i2_verde.txt`): 10 de 10. Incluye el control de que la extracción no movió la decisión (un brazo que
lleva K a mitad de camino hacia MIROVA sigue dando MEJORA con 3 volcanes) y el control de que el placebo **no**
invalida cuando K calza con MIROVA.

**Mutaciones** (`i2_mutaciones.txt`): **6 de 6 atrapadas por aserción**: el defecto vuelve a la calibración original; el placebo no se corre; sólo prueba 1,2 (en la primera corrida esta mutación caía por `KeyError` y no contaba: la prueba se corrigió para fallar por aserción y se repitió); un placebo con MEJORA no invalida; el veredicto ignora el placebo; `combinar` no trata INVALIDO como malo..

**Prueba de punta a punta** (`probar_evaluar_d25.py`, salida en `probar_evaluar_d25_salida.txt`): los casos de reglas
corren con `--omitir-placebo-solo-prueba` (si no, el placebo los taparía a todos, ver abajo); `sellada` y `p2_m_indec`
pasan `--calibracion sellada` explícito porque el defecto cambió; caso nuevo `placebo` con el placebo encendido.
**28 de 28 casos OK** (los 27 de S157 más `placebo`). El caso `placebo` da, sobre el nulo de V1 con los K reales: «INVALIDO POR INSTRUMENTO (placebo x1.2 da MEJORA en VIIRS750|z<=40; placebo x1.2 da MEJORA en VIIRS375|sin_kernel|z<=40) | sin el placebo: SIN EFECTO». Los demás casos dan lo mismo que en `probar_salida.txt` de S157, incluido `sellada` (INDECIDIBLE), lo que comprueba que extraer `decidir_estrato` no movió ninguna decisión. El mutador viejo `mutar_evaluador_d25.py` no se volvió a correr (sus textos siguen presentes en el
archivo, ahora dentro de `decidir_estrato`).

**El placebo sobre los pares reales de K** (`placebo_real.py`, salida `placebo_real_salida.txt`; mismos pares que
`calibracion_previa.py`, D = K):

| ventana | calibración | estratos que deciden con K×1,2 = MEJORA | veredicto del placebo |
|---|---|---|---|
| V1 | simétrica (sellada D-27) | VIIRS 750 z≤40 (n 29, razón K 0,659) y VIIRS 375 sin kernel z≤40 (n 103, razón 0,518) | **INVALIDO** |
| V2 | simétrica (sellada D-27) | VIIRS 750 z≤40 (n 64, razón 0,540) y VIIRS 375 sin kernel z≤40 (n 108, razón 0,579) | **INVALIDO** |
| V1 y V2 | original (§5) | ninguno: todos INDECIDIBLE | OK, pero esa calibración no decide nada |

En VIIRS 750 z>40 el placebo da NEUTRO sólo porque la opción A exige dos volcanes y ese estrato es casi todo Chillán.
K×0,8 da EMPEORA en todos. **Consecuencia: con el placebo obligatorio, el A/B de D25 sale INVALIDO POR INSTRUMENTO en
las dos ventanas pase lo que pase con D25.** Es el choque entre el sello y el placebo que pide anotar el encargo; va a
decisiones pendientes.


## I3. Cuatro definiciones de «alerta de MIROVA» (H8 del meta-auditor de la segunda ronda)

**Inventario.** Dos preguntas distintas: qué fila es una alerta (tipo) y con qué pasada nuestra se parea (ventana).

| dónde | qué es alerta | pareo | uso |
|---|---|---|---|
| `scripts/banco_paridad.py:196-199` `es_alerta` | tipo que **empieza** con «ALERTA», salvo `ALERTA_SIN_GEOMETRIA_OCR` | `TOL_S`, l. 76: ±120 s; `parear`, l. 251 | etiquetador de producción (F/K, D25, autoauditoría, más de 70 scripts) |
| `scripts/clase_mirova.py:47` `TIPOS_ALERTA` | lista **cerrada** `ALERTA_TERMICA`, `ALERTA_TERMICA_OCR` | `VENTANA_S`, l. 112: ±120 s («la del pareo del etiquetador») | protegidas (l. 65), regla de mínimas D-9 (l. 130) |
| `pipeline/mirova_csv_loader.py:111` `_ALERT_TIPOS` | la misma lista cerrada | propio del loader | loader viejo (memoria S139: borra negativos) |
| `scripts/vigilancia_sombra.py:62`, `scripts/auto_audit_weekly.py:400` | (heredan de banco_paridad) | `cm.VENTANA_S` | vigilancia de la sombra, auto-audit |
| `scripts/validate_lascar_vs_mirova.py:61` | | 30 min, «el más cercano» | script viejo de Láscar |
| `frontend/index.html:1452` y `:1559` | | `TOL_MS = 60 min`, el más cercano | sólo para dibujar la línea de MIROVA en el gráfico |
| primera ronda S158 F1 (`experiments/_s158_audit/f1/alertas_mirova_perdidas.py:38,49`, `cruce_referencia.py:56`) | sólo tabla, `ALERTA_TERMICA` | 20 min | auditoría |
| primera ronda S158 V1 (`experiments/_s158_audit/v1/cruce_v750_k.py:69`, `h5_cruce.py:13`, `recall_k.py:16`) | tabla más OCR | 8 min | auditoría |
| primera ronda S158 F3 (`experiments/_s158_audit/f3/mismo_k.py:37`) | `banco_paridad` | 5 min | auditoría |
| primera ronda S158 V2 / F3 (`experiments/_s158_audit/f3/scraper2026.py:43`, `dentro_inner.py:22`) | | minuto exacto (`[:16]`) | auditoría |

(Las rutas de `experiments/_s158_audit*` están en la rama de `C:\vrp-trabajo\s159-pruebas`, leídas con `git grep`.)

**Lo que difiere hoy, medido.** Los CSV de referencia traen sólo `ALERTA_TERMICA` (1.652 en el consolidado, 445 en el
respaldo), `ALERTA_TERMICA_OCR` (987) y `ALERTA_SIN_GEOMETRIA_OCR` (41) como tipos de alerta, así que el prefijo de
`banco_paridad` y la lista cerrada de `clase_mirova` dan **lo mismo** en las reglas «original» y «SN». Difieren en el
modo SE de D-9, donde `aplicar_regla_minimas` crea `ALERTA_MINIMA_SE`: el prefijo lo cuenta como alerta de la noche y
la lista no, y eso es **a propósito** (`clase_mirova.py:91-93`, «la noche no cambia»). Y difieren ante cualquier tipo
nuevo que invente el scraper. En los scripts de producción el pareo ya era uno solo (±120 s); los 20, 8, 5 minutos y
el minuto exacto son de scripts de auditoría.

**Lo implementado (mecánico, no cambia ningún número).** La ventana de pareo estaba escrita como literal dos veces
(`banco_paridad.TOL_S = 120` y `clase_mirova.VENTANA_S = 120`). Ahora `banco_paridad.TOL_S` se importa de
`clase_mirova.VENTANA_S`. Prueba `tests/test_pareo_unico_mirova_s159.py`: roja antes (`i3_rojo.txt`, por aserción:
«ventana de pareo escrita como literal en: ['banco_paridad.py', 'clase_mirova.py']»), verde después; mutación que
vuelve a escribir el literal: atrapada por aserción (`i3_mutacion.txt`).

**Lo propuesto (no implementado: no es mecánico).** Una sola función en `scripts/clase_mirova.py`:

```python
def alerta_mirova(fila, modo_minimas=MODO_MINIMAS) -> str:
    """'alerta' | 'minima_se' | 'sin_geometria' | 'fp' | 'rutina'. Única definición del tipo; la noche, la
    protegida y la regla D-9 se derivan de esta clasificación, no de prefijos ni listas sueltas."""

def parear_pasada(lista, t, tol_s=VENTANA_S):
    """Todas las filas a ±tol_s de t (lo que hoy hace banco_paridad.parear)."""
```

Para adoptarla hay que decidir qué hacer con `ALERTA_MINIMA_SE` y con un tipo nuevo desconocido (¿error ruidoso o
rutina?), y migrar `banco_paridad.es_alerta`, `clase_mirova.TIPOS_ALERTA` y `mirova_csv_loader._ALERT_TIPOS`. Con la
referencia de hoy no cambiaría ningún número en «original» ni «SN», pero sí podría cambiar el modo SE y los scripts de
auditoría que parean a 20, 8 o 5 minutos, cuyos números ya están publicados en `docs/AUDIT_S158*.md`. Por eso queda
escrita y no aplicada. Lo que sí conviene desde ya: todo script nuevo que cruce con MIROVA importa `cm.VENTANA_S` y
`bp.es_alerta` en vez de escribir su propio pareo.


## A. El tope de cordura de `pipeline/store.py` anula VIIRS 375 sin mirar la temperatura (R2-7)

**El fenómeno.** El tope de 50.000 MW existe para descartar basura (un número de DN sin enmascarar que dio 1,5 millones
de MW con BT 566 K). Pero el récord documentado por MIROVA es del orden de 70 GW, sobre el tope: una erupción enorme
de verdad también lo pasaría. Por eso el tope decide por la **causa**: si la temperatura de brillo supera el límite
físico del sensor (500 K) es saturación y se anula; si es plausible, se conserva y se marca. En VIIRS 375 la
temperatura viene en `t_max_i04_k`, y `append_record` la copia a `t_max_k` **después** de aplicar el tope
(`pipeline/store.py:551` el tope, `:556-557` la copia). El tope ve `t_max_k = None`, lo toma como «no se puede
juzgar» y anula. O sea: en VIIRS 375 la erupción más grande imaginable se publicaría como cero. Hoy 0 de 74.811 records.

**Prueba** (`tests/test_tope_cordura_v375_s159.py`, `append_record` real sobre `tmp_path`, nunca `data/`):
- VIIRS 375 con 60.000 MW y 420 K: tiene que conservarse con `vrp_exceeds_sanity_cap`. Marcada
  `xfail(strict=True)` con el motivo. Hoy: XFAIL. Con `--runxfail` cae por aserción: «el tope anuló una magnitud con BT
  de 420 K» (`a_rojo_runxfail.txt`).
- Controles que pasan hoy: VIIRS 750 con la misma magnitud y temperatura se conserva; VIIRS 375 a 600 K se anula (prueba
  que `append_record` sí corre el tope; sin eso el caso de arriba no diría nada).

**Control de la marca** (`a_control_arreglo_simulado.txt`): el plugin `simula_arreglo_tope.py` envuelve
`store._apply_sanity_cap` para copiar la temperatura antes de juzgar, **sin editar** `store.py`. Con el arreglo
simulado la prueba pasa y la suite se pone roja por `XPASS(strict)`, y los dos controles siguen verdes (el de 600 K
sigue anulándose). La marca vigila el defecto y no otra cosa.

**Diff propuesto** (no aplicado: A45 pide tag defensivo `pre-s159-tope-cordura` y el sí de Nicolás). Entre el tope y la
copia sólo corre `_apply_vrp_floor`, que no lee `t_max_k` (`grep` de `t_max_k` en `store.py`: sólo la l. 165 del tope
y la copia), así que mover la copia no cambia nada más que la decisión del tope:

```diff
@@ pipeline/store.py, append_record
-    _apply_sanity_cap(record)
-
-    _apply_vrp_floor(record)
-
-    # Normalize t_max_k for VIIRS 375m (uses t_max_i04_k internally)
-    if "t_max_i04_k" in record and "t_max_k" not in record:
-        record["t_max_k"] = record["t_max_i04_k"]
+    # Normalize t_max_k for VIIRS 375m (uses t_max_i04_k internally).
+    # S159 (R2-7): ANTES del tope de cordura, que juzga la causa con t_max_k. Después, el tope veía None en
+    # VIIRS 375 y anulaba una magnitud con temperatura plausible (la erupción más grande se publicaba como cero).
+    if "t_max_i04_k" in record and "t_max_k" not in record:
+        record["t_max_k"] = record["t_max_i04_k"]
+
+    _apply_sanity_cap(record)
+
+    _apply_vrp_floor(record)
```

Al aplicarlo, quitar la marca `xfail` de `test_v375_magnitud_enorme_con_temperatura_plausible_se_conserva`.


## Suite completa (A112: árbol quieto; A50: comparada con `origin/main`)

- **Antes** (`suite_antes.txt`): corrida sobre el worktree recién cortado de `origin/main` (`ac60cc9f2`), sin ningún
  cambio y sin editar nada mientras corría: **2.342 pasan, 29 saltadas, 1 xfail**, 216 s. Es la línea base de
  `origin/main`.
- **Después** (`suite_despues.txt`): **2.369 pasan, 29 saltadas, 2 xfail, 0 fallas**, 193 s, sobre el árbol quieto con todos los cambios. Diferencia con la línea base: +27 pruebas nuevas que pasan (13 de I1, 10 de I2, 2 de I3, 2 controles de A) y +1 xfail (la marca de A). Ninguna falla, así que no hay nada que llamar «preexistente».
- **Una corrida intermedia falló y era mía** (A50): con el registro de `sin_geolocalizacion` escrito en línea en los tres procesadores, `test_guard_declarado_vs_efectivo_s131.py::test_g8_*` cayó en 2 casos, porque CLAUDE.md cita `scripts/run_pipeline.py:234` (`get_detection_anchor`) y `:244` (`local_kernel_bg`) y las tres líneas nuevas las corrían. En la línea base de `origin/main` esas pruebas pasaban. Arreglo: el registro vive en una función aparte (`_sin_geolocalizacion`) y cada procesador cambia una línea por una línea, así que las citas no se mueven y CLAUDE.md no se tocó. Después de eso se repitieron I1, sus 9 mutaciones y la suite completa.

## Decisiones pendientes para Nicolás

1. **El sello D-27 y el placebo chocan (I2).** Con la calibración sellada (simétrica, opción A), K×1,2 da MEJORA en
   VIIRS 750 z≤40 y en VIIRS 375 sin kernel z≤40, en V1 y en V2, porque K queda bajo MIROVA. Con el placebo
   obligatorio que pidió el coordinador, el A/B de D25 sale INVALIDO POR INSTRUMENTO en las dos ventanas pase lo que
   pase con D25 (si V1, V2a y V2b se evalúan con este evaluador, saldrán así). La regla sellada no se tocó. Opciones:
   - **(a) dejar el placebo tal cual** y rediseñar M antes de leer el A/B. Ejemplo de M que un placebo no aprueba: la
     dispersión de log10(D/MIROVA) alrededor de su propia mediana, que una ganancia uniforme no cambia.
   - **(b) usar el placebo como comparador y no como compuerta:** MEJORA sólo si D queda más cerca de MIROVA que K×ĝ,
     con ĝ la mediana de D/K de los mismos pares (una ganancia uniforme del mismo tamaño que el efecto medio de D25).
     Pregunta si D25 sube **los pares correctos**, no si sube en promedio. Recomendado, porque se espera que D25 suba la
     magnitud (vecinos más fríos que el anillo, probe del L1B de Chillán) y lo que importa es dónde.
   - **(c) quitar el placebo** y leer M como «más cerca, por la razón que sea», escrito así en el veredicto.
   Cualquiera es un cambio de la regla sellada o de su lectura: requiere sello nuevo.
2. **Mergear I1 toca el flujo del NRT** (`pipeline/fetch.py`, `scripts/run_pipeline.py`). El código de salida del NRT no
   cambia; su resumen deja de decir «completa» en cada corrida (el día en curso es parcial) y los reprocesos con
   `--estricto-cobertura` pasan a salir rojos por un L1B sin geolocalización o un día sin terminar. Requiere tu sí.
3. **Aplicar el diff de `store.py` (A)** con tag `pre-s159-tope-cordura` y quitar la marca `xfail`. Requiere tu sí (A45).
4. **Una sola definición de alerta de MIROVA (I3):** qué hacer con `ALERTA_MINIMA_SE` (hoy alerta de noche en
   `banco_paridad` y no en `clase_mirova`, a propósito) y con un tipo nuevo del scraper (¿error ruidoso o rutina?). Sin
   eso la función única no es mecánica.
5. **La salida `--omitir-placebo-solo-prueba`** existe sólo para que `probar_evaluar_d25.py` pruebe cada regla sin que
   el placebo la tape; deja el veredicto marcado como «no vale para decidir». Si prefieres que no exista, la prueba de
   punta a punta tiene que esperar a que se resuelva el punto 1.


## Nota del coordinador (S159, 2026-10-21)

La pieza I2 (evaluador de D25 y su placebo) salió de este PR a uno aparte, rama `s159-evaluador-d25`, porque cambia el instrumento de un pre-registro sellado y se corrige sólo por adenda con Nicolás (R2.1 c del loop). Sus pruebas, salidas y `placebo_real.py` viven en esa rama; las mutaciones I2 de `mutar.py` apuntan a un archivo que en esta rama sigue como en `main`.
