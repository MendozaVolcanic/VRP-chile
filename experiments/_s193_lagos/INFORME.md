# Falsos positivos sobre lagos: Laguna del Maule y los demás (S193, 2026-11-21)

Pregunta de Nicolás (2026-11-21): «como enfrentamos falsos positivos dentro de lagos o cuerpos de agua como los que
aparecen en laguna del maule, es una falla del codigo mirova o hay algo que se puede hacer? si no esta en el codigo
esas mejoras pueden quedar para el experimental».

Archivos de esta medición (todos en `D:\vrp-trabajo\temporales\s193\lagos\`):

- `D:\vrp-trabajo\temporales\s193\lagos\medir_agua.py`: cruza cada píxel alertado con la máscara de agua.
- `D:\vrp-trabajo\temporales\s193\lagos\resumir.py`: arma las tablas.
- `D:\vrp-trabajo\temporales\s193\lagos\records.csv` (14.391 pasadas con detección) y
  `D:\vrp-trabajo\temporales\s193\lagos\pixeles.csv` (41.989 píxeles).
- `D:\vrp-trabajo\temporales\s193\lagos\resumen.txt`: salida completa de `resumir.py`.
- `D:\vrp-trabajo\temporales\s193\lagos\verificaciones.py` y
  `D:\vrp-trabajo\temporales\s193\lagos\verificaciones.txt`: los números que no salen de `resumir.py` (BT del lago,
  lagos cratéricos, agua alrededor de cada punto, detector anterior de abril).

Todo número de este informe sale de `resumen.txt` o de `verificaciones.txt`. Copia en el repo, sin `pixeles.csv` (se
regenera con `medir_agua.py`): `experiments/_s193_lagos/`.

## Respuesta corta

1. **No es una falla del código de MIROVA: es su comportamiento esperado, y MIROVA lo dice.** Coppola et al. 2016a
   (`documentacion/sp426_5.txt`, l. 689 a 694) reconoce falsas detecciones asociadas a contrastes altos de NTI en el
   borde de cuerpos de agua, que según el paper típicamente irradian menos de 5 MW y se reconocen por inspección visual del mapa
   NTI; agrega que bajar esa tasa haría perder muchas alertas reales débiles. El código operacional de VIIRS 750 (OSF
   zm62w) no tiene máscara de agua: su único filtro de superficie es el rechazo por reflejo solar bajo 12°, que sólo
   actúa de día. La producción (`mirova_equivalent`) es fiel en esto y no se toca.
2. **Lo medido en la vía (producción):** de 14.391 pasadas con detección en 41 volcanes, 124 (0,9 %) tienen el píxel
   más caliente sobre agua (más de la mitad de la celda es agua en JRC). Todas son de noche (la vía no procesa el día),
   con potencia mediana de 0,29 MW y máxima de 5,3 MW, en línea con el «menos de 5 MW» de Coppola.
3. **Laguna del Maule es el caso extremo, y por geometría:** 35 de sus 123 pasadas con detección (28,5 %) tienen el pico
   sobre el lago, 33 de ellas a 5 km o menos del punto del volcán. La razón es que la coordenada del volcán en
   `volcanoes.yaml` está dentro del lago (la celda de 1 km del centro es 100 % agua; en el cuadro de 10 km, 57 %): la
   «cumbre» de Laguna del Maule es agua. Las 9 detecciones MODIS que tiene en toda su historia caen sobre el lago.
   Lo que se ve hoy en el tablero es eso: la sombra diaria del 2026-11-20 publicó 2,30 MW (MODIS Terra, 01:30 UTC,
   2,24 km) y 0,12 MW (NOAA-20, 05:42 UTC), las dos sobre el lago.
4. **Sí hay algo que hacer, y el propio código de MIROVA trae la herramienta**: la matriz `BOX` admite píxeles
   excluidos (`NaN`) por volcán, y su comentario (l. 122 a 125 de `MIROVA_VIIRS750_hotspot_detection.m`) dice que las
   ROI se pueden adaptar «para excluir» otras fuentes térmicas persistentes de la ventana. Como MIROVA no monitorea
   Laguna del Maule, no hay una `BOX` suya que copiar: definirla es decisión de geólogo. Una regla general de máscara
   de agua no está en MIROVA y va al perfil `experimental`, como pidió Nicolás.
5. **El costo de una máscara mal hecha es alto y está medido:** los lagos cratéricos de Tupungatito, Planchón-Peteroa y
   Copahue ponen 1.693 pasadas de cumbre (a 5 km o menos) «a la orilla» del agua, 53 de ellas de 1 MW o más en Planchón-Peteroa. Una
   máscara con margen (orilla) las borraría. Una máscara que sólo saca celdas con 50 % o más de agua no toca ninguno de
   sus 3.926 píxeles de cumbre (0 de 3.926), porque esos lagos son más chicos que un píxel.

## 1. El fenómeno

De noche el terreno pierde calor rápido (roca y nieve tienen poca inercia térmica y emiten bien), mientras el agua
guarda el calor del día y de la estación: su capacidad calórica es alta y la mezcla vertical renueva la superficie. En
alta cordillera el contraste es grande, porque la roca alrededor se enfría bajo cero y el lago queda cerca de 0 a 5 °C
mientras no se congele. Para el detector, un lago así es un conjunto de píxeles más tibios que sus vecinos, que es
justamente lo que busca: el NTI (MIR contra TIR) sube un poco y el contraste espacial (dNTI, el píxel contra la media de
su 3 × 3) lo destaca, sobre todo en el borde, donde agua tibia y roca fría quedan lado a lado.

Lo que dicen los datos de Laguna del Maule (35 pasadas con el pico sobre el lago):

| | mediana | mínimo | máximo |
|---|---|---|---|
| BT MIR del píxel sobre el lago | 271,9 K | 245,4 K | 295,7 K |
| Temperatura del fondo (`t_bg_k`) | 266,9 K | 233,2 K | 287,3 K |

El lago se ve a unos −1 °C de brillo en el infrarrojo medio, unos 5 K sobre un fondo de −6 °C: es agua fría pero más
tibia que su entorno, no una fuente volcánica (una fuente volcánica de 1 MW sobre un píxel de 375 m daría BT de MIR
muy por encima de eso). La señal es intermitente: 35 pasadas en 21 meses, sobre 6.643 pasadas nocturnas de la historia
de la vía y 139 de la sombra; hace falta una noche despejada con el terreno muy frío para que el contraste cruce el umbral. No hay
estacionalidad marcada (hay detecciones de marzo a enero); la medición no separa si el lago estaba congelado, porque la
máscara JRC es un promedio 1984 a 2021, no el estado de esa noche. Ese máximo de 295,7 K (23 °C) es raro para el lago a
2.160 m y queda SIN EXPLICAR: puede ser una celda mixta con nube o con orilla; no se revisó la imagen.

En los 124 casos sobre agua de todos los volcanes, el pico está 10,0 K (mediana) sobre el fondo, contra 12,3 K en las
detecciones sobre tierra: el contraste del agua es algo menor, pero se solapa con el de las detecciones reales, así que
el contraste solo no las separa.

## 2. Lo que se midió

**Máscara**: JRC Global Surface Water v1.4 (Pekel et al. 2016, Nature 540), capa `occurrence` 1984 a 2021, 30 m,
leída por ventana desde el almacenamiento público de Google (`storage.googleapis.com/global-surface-water`), una
ventana de ±40 km por volcán. Incluye lagos, embalses y también mar y fiordos (Chaitén tiene 33 % de agua en su
ventana; es el golfo). Se busca primero lo local: el repo no tenía máscara de agua (sólo el `exclusion_zones.py` de S16,
ver §5) y `documentacion/` no trae ninguna; `docs/DATA_SOURCES.md` lista el MCDWD de MODIS como «no usado, gap».

**Criterio**: un píxel está «sobre agua» si 50 % o más de su celda (375 m en VIIRS 375, 750 m en VIIRS 750, 1 km en
MODIS, la grilla de MIROVA) tiene ocurrencia de agua de 50 % o más; está «a la orilla» si no lo está pero hay agua en
su cuadrado de 3 × 3 celdas (los vecinos que entran al dNTI). Una pasada se clasifica por su píxel de mayor BT de MIR.
Limitación: la huella real fuera de nadir es más grande que la celda; se usa la celda remuestreada.

**Datos**: sólo records de la vía «código MIROVA» (`via_codigo_mirova: true`): `data/historia_34/` (2025-02-15 a
2026-11-02), `data/sombra_34/` (desde 2026-11-03) y `data/mirova_equivalent/` de los 11 Tier A, deduplicados por
sensor y hora. El `data/mirova_equivalent/LagunaDelMaule.json` es del detector anterior (abril 2026) y no entra.

**Por sensor** (pico de la pasada; todas de noche):

| sensor | pasadas | sobre agua | % | a la orilla | % |
|---|---|---|---|---|---|
| MODIS | 545 | 9 | 1,7 | 34 | 6,2 |
| VIIRS 375 | 11.569 | 96 | 0,8 | 1.817 | 15,7 |
| VIIRS 750 | 2.277 | 19 | 0,8 | 215 | 9,4 |

Las 9 de MODIS son todas de Laguna del Maule.

**Por volcán** (los que tienen alguna pasada sobre agua; lista completa en `resumen.txt`):

| volcán | pasadas con detección | pico sobre agua | a 5 km o menos | VRP mediana sobre agua (MW) | máx. (MW) | distancia mediana (km) | qué agua |
|---|---|---|---|---|---|---|---|
| Laguna del Maule | 123 | 35 (28,5 %) | 33 | 0,29 | 2,30 | 2,5 | el lago, donde está el punto del volcán |
| Carrán-Los Venados | 120 | 21 (17,5 %) | 20 | 0,21 | 2,18 | 1,8 | cuerpos de agua a menos de 2 km del punto (no identificados por nombre) |
| Calbuco | 48 | 12 | 0 | 0,25 | 2,02 | 19,4 | lago a ~19 km (Llanquihue, por la distancia) |
| Osorno | 64 | 10 | 0 | 0,53 | 1,60 | 19,2 | lago a ~19 km (Llanquihue o Todos los Santos) |
| Huequi | 34 | 7 | 0 | 0,25 | 0,90 | 26,5 | mar o fiordo |
| Láscar | 2.837 | 5 | 0 | 0,39 | 0,81 | 19,5 | lagunas o salar al borde de la ventana |
| Villarrica | 132 | 5 | 0 | 0,19 | 0,58 | 24,8 | lago a ~25 km |
| Chaitén | 300 | 4 | 0 | 1,30 | 1,81 | 24,0 | mar |
| otros 13 volcanes | | 1 a 4 cada uno | 0 | | 5,29 (Antuco) | | |

Fuera de Laguna del Maule y Carrán-Los Venados, el agua aparece lejos del cráter (14 a 30 km), en la clase «lejos»
del tablero, no en la cumbre. Totales: 124 pasadas sobre agua, 53 a 5 km o menos (33 de Laguna del Maule y 20 de
Carrán-Los Venados), 19 de 1 MW o más, suma de 70,4 MW contra 22.561 MW de las pasadas sobre tierra.

**Antes y después de la vía en Laguna del Maule.** La semana del 17 al 24 de abril de 2026, el detector anterior
(`data/mirova_equivalent/LagunaDelMaule.json`) dio 30 detecciones con mediana de 82,7 MW y hasta 157 MW, con hasta 100
píxeles: el lago entero (es el caso del plan S15 P3.6 y de los «262 píxeles a ΔT 17 K»). La vía, sobre la misma
semana, da 2 detecciones (0,80 y 2,87 MW). El problema grande ya lo resolvió el cambio al código de MIROVA; lo que
queda es un goteo de pasadas de menos de 3 MW sobre el lago.

## 3. Qué hace MIROVA

- **Código operacional VIIRS 750** (`experiments/_s158_d17_diseno/osf_codigo_mirova/MIROVA_VIIRS750_hotspot_detection.m`):
  no hay máscara de agua, de lago ni de tierra. Lo único que mira la superficie es el rechazo de toda la escena si el
  ángulo de reflejo solar es menor que 12° (l. 83 a 88), que es de día. Sí hay un mecanismo de exclusión por volcán: la
  `BOX` con `NaN` en los píxeles que no se analizan (l. 25 a 29 y 140), y el comentario de l. 122 a 125 dice que las
  ROI «can also be adapted to exclude neighbouring active volcanoes or other persistent thermal sources». Qué excluye
  MIROVA en cada volcán no está publicado (SIN DATO; A4).
- **Coppola et al. 2016a** (`sp426_5.txt`): l. 689 a 694, las falsas detecciones en el borde de cuerpos de agua
  (menos de 5 MW, se quitan mirando el mapa NTI); y la Fig. A6, Villarrica 24 de junio de 2009: el lago Villarrica
  (215 m) se ve claramente tibio en NTI y NTIbk, y «casi desaparece» en el ETI (l. 816 a 818). Es decir, MIROVA cuenta
  con el ETI y el filtrado espacial para atenuar el lago, no con una máscara.
- **Aveni et al. 2024, TIRVolcH** (grupo MIROVA, producto de baja temperatura en I05): usa la máscara tierra/agua del
  L1B de VIIRS, pero para separar escenas dominadas por tierra o por agua (umbral de 20 % de tierra) y cambiar la
  estadística, no para borrar píxeles de agua (`Aveni_2024_TIRVolcH_RSE.md`, l. 579 y 688 a 699). No es el detector
  MIR de MIROVA.

Por las tres preguntas de `docs/MISSION.md`: una máscara de agua general no está en los papers ni en el código del
detector MIR, no cierra una divergencia del catálogo y no es alineación interna. No entra a `mirova_equivalent`.

## 4. Propuesta para el perfil `experimental`

Dos piezas, de menor a mayor alcance. Ninguna se implementa aquí (A45: `pipeline/` no se toca).

**A. Laguna del Maule: corregir la geometría antes que la física.** El problema de la cumbre es que el punto del
volcán está en el lago. Dos caminos, los dos de geólogo (decisión D5 de los 34):

1. Mover el punto de referencia al foco que interesa vigilar (por ejemplo el centro de deformación de la caldera, o un
   centro eruptivo del Holoceno), con su fuente citada. No se propone un valor aquí: no se adivinan coordenadas.
2. Poner en `NaN` de la `BOX` las celdas que son lago (mecanismo que el código de MIROVA ya prevé). Como MIROVA no
   publica Laguna del Maule, esto no rompe la réplica de nada; por eso podría ir incluso a la sombra de los 34, pero
   eso lo decide Nicolás. Medido: sacaría 33 de las 33 pasadas sobre agua a 5 km o menos.

**B. Regla general (sólo `experimental`): descartar un píxel alertado si su celda es mayoritariamente agua.**

- Regla: `frac_agua(celda) >= 0,5` en JRC (ocurrencia de 50 % o más), sin margen de orilla.
- Lo que sacaría en la historia de la vía: las 124 pasadas cuyo pico cae sobre agua (las pasadas con otros píxeles
  sobre tierra conservan esos píxeles; hay que recalcular su VRP con el fondo del `.m`, cosa que esta medición no hace).
- Lo que no sacaría: los lagos cratéricos chicos. En Tupungatito, Planchón-Peteroa y Copahue, de 3.926 píxeles
  alertados a 5 km o menos, ninguno tiene la mitad de su celda en agua (Tupungatito 0 de 2.576; Planchón-Peteroa 0 de
  1.289; Copahue 0 de 61). En cambio, 1.693 de sus pasadas de cumbre caen «a la orilla» (agua dentro del 3 × 3), con 53
  de 1 MW o más en Planchón-Peteroa: **una máscara con margen está prohibida**, borraría actividad real.
- Costo físico (qué alerta real se perdería): un lago cratérico caliente que llene la celda entera, o una erupción
  sublacustre. En Chile ningún lago cratérico activo de los monitoreados llena un píxel de 375 m (medido arriba), pero un
  evento nuevo en un lago grande (Laguna del Maule es justamente un sistema riolítico en reactivación) caería bajo la
  regla. Salvaguarda propuesta, a medir antes de adoptar: conservar el píxel de agua si su BT de MIR supera lo que un lago
  sin aporte volcánico puede tener (en esta muestra el pico sobre agua tiene mediana 278,8 K, percentil 90 de 300,0 K y
  máximo 315,5 K en todos los volcanes; en Laguna del Maule, máximo 295,7 K). El umbral sale de la referencia
  (A115), no se elige: con la serie de OVDAS y SWIR, no con este informe.
- Máscara: JRC es fija (1984 a 2021) y no sabe si esa noche el lago estaba congelado o si un embalse creció. Para la
  versión operativa habría que congelar la capa en `data/geo/` (no leerla de internet en cada corrida) y anotar su versión.
- Requisito previo: hoy el perfil `experimental` sigue con el detector anterior (A117), no con la vía. La regla se
  aplicaría sobre la vía, así que antes hace falta que `experimental` corra la vía, o probarla como A/B de la vía con
  `data_subdir` aislado.

**Cómo se mide que es mejor** (§12 de `docs/BEYOND_MIROVA_EXTENSIONS.md`; A115: contra OVDAS y SWIR, no contra MIROVA):

1. Falsos positivos quitados: para cada pasada descartada sobre agua, buscar en los reportes del OVDAS (RAV) si hubo
   anomalía térmica en ese lago, y en Landsat 8/9 OLI o Sentinel 2 MSI (SWIR, bandas 6, 7 y 12) dentro de ±3 días si
   hubo píxeles calientes. Un lago a 0 a 20 °C no emite en SWIR; una fuente volcánica de más de unos 200 °C sí. Sin
   anomalía en ninguno de los dos, el descarte era correcto.
2. Alertas reales perdidas: 0 pasadas de cumbre perdidas en Tupungatito, Planchón-Peteroa, Copahue y Villarrica en la
   historia de la vía (control ya medido: 0 de 3.926 píxeles) y 0 pasadas con SWIR positivo descartadas.
3. Control del instrumento (A110, A116): correr la regla sobre una ventana sin lagos (por ejemplo Láscar a menos de
   5 km) y comprobar que no saca nada; y sobre Laguna del Maule, que saca las 33 de cumbre.

## 5. Antecedentes en el repo (para no repetirlos)

- **S15, plan P3.6** (`tasks/_archive_s80/plan_s15_p3_6_water_aware_filter.md`): ya propuso un filtro de agua con
  Natural Earth y lista blanca de lagos cratéricos activos, motivado por Laguna del Maule. **S16** lo simplificó a
  `pipeline/exclusion_zones.py` (círculos a mano por volcán: Salar de Atacama, Embalse El Yeso) y **S27** lo apagó en el
  clon literal (`enable_exclude_zones: false`) porque ningún paper MIROVA documenta máscaras. Esta medición dice por qué
  no hay que revivir los círculos: un círculo alrededor de un lago es una máscara con margen y se come la orilla.
- **S190** (`experiments/_s190_coordenadas/INFORME.md`, l. 39): la coordenada de Laguna del Maule la fijó Nicolás en
  `5c71e207a` (2026-04-16) como «centro de la laguna». Es la razón de que la cumbre de este volcán sea agua.

## 6. Qué queda SIN MEDIR

- Si las pasadas sobre agua coinciden con noches de lago descongelado (la máscara es climatológica).
- El VRP que quedaría en las pasadas mixtas si se quitan sólo sus píxeles de agua (hay que correr el `.m` con esos
  píxeles en `NaN`; no basta restar).
- Qué cuerpo de agua es el de Carrán-Los Venados (a menos de 2 km del punto): mirarlo en el mapa antes de decidir.
- Nada se cotejó contra OVDAS ni SWIR todavía: la propuesta es una hipótesis medida en su alcance, no en su acierto.
