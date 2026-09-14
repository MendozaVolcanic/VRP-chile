# S139 tanda 2: por qué el NRT corre 5 veces al día y cómo mejorarlo

**Fecha del servidor (A86)**: `gh api -i repos/MendozaVolcanic/VRP-chile` devolvió
`Date: Mon, 14 Sep 2026 11:51:09 GMT`. Todas las ventanas de abajo terminan el 2026-09-13
inclusive, porque el 14 está en curso.

**Alcance**: auditoría de sólo lectura. No se modificó ningún archivo del repositorio fuera
de este informe y de los scripts en `experiments/_s139_audit/nrt/`. No se disparó ningún
workflow.

**Scripts de medición** (todos con las dos preguntas del instrumento en su encabezado):

| script | qué mide |
|---|---|
| `experiments/_s139_audit/nrt/analiza_cadencia.py` | corridas por schedule al día contra el cron declarado |
| `experiments/_s139_audit/nrt/analiza_franjas.py` | franja horaria, minuto de creación, techo global del repo, espaciado |
| `experiments/_s139_audit/nrt/analiza_intervalos.py` | intervalo entre corridas consecutivas del mismo workflow |
| `experiments/_s139_audit/nrt/analiza_solape.py` | si la franja que falta coincide con una corrida anterior viva |
| `experiments/_s139_audit/nrt/analiza_retraso.py` | retraso real de cada corrida respecto de su franja |
| `experiments/_s139_audit/nrt/analiza_rafagas.py` | si los workflows llegan agrupados en pasadas |
| `experiments/_s139_audit/nrt/analiza_cobertura.py` | pasadas de satélite por día y por volcán, agujeros |
| `experiments/_s139_audit/nrt/analiza_latencia.py` | latencia pasada a publicación, por sensor y por hora |

---

## 1. Causa raíz de la cadencia

### El fenómeno, primero

Un cron de GitHub no es un reloj propio: es un pedido que se le hace a un despachador
externo. Nosotros declaramos doce franjas al día y el despachador decide cuándo las
atiende. Lo que pasó el 2026-08-27 no es que se perdieran eventos al azar: es que el
despachador de este repositorio empezó a atender los pedidos con **unas tres horas y media
de atraso**, y como sólo mantiene un pedido pendiente por workflow, las franjas que vencen
mientras uno espera se funden en una sola. Un cron de dos horas atendido con tres horas y
media de cola no puede entregar doce corridas: entrega una cada cuatro o cinco horas.

Esto se ve **sólo** si mides un cron cuyo período sea más largo que el atraso. Los cuatro
workflows que miró S133 son de una o dos horas: en todos ellos el atraso queda plegado
dentro del período y se lee como "faltan corridas". El `nrt-healthcheck`, que corre una vez
al día, es el único instrumento del repo capaz de medir un atraso de horas, y nadie lo
había mirado.

### La medición

`analiza_retraso.py`, ventana 2026-08-01 a 2026-09-13, denominador = corridas por evento
`schedule` de cada tramo:

```
workflow             tramo     n    p05  mediana     p95     max   (retraso en min)
nrt-healthcheck      ANTES    26     16       26     100     132
nrt-healthcheck      DESDE    18    129      209     564     574
```

Corroboración independiente, `audit-weekly` (cron `0 9 * * 1`, una vez por semana), leído
directo de `experiments/_s139_audit/nrt/runs_audit-weekly.json`:

| lunes | hora de creación | atraso |
|---|---|---|
| 2026-08-24 | 09:49 | +49 min |
| 2026-08-31 | 16:49 | +7 h 49 |
| 2026-09-07 | 14:52 | +5 h 52 |

Dos workflows independientes, de período distinto, dan el mismo salto en la misma fecha.

### Las hipótesis que se cayeron con datos

**No es caída aleatoria por evento.** Si GitHub descartara cada evento con probabilidad
0,6, el `nrt-healthcheck` mostraría unos 7 de 17 días. Muestra 17 de 17
(`analiza_cadencia.py`: `nrt-healthcheck ANTES 100.0% / DESDE 100.0%`, n=90/17 días). La
probabilidad de ese resultado bajo caída aleatoria es 0,4^17, del orden de 1e-7.

**No es proporcional a lo que declaras: declarar más no trae más.** `analiza_cadencia.py`,
ventana 2026-08-27 a 2026-09-13, 18 días:

| workflow | declara/día | entrega/día | % |
|---|---|---|---|
| nrt | 12 | 4,83 | 40,3 |
| sync-mirova-csv | **24** | 5,44 | 22,7 |
| pages-deploy | 12 | 4,94 | 41,2 |
| nrt-retry | 12 | 5,44 | 45,4 |
| reproc-watchdog | **24** | 6,31 | 26,3 |
| nrt-healthcheck | 1 | 1,00 | **100** |

Los que declaran 24 no reciben el doble que los que declaran 12: todos convergen a cinco o
seis. Esto es lo que mata la idea de "subamos el cron a cada hora para compensar".

**No es el solape ni el grupo de concurrencia `push-main`.** `analiza_solape.py`, tramo
DESDE, 216 franjas declaradas del NRT: de las 104 que faltan, **97 (93 %)** ocurren con el
workflow completamente ocioso, sin nada en cola ni en curso. Para `sync-mirova-csv`,
`pages-deploy`, `nrt-retry` y `reproc-watchdog` el número es 100 %. Y no hay corridas
canceladas: `analiza_cadencia.py` muestra 8 canceladas en las 400 corridas del NRT desde el
2026-07-29, todas del 2026-08-09 y 08-10, ninguna posterior al corte.

**No es que GitHub evalúe el repo por pasadas** (hipótesis mía, refutada por mi propia
medición). `analiza_rafagas.py`: si los seis workflows se despacharan juntos en cinco o
seis pasadas diarias, habría ráfagas con cuatro o más workflows distintos. Hay **cero**
ráfagas de ese tipo, y 23,3 momentos distintos de despacho por día en el tramo DESDE
(ventana 2026-09-01 a 2026-09-13, 394 corridas). Cada workflow tiene su propia cola, con su
propia fase.

### Lo que queda en pie

Un **atraso de despacho por workflow** que saltó de unos 26 minutos a unos 209 minutos
(mediana) el 2026-08-27, con **fusión de las franjas que vencen mientras hay un pedido
pendiente**. La fusión está respaldada por el piso de espaciado: `analiza_intervalos.py`,
tramo DESDE, `sync-mirova-csv` (nominal 60 min) tiene **mínimo 128 min y cero intervalos
x1**; `reproc-watchdog` (nominal 60 min) mínimo 101 min y cero x1. Ningún cron horario
logra dos entregas seguidas separadas por una hora.

**Por qué GitHub empezó a atrasar este repo: no lo sé y no lo invento.** Lo que sí se
puede anotar como coincidencia temporal, no como causa: el 2026-08-26 y 27 el repo pasó de
0 a 7 corridas diarias de `Tests` a 25 y 34, y arrancó `Reproc por trozos`
(`experiments/_s139_audit/nrt/runs_repo_agosto.tsv`). Pero la correlación no se sostiene en
septiembre: el 2026-09-03 y el 2026-09-11 el repo tuvo 39 corridas totales, de las más
tranquilas, y el `nrt-healthcheck` igual salió a las 15:24 y 15:26 (+3 h 24). El atraso es
persistente, no sigue la carga del día.

### Hallazgos formales de esta sección

---

**H1. El token de Earthdata vence en unos 19 días y nada avisa**

- **ARCHIVO:LÍNEA** `gh api repos/MendozaVolcanic/VRP-chile/actions/secrets` devuelve
  `EARTHDATA_TOKEN  updated_at 2026-08-04T07:19:42Z`. Los tokens de Earthdata duran 60
  días, así que el vencimiento cae alrededor del 2026-10-03. Hoy es 2026-09-14.
  `.github/workflows/nrt-healthcheck.yml` no contiene ninguna verificación de vencimiento
  (`grep -n "expir\|caduc\|token"` sobre ese archivo no devuelve nada).
- **QUÉ PASA** El pipeline no consulta a NASA con usuario y clave sino con un token que
  caduca. Cuando caduca, la descarga del L1B falla y no entra ni un granule. Ya pasó: los
  comentarios de `.github/workflows/nrt.yml` documentan 13 días sin datos entre el 23-jul y
  el 04-ago y 107 corridas rojas. En los datos de esta sesión eso se ve como 54 corridas
  fallidas del NRT concentradas entre el 2026-07-29 y el 2026-08-04, y **ninguna falla
  desde entonces** (`analiza_cadencia.py`, conteo por fecha).
- **CÓMO SE VE EN EL DASHBOARD** El dashboard se congela. Al principio no se distingue de
  una noche sin anomalías: el operador ve el último dato y no tiene forma de saber que es
  viejo hasta que `nrt-healthcheck` abre issue a las 48 h.
- **CÓMO REPRODUCIRLO** `gh api repos/MendozaVolcanic/VRP-chile/actions/secrets -q '.secrets[] | [.name, .updated_at] | @tsv'`
- **CONFIANZA** CONFIRMADO la fecha del secreto y la ausencia de alerta. SOSPECHA la
  duración exacta de 60 días, que no verifiqué contra la documentación de Earthdata en esta
  sesión.
- **GRAVEDAD 5** Apaga el sistema entero por varios días, sobre los once volcanes a la vez.

---

**H2. La cadencia real del NRT es de 4,83 corridas al día desde el 2026-08-27**

- **SCRIPT:SALIDA** `experiments/_s139_audit/nrt/analiza_cadencia.py`, ventana 2026-08-27 a
  2026-09-13, denominador 18 días y 12 franjas declaradas por día:
  `nrt  ANTES 89.9% (28 días) / DESDE 40.3% (18 días)`. Serie diaria completa en la salida
  del script: 08-26=11, 08-27=2, 08-28=2, después estable entre 4 y 7.
- **QUÉ PASA** El despachador de cron de GitHub atiende los pedidos de este repo con una
  mediana de 209 minutos de atraso y funde las franjas que vencen mientras espera. No es
  configuración nuestra ni concurrencia nuestra (ver arriba las cuatro hipótesis
  descartadas).
- **CÓMO SE VE EN EL DASHBOARD** Invisible como falla y visible como demora: el operador ve
  todas las pasadas, más tarde. La latencia real de publicación medida sobre MODIS es de
  6,34 a 6,70 h medianas (`analiza_latencia.py`), contra las 3 a 4 h del régimen anterior
  que documenta `docs/s133/CADENCIA_DEL_CRON.md`.
- **CÓMO REPRODUCIRLO** `gh run list --workflow nrt.yml --limit 400 --json databaseId,createdAt,event,status,conclusion,startedAt,updatedAt`
  y correr los scripts de la tabla de arriba.
- **CONFIANZA** CONFIRMADO el fenómeno y la magnitud. SOSPECHA la razón del lado de GitHub.
- **GRAVEDAD 3** No pierde datos (ver H3), pero en una escalada de actividad seis horas de
  demora sobre una pasada nocturna es la diferencia entre avisar esta madrugada y avisar al
  mediodía.

---

**H3. No se perdió ni un dato: la ventana de siete días absorbe la caída de cadencia**

- **SCRIPT:SALIDA** `experiments/_s139_audit/nrt/analiza_cobertura.py`, 5222 records en la
  ventana 2026-08-01 a 2026-09-13. Pasadas distintas por día y por volcán, denominador 26
  días antes y 18 días después:

  | volcán | antes/día | desde/día | delta |
  |---|---|---|---|
  | Chaiten | 12,08 | 12,22 | +1,2 % |
  | Villarrica | 11,23 | 11,50 | +2,4 % |
  | Lascar | 9,65 | 9,50 | -1,6 % |
  | **TOTAL 11 Tier A** | **117,92** | **119,78** | **+1,6 %** |

  Días completamente vacíos: **0 antes y 0 después**, en los once volcanes.
- **QUÉ PASA** `scripts/run_pipeline.py:384` define `default_date_window(today,
  lookback_days=7)`: cada corrida procesa el día en curso más los siete anteriores, y no
  hay ningún salteo de fechas ya procesadas (no existe lógica de skip en el bucle de
  `main()`, líneas 466 a 471). Con cinco corridas al día, cada fecha se vuelve a barrer unas
  35 veces antes de salir de la ventana. Esa redundancia es la que hace que perder siete de
  cada doce franjas no cueste un solo record.
- **CÓMO SE VE EN EL DASHBOARD** Nada, y ese es el punto: la completitud está sana.
- **CÓMO REPRODUCIRLO** `PYTHONIOENCODING=utf-8 python experiments/_s139_audit/nrt/analiza_cobertura.py`
- **CONFIANZA** CONFIRMADO.
- **GRAVEDAD 1** Es una verificación en verde, no un defecto. Se anota porque fija la
  prioridad: el problema es de latencia, no de cobertura.

---

## 2. Riesgos del NRT verificados hoy

**H4. El cortacircuitos de host caído (A64) deja la corrida en verde sin haber descargado**

- **ARCHIVO:LÍNEA** `pipeline/fetch.py:657-661` levanta
  `RuntimeError(f"download host(s) down this run: {sorted(hosts)}")`, y
  `pipeline/fetch.py:824-826` lo atrapa con
  `except Exception as e: print(f"  WARN: Failed to fetch {platform}: {e}")` y deja
  `results[platform] = []`. Sólo `EarthdataCredentialError` se vuelve a levantar
  (líneas 816 a 823, blindaje S123).
- **QUÉ PASA** Cuando el host de LANCE deja de aceptar conexiones, el cortacircuitos hace
  lo correcto, que es no colgarse 50 minutos reintentando. Pero el aviso muere en un WARN
  del log: esa plataforma devuelve cero granules y la corrida sigue y cierra en verde. Es
  una pérdida parcial y silenciosa, un volcán y un sensor a la vez.
- **CÓMO SE VE EN EL DASHBOARD** Invisible. El volcán queda sin sus pasadas de VIIRS de ese
  día y el dashboard muestra un hueco que se lee igual que una noche nublada. El aviso de
  frescura de `nrt.yml` (A57) recién mira a las 72 h, y desde S123 sólo avisa, no falla; el
  `nrt-healthcheck` mira a las 48 h. Un hueco de un sensor en un volcán no llega a ninguno
  de los dos umbrales.
- **ATENUANTE medido** La ventana de siete días (H3) recupera el hueco en la corrida
  siguiente si el host vuelve. Se vuelve permanente sólo si el host está caído más de siete
  días para esa plataforma.
- **CÓMO REPRODUCIRLO** Lectura de código. Para verlo en vivo hay que buscar
  `DOWNLOAD_CONNFAIL` o `DOWNLOAD_SKIP` en el log de una corrida y confirmar que el job
  igual cerró en verde.
- **CONFIANZA** CONFIRMADO el camino de código. SOSPECHA la frecuencia real con que ocurre
  hoy: no conté ocurrencias de `DOWNLOAD_CONNFAIL` sobre el historial de logs.
- **GRAVEDAD 3** Una anomalía térmica real puede quedar sin ver durante horas o días, sin
  ninguna señal.

---

**H5. El perfil `experimental` corre en cada corrida del NRT y su resultado se tira a la basura**

- **ARCHIVO:LÍNEA** `pipeline/profiles/experimental.yaml:50` dice
  `data_subdir: experimental_v2`, puesto por el commit `772f000c4` del 2026-08-25 12:18
  (`fix(s124): aislar la base de datos de cada perfil`). El paso de commit de
  `.github/workflows/nrt.yml:330` sigue haciendo
  `git add "data/experimental/${{ matrix.volcano }}.json"`, que es el directorio viejo.
  `git ls-files data/experimental_v2` devuelve vacío: ese directorio no está versionado.
- **QUÉ PASA** Cada job del NRT procesa cada volcán dos veces: una con
  `mirova_equivalent` y otra con `experimental`. En el log del run 34802878455, Lascar
  arranca el perfil operacional a las 03:32:21 y el experimental a las 03:45:05, sobre un
  job de 29,9 minutos. Ese segundo pase escribe en `data/experimental_v2/`, que el paso de
  commit no agrega, así que se borra junto con el runner. Los archivos de
  `data/experimental/` de los once Tier A están congelados exactamente en la pasada
  `2026-08-25 06:12`, que es el día del cambio.
- **CÓMO SE VE EN EL DASHBOARD** Invisible de forma directa: el dashboard vive de
  `data/mirova_equivalent/`. Indirecta y sí relevante: ese pase duplica la duración de cada
  corrida, y la duración es la mitad del retraso que sí ve el operador.
- **CÓMO REPRODUCIRLO**
  `gh run view 34802878455 --log | grep "process (Lascar)" | grep "VRP profile="`
  muestra las dos cabeceras con sus horas. Y
  `python -c "import json;d=json.load(open('data/experimental/Villarrica.json'));print(d['records'][-1]['datetime_utc'])"`
  devuelve `2026-08-25 06:12`.
- **CONFIANZA** CONFIRMADO.
- **GRAVEDAD 2** No tuerce ninguna alerta por sí solo, pero es la palanca más grande y más
  barata sobre la latencia, que sí la tuerce.

---

**H6. El detector de granules NRT de MODIS sigue roto y el arreglo existe sin llamador**

- **ARCHIVO:LÍNEA** `pipeline/fetch.py:367` define `product_version_from_granule`, que S133
  escribió documentando esta misma asimetría: VIIRS marca `_NRT` y MODIS marca `.NRT.`.
  Esa función **no tiene ningún llamador en producción**:
  `grep -rn "product_version_from_granule" --include=*.py .` devuelve sólo su definición y
  `tests/test_nrt_short_names_modis_s133.py:132`. Los tres productores siguen con el
  chequeo viejo en línea: `pipeline/process_modis.py:1546`, `pipeline/process_viirs.py:2100`
  y `pipeline/process_viirs_mod.py:1391`, todos `"nrt" if "_NRT" in name else "standard"`.
- **QUÉ PASA** Un granule de LANCE de MODIS se llama
  `MYD021KM.A2026256.0840.061.2026256102620.NRT.hdf`, con punto y no con guion bajo. El
  chequeo no lo reconoce y lo guarda como `standard`. `pipeline/store.py:612` sólo
  reemplaza un record por su versión definitiva cuando el guardado dice `nrt` y el nuevo
  dice `standard`: con la etiqueta falsa esa condición nunca se cumple y el record se queda
  con la calibración provisional para siempre.
- **MEDIDA** Sobre la ventana 2026-08-01 a 2026-09-13, cruzando nombre de granule contra
  etiqueta en los 45 archivos de `data/mirova_equivalent/`: **235 records tienen `.NRT.` en
  el nombre y dicen `standard`**, todos MODIS (130 Aqua y 105 Terra), contra 4923 sanos y
  64 correctamente marcados `nrt` (que son los de VIIRS).
- **CÓMO SE VE EN EL DASHBOARD** Invisible. La diferencia de temperatura de brillo entre
  NRT y Standard es menor a 0,1 K según la documentación del proyecto, o sea despreciable
  para el VRP. El daño es de trazabilidad: la ficha del SDA no puede decir con qué producto
  se calculó cada magnitud.
- **CÓMO REPRODUCIRLO**
  ```
  python -c "import json;from collections import Counter;from pathlib import Path;c=Counter();[c.update([(r.get('product_version'),'.NRT.' in (r.get('granule') or ''))]) for f in Path('data/mirova_equivalent').glob('*.json') for r in json.loads(f.read_text(encoding='utf-8'))['records'] if '2026-08-01'<=r.get('datetime_utc','')[:10]<'2026-09-14'];print(c)"
  ```
- **CONFIANZA** CONFIRMADO.
- **GRAVEDAD 2** No mueve una magnitud lo suficiente para torcer una alerta, pero rompe la
  procedencia del dato en un sistema que está obligado a poder explicarla.

---

**H7. `nrt-retry` gasta seis franjas al día y no reintenta nunca**

- **ARCHIVO:LÍNEA** `.github/workflows/nrt-retry.yml:60-64`: sólo reintenta si
  `LAST_STATUS = completed` y `LAST_CONCLUSION = failure`.
- **QUÉ PASA** Desde S123 el aviso de frescura ya no hace fallar la corrida, y el
  cortacircuitos de H4 convierte los problemas de descarga en WARN. El resultado es que el
  NRT casi no vuelve a cerrar en rojo: cero corridas fallidas desde el 2026-08-05, contra
  54 en los siete días anteriores. Un reintento que sólo se activa con el rojo quedó sin
  disparador.
- **EVIDENCIA** De las 400 corridas del NRT desde el 2026-07-29, 398 son `schedule` y 2 son
  `workflow_dispatch`, ambas del 2026-09-04 (17:03 y 18:26), que corresponden a pruebas
  manuales. Ninguna corrida del NRT fue lanzada por `nrt-retry` en la ventana.
- **CÓMO SE VE EN EL DASHBOARD** Invisible. Es una red de seguridad que ya no está tendida.
- **CÓMO REPRODUCIRLO**
  `python -c "import json;d=json.load(open('experiments/_s139_audit/nrt/runs_nrt.json'));print([ (r['createdAt'],r['event']) for r in d if r['event']!='schedule'])"`
- **CONFIANZA** CONFIRMADO que no se disparó en la ventana. SOSPECHA que el diseño esté
  mal: puede ser simplemente que NASA no se cayó en 40 días.
- **GRAVEDAD 2** Cuando NASA vuelva a caerse, la recuperación dentro del mismo ciclo
  depende de una condición que el resto del sistema ya casi no produce.

---

**H8. `max-parallel: 8` con once volcanes deja tres empezando media hora tarde**

- **ARCHIVO:LÍNEA** `.github/workflows/nrt.yml`, `max-parallel: 8` en la estrategia de la
  matriz, con once entradas.
- **MEDIDA** Run 34802878455 (creado 2026-09-14T03:31): ocho jobs arrancan a las 03:31 y
  los otros tres a las 03:57, 04:01 y 04:06. Duraciones de 26,6 a 44,8 minutos. La corrida
  completa toma unos 80 a 100 minutos de reloj, que es lo que da la mediana de 81 minutos
  de `createdAt` a `updatedAt` medida en `analiza_solape.py` para el tramo DESDE.
- **CÓMO SE VE EN EL DASHBOARD** Los últimos tres volcanes del lote se publican entre media
  hora y una hora después que los primeros, sin ninguna razón física.
- **CÓMO REPRODUCIRLO**
  `gh run view 34802878455 --json jobs -q '.jobs[] | [.name, .startedAt, .completedAt] | @tsv'`
- **CONFIANZA** CONFIRMADO.
- **GRAVEDAD 1** Suma latencia, no pierde nada.

---

## 3. Una trampa del instrumento que conviene no repetir

La latencia medida sobre VIIRS da 21 a 22 h medianas contra 6,3 a 6,7 h de MODIS
(`analiza_latencia.py`, 1315 records con `processed_utc`, ventana 2026-09-02 a 2026-09-13).
**Ese número no es la latencia que ve el operador.** `pipeline/store.py:491` reescribe
`processed_utc` cada vez que el record se vuelve a guardar, y el comentario del código lo
dice explícito. El auto-upgrade de NRT a Standard (`store.py:612`) reescribe el record
cuando aparece el producto definitivo, un día después, y con él la marca de tiempo.

El control que lo demuestra es H6: en MODIS el upgrade **nunca** se dispara, porque la
etiqueta está rota, así que su `processed_utc` sí es el de la primera publicación. VIIRS,
donde el upgrade sí funciona, muestra la marca del reemplazo. La diferencia de 3,5 veces
entre los dos sensores es exactamente ese artefacto.

**Conclusión operativa**: la latencia real de primera publicación es la de MODIS, unas
6,5 h, y el campo `processed_utc` no sirve para medir latencia mientras se reescriba en
cada pase. Además, `processed_utc` entró con el commit `d3b55ac4c` (S132, 2026-09-02), así
que **no existe comparación antes y después del 2026-08-27**: para ese tramo el dato es SIN
DATO, no cero.

---

## 4. Propuesta de mejora, priorizada

Ninguna se implementa acá. Las tres primeras son las que Nicolás debería decidir.

### M1. Sacar el perfil `experimental` del cron del NRT

- **Qué cambiar** En `.github/workflows/nrt.yml`, quitar el segundo paso de pipeline, el
  cuyo nombre termina en `experimental profile` del camino `schedule`, dejándolo accesible sólo
  por `workflow_dispatch`. Alternativa si la serie se quiere conservar: corregir
  `nrt.yml:330` para que agregue `data/experimental_v2/` y versionar ese directorio.
- **Por qué** Hoy ese pase consume alrededor de la mitad del reloj de cada job y su salida
  se borra con el runner desde el 2026-08-25 (H5). No es una optimización de costo: la
  duración del job es la mitad del retraso que el operador ve.
- **Efecto esperado** Job de unos 15 a 25 minutos en vez de 27 a 49.
- **Riesgo** Bajo. Ninguna vista del frontend lee `data/experimental`. Antes de tocar hay
  que preguntarle a Nicolás si la serie experimental le interesa, porque la decisión entre
  "sacarlo" y "arreglar la ruta" es suya, no técnica.
- **Cómo verificar** Correr una vez por dispatch con el cambio, comparar duración de job
  contra el run 34802878455, y confirmar con `analiza_cobertura.py` que las pasadas por día
  de los once Tier A no bajan.

### M2. Vigilar el vencimiento del token de Earthdata

- **Qué cambiar** Agregar al `nrt-healthcheck` diario, que ya corre y ya tiene permiso de
  issues, una comprobación de la antigüedad de `EARTHDATA_TOKEN` vía
  `gh api repos/{owner}/{repo}/actions/secrets/EARTHDATA_TOKEN`, con aviso a los 50 días y
  issue a los 55.
- **Por qué** El vencimiento es la única causa documentada de un apagón total del sistema, y
  el próximo cae alrededor del 2026-10-03 (H1). Es la única mejora de esta lista que evita
  una pérdida de datos, no una demora.
- **Riesgo** Ninguno: es un canal de aviso nuevo, no toca `pipeline/`.
- **Cómo verificar** Correr el healthcheck por dispatch y confirmar que imprime la
  antigüedad correcta contra la fecha que devuelve la API.
- **Nota**: rotar el token es acción de Nicolás. Yo no toco credenciales.

### M3. Convertir el WARN del cortacircuitos en una señal visible

- **Qué cambiar** En el paso de commit o en un paso nuevo de `nrt.yml`, contar las
  ocurrencias de `DOWNLOAD_CONNFAIL` y `DOWNLOAD_SKIP` en `pipeline.log` y emitir un
  `::warning::` con el volcán y la plataforma, más una línea en el resumen del job. No
  cambiar el código de salida: la corrida debe seguir en verde, porque el dato igual se
  recupera con la ventana de siete días.
- **Por qué** Hoy una plataforma entera puede quedar sin descargar y no lo sabe nadie (H4).
  Es exactamente el patrón A87: una métrica verde sobre un mecanismo degradado.
- **Riesgo** Bajo, es sólo lectura del log. Cuidado con el precedente de la issue #567: si
  esto abriera issues por corrida sería ruido; debe ser anotación en el run y agregado
  diario en el healthcheck.
- **Cómo verificar** Buscar en el historial de logs una corrida que ya tenga
  `DOWNLOAD_CONNFAIL` y confirmar que el nuevo paso la habría marcado.

### Lo que NO hay que hacer

- **Subir el cron a cada hora.** Medido y refutado: `sync-mirova-csv` declara 24 franjas al
  día y recibe 5,44; `nrt` declara 12 y recibe 4,83. Declarar más no trae más.
- **Sacar el NRT del grupo `push-main`.** El 93 % de las franjas que faltan ocurren con el
  workflow ocioso y no hay corridas canceladas desde el 2026-08-10 (H2). La concurrencia no
  es la causa, y salir del grupo reabre la carrera de `cannot lock ref` que ese grupo vino a
  cerrar.
- **Recortar la ventana de siete días.** Es la única razón por la que perder siete de cada
  doce franjas no costó ni un record (H3). Tocarla sin antes arreglar la cadencia cambia un
  problema de latencia por uno de cobertura.

### Ideas que quedan sin medir

- Alinear el cron a la ventana que importa. Las pasadas útiles se concentran en 04, 05 y 06
  UTC (171, 458 y 406 records de 1315 en `analiza_latencia.py`), que es la madrugada
  chilena. Con cinco entregas diarias que llegan cuando llegan, no controlamos la fase. Si
  el atraso de despacho se mantuviera estable en unas 3,5 h se podría declarar el cron a las
  horas que, atrasadas, caen justo después de la ventana nocturna. **SOSPECHA**: no medí si
  el atraso es estable por franja ni si esa estabilidad se sostiene en el tiempo. Sin eso,
  es adivinar.
- Subir `max-parallel` de 8 a 11 (H8). Gana media hora en tres volcanes, pero aumenta la
  contención de push. Sólo tiene sentido después de M1, cuando los jobs sean cortos.

---

## VERIFICADO LIMPIO

Lo que miré en esta sesión y está sano, con el comando que lo confirma:

| qué | resultado | comando |
|---|---|---|
| Cobertura de pasadas por volcán | +1,6 % después del corte, cero días vacíos en los 11 Tier A | `python experiments/_s139_audit/nrt/analiza_cobertura.py` |
| Fallas del NRT | cero desde el 2026-08-05; las 54 fallas son del apagón de token de julio | `python experiments/_s139_audit/nrt/analiza_cadencia.py` |
| Corridas canceladas por concurrencia | 8 en 400, todas del 2026-08-09 y 08-10, ninguna posterior | mismo script, sección `conclusiones` |
| Reintento de push del NRT | bucle de 5 intentos con backoff y `rebase --abort` entre intentos, presente | `.github/workflows/nrt.yml`, paso `Commit updated data files` |
| `git add` por archivo | un `add` por archivo, no multi-pathspec, como pide la lección S120 | mismo paso, tres líneas `git add` separadas |
| `timeout-minutes` | 80 a nivel job y 50 por paso de pipeline; peor job observado 48,9 min | `.github/workflows/nrt.yml` y `gh run view 34785837550 --json jobs` |
| Publicación del dashboard | no depende del cron: `pages-deploy` se dispara por `workflow_run` al terminar el NRT (192 de 400 corridas) | `.github/workflows/pages-deploy.yml:30-32` y `runs_pages-deploy.json` |
| Blindaje de credencial muerta | `EarthdataCredentialError` se vuelve a levantar y no se degrada a WARN | `pipeline/fetch.py:816-823` |
| Grupo `push-main` | compartido por `nrt`, `sync-mirova-csv`, `backfill-geometry`, `backfill-tier-a` y `reproc-s120-eq16-villarrica`, con `cancel-in-progress: false` | `grep -rn "group:" .github/workflows/*.yml` |
| Cambios de workflow alrededor del corte | ninguno toca `nrt.yml` entre el 2026-08-20 y el 2026-08-29; el primero es del 2026-09-04 | `git log --since=2026-08-15 --oneline -- .github/workflows/` |
| Instrumento de cadencia de S133 | `scripts/medir_cadencia_cron.py` existe y está enchufado al healthcheck | `.github/workflows/nrt-healthcheck.yml` |

Y una anotación de honestidad: mi propia hipótesis de que GitHub despachaba el repo por
pasadas quedó **refutada** por `analiza_rafagas.py`, que es un script que escribí para
confirmarla. Se deja escrito porque el resultado negativo es parte de la evidencia: cero
ráfagas con cuatro o más workflows distintos, sobre 303 ráfagas en 13 días.
