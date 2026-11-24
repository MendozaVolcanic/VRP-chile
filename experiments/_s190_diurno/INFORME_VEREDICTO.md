# A/B diurno sobre la vía «código MIROVA»: veredicto (adenda V, issue #813)

Calculado el 2026-11-21 sobre el commit `dda72573f` de la rama `s190-diurno`, con la regla sellada (`ADENDA_VIA.md`) y
R-W7 en la lectura 2 que eligió Nicolás (`PREGUNTA_R_W7.md`). Corridas desde el tag `s190-diurno-via-codigo`
(`51aafdf14`). Revisado por un verificador de contexto limpio con esfuerzo alto, que lo reprodujo byte a byte
(`verificador/INFORME.md`). **No cambia nada en producción**: encender el día es un PR aparte que espera a Nicolás.

## Decisión de Nicolás (2026-11-21) y veredicto con la desviación declarada

Nicolás aceptó D1, D2 y D3. Lo dijo así, textual, el 2026-11-21 en la sesión S193, después de ver este informe con la
recomendación «D1: dejar pasar el caso de Isluga; D2: encender el día sólo en MODIS»: «continua con todo lo que
recomiendes».

- **D1.** La desviación quedó declarada en `ADENDA_VIA.md` §8, mecánica y leída del registro de cada job. Con ella, el
  evaluador dispensa exactamente un caso: `Isluga|MODIS|2026-07-22`. El veredicto sale **DECIDE NICOLÁS CON M4 en las
  dos opciones** (`resultado/veredicto_desviacion1_salida.txt`). Fuera de las líneas de la desviación, esa salida es
  idéntica a `resultado/informativo_sin_i4b_salida.txt`.
- **D2, con M4 a la vista.** Se enciende el día **sólo en MODIS** (`enable_daytime_modis`). VIIRS queda apagado.
  Queda pendiente mirar en imagen las 5 publicaciones de 1 MW o más fuera de Chillán y las 19 protegidas de VIIRS 375
  que no se recuperan. Antes de encender: el PR del frontend con pasadas diurnas y el PR de perfil con A45.
- **D3.** Nota sobre ceses de plataforma en `ADENDA_VIA.md` §9.

## En una pantalla

1. **Con la regla sellada: INVÁLIDO POR INSTRUMENTO en las dos opciones** (`enable_daytime_modis` y
   `enable_daytime_viirs`), por **un solo caso** de la compuerta I4 (b): Isluga, MODIS, 2026-07-22.
2. Ese caso no es una falla del brazo ni de NASA. El único gránulo diurno de Terra sobre Isluga ese día se bajó y se
   procesó, y la vía no guardó record: lo descartó por borde (171-01). Es el mismo descarte que ocurre de noche.
3. **Si Nicolás deja pasar ese caso** (desviación declarada, sólo él la decide), el resultado es **DECIDE NICOLÁS CON M4
   en las dos opciones**. Lo mismo sale con los 13 días excluidos y sin excluirlos (verificador, H2).
4. El día sí recupera alertas que MIROVA publica: MODIS 7 de 7 protegidas, VIIRS 375 23 de 42, VIIRS 750 13 de 18. Casi
   todo es de la erupción de Chillán. Fuera de Chillán, VIIRS publica de día anomalías de 1 MW o más en pasadas que
   MIROVA no lista, y eso es lo que impide adoptar VIIRS sin mirar.

## 1. El fenómeno

De día, el canal de 4 µm suma a la emisión térmica la luz del Sol reflejada: un salar, un glaciar o una nube al
mediodía levantan píxeles sin nada caliente debajo. MIROVA mira igual de día, con umbrales más altos y descartando las
escenas con reflejo especular (ángulo menor que 12°), y publica alertas diurnas. Nosotros hoy no publicamos ninguna. El
A/B corre dos copias de producción sobre los mismos días: el control (sólo noche, como hoy) y el brazo con el día
abierto en los tres sensores. Después mide, contra la hoja de respuestas de MIROVA, qué gana y qué ensucia el día.

## 2. Datos y cobertura (A108)

Seis ventanas, los 11 Tier A: W2 (06-13 a 06-30), W3 (07-20 a 07-31), W4 (08-13 a 08-31), W5 (09-01 a 09-20),
W6 (10-01 a 10-14) y W7 (10-15 a 11-15). En W2, W4 y W5, NASA cortó descargas en algunos trabajos: esos volcanes se
repitieron en los dos brazos desde el mismo tag (`resultado/ORIGEN.txt`; issues #1040, #1047 y #1052). En las seis
ventanas los dos brazos tienen las mismas noches, sin faltantes ni sobrantes. Ningún registro de los trabajos que entran
trae fallas de descarga. El verificador lo volvió a contar por su cuenta y comprobó que los dos brazos de cada volcán
salen del mismo run.

**Días excluidos.** La regla (a) más (b') de S163 excluye del 2026-11-03 al 2026-11-15
(`dias_excluidos_via_salida.txt`): CMR no tiene gránulos de Suomi NPP y el control tampoco tiene records de ese
satélite. La causa es el cese anunciado de Suomi NPP desde el 2026-11-02 a las 13:00 UTC (`scripts/ceses_esperados.json`,
aviso de NASA), no un hueco pasajero. La regla, mecánica, saca esos 13 días en los tres sensores. Eso incluye 9
protegidas MODIS, 13 de VIIRS 375 y 12 de VIIRS 750, casi todas de Chillán (verificador, H2). Sin excluirlos, el
veredicto no cambia. MODIS no tiene huecos en CMR.

## 3. Resultado por sensor

Tablas impresas por `resultado/tablas.py` desde los JSON del evaluador (`resultado/tablas_salida.md`). Los valores por
sensor son los mismos con la regla sellada y en el informativo: la compuerta sólo cambia la línea final.

| sensor | protegidas recuperadas | alertas recuperadas | negativos publicados | base (caso) | sin Chillán | sin W7 | M5 pares, mediana | M8 ≥1 MW sin fila | veredicto del sensor |
|---|---|---|---|---|---|---|---|---|---|
| MODIS | 7 de 7 | 7 de 9 | 1 de 2223 | DECIDE NICOLÁS CON M4 (e-ii) | SIN CAMBIO | ADOPTAR | 7, 1.110 | 0 | DECIDE NICOLÁS CON M4 |
| VIIRS375 | 23 de 42 | 31 de 53 | 8 de 2620 | ADOPTAR (b) | DECIDE NICOLÁS CON M4 | DECIDE NICOLÁS CON M4 | 31, 1.003 | 11 | DECIDE NICOLÁS CON M4 |
| VIIRS750 | 13 de 18 | 13 de 18 | 0 de 2910 | ADOPTAR (b) | NO ADOPTAR | ADOPTAR | 13, 1.000 | 5 | DECIDE NICOLÁS CON M4 |

Cómo se lee, sensor por sensor:

- **MODIS.** Recupera las 7 alertas protegidas diurnas de MIROVA (todas de W6 y W7) y publica de más una sola vez en
  2.223 pasadas diurnas negativas: Chillán el 2026-10-27, en plena erupción. La magnitud coincide con la de MIROVA
  (mediana 1,11). No sale ADOPTAR directo por el caso e-ii de la regla de S163: el beneficio es chico en número.
- **VIIRS 375.**
  - **Lo que gana.** Recupera 23 de las 42 protegidas.
  - **Lo que no recupera.** Las 19 que faltan son casi todas de Láscar y Lastarria al mediodía de junio, el patrón
    de reflejo solar probable que MIROVA publica (A76). Que sean reflejo es SOSPECHA, no está medido.
  - **Lo que publica de más.** Publica 11 veces de 1 MW o más en pasadas que la tabla de MIROVA no lista (M8), y
    eso lo saca de ADOPTAR. 6 de esas 11 son de Chillán. Las otras 5 son Tupungatito (1,65 MW), Villarrica (2,94 y
    2,50 MW), Láscar (2,12 MW) y Lastarria (6,22 MW), y nadie las ha mirado todavía.
- **VIIRS 750.** Recupera 13 de 18 protegidas y no publica ningún negativo. Pero sin Chillán sale NO ADOPTAR
  (R-CH): el beneficio es de un solo volcán en erupción. M8 da 5 casos: 4 de Chillán y 1 de Puyehue-Cordón Caulle
  (2,36 MW).
- **Defensa contra el Sol (M7).** El filtro de reflejo de la vía actúa en el brazo diurno: descarta 23 escenas
  MODIS y 4 en cada VIIRS. En el control no descarta ninguna.

## 4. El caso que invalida

La compuerta I4 (b) de S163 dice: «Ningún volcán, sensor y día con pasadas diurnas de MIROVA queda con cero records
diurnos del brazo». Se escribió para cazar un brazo que no bajó el día. Bajo K servía con tolerancia cero, porque
producción no perdía records de noche. La vía sí los pierde: de noche, 98 de 2.674 pasadas MODIS de MIROVA quedan sin
record (cuántas por el descarte de borde y cuántas por volcán fuera del gránulo no está separado: el registro no distingue). La adenda V ajustó a esa tasa la compuerta I4 (c), que pasa en los tres
sensores, pero dejó la I4 (b) con tolerancia cero. En Isluga, el 2026-07-22, MIROVA lista una sola pasada diurna MODIS
(Terra 12:25, RUTINA, 0 MW). La vía descartó ese gránulo por borde, y ese día no hubo otro gránulo diurno de MODIS
(Aqua no tiene ninguno en CMR). La pasada es negativa: dejarla pasar no puede inflar nada a favor de adoptar.

## 5. Decisiones para Nicolás

- **D1. ¿Dejar pasar ese caso de I4 (b)?** Recomendación: **sí, como desviación declarada**, limitada a pasadas cuyo
  gránulo se bajó y la vía descartó por borde según el registro. Por qué: la compuerta pretendía cazar descargas
  perdidas, y ésta no lo es. La pasada es RUTINA, así que no puede inflar el beneficio, y lo mismo pasa de noche en
  producción. Si dices que no, el A/B queda inválido y no se enciende nada. Si dices que sí, pasa a D2.
- **D2. Con M4 a la vista (tabla por ventana en `resultado/tablas_salida.md`), ¿qué se enciende?**
  - **MODIS: encender el día.** Es la recomendación, con lo que sigue como condición previa. Recupera las 7
    protegidas, publica de más 1 vez en 2.223 (Chillán en erupción) y su magnitud coincide con la de MIROVA.
  - **VIIRS: todavía no.** Primero hay que mirar dos cosas en imagen. Las 5 publicaciones de 1 MW o más fuera de
    Chillán sin fila de MIROVA: ¿reflejo o calor real? Y las 19 protegidas de VIIRS 375 que no recuperamos:
    ¿reflejo publicado por MIROVA? Con VIIRS 750, el beneficio es sólo de Chillán.
  - **Condiciones previas a encender cualquier sensor.** El frontend tiene que dejar de suponer que toda pasada es
    nocturna (`frontend/index.html` y la nota FRONTEND de `pipeline/diurno.py`). Hacen falta además el PR de
    perfil con A45 y tu «mergea #N».
- **D3 (sin urgencia).** Agregar a la regla de exclusión una nota sobre ceses definitivos de plataforma, para los A/B
  futuros (verificador, H2). No cambia este resultado.

## 6. Lo que no se midió

La geometría del gránulo de Isluga (bajarlo pide el token, que sólo está en los secretos). La causa de que la vía no
reproduzca las alertas diurnas de MIROVA en Láscar y Lastarria. La naturaleza (reflejo o calor) de las publicaciones
M8 fuera de Chillán.

## Archivos

- Salida del evaluador, regla sellada: `resultado/veredicto_salida.txt`.
- Salida informativa sin el I4b de Isluga: `resultado/informativo_sin_i4b_salida.txt`.
- Tablas: `resultado/tablas.py` y `resultado/tablas_salida.md`.
- Días excluidos: `resultado/dias_excluidos.json`.
- Origen de cada volcán: `resultado/ORIGEN.txt`.
- Verificador: `verificador/INFORME.md`, con sus caminos escritos antes de abrir las salidas (`caminos.md` y su
  sha256).
- Datos crudos, fuera del repo: `D:\vrp-trabajo\temporales\s190_diurno\eval\`.
