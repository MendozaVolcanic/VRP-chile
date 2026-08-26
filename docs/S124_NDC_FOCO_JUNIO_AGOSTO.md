# Foco Nicanor (NdC): junio → 26-ago-2026, releído con el filtro solar

Data: `data/experimental_ndc_focus/NevadosDeChillan.json` (505 records,
2026-05-01 .. 2026-08-24, run 32885279059) · Perfil: `experimental_ndc_focus`
(VIIRS375, piso 0.005 MW, **no operacional**).

## 1. Lo que hizo la fuente

| mes | noches con señal en el foco | VRP mediana | VRP máx |
|---|---|---|---|
| 2026-05 | 6 | 0,0725 | 0,078 |
| **2026-06** | **9** | 0,060 | 0,079 |
| 2026-07 | **1** | 0,045 | 0,045 |
| **2026-08** | **7** | 0,047 | **0,105** |

**Pulso en junio → silencio en julio → recuperación en agosto**, y agosto trae
el valor más alto de toda la serie (0,105 MW el día 18). MIROVA acompaña: 1
ALERTA nocturna en junio contra **3 en agosto** (18-ago 0,07; 20-ago 0,06 y 0,09).
Por su propia cuenta, NdC está hoy más activo que en junio.

## 2. Hallazgo nuevo: la ALERTA más grande de la ventana es DIURNA

| fecha UTC | sensor | MIROVA | elev. solar | |
|---|---|---|---|---|
| 2026-05-02 05:24 | VIIRS375 | 0,030 | −66,8° | noche |
| 2026-05-14 05:48 | VIIRS375 | 0,060 | −67,1° | noche |
| **2026-06-12 18:18** | **VIIRS375** | **0,320** | **+26,3°** | **DÍA** |
| 2026-06-16 05:30 | VIIRS375 | 0,060 | −73,3° | noche |
| 2026-07-15 04:48 | VIIRS375 | 0,020 | −74,7° | noche |
| 2026-08-18 05:48 | VIIRS375 | 0,070 | −62,8° | noche |
| 2026-08-20 05:12 | VIIRS375 | 0,060 | −65,3° | noche |
| 2026-08-20 06:06 | VIIRS375 | 0,090 | −60,0° | noche |

El 12 de junio, **0,320 MW con el sol a +26°**: es **3,5× más grande que
cualquier valor nocturno** de toda la ventana. Firma de libro de texto del
artefacto solar diurno que documenta **A76** (VIIRS375 diurno cerca del mediodía
solar sobre nube: reflexión en MIR 3,74 µm + TIR frío → NTI enorme → VRP
fantasma). NdC es el volcán con más contaminación diurna de la flota: **20 %**.

**Consecuencia interpretativa**: si el "pico de junio" de NdC se leyó a partir de
ese 0,320, se leyó un artefacto. El pulso de junio **existe** — está en nuestras
9 noches y en la ALERTA nocturna del 16 — pero su magnitud es de centésimas de MW,
no 0,32. Nuestro pipeline nunca lo generó: es nocturno por diseño, o sea que
estuvo bien por construcción.

## 3. El validador interno es más fuerte de lo documentado

El perfil documentó **2** noches de coincidencia con MIROVA. Con la serie hasta
agosto son **5**, todas en banda estrecha:

| noche | MIROVA | foco nuestro | ratio |
|---|---|---|---|
| 2026-05-14 | 0,060 | 0,073 | 1,22× |
| 2026-06-16 | 0,060 | 0,073 | 1,22× |
| 2026-08-18 | 0,070 | 0,105 | 1,50× |
| 2026-08-20 | 0,060 | 0,100 | 1,67× |
| 2026-08-20 | 0,090 | 0,100 | 1,11× |

Cuando la fuente sube lo suficiente para que MIROVA la publique, **medimos lo
mismo que ella**. Eso valida la calibración del foco sin ground truth externo.

## 4. Las dos "pérdidas" no son iguales

- **2026-05-02** (MIROVA 0,030): **no la perdimos**. Detectamos las 3 pasadas con
  VRP **0,032-0,033** — un ratio de 1,1× contra MIROVA — pero el centroide cayó a
  **2,4-2,8 km** del foco y el gate de 750 m la descartó. `nti_max` está en el
  piso (−0,943): es el sesgo de posición irreducible **A84**, no un fallo de
  detección.
- **2026-07-15** (MIROVA 0,020): **FN real**, cero detección esa noche. Es el
  valor más bajo que MIROVA publicó en la ventana, en su propio piso.

Separando los dos conceptos: **detección 5/6 (83 %)**, **acierto en el foco
4/6 (67 %)**.

## 5. ¿Hay que cambiar código?

- **Pipeline: NO.** El diseño nocturno excluyó el artefacto del 12-jun por
  construcción. La detección funciona y la magnitud calibra 1,1-1,7×.
- **Capa de auditoría: SÍ** — `scripts/auto_audit_weekly.py` no filtra elevación
  solar. NdC es el caso más fuerte de la flota: su ALERTA más grande de la
  ventana es diurna. Cualquier métrica de NdC que la incluya está inflando el
  denominador con algo que decidimos no mirar.
- **Gate del foco (750 m): NO ampliar.** Medido: a 3 km el recall sube 67 %→83 %
  (recupera el 05-02) pero las noches sin respaldo de MIROVA saltan de **19 a 52**
  — se admite el campo difuso, no el foco. A esa distancia el foco sub-píxel y el
  ruido topográfico son el mismo objeto (**A83**). El gate estrecho es lo que hace
  que este perfil sea un rastreador de foco y no otro detector de escena. Lo que
  cambia es el **reporte**: publicar detección y acierto-en-foco por separado.
- **Documentación del perfil: actualizar** — dice 2 coincidencias, son 5.
