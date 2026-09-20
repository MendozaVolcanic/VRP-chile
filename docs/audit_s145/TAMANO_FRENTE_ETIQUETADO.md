# Cuánto pesa, en el dashboard, lo que pintamos summit lejos del cráter (S145)

> Generado por `experiments/_s145_etiquetado/tamano_del_frente.py` desde
> `tamano_del_frente.json` (2026-09-20). Ningún número escrito a mano (S91). Ventana
> **2026-03-01 a 2026-09-20**, umbral **3,0 km**. "Publica" es el predicado del dashboard
> ejecutado con node (A97), con su control de identidad en el valor que exige
> `tests/test_evaluador_ab_s143.py:603`.

## Por qué existe este documento

La decisión 3 del traspaso de S145 pregunta si abrir el frente de **etiquetado**: cómo mostrar en
el dashboard un sitio tibio estable lejos del cráter. El propio traspaso marca su premisa como
**sospecha**, no como hecho: *"el sitio tibio que publicamos molesta al operador: nadie lo
reportó"*. Antes de proponer cualquier cambio de display (A72) hace falta saber de qué tamaño es la
cosa. Esto lo mide y nada más.

## Lo que este número NO es, antes de leerlo

Dos límites, y el primero es grave para quien quiera usar esto como el tamaño del frente de
`keep_peak`:

1. **Ningún record marca si pasó por `keep_peak`.** Se verificó recorriendo los 11 JSON: no existe
   ningún campo con `keep` ni `peak` en el schema. Y D19 dice que `keep_peak` publica su píxel
   **a 0,0 km** del ancla, no lejos, así que una cuenta por distancia **no puede** capturarlo. Este
   documento mide *"el dashboard pinta summit algo que está lejos del ancla"*, que es una pregunta
   de display legítima y vecina, pero **no es** el frente de `keep_peak`. Para ese haría falta
   persistir la marca (gap de schema, familia A7: el pipeline lo sabe y no lo guarda).
2. **Para los volcanes con radio interno de 3 km el cero es por construcción.** Lastarria y
   Planchón-Peteroa dan 0 porque un cúmulo a más de 3 km del ancla ya queda **fuera** del radio
   interno y el dashboard no lo pinta summit. No es un hallazgo sobre esos volcanes: es el umbral
   comiéndose la banda entera. Lo mismo, atenuado, en Copahue (radio 4 km).

Además, `centroid_dist_km` mide desde el **ancla de detección**, que es el cráter en la mayoría de
los volcanes pero es una elección del pipeline y no la coordenada nominal del GVP (A3, A6, D17).

## El tamaño

Sobre los **11 volcanes Tier A** (lo que carga `banco_paridad`; los otros 34 del `volcanoes.yaml`
quedan fuera): **894 de 9513 pasadas publicadas (9,4 %)** tienen su cúmulo a más de 3 km del ancla y aun así se
pintan summit.

| volcán | radio interno | publicadas | lejos | fracción | mediana km | noches donde **todo** lo publicado está lejos |
|---|---|---|---|---|---|---|
| PuyehueCordonCaulle | 20 | 1612 | **532** | 0,330 | 9,28 | 2 de 202 |
| Llaima | 5 | 809 | 74 | 0,091 | 4,22 | 1 de 200 |
| Chaiten | 5 | 987 | 76 | 0,077 | 3,98 | 0 de 195 |
| Villarrica | 5 | 899 | 63 | 0,070 | 3,98 | 0 de 199 |
| NevadosDeChillan | 5 | 401 | 27 | 0,067 | 4,27 | 5 de 131 |
| Tupungatito | 7 | 782 | 40 | 0,051 | 5,00 | 3 de 195 |
| Isluga | 5 | 881 | 38 | 0,043 | 3,96 | 0 de 203 |
| Copahue | 4 | 831 | 32 | 0,038 | 3,49 | 0 de 199 |
| Lascar | 5 | 851 | 12 | 0,014 | 4,08 | 1 de 186 |
| Lastarria | 3 | 652 | 0 | por construcción | — | 0 de 188 |
| PlanchonPeteroa | 3 | 808 | 0 | por construcción | — | 0 de 192 |

Por sensor: VIIRS 750 aporta 425, VIIRS 375 aporta 351 y MODIS 118.

## Qué dicen estos números

**Es un fenómeno de Cordón Caulle.** 532 de las 894 (el 60 %) son de un solo volcán, con mediana de
**9,28 km**, y ahí no hay nada que arreglar: es el lacolito del Cordón Caulle, desplazado del
cráter unos 7 km y con unos 707 km² de extensión, que ya está documentado como anomalía **real**
(A68). Su radio interno de 20 km existe justamente para no perderlo. De esas 532, MIROVA confirmó 2
y miró sin ver nada en 319, que es exactamente el perfil de la categoría b de A54: señal
volcánica real que MIROVA no publica por alcance operacional. **Filtrarla sería destruir el valor
agregado del proyecto, no limpiar un error.**

**Fuera de Cordón Caulle el fenómeno es chico y está pegado al umbral.** Las 362 restantes se
reparten entre nueve volcanes con fracciones de 1 a 9 %, y su mediana ronda los **4 km**, o sea
apenas pasando los 3 km del corte. Con el ancla y la cuantización de por medio, buena parte de eso
es el borde del disco del Test 1 que A69 describe, no un objeto a kilómetros del cono.

**En la unidad en que el operador vive el sistema, casi no existe.** Las noches en que *todo* lo
que publicamos de un volcán está lejos del cráter, que son las únicas en que el operador no tiene
nada cerca del cono con que contrastar, suman **12 en once volcanes y siete meses**. Las demás
noches traen las dos cosas y el mapa se lee solo.

## Lectura para la decisión 3

Los datos **sostienen la recomendación de dejarlo en backlog** que traía el traspaso, y agregan la
razón: el grueso del fenómeno es Cordón Caulle y ahí el dato es real, así que un cambio de display
que lo atenúe estaría escondiendo categoría b (A72 lo prohíbe explícitamente para señal real). El
resto es pequeño y está en el borde del umbral.

Lo que sí queda como trabajo concreto y barato, si el frente se abre alguna vez: **persistir la
marca de `keep_peak` en el record**. Sin ella, el frente que S144 dejó nombrado no se puede medir
con lo que hay en disco, y cualquier cuenta que se intente va a medir otra cosa, como midió ésta.
