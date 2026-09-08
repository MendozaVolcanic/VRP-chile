# Pre-registro — test de conformidad contra el caso A6 del paper (Villarrica, 24-jun-2009)

> Criterio fijado **antes** de correr nada y antes de mirar ningún dato de esa fecha.
> Caso: `documentacion/sp426_5.txt:812-817` (Fig. A6 del Apéndice A de Coppola 2016a SP 426.5).

## Por qué este caso, y por qué recién ahora

El Apéndice A del paper trae **nueve casos resueltos por el propio autor**, con fecha exacta y
veredicto conocido — seis donde el algoritmo detecta y **tres donde deliberadamente no**. Es el
conjunto de validación del algoritmo que estamos clonando, publicado por quien lo escribió. En 136
sesiones el proyecto **nunca lo usó**: «Dubbi» y «Tolbachik» tienen cero menciones en todo el repo
fuera del PDF, y «24 June 2009» tampoco aparece.

Para un proyecto cuya misión es el clon literal, esto es el test que faltaba, y los tres negativos
valen tanto como los positivos: si detectamos donde el autor no detecta, eso es sobre-detección
estructural, que es justo el frente abierto del artefacto.

**A6 es el primero porque es Villarrica**: está configurado con coordenadas ya validadas, no exige
inventar nada, y el fenómeno es exactamente el de la regla A69 — cumbre helada a 2.847 m contra el
lago Villarrica a 215 m, o sea el gradiente topográfico que en nuestro pipeline contamina los
caminos de infrarrojo medio absoluto.

## Qué afirma el paper sobre este caso

Cita verbatim (`sp426_5.txt:812-817`), imagen «cloud-free» de MODIS del 24 de junio de 2009:

> el contraste entre la cumbre helada y el lago *"is clearly visible on the NTI and NTIbk"*;
> sin embargo *"a very small thermal anomaly (NTI ≈ −0.93) at the summit of Villarrica is easily
> detected after performing the spatial filtering (dNTI and dETI)"*; y
> *"the warm lake surface almost disappears in the ETI map"*.

Dos afirmaciones comprobables, no una:

1. **Detecta** la anomalía de la cumbre, pese a ser muy pequeña (NTI ≈ −0,93, **muy por debajo**
   del umbral fijo K1 = −0,80, que por lo tanto no la ve).
2. **No** genera detección sobre el lago tibio: el filtrado espacial lo cancela.

Que las máscaras geográficas estén apagadas en el perfil operacional
(`ENABLE_EXCLUDE_ZONES = False`, verificado leyendo `pipeline.profile`) hace el test **limpio**:
nada oculta artificialmente el lago, así que la segunda afirmación se mide de verdad.

## Diseño

Un granule, sin reproceso masivo. Se procesan **todas las pasadas nocturnas de MODIS del
24-jun-2009** sobre Villarrica (Terra y Aqua; el paper no dice hora ni plataforma), con el perfil
`mirova_equivalent` y el código de hoy, sin tocar `pipeline/`. Corre en GitHub Actions porque
`pyhdf` no funciona en Windows.

## Criterio de desenlace

Sea el cráter `vent_lat/lon` de `volcanoes.yaml` y el lago el centro declarado en la zona «Lago
Villarrica» del mismo archivo (−39,27 / −72,09), con radio 7 km.

- **CONFORME** — al menos una pasada nocturna publica detección con el cúmulo primario **a ≤ 5 km
  del cráter** (el `inner_radius_km` del volcán), **y** ninguna pasada publica detección cuyo
  cúmulo caiga dentro del radio del lago.
- **NO CONFORME, falso negativo** — ninguna pasada nocturna detecta en la cumbre. Localiza el
  defecto en nuestro contextual: el paper detecta lo que nosotros no.
- **NO CONFORME, falso positivo** — alguna pasada publica detección sobre el lago. Localiza el
  defecto en la cancelación del gradiente (A69 / D11), con referencia del autor.
- Los dos anteriores pueden darse **a la vez**; se reportan ambos.
- **INDETERMINADO** — no hay granule nocturno de esa fecha que cubra el volcán, o la descarga
  falla, o el granule está nublado de un modo que el paper no describe (él lo llama «cloud-free»).

## Control de validez, se evalúa primero

El paper entrega **un** número: NTI ≈ −0,93 en la anomalía. Se reporta el `nti_max` observado de
cada pasada **antes de cualquier veredicto**. Si ninguna pasada nocturna cae en **[−0,97, −0,85]**,
no estamos mirando la escena del paper o el índice no es comparable, y **ningún otro número del run
es interpretable** — el desenlace es INDETERMINADO por control, no NO CONFORME.

Esta condición existe porque en esta misma sesión cinco veredictos se apoyaron en instrumentos que
medían otra cosa que la que decían medir, y en todos los casos lo delató un control, no una
revisión del método.

## Límites aceptados de antemano

- **Es MODIS, no VIIRS 375 m.** Valida la implementación del contextual en el sensor del paper, no
  en el que hoy carga el recall. Un resultado conforme **no** absuelve a VIIRS.
- El paper no da μ, σ, dNTI ni dETI, así que el test es **binario y de posición**, no una
  comparación numérica fina. Es lo que el material permite.
- `vent_lat/lon` y la geometría de hoy pueden no ser los que MIROVA usó en 2009.
- Una sola fecha. Un caso conforme no valida el algoritmo entero; uno no conforme sí localiza un
  defecto, que es el valor asimétrico que hace que valga la pena.
- El paper no dice si su imagen es nocturna. Nuestro pipeline es *night-only* por diseño (el MIR
  diurno está contaminado por reflexión solar). Si las únicas pasadas de esa fecha fueran diurnas,
  el desenlace es INDETERMINADO y **no** un fallo nuestro.

## Qué NO decide este test

- Nada sobre la intersección contextual del Test 1 (ése es el probe de 3 brazos, desenlace C).
- Nada sobre el «Test 1 integrado» ni sobre su procedencia.
- No autoriza ningún cambio en `pipeline/`. Es una medición.
