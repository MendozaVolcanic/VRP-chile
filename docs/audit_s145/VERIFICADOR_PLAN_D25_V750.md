# Verificador con contexto limpio: plan D25 (fondo por vecinos) en VIIRS 750

**Objeto**: `docs/superpowers/plans/2026-09-20-d25-fondo-vecinos-viirs750.md`
(md5 `01bfe971f9463ff211ff6ba976d3b785`) y `experiments/_s145_d25_v750/sustrato.py`
(md5 `e6e54e7cf7fff0ec55cc84ec3c17a4d6`) con su `sustrato.json`.

**Fecha**: 2026-09-20. **HEAD**: `556590265`. Nada del repo fue modificado por esta revisión
(un `git checkout --` devolvió `experiments/_s133/auditar_guards_por_subcadena.json`, que el
auditor de A92 reescribe al correr).

**Advertencia sobre el objeto**: el árbol de trabajo se movió DURANTE la revisión. Al empezar,
`git status` daba tres entradas sin seguimiento; al terminar daba además
`M docs/MIROVA_DIVERGENCES.md`, `?? docs/audit_s145/`, `?? experiments/_s145_etiquetado/` y
`?? tests/test_sustrato_s145.py`, y `sustrato.py` había sido refactorizado (extracción de la
función `noches()`, 01:06:48) con su JSON regenerado (01:07:33). Todo lo que sigue está medido
contra el estado final, y las diferencias que eso introduce están marcadas.

---

## 1. Cobertura: qué revisé y qué no

**Revisado con herramienta**:

- Las 6 tareas y sus 30 pasos, uno por uno.
- Los tres bloques de Python de las Tareas 1, 3 y 4, y los cinco bloques de test.
- Ejecución real del envoltorio de la Tarea 1 con el helper de producción (no lectura).
- Las 14 citas `archivo:línea` del plan (`process_viirs_mod.py` x6, `process_viirs.py` x5,
  `profile.py` x2, `tests/` x3).
- Los 12 números de las tablas de §1.2 contra `sustrato.json`.
- El cuerpo de `sustrato.py` (clasificación, denominadores, cuenta en noches) y su dependencia
  `scripts/banco_paridad.py` (`cargar_nuestros`, `etiquetar`, `correr_node`, `BUCKETS`).
- Los dos tests que el plan declara en §1.5, más una búsqueda dirigida de terceros:
  `test_flags_d22_d25_perfil_s142.py`, `test_gr2_profile_invariants.py`,
  `test_viirs_diag_schema.py`, `test_guard_declarado_vs_efectivo_s131.py`,
  `test_remapear_citas_s141.py`.
- La suite completa como línea base (`1551 passed, 4 skipped, 2 xfailed in 116.54s`) y la
  colección antes y después de que apareciera el archivo de test nuevo.
- Existencia de los 6 documentos que el plan referencia.

**NO revisado**:

- No corrí el pipeline ni el arnés sintético con el flag encendido: el cambio no está hecho.
  Por lo tanto **no verifiqué que el cableado propuesto produzca el efecto físico que el plan
  describe**, sólo que compila conceptualmente y que las variables están en alcance.
- No verifiqué las citas a papers de §0 y §1.1 (Coppola 2016a p. 8 ec. 6, Fernandina 2025 p. 9,
  Campus 2024 p. 3) contra los PDF renderizados (A95). Sí confirmé que `docs/MIROVA_DIVERGENCES.md`
  D25 las sostiene con localizador, y que D25 existe y está abierta.
- No reproduje `sustrato.py` de punta a punta (baja la referencia remota de MIROVA): verifiqué el
  JSON que produjo, sus definiciones y su código, no una segunda corrida.
- No revisé `docs/audit_s143/PERDIDAS_V750.md` en detalle: confirmé que existe, no que diga cinco.
- No evalué si el criterio 3 del A/B de §4 (razón de magnitud en [0,9, 1,1]) es medible con el
  instrumental actual.

---

## 2. Hallazgos GRAVES

### G1. La Tarea 4 no es ejecutable: en M-band no existe la variable `record`

**Ubicación**: plan, Tarea 4 Paso 1 (test) y Paso 3 (instrucción).

El Paso 3 dice "agregar el bloque antes del `return record`" y el test del Paso 1 exige
`assert 'record["diag_L_bg_vecinos_w_m2_sr_um"]' in s`. En `pipeline/process_viirs_mod.py` no hay
ningún `return record` ni ninguna variable `record`:

```
$ grep -n "return" pipeline/process_viirs_mod.py
...
1328:    return {
...
$ grep -n "record" pipeline/process_viirs_mod.py
172:# del record PP 2026-03-18 de 695.431 MW, F28).
1225:            # píxeles del dashboard para records VIIRS750 pure-Test1. Espejo del fix
```

Las dos únicas apariciones del string son comentarios. `calculate_vrp` termina en un **dict
literal** que empieza en la l. 1328 y cierra en la l. 1405. El espejo de I-band sí tiene la
variable (`process_viirs.py:2205-2209` escribe `record[...]` y después `return record`), y el plan
copió esa forma sin comprobarla: es el caso exacto de A89 al revés (dar por hecho que el nombre del
otro archivo está acá).

**Qué le pasa al ejecutor**: llega al Paso 3, no encuentra dónde pegar el bloque, y tiene dos
salidas. O inventa un refactor (convertir el literal en `record = {...}` seguido de
`return record`, ~78 líneas de un archivo que corre 12 veces al día sobre 11 volcanes, A45), que el
plan no declara en §2.2 ni en ninguna tarea y para el que no hay tag ni criterio de aceptación. O
"arregla" el test cambiando el aserto, con lo que el diagnóstico queda a medio construir.

**Dato a favor del refactor, si se elige**: `tests/test_viirs_diag_schema.py::_return_dict_text`
busca `(?:return|record\s*=)\s*\{` y toma la ÚLTIMA aparición, así que la conversión a
`record = {` **no** rompe `test_process_viirs_mod_paridad_diag_fields`. Lo verifiqué leyendo la
heurística completa (l. 33-52 de ese archivo). Pero eso es un dato que el plan debería traer, no
que el ejecutor tenga que descubrir.

### G2. La Tarea 4 pone en rojo un test que la Tarea 3 acaba de dejar en verde

**Ubicación**: plan, Tarea 3 Paso 1 (`test_los_tres_sitios_de_fondo_consultan_el_flag`) contra
Tarea 4 Paso 3.

El test de la Tarea 3 exige **exactamente tres** guardas:

```python
guardas = re.findall(r"if ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750:", s)
assert len(guardas) == 3, f"esperaba 3 guardas (sitios A, B y C), hay {len(guardas)}"
```

El bloque de diagnósticos de la Tarea 4 Paso 3 abre una **cuarta** con el mismo texto literal. Que
son cuatro y no tres lo dice el propio espejo:

```
$ grep -c "if ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375:" pipeline/process_viirs.py
4
$ grep -n "if ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375:" pipeline/process_viirs.py
1459, 1921, 1952, 2205    # 2205 es justamente el bloque de diagnósticos
```

**Qué le pasa al ejecutor**: el Paso 4 de la Tarea 4 espera `10 passed` y va a ver
`9 passed, 1 failed` con el mensaje "esperaba 3 guardas (sitios A, B y C), hay 4". El fallo llega
dos tareas después de haber escrito ese test, con un mensaje que apunta al lugar equivocado (dice
"sitios A, B y C" cuando el cuarto no es un sitio de fondo). El arreglo correcto es acotar el
`findall` a las guardas que preceden una llamada al envoltorio, o subir el conteo a 4 y decir por
qué, pero cualquiera de los dos es una decisión que el ejecutor toma solo, a ojo, sobre un test que
es el único control del cableado.

### G3. El plan rompe dos tests más de los que declara: el contrato de citas G8

**Ubicación**: `tests/test_guard_declarado_vs_efectivo_s131.py:146-158` y `:201-207`, contra la
Tarea 1 Pasos 3 y 4 y la Tarea 3 Paso 3.

El contrato `CITAS_CLAUDE_MD` pinea dos líneas del archivo que el plan modifica:

```python
("pipeline/process_viirs_mod.py", 440, "Villarrica/PP/Lastarria/Chaiten/PCC"),
("pipeline/process_viirs_mod.py", 159, "compute_test1_mir"),
```

y `test_g8_citas_file_line_de_claude_md_apuntan_bien` exige que el token siga en esa línea exacta.
La Tarea 1 Paso 3 manda insertar una línea de import "junto al import de `cluster_focal_vrp_mw`
(hoy la línea 147)". Simulé la inserción sobre el archivo de hoy:

```
HOY 159: 'from .test1_integrated import compute_test1_mir'
TRAS Tarea1 Paso3, linea 159: ')'
contiene compute_test1_mir? False
HOY 440: '            (Villarrica/PP/Lastarria/Chaiten/PCC), M-band sigue usand...'
TRAS insercion, 440: '            (a diferencia de process_viirs.py I-band 375m). Para vols...'
```

Las dos instancias parametrizadas caen con **una sola línea** insertada. Y el corrimiento crece:
la Tarea 1 Paso 4 agrega ~21 líneas del envoltorio antes de la l. 412, y la Tarea 3 Paso 3 agrega
dos imports dentro del bloque que empieza en la l. 73. La l. 440 termina corrida ~24 líneas.

El plan no menciona ni el contrato G8, ni `CLAUDE.md` (que cita esas mismas líneas y que la regla
A101 manda remapear por contenido con `scripts/remapear_citas.py`), ni la Tarea 6 lo contempla:
el Paso 1 espera `1561 passed` y va a ver dos fallas cuyo mensaje habla de citas de `CLAUDE.md`, un
archivo que el ejecutor no tocó. Es exactamente el escenario que ese test documenta en su docstring
("en S135, al insertar una línea en los tres procesadores... CI quedó en verde mientras CLAUDE.md
citaba las líneas viejas"), sólo que acá el guard sí lo va a atrapar, sin que el plan lo espere.

**Nota de alcance, para que no se sobre-corrija**: `test_g8b_toda_linea_citada_en_claude_md_existe_en_su_archivo`
**no** se rompe (sólo verifica que la línea exista, y el archivo crece). Y el guard de citas no lee
`docs/`, así que las citas del propio plan no son objeto de CI. Lo comprobé leyendo el cuerpo de
ambos tests.

---

## 3. Hallazgos MODERADOS

### M1. Los conteos de tests prometidos ya están desactualizados respecto del árbol de trabajo

La línea base del plan era correcta **cuando se escribió**. La medí:

```
$ python -m pytest tests/ -q -p no:cacheprovider
1551 passed, 4 skipped, 2 xfailed in 116.54s   (1557 colectados)
```

Pero durante esta revisión apareció sin commitear `tests/test_sustrato_s145.py` con 5 tests, y la
colección pasó a **1562**. Con eso la base de la Tarea 0 Paso 3 es `1556 passed, 4 skipped,
2 xfailed` y el total de la Tarea 6 Paso 1 sería 1566, no 1561. El propio plan dice que "cualquier
otro número exige explicarlo antes de seguir": el ejecutor se va a frenar en el primer paso de la
Tarea 0 por una diferencia que no es una regresión. Arreglo: recontar al ejecutar, o fijar los
números en función de la colección del momento en vez de un absoluto (A90).

### M2. Ningún test nuevo ejerce el flag encendido: los seis controles del cableado son greps de texto

De los 10 tests que el plan crea, 2 son unitarios reales (el envoltorio), 2 leen `pipeline.profile`
y **6 son búsquedas de texto sobre el fuente**. No hay ni uno que corra el sensor con el flag ON y
compare la salida. El resultado es que un cableado que lee el flag, llama al envoltorio y descarta
el valor (por ejemplo asignando a una variable que nadie usa después) pasaría los 10 en verde.

Esto es evitable con lo que ya hay: `tests/arnes_sintetico_s142.py` define `correr_v750(tipo)` con
las escenas `("nevado", "plana")`, y `test_apagado_no_cambia_nada_s142.py` ya tiene el patrón del
perfil de verificación con subproceso, incluido su propio control de instrumento
(`test_el_perfil_de_verificacion_si_mueve_viirs375`, que existe precisamente porque un test de
invariancia puede pasar por la razón equivocada). El plan lista el arnés en "Herramientas" y después
no lo usa en ninguna tarea. Es la lección A110 sin aplicar: el control se valida midiendo que
detecte el caso que dice detectar.

Caveat honesto: no verifiqué que las escenas `nevado` y `plana` de V750 produzcan un cúmulo con
píxeles alertados, así que no puedo afirmar que un test de extremo a extremo sería no vacío. Eso
hay que medirlo antes de exigirlo.

### M3. La Tarea 6 Paso 3 ya está hecha en el árbol de trabajo

`docs/MIROVA_DIVERGENCES.md` aparece modificado y su sección D25 ya contiene el párrafo
"**S145, sustrato de M-band medido antes de cualquier A/B**" con los 1035, los 2301/2299, las 48,
las 0 noches, las 20 y el enlace a este mismo plan. No está en HEAD
(`git show HEAD:docs/MIROVA_DIVERGENCES.md | grep -c "S145, sustrato de M-band"` da 0), así que es
trabajo sin commitear. El ejecutor que siga el plan al pie de la letra lo va a duplicar.

### M4. Tensión no atendida: el propio D25 dice que estos flags no se pueden A/B-ear por separado

`docs/MIROVA_DIVERGENCES.md:2259` afirma, en la misma divergencia que el plan cita como su
justificación: *"D22, D19/D2 y D25 no se pueden A/B-ear por separado"*, con la medición que la
sostiene (14 % de los records VIIRS375 y 17 % de los VIIRS750 se detectan sólo en el segundo pase).
El §4 del plan diseña un A/B de D25 sola en V750 sin nombrar esa frase. Puede que en M-band la
situación sea distinta (el sustrato muestra 1035 candidatos para D25 sola), pero eso hay que
decirlo: un A/B pre-registrado que contradice sin comentario una conclusión escrita del catálogo es
la forma de A95 (un cierre hereda la lectura con que se derivó, y acá se está pasando por encima de
uno sin refutarlo).

---

## 4. Hallazgos MENORES

| # | dónde | qué |
|---|---|---|
| m1 | §1.4, "`hot_mask_2d`, fijada en `:785-853`" | se sigue reasignando después: `911` (`= final_active_mask`), `928` (`&= final_thr_mask`), `937` (`= np.zeros_like`). La conclusión del plan (los 3 sitios son posteriores, el sitio A está en la 983) **es correcta**; la cita subestima dónde queda fijada, y un ejecutor que la tome al pie podría insertar algo entre 853 y 937 creyendo que ya está cerrada |
| m2 | Tarea 5 Paso 2, "el decorador ... hoy la línea 221" | está en la **222**; el `def` en la 223, que el plan sí cita bien en §1.5 |
| m3 | Tarea 3, `test_el_recorte_a_cero_sigue_despues_del_fondo_nuevo` | `assert s.count("np.maximum(") >= 3` ya vale 3 hoy sin ningún cambio, y seguirá valiendo 3 después (los sitios B y C sustituyen dentro del `np.maximum` existente). El test no vigila nada; es del tipo que A92 llama "peor que no tenerlo" |
| m4 | §1.2, tabla de exposición, "le sube la magnitud" | unidireccional. La media de los vecinos puede ser MÁS tibia que la mediana del anillo, y el propio D25 lo dice ("al revés, infla donde el anillo es más frío que el entorno del foco, glaciar de Tupungatito, A19"): la magnitud puede BAJAR y una pasada puede dejar de publicar. El criterio 1 del A/B lo cubre; la tabla de §1.2 no lo insinúa |
| m5 | §1.2, "noches nuevas que se estrenarían: 20" | es un techo igual que los 1035, por la misma razón (el script clasifica, no corre el pipeline, y despegar de cero no garantiza pasar el predicado del dashboard). El ⚠️ del plan se lo aplica sólo a los 1035 |
| m6 | plan, "Herramientas" | nombra `tests/arnes_sintetico_s142.py` y `scripts/banco_paridad.py`; el arnés no se usa en ninguna tarea (ver M2) |

---

## 5. Lo que está BIEN y podría parecer mal

Lo digo explícitamente porque la lista de arriba es larga y la mayor parte del plan resiste.

**Los números de §1.2 son exactos, los doce.** Contra el `sustrato.json` regenerado
(`generado_utc` 2026-09-20T04:07:33Z, ventana 2026-03-01 a 2026-09-20):

| plan | JSON |
|---|---|
| 9338 pasadas nocturnas | `n_pasadas_nocturnas: 9338` |
| sin cúmulo 5831 / fuera del inner 171 | `sin_cumulo: 5831`, `cumulo_fuera_del_inner: 171` |
| rescate 1035 | `rescate.n: 1035` |
| exposición 2301, publican 2299 | `expuesta.n: 2301`, `n_publica_hoy: 2299` |
| rescate con alerta 48 / negativo limpio 489 | `n_pos_mirova_alerto: 48`, `n_neg_limpio: 489` |
| noches sin cubrir 0 / estrenarían 20 | listas de largo 0 y 20 |
| exposición: no vio 1130, alertó 223 | `1130`, `223` |

Y el dato de §5 sobre MODIS ("11 pasadas de rescate con 0 alertas") también:
`MODIS.rescate = {n: 11, n_pos_mirova_alerto: 0}`.

**El control de identidad del predicado es el que el plan dice.** `sustrato.json` trae
`[[0,1,1,1,0],[1,0]]`, el mismo valor que `tests/test_evaluador_ab_s143.py` exige en
`test_identidad_del_predicado_node` (el assert está en la l. 602; el plan cita `:603`, un
desplazamiento sin consecuencia).

**El script mide lo que dice medir, en los tres puntos que me pediste mirar.**
- "Publica" es el predicado real del dashboard: `banco_paridad.correr_node` extrae con node
  `isSummitDetection`, `isValidDetection`, `isThermalArtifact` y `mirovaEqVrpDisplay` del
  `frontend/index.html` y publica = `summit && valid && !art && disp > 0`. No hay reconstrucción a
  mano (A97).
- El campo de magnitud es el correcto para este sensor: `pc_vrp = primary_cluster.vrp_mw`
  (`banco_paridad.py:255`). El matiz de A46/S132 (que en VIIRS 375 el dashboard publica
  `f5_core_vrp_mw` y no `pc.vrp_mw`) **no aplica a V750**, que es el bucket del que habla §1.2.
- La cuenta en noches hace lo que promete: `noches_publicadas` se arma con TODAS las pasadas
  publicadas de TODOS los sensores, la clave es `(volcán, noche)` y no sólo la noche, y el conjunto
  se deduplica. Además ahora está cubierta por `tests/test_sustrato_s145.py`, que prueba justamente
  las dos trampas (noche ya cubierta por otra pasada; radio interno por volcán y no corte fijo).
- El denominador es el del bucket ("pasadas nocturnas" = records del bucket en ventana que
  `es_pasada_diurna_descartada` no descartó), y cada celda va con su denominador y su ventana, como
  pide A90.

**El código de la Tarea 1 corre.** No lo leí: lo ejecuté. Copié el envoltorio tal cual está escrito
en el plan, contra el helper real de `pipeline/vrp_regimes.py`, y corrí los dos tests del Paso 1:

```
T1 n_sin 0 l_bg [0.21101554] esp [0.21101554]
T2 n_sin 1 l_bg [0.1234]
OK ambos tests del plan (Tarea 1) PASAN con el envoltorio tal como esta escrito
```

La firma del helper coincide (`(bt_grid, alert_mask, hot_rows, hot_cols, wavelength_um, *,
max_half_px)` y devuelve `(l_bk, half_used)`), el desempaquetado `esperado, _` es correcto, y el
`np.broadcast_to` sobre un escalar funciona.

**El plan acierta en la trampa que sí avisó.** `M13_LAMBDA` está en
`pipeline/process_viirs_mod.py:165` y no en `pipeline/constants`: el comentario del test
("importarlo de constants da ImportError") es correcto y previene un error real.

**Las variables están en alcance en los tres sitios.** En el sitio A (l. 983): `bt`, `hot_rows` y
`hot_cols` vienen de `hot_rows, hot_cols = np.where(hot_mask_2d)` en la l. 964; `hot_mask_2d` ya no
se reasigna después de la 937. En los sitios B y C: `t1_rows`/`t1_cols` se definen justo arriba
(l. 1200 y 1215), `test1_hot_filtered` y `effective_L_bg` también. `redondear_diag` está importado
a nivel de módulo (l. 50). `L_bg_rad` sólo se usa en las l. 983 y 987, así que convertirlo de
escalar a arreglo no rompe nada aguas abajo (lo verifiqué con grep).

**Las citas de código, salvo las dos de m1 y m2, apuntan a lo que el plan dice.** Sitio A 983-987
(`L_bg_rad` en 983, `delta_L` en 987), sitio B 1198-1205 (`t1_delta_L` en 1204), sitio C 1214-1221
(`t1_delta_L` en 1219), `process_viirs.py:682` (el envoltorio de I-band), `:1459`, `:1921`, `:1952`
(las tres guardas de magnitud) y `:1386` (`hot_mask_2d = np.zeros_like`), `profile.py:497-498` (el
flag de I-band, y la 498 es donde manda insertar), `from pipeline.profile import (` en la l. 73,
`from .vrp_regimes import cluster_focal_vrp_mw` en la 147,
`tests/test_d25_fondo_vecinos_s142.py:223` y `tests/test_apagado_no_cambia_nada_s142.py:133`.

**La fila 2 de §1.5 es correcta: `test_modis_y_viirs750_no_cambian_con_los_dos_flags_on` NO se rompe.**
Ese test corre con el perfil `_s142_verif_flags_nuevos`, y
`test_el_perfil_de_verificacion_solo_enciende_los_dos_flags_nuevos` custodia que ese perfil sólo
encienda los dos de I-band y no toque ningún otro flag. Un flag nuevo con default `False` no entra.

**Busqué el tercer test roto en el lugar más probable y ahí no está.** Ni
`test_flags_d22_d25_perfil_s142.py` (comprueba sólo las claves de 375 y que `vrp_bg_neighbor_max_half_px`
esté en `thresholds:`) ni `test_gr2_profile_invariants.py` (lista blanca parametrizada de flags
pineados) se rompen con una clave nueva en `paths:`. El tercero apareció en otro lado (G3).

**El barrido de A92 de la Tarea 5 Paso 4 es ejecutable y su expectativa es correcta**:
`experiments/_s133/auditar_guards_por_subcadena.py` existe y hoy da "asserts por subcadena
revisados: 19 / candidatos a falso verde: 0".

**No hay linter en CI** (no hay `.flake8`, `setup.cfg`, `ruff.toml` ni `pyproject.toml`, y ningún
workflow menciona flake8/ruff/pylint), así que las líneas de ~105 caracteres de los sitios B y C no
son un problema, igual que no lo son hoy en `process_viirs.py:1925`.

**El veredicto de §1.2 y §6 es el que los datos soportan, y hay una medición previa independiente
que concuerda.** "Cero noches de alerta hoy sin cubrir" sale de la lista vacía del JSON, y la cuenta
es además conservadora en la dirección correcta: no todo rescate publicaría (haría falta pasar
`summit && valid && !artifact`), así que el cero es un techo del premio y el premio real sólo puede
ser cero. Y el propio D25 ya traía, de otra sesión y otra ventana, el mismo resultado por otra vía:
"VIIRS750 33 de 246 noches ALERTA de MIROVA con el cráter en cero... **en noches de volcán, 0 de
33**: todas cubiertas por otra pasada (verificador S138 §3.d)". Dos mediciones distintas, mismo
signo. El plan no dice de más: dice que no agrega recall en noches, que el efecto dominante es
sobre-publicación, y que los 1035 son techo y no predicción.

---

## 6. Veredicto

**El plan NO es ejecutable tal como está.** No por su razonamiento, que resiste: el sustrato está
bien medido, el veredicto es el que los datos soportan y está corroborado por una medición
independiente previa, el gate de misión es defendible, y la mitad del andamiaje (envoltorio, flag,
sitios A/B/C) está correctamente ubicada y corre. El problema es de instrucciones.

Tres cosas hay que arreglar antes de entregárselo a un ejecutor:

1. **La Tarea 4 entera** (G1): decidir y escribir el refactor del `return {` a `record = {` + `return record`,
   con su propio paso, su propia verificación A49 y la nota de que `test_viirs_diag_schema` lo
   tolera. O cambiar el diseño del diagnóstico para que no necesite variable.
2. **El conteo de guardas de la Tarea 3** (G2): tres o cuatro, pero coherente con lo que la Tarea 4
   agrega, y con un mensaje de fallo que no mienta sobre qué falta.
3. **Declarar el contrato G8 y CLAUDE.md como parte del cambio** (G3): son dos tests que el plan
   rompe, hay un script para remapear (`scripts/remapear_citas.py`, A101) y hoy no aparecen ni en
   §1.5 ni en §2.2 ni en la Tarea 6.

Y dos que conviene arreglar aunque no bloqueen: recontar la línea base (M1, ya está desfasada) y
agregar un test que ejerza el flag encendido de punta a punta (M2), porque hoy seis de los diez
controles son búsquedas de texto y ninguno mira una salida.

Con esos cinco cambios el plan queda ejecutable. No encontré nada que indique que el cambio en sí
sea peligroso para el NRT: el flag queda apagado, los tres sitios son posteriores a que la máscara
de detección quede fijada, y con el flag OFF el record no cambia en ninguna clave.
