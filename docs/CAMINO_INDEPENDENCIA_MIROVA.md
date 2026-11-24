# Camino hacia la independencia de mirovaweb.it (borrador)

> **Estado: BORRADOR de S194 (2026-11-22), para que Nicolás lo lea y corrija.** Documento de planificación: no
> cambia código ni datos. Método «ingeniería inversa» del plan `tasks/PLAN_S194_PROMPTS.md` §1: se parte de la meta y
> se pregunta qué tiene que ser cierto justo antes, hasta llegar a lo que existe hoy. Se revisa en cada auditoría
> integral (A51).
>
>
> **S196 (2026-11-23): paso 2 del §5 hecho y traído a main.** E2a (latencia) se repitió con `first_processed_utc`
> (`experiments/_s196_latencia/`) y E3 suma a la comparación diaria la franja diurna de MODIS, separada de la nocturna
> (`experiments/_s196_e3/IDENTIDAD.md`). Las secciones E2a, E3, las debilidades 4 y 5 y el §5 dicen lo medido; el texto
> anterior queda marcado donde cambió.
>
> Todas las rutas de este documento cuelgan de la raíz del repo,
> `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\`, salvo las que se dan completas.
> Los números vienen de scripts o documentos citados; lo que no tiene respaldo va marcado SOSPECHA o SIN MEDIR (A111).

## 0. Por qué hace falta este camino

El objetivo de independencia está escrito desde el principio (`Volcanologia\CLAUDE.md`: «Objetivo: independencia de
mirovaweb.it»), pero 193 sesiones trabajaron casi sólo en un eslabón: que el detector haga lo mismo que MIROVA. Ese
eslabón está muy avanzado (sección 2, E3). Lo que no existe es la cadena completa: qué más tiene que pasar para que
un operador de turno del OVDAS, frente a una anomalía térmica en un volcán, abra VRP Chile y no mirovaweb.it ni el
CSV del scraper Mirova-v1. Sin esa cadena, el proyecto puede quedar con un detector excelente que nadie usa
(`memory\project_sin_consumidores_operacionales.md`, 2026-11-03: «nadie consume el producto»).

## 1. La meta, en términos que se puedan comprobar

**Meta:** el OVDAS usa VRP Chile como su fuente térmica satelital en lugar de mirovaweb.it y del scraper Mirova-v1.

Está cumplida cuando las tres cosas siguientes son ciertas a la vez:

1. El procedimiento de turno del OVDAS (o el documento que haga sus veces) nombra a VRP Chile como la fuente térmica
   satelital; el scraper Mirova-v1 queda como verificación cruzada o se apaga.
2. Durante un período fijado de antemano, los operadores consultaron VRP Chile y no MIROVA para el dato térmico
   (registro de turno o bitácora).
3. SERNAGEOMIN reconoce el sistema como suyo: ficha SDA publicada sin campos `<completar>`.

Quién declara cumplida la meta: la jefatura del OVDAS, no este repo. SOSPECHA: el documento no sabe quién es esa
persona ni si Nicolás tiene la autoridad para decidir solo (ver debilidad 1).

## 2. La cadena hacia atrás

Cada eslabón dice qué tiene que ser cierto, qué pide, quién lo destraba, cómo se sabe que está cumplido y qué hay hoy.
Se lee de arriba (lo más cercano a la meta) hacia abajo (lo que ya existe).

### E1. Un operador confía en el tablero porque lo usó en paralelo y no lo pilló en falta

**Qué tiene que ser cierto.** Antes de soltar MIROVA, un operador tiene que haber mirado las dos fuentes lado a lado
durante semanas y haber visto que cada vez que MIROVA mostraba calor en un volcán, VRP Chile también, con una magnitud
parecida y en el mismo lugar. La confianza no sale de una métrica agregada: sale de no encontrar el caso que falta.

- **Pide:** una marcha blanca con fecha de inicio y fin, una planilla de discrepancias (fecha, volcán, qué vio cada
  fuente, quién tenía razón) y una regla escrita de qué cuenta como falla.
- **Destraba:** Nicolás y la jefatura del OVDAS (fecha, duración, quién registra).
- **Cumplido cuando:** la marcha blanca terminó con 0 alertas protegidas (1 MW o más, lectura A de
  `docs/MISSION.md`) que MIROVA mostró y VRP Chile no, sin explicación escrita.
- **Hoy:** no existe. Nadie consume el producto (memoria citada en §0). Lo más cercano es
  `docs/PLANTILLA_EPISODIOS_OVDAS_S190.md`, pensada para el laboratorio y no para la marcha blanca; su llenado espera a
  Nicolás (decisión 4 del bloque `tasks/BLOQUE_ARRANQUE_S194.md` §b).
- **Brecha:** total, pero barata: la marcha blanca puede empezar con lo que ya está publicado.

### E2. El tablero responde las preguntas del turno tan rápido como MIROVA

**Qué tiene que ser cierto.** El operador llega con tres preguntas: ¿pasó algo recién en la red?, ¿en qué volcán y con
qué sensor?, ¿dónde está el calor? Si VRP Chile las contesta más lento o con más ruido que MIROVA, el operador vuelve a
MIROVA aunque los números sean iguales.

Tres partes:

**E2a. Latencia.** El dato tiene que aparecer en VRP Chile no mucho después que en MIROVA.
- **Hoy (S196, medido):** `experiments/_s196_latencia/README.md` (script `latencia.py`, salida `resumen.json` y
  `pasadas.csv`), 11 Tier A, pasadas nocturnas del 2026-11-09 al 2026-11-22 y MODIS diurno desde #1090. Del paso del
  satélite al tablero (término del despliegue de Pages), mediana:

  | Sensor y franja | Pasadas | VRP Chile al tablero | Pareadas | VRP Chile (pareadas) | MIROVA por el scraper | Mediana de VRP menos MIROVA | VRP primero |
  |---|---|---|---|---|---|---|---|
  | MODIS noche | 334 | 2,31 h | 325 | 2,31 h | 2,36 h | -0,05 h | 170 de 325 |
  | VIIRS 375 noche | 432 | 2,86 h | 376 | 2,83 h | 2,79 h | 0,00 h | 183 de 376 |
  | VIIRS 750 noche | 445 | 2,84 h | 386 | 2,80 h | 2,80 h | 0,00 h | 200 de 386 |
  | MODIS día (un solo día) | 21 | 2,23 h | 21 | 2,23 h | 1,69 h | 0,70 h | 8 de 21 |

  Para el turno: de noche la alerta aparece en VRP Chile unas 2,3 h después del paso de MODIS y 2,8 h después del de
  VIIRS, lo mismo que llega MIROVA por el scraper, y VRP Chile llega primero en cerca de la mitad de las pasadas. Casi todo
  es espera de NASA (el gránulo NRT sale 1,8 h y 2,3 h después del paso); lo nuestro, del gránulo al tablero, es 0,62 h
  en mediana por pasada. El navegador puede ver el dato hasta 10 min más tarde por la caché de Pages (`max-age=600`), no
  sumado. La hora de MIROVA es la del scraper: es como el OVDAS ve hoy a MIROVA, y cota superior de mirovaweb.it (SIN
  MEDIR cuánto antes publica la página misma). De día, MODIS llega más tarde que MIROVA, pero con 21 pasadas de un día:
  SIN CONCLUIR. Por la letra del criterio de abajo, de noche se cumple en MODIS y VIIRS 750 y no en VIIRS 375 por 0,04 h
  (unos 2 min; la mediana de la diferencia por pasada es 0,00). Qué cambio cerró la brecha desde S150: SIN ATRIBUIR.
- **Antes (texto de S194, conservado):** medido en S150 (`experiments/_s150_latencia/README.md`, 1.660 pares nocturnos del 2026-09-14 al
  2026-10-02): VRP Chile mediana 5,05 h desde la adquisición, MIROVA 2,77 h; VRP Chile llega primero en 319 de 1.660.
  Esa medición es el «antes» del disparador externo del NRT; la medición «después» no la encontré (SIN MEDIR). Desde
  S150 cada record trae `first_processed_utc`, así que repetirla es barato. (⚠️ S196: ya medida, arriba.)
- **Destraba:** nadie (medir es trabajo del loop). Bajar la latencia puede pedir decisiones de infraestructura.
- **Cumplido cuando:** la mediana de VRP Chile no supera la de MIROVA en una ventana de al menos dos semanas, por
  sensor (umbral SOSPECHA: el OVDAS puede tolerar más; lo define E1).

**E2b. Vista que el operador de MIROVA reconozca.**
- **Hoy:** plan de tres fases escrito en S176 (`docs/superpowers/plans/2026-11-08-visualizador-como-mirova.md`, en
  `loop/activo`), «espera la decisión de Nicolás»: tabla de últimas pasadas de la red (como `latest.php`), tarjetas más
  cortas, agrupar por sensor y no por satélite, liga a MIROVA por volcán. PR #1015 abierto («Últimas 10 pasadas» como
  MIROVA). Lo que no se puede dar hoy es la imagen: el pipeline guarda los píxeles alertados, no la escena, y un GeoTIFF
  como el de MIROVA pide tocar `pipeline/` (hallazgo 6 del plan S176; A45).
- **Destraba:** Nicolás (qué fases, A45 para `frontend/` y para guardar la escena).
- **Cumplido cuando:** las tres preguntas del turno se contestan en VRP Chile sin abrir MIROVA (lo juzga el operador en
  la marcha blanca).

**E2c. Aviso automático.**
- **Qué tiene que ser cierto:** si un volcán cruza un umbral de noche, alguien del turno se entera sin estar mirando
  la página.
- **Hoy:** no existe aviso al operador. Los workflows que abren issues o mandan correo (`nrt-healthcheck.yml`,
  `nrt-monitor.yml`, vigilancias) avisan fallas de infraestructura o de la guardia, no anomalías térmicas. Si el
  scraper Mirova-v1 o MIROVA avisan algo hoy al OVDAS: SIN VERIFICAR; de eso depende si el aviso es requisito o mejora.
- **Destraba:** Nicolás (canal: correo, Telegram, issue; umbral; a quién). El canal puede pedir una credencial nueva,
  que va antes a `C:\Users\nmend\OneDrive\Escritorio\claude\REGISTRO_CREDENCIALES.md`.
- **Cumplido cuando:** un aviso de prueba llegó al canal acordado y una alerta real de la marcha blanca llegó a tiempo.

### E3. Hay paridad medida, publicada y sostenida en los volcanes que MIROVA vigila

**Qué tiene que ser cierto.** El operador no va a creer en un «igual a MIROVA» dicho; tiene que poder verlo, cada día,
por volcán y por sensor, y tiene que seguir siendo cierto después del cambio.

- **Hoy (el eslabón más avanzado):** la comparación diaria contra MIROVA se publica en `frontend/comparacion.html`,
  pestaña «Vía, K y MIROVA» (pública desde la ficha v1.28), y sale de `scripts/comparacion_via_k.py` a
  `data/audit_continuous/comparacion_via_k.json`. La corrida del 2026-11-22 03:19 UTC (en `origin/main`) da, con la
  tabla de MIROVA sola y sólo de noche:

  | Ventana | Sensor | Pasadas pareadas | Recall | Precisión | Protegidas | Protegidas perdidas | Mediana de la razón de VRP |
  |---|---|---|---|---|---|---|---|
  | historia (2026-03-01 a la adopción) | MODIS | 5.650 | 0,972 | 0,963 | 64 | 0 | 0,997 |
  | historia | VIIRS 375 | 11.136 | 0,981 | 0,916 | 122 | 0 | 1,000 |
  | historia | VIIRS 750 | 11.128 | 0,939 | 0,942 | 131 | 0 | 1,000 |
  | desde la adopción | MODIS (desde 2026-11-02) | 470 | 0,920 | 0,958 | 24 | **1** | 1,037 |
  | desde la adopción | VIIRS 375 (desde 2026-11-11) | 330 | 1,000 | 0,947 | 16 | 0 | 1,000 |
  | desde la adopción | VIIRS 750 (desde 2026-11-11) | 330 | 1,000 | 1,000 | 16 | 0 | 0,998 |

  Con tabla más OCR, la historia de VIIRS 375 tiene 18 protegidas perdidas de 176; la memoria S183
  (`memory\project_s183_comparacion_via_k.md`) explica 15 de ese tipo como alertas sólo OCR cuya clase vino de la
  imagen de otra pasada (Mirova-v1#20). La protegida MODIS perdida tras la adopción es Chaitén, MODIS Terra, noche
  del 2026-11-19, 1,07 MW en MIROVA (fila de `noches` del mismo JSON); es la pasada de las 02:30 que #1085 juzgó
  «alerta marginal de MIROVA no reproducible». Por la letra del criterio de victoria, una pérdida es una pérdida: el
  juicio la explica, no la borra.

  **S196: el foco del cráter de Láscar en MODIS entra a esta cuenta (MEJ-7, cerrada por paridad, D-E de Nicolás del
  2026-11-23).** Es parte de la precisión MODIS de la historia, no una mejora pendiente: la vía publica un píxel chico y
  caliente en el cráter de Láscar en noches en que MIROVA dejó su MODIS en RUTINA (el foco queda al borde del umbral y
  cruza unas noches sí y otras no, según el ángulo y cómo cae dentro del píxel de 1 km). Del 2026-03-01 al 2026-11-22
  la vía publica (predicado del tablero) 6 de las 5.758 pasadas MODIS nocturnas con record nuestro que la tabla lista
  como RUTINA: 4 de Láscar (0,21 a 1,43 MW, a 0,26 a 0,42 km del cráter), 1 de Nevados de Chillán y 1 de Llaima
  (`experiments/_s196_plan_mejoras/salida_m7_modis_sobre_rutina.txt`; fila MEJ-7 de
  `docs/BEYOND_MIROVA_EXTENSIONS.md` §12). Si hay que seguirlo, se sigue aquí, no en el laboratorio.

  **S196: noche y día separados.** Desde el 15-nov el día de MODIS se colaba en esa cuenta nocturna: una fila diurna de
  MIROVA con calor lejos del volcán anulaba las noches tranquilas de la misma fecha, y una pasada diurna nuestra entraba
  en la fila de la noche (`experiments/_s196_e3/IDENTIDAD.md`). La comparación ahora cuenta cada franja aparte. Prueba de
  identidad contra la versión de main con los mismos datos: todo lo anterior al 15-nov es idéntico (12 resultados y 2.400
  noches con `--hoy 2026-11-14`; las 6 ventanas de historia y las 2.400 noches previas con `--hoy 2026-11-23`). Lo único
  que cambia es MODIS desde la adopción: 8 noches tranquilas más se juzgan (negativos bien callados de 409 a 417 en la
  vía y de 404 a 412 en K); recall, precisión, protegidas y cociente no se mueven. La franja diurna, con la corrida del
  2026-11-23 (tabla de MIROVA, igual con OCR):

  | Franja | Sensor | Pasadas | Días-satélite juzgados | Recall | Precisión | Protegidas | Perdidas | Razón de VRP |
  |---|---|---|---|---|---|---|---|---|
  | día (2026-11-15 a 2026-11-23) | MODIS, sólo la vía (K no corre de día) | 157 | 147 | 1 de 1 | sin falsas alarmas en 146 tranquilos | 1 | 0 | 1,096 |

  La única alerta diurna de MIROVA es Nevados de Chillán, MODIS Aqua, 2026-11-22 20:40 (6,07 MW; la vía 6,65 MW en la
  cumbre). De 179 records diurnos, 22 son escenas que la vía no pudo medir (21 por reflejo solar) y quedan fuera. La
  pestaña pública lo muestra en «☀ MODIS de día» de `frontend/comparacion.html`.
- **Lo que falta:**
  1. **Un criterio de adopción operacional escrito.** `docs/MISSION.md` fija el criterio de victoria de la réplica
     (ninguna protegida perdida; medir en las dos direcciones), pero nadie escribió cuánto tiempo seguido tiene que
     cumplirse, en qué ventana, ni qué hacer con una pérdida «juzgada no reproducible». Sin eso, «hay paridad» no tiene
     fecha.
  2. **El día.** El criterio vigente es sólo nocturno (#1082). MIROVA sí publica alertas diurnas: el issue #813 cuenta
     94 pasadas diurnas con alerta protegida contra 346 nocturnas (40 contra 232 tras A119). La producción procesa MODIS
     de día recién con #1090 (abierto); VIIRS sigue de noche (decisión 2 del bloque S194). ⚠️ S196: #1090 está mergeado
     (2026-11-22, ficha v1.71) y la comparación diaria ya mide el día de MODIS aparte (arriba); con un solo día-satélite
     con alerta en ocho días, el día de MODIS todavía no tiene muestra para decir nada de recall. VIIRS de día sigue
     cerrado y sin medir en la comparación.
- **Destraba:** Nicolás (criterio de adopción; día en VIIRS), el loop (medir).
- **Cumplido cuando:** el criterio escrito se cumple en una ventana fijada de antemano, de noche y de día, en los tres
  sensores, y la pestaña pública lo muestra.

### E4. VRP Chile cubre los volcanes que el OVDAS vigila, no sólo los 11 de MIROVA

**Qué tiene que ser cierto.** Si el OVDAS tiene que seguir abriendo MIROVA para algún volcán, no hay independencia. Y
para los volcanes que MIROVA no vigila, no hay hoja de respuestas: la vara es el propio OVDAS (A115).

- **Hoy:** los 11 Tier A en el NRT. Los otros 34 del `volcanoes.yaml` (32 activos) corren a diario en la sombra
  (`sombra-34.yml`, `data/sombra_34/`), se muestran en el tablero (ficha v1.26) y tienen su historia completa desde
  2025-02-15 (bloque S194 §a, tanda 7 aplicada). La publicación formal espera la Compuerta B del plan
  `docs/superpowers/plans/2026-11-02-nrt-34-volcanes.md` (en `loop/activo`; estimada ~2026-12-29) y las decisiones D1 a
  D15 de su §11; D14 dice que Nicolás avisa al OVDAS antes de publicar. Sus detecciones caen casi siempre lejos del
  cráter y sin `distance_class` (falta `inner_radius_km`, D5).
- **Destraba:** Nicolás (D1 a D15); la tabla de episodios del OVDAS para validar sin MIROVA.
- **Cumplido cuando:** la lista de volcanes del turno del OVDAS está entera en VRP Chile con clase de distancia, y la
  validación contra episodios del OVDAS está escrita.

### E5. El sistema sigue andando sin Claude, sin Nicolás un mes y con NASA caída

**Qué tiene que ser cierto.** Una fuente operacional no puede depender de una persona ni de sesiones de un asistente.
MIROVA tiene un grupo detrás; VRP Chile tiene a Nicolás y al loop.

- **Hoy, lo que hay:** el NRT corre solo en GitHub Actions (`nrt.yml`, cron 2 h, `nrt-retry.yml`), con vigilancias que
  abren issues (`nrt-healthcheck.yml`, que además lee el vencimiento del token; `nrt-monitor.yml`; guardias K de MODIS
  y VIIRS con reversión pre-autorizada). El hook de esta sesión informa el NRT verde (2026-11-22 05:14) y el
  `EARTHDATA_TOKEN` vigente hasta el 2027-01-14.
- **Hoy, lo que falta:**
  1. **Mantención sin Claude.** No encontré manual de operación en `docs/` (búsqueda de «runbook», «manual»,
     «operación»: sólo auditorías). La práctica es el loop de sesiones con bloques de arranque (`tasks/BLOQUE_ARRANQUE_S*`)
     y la regla A45, que exige a Nicolás para tocar el pipeline.
  2. **El token se rota a mano** cada 50 días y vive como secreto del repo (CLAUDE.md del proyecto, «Credenciales»); ya
     hubo un apagón por token vencido del 2026-07-17 al 2026-08-04 (`C:\Users\nmend\OneDrive\Escritorio\claude\MAPA_WORKSPACE.md`,
     ficha de VRP Chile).
  3. **El repo está en una cuenta de usuario** (`gh api users/MendozaVolcanic`: tipo `User`), no de una organización
     institucional.
  4. **Respaldo de datos:** `fetch.py` cae del producto estándar al NRT, pero ambos son de NASA. Si NASA corta, se cae
     VRP Chile y también MIROVA, que usa los mismos satélites; la independencia de mirovaweb.it no compra independencia
     de NASA. Fuente alternativa (por ejemplo FIRMS u otro proveedor): SIN VERIFICAR.
  5. **Vida de los sensores:** Suomi NPP dejó de producir (#943). Fin de misión de Terra y Aqua: SOSPECHA, no hay
     documento en el repo que lo fije; si MODIS se apaga, la cadena de VIIRS 375 y 750 (NOAA-20 y NOAA-21) queda sola.
- **Destraba:** Nicolás y TI de SERNAGEOMIN (cuenta institucional, token de servicio, segunda persona entrenada).
- **Cumplido cuando:** (a) existe un manual de operación que otra persona del OVDAS siguió con éxito al menos una vez
  (rotar el token, relanzar un NRT caído, leer una vigilancia en rojo); (b) el token no depende de una sola persona;
  (c) hay un plan escrito para el fin de MODIS.

### E6. SERNAGEOMIN lo reconoce como suyo

**Qué tiene que ser cierto.** El OVDAS es parte de un servicio público y el sistema es un SDA bajo la Resolución CPLT
N°372: para que sea la fuente oficial, la institución tiene que haberlo asumido, con su ficha publicada y su licencia.

- **Hoy:** la ficha `docs/FICHA_SDA_VRP_CHILE.md` está al día en lo técnico (v1.69 en este checkout) pero tiene campos
  `<completar>`: canal de consulta, acto que lo estableció, titularidad institucional, enlace. Su Subítem 2 dice
  «Unidad que lo usa: OVDAS», que hoy describe la meta y no el estado. El repo no tiene licencia (`git show
  origin/main:LICENSE`: no existe); la recomendación previa es MIT, consultando a SERNAGEOMIN
  (`memory\project_pendientes_de_nicolas.md`, punto 3). El correo a Coppola está en espera por decisión de Nicolás
  (mismo archivo, punto 5).
- **Destraba:** SERNAGEOMIN (jurídica, TI, jefatura); Nicolás lo inicia.
- **Cumplido cuando:** ficha sin `<completar>` publicada donde SERNAGEOMIN publica sus SDA, licencia en el repo,
  titularidad escrita.

### E0. Punto de partida: lo que ya existe

Para que quede claro qué no hay que rehacer:

- Detector de los tres sensores con el código operacional que MIROVA publicó (vía «código MIROVA», S186), validado
  contra Octave y MATLAB en VIIRS 750 (CLAUDE.md del proyecto, «Reglas científicas»).
- Historia de los 11 Tier A desde 2025-02-15 y de los 32 activos restantes desde la misma fecha, toda con la vía.
- Comparación diaria pública contra MIROVA (E3) y vigilancias automáticas (E5).
- Ficha SDA técnica al día (E6) y pre-registros sellados para cada cambio de detector.
- Lo que este camino no encontró: usuario, aviso, manual de operación, criterio de adopción operacional, licencia.

## 3. Orden de dependencias

```
E6 institucional ─────────────────────────────────┐
E5 robustez (manual, token, cuenta) ──────────────┤
E4 cobertura de los volcanes del OVDAS ───────────┤
E3 paridad + criterio de adopción + día ──┐       ├──> E1 marcha blanca ──> META
E2 latencia, vista, aviso ────────────────┴───────┘
```

E2 y E3 son condición para empezar la marcha blanca (E1); E4, E5 y E6 son condición para terminarla y declarar la
meta, pero pueden avanzar en paralelo y son los más lentos porque dependen de otras personas. La marcha blanca puede
partir con los 11 Tier A y sumar los 34 cuando se publiquen.

## 4. El crítico despiadado sobre este camino

Hasta cinco debilidades reales; cada una con su evidencia o marcada SOSPECHA.

1. **No sabemos qué le pide el OVDAS al sistema; la vara «paridad» es de Nicolás, no del OVDAS.** La única fuente de
   la condición de adopción es una frase de Nicolás del 2026-11-03 (`memory\project_sin_consumidores_operacionales.md`:
   el OVDAS usa el scraper «hasta que VRP Chile demuestre que entrega los mismos datos que MIROVA»). No hay registro de
   que la jefatura del OVDAS haya pedido algo ni de qué usa hoy del scraper (¿el CSV, el nivel, un aviso?). Si lo que
   el OVDAS necesita es otra cosa (alojamiento en TI institucional, un aviso, un formato de reporte), todo E3 puede
   estar cumplido y la meta seguir lejos. **Qué lo haría fracasar:** llegar a la Compuerta B y descubrir que el
   requisito era otro. SOSPECHA, por falta de evidencia en los dos sentidos.

2. **La vara de la paridad es MIROVA, y MIROVA puede desaparecer o congelarse.** Toda la validación de E3 lee la
   referencia que baja el scraper Mirova-v1 (`scripts/comparacion_via_k.py`). Los GeoTIFF de MIROVA ya están congelados
   desde el 2026-09-22 (`memory\reference_mirova_tif_congelados_20260922.md`) y el OCR estuvo mal calibrado hasta el
   2026-06-11 (A119). La meta es justamente dejar de depender de MIROVA, pero el criterio de victoria
   (`docs/MISSION.md`) sólo existe en relación con MIROVA. **Qué lo haría fracasar:** si mirovaweb.it cambia de formato
   o se cae antes de la adopción, el instrumento de E3 muere y no hay vara de reemplazo; la tabla de episodios del
   OVDAS (decisión 4 del bloque S194) es esa vara y sigue sin llenarse.

3. **El sistema depende de una persona y de un asistente.** A45 exige el sí de Nicolás para tocar el pipeline; la
   operación diaria es un loop de sesiones de Claude (S194 es la sesión 194; `tasks/BLOQUE_ARRANQUE_S194.md`); el
   token se rota a mano y ya produjo un apagón de 18 días (E5); el repo es de una cuenta de usuario. No encontré manual
   de operación. **Qué lo haría fracasar:** que Nicolás cambie de funciones o no esté un mes; una institución no adopta
   como fuente oficial algo que sólo una persona sabe mantener.

4. **Hoy VRP Chile llega más tarde que MIROVA y no avisa.** Mediana 5,05 h contra 2,77 h (S150, E2a), sin medición
   posterior al disparador externo; ningún aviso térmico al operador (E2c). **Qué lo haría fracasar:** en una crisis
   el operador mira lo que llega primero; si MIROVA (vía scraper) sigue llegando antes, VRP Chile queda como archivo
   histórico y no como fuente de turno. Que la latencia haya mejorado desde S150: SIN MEDIR. ⚠️ S196: la parte de la
   latencia ya no vale de noche. Medida de nuevo (E2a): de noche VRP Chile llega al tablero a la par que MIROVA por el scraper
   (MODIS 2,31 contra 2,36 h; VIIRS 2,83 y 2,80 contra 2,79 y 2,80 h) y primero en cerca de la mitad de las pasadas. Lo
   que sigue vivo es el aviso (E2c) y el día de MODIS, que por ahora llega más tarde (un solo día de datos).

5. **El criterio vigente es sólo nocturno y MIROVA publica de día.** #813 cuenta 94 pasadas diurnas con alerta
   protegida contra 346 nocturnas; la producción recién abre el día en MODIS (#1090, abierto) y VIIRS sigue cerrado de
   día. **Qué lo haría fracasar:** en la marcha blanca el operador ve una alerta diurna de MIROVA que VRP Chile no
   tiene, y eso cuenta como la falla que E1 no tolera. El A/B diurno dejó la decisión a Nicolás (bloque S194 §a).
   ⚠️ S196: el día de MODIS ya está en producción (#1090) y medido aparte en la comparación diaria (E3): 1 de 1 alertas
   diurnas de MIROVA publicada y ninguna falsa alarma en 146 días-satélite tranquilos, en ocho días. La debilidad sigue
   viva en VIIRS, que de día no procesa, y en la muestra diurna de MODIS, todavía chica.

## 5. El camino más corto

Los pasos en orden; cada uno dice qué destraba.

1. **Conversar con el OVDAS y escribir su requisito** (Nicolás con la jefatura). Salida: un documento corto,
   `docs/CRITERIO_ADOPCION_OVDAS.md`, con qué volcanes, qué latencia, si hace falta aviso y por qué canal, cuánto dura
   la marcha blanca y quién declara la meta cumplida. **Destraba:** la debilidad 1; da el número contra el que se miden
   E2 y E3; puede volver innecesarios eslabones de este documento.
2. **Medir lo que ya se puede medir, sin decisiones** (loop). Repetir la latencia con `first_processed_utc` por sensor
   (E2a) y sumar a la comparación diaria la ventana diurna de MODIS cuando entre #1090 (E3). **Destraba:** saber si la
   debilidad 4 sigue viva y cuánto pesa el día. ⚠️ S196: **hecho.** De noche la latencia ya está a la par con MIROVA por
   el scraper; la comparación diaria cuenta el día de MODIS aparte, sin mover un solo número nocturno anterior al 15-nov.
   Queda para el loop: repetir la latencia diurna con dos semanas de datos y vigilar la franja diurna de la comparación.
3. **Escribir y sellar el criterio de adopción operacional** (loop propone, Nicolás aprueba): qué ventana, qué hacer con
   una protegida perdida «juzgada no reproducible», y la vara sin MIROVA para los 34 (tabla de episodios del OVDAS).
   **Destraba:** que «hay paridad» tenga fecha (E3) y la debilidad 2.
4. **Partir la marcha blanca con los 11 Tier A** (Nicolás en turno, planilla de discrepancias), sin esperar el aviso
   ni la vista nueva; lo que el operador eche de menos ordena E2b y E2c. **Destraba:** E1, que es el único eslabón que
   convierte la paridad en confianza.
5. **En paralelo desde ya, lo institucional** (Nicolás inicia con SERNAGEOMIN): licencia, titularidad, cuenta
   institucional para el repo y el token, una segunda persona con el manual de operación. **Destraba:** E5 y E6, que
   son lentos y no dependen de nada técnico.

## 6. Decisiones que este camino le pide a Nicolás

| # | Decisión | Por qué ahora |
|---|---|---|
| C1 | ¿Quién en el OVDAS fija el requisito de adopción, y cuándo conversarlo? | Sin eso, todo lo demás optimiza una vara supuesta (debilidad 1) |
| C2 | ¿La marcha blanca parte ya con los 11, o espera a los 34 y al día? | Partir ya es gratis y da información; esperar la atrasa a 2027 |
| C3 | ¿Hace falta un aviso automático? ¿Por qué canal y con qué umbral? | Pide credencial y diseño; depende de lo que use hoy el turno |
| C4 | ¿Se inicia con SERNAGEOMIN licencia, titularidad y cuenta institucional? | Es el eslabón más lento y nadie más puede iniciarlo |
| C5 | ¿Qué fases del plan del visualizador (S176) entran antes de la marcha blanca? | El plan espera su decisión desde el 2026-11-09 |
