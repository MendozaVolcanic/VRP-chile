# El piso VRP no suprime nada que se vea — y arreglarlo cortaría Láscar

> Números de `experiments/_s126_piso/01_que_suprime_el_piso.py` → su `.json` (S91).
> Read-only sobre `data/mirova_equivalent/`, 2026-05-01 a 2026-08-28.

## Lo que S125 ya había probado

- **Los papers no lo justifican**: Coppola 2016a tiene una clase de alerta explícita
  *"Low < 1 MW"*. El criterio de MIROVA es de **contraste contra el fondo**; el VRP es
  una salida, nunca una compuerta. Nuestro piso invierte esa relación.
- **La justificación del YAML está falsada**: decía "mínimo observado" con n=1 y n=2.
  Con n=1000 el mínimo real que MIROVA publica es 0,010 en VIIRS 375 y 0,090 en
  VIIRS 750 — los dos pisos quedaron **por encima** del mínimo de la referencia.
- **Está mal aplicado**: `store.py:466` lo aplica a `record["vrp_mw"]` (suma de
  escena) y no a `primary_cluster.vrp_mw`, que es lo que grafica el dashboard.

Todo eso apunta a quitarlo. Faltaba la pregunta que decide: **¿qué hay adentro de lo
que suprime?** Porque S126 mostró que en las noches quietas el pipeline reporta una
fluctuación del fondo a ~2,8 km del cráter con VRP ~0,045 MW — justo el orden del
piso. Si lo que corta es eso, está haciendo un trabajo útil por accidente.

## Primero: el piso es un no-op para lo que se ve

| sensor | records | pisados | % | siguen con `pc.vrp>0` |
|---|---|---|---|---|
| VIIRS 375 | 5.570 | 231 | 4,15 % | **231 (100 %)** |
| VIIRS 750 | 5.530 | 246 | 4,45 % | 240 (97,6 %) |
| MODIS | 2.906 | **0** | 0 % | — |

**El 100 % de los records que el piso apaga siguen mostrando `pc.vrp_mw > 0`**
(mediana 0,014 MW en VIIRS 375, contra un piso de 0,02). El piso pone en cero un campo
que el dashboard no lee. Y el de MODIS no toca **ninguno** de 2.906 records: código
muerto confirmado.

O sea que quitarlo **no cambia nada visible**. Lo que sí importa es la otra pregunta:
qué pasaría si se lo *arreglara* — es decir, si se aplicara a `pc.vrp_mw`.

## Y ahí la respuesta se parte en dos regímenes

Distancia al cráter del clúster que el piso alcanzaría:

| volcán | pisados | dist. mediana | % a <1 km | % en el anillo 1,5–3 km |
|---|---|---|---|---|
| **Láscar** | 66 | **0,67 km** | **59 %** | 20 % |
| **Isluga** | 22 | **1,01 km** | **41 %** | 18 % |
| PCC | 52 | 2,86 | 38 % | 17 % |
| Planchón-Peteroa | 24 | 1,99 | 17 % | 67 % |
| Chaitén | 32 | 2,72 | 22 % | 34 % |
| Nevados de Chillán | 40 | 2,54 | 10 % | 60 % |
| Tupungatito | 62 | 4,44 | 10 % | 18 % |
| Villarrica | 20 | 2,94 | 5 % | 50 % |
| Copahue | 24 | 2,71 | 4 % | 71 % |
| Llaima | 24 | 2,76 | 4 % | 58 % |
| Lastarria | 111 | 2,24 | 4 % | **76 %** |

**En los nevados, lo pisado está en el anillo** (50-76 % en 1,5–3 km, casi nada al
cráter): es la firma del artefacto topográfico que S126 documentó. Ahí un piso que
funcionara estaría cortando terreno.

**En Láscar e Isluga está en el cráter** (59 % y 41 % dentro de 1 km): ahí es señal
real y débil, y un piso que funcionara sería un generador de falsos negativos —
precisamente en el volcán al que ya le falta un píxel
(`docs/S126_LASCAR_ES_UN_PIXEL.md`).

### El caso que no se puede resolver por posición: Lastarria

Lastarria concentra el mayor número de pisados (111, y 56 en noches que MIROVA
publicó) con el **76 % en el anillo**. Por posición parecería artefacto — pero en
Lastarria el offset **es real**: el campo fumarólico de Lazufre está genuinamente
desplazado del cráter, y A84 documenta que el `ctx_cluster` lo conserva a propósito.

Es el problema de A83 en estado puro: donde lo real está offset, el eje espacial deja
de separar. Lastarria necesita su propio criterio, no el de los nevados.

## Recomendación

**Quitar el piso, y NO "arreglarlo".** Las dos mitades de la recomendación importan:

- **Quitarlo** porque hoy es un no-op que además *miente*: deja `vrp_mw = 0` en
  registros que el dashboard muestra con valor, así que cualquier auditoría que lea ese
  campo mide una cosa distinta de la que el operador ve. Es la misma clase de
  incoherencia que A46 (dos representaciones del mismo concepto, gates que leen la que
  no es). Y no tiene respaldo en los papers.
- **No aplicarlo a `pc.vrp_mw`** —que sería "arreglarlo"— porque cortaría el cráter de
  Láscar e Isluga. El beneficio (tapar el artefacto de los nevados) se consigue mejor
  atacando el artefacto en su raíz, que es el fondo autorreferente, y no con un umbral
  de energía que no distingue de dónde viene esa energía. Es A72: si es artefacto, se
  arregla el algoritmo; un piso de magnitud es un parche que corta por igual señal y
  ruido.

**Cuándo hacerlo**: después de leer el A/B de la corona. Si la corona desinfla el
artefacto de los nevados, el argumento para quitar el piso queda todavía más limpio,
porque desaparece el único efecto colateral útil que hoy tiene.

## Lo que NO hay que concluir

- **No "el piso protege de falsos positivos"**: no protege de nada que se vea, porque
  el dashboard lee `pc.vrp_mw` y ese campo no lo toca.
- **No "hay 761 records suprimidos por el piso"**: en esta ventana son 477 (231 + 246),
  y ninguno está realmente suprimido de la vista.
- **No mover los valores del piso**: el problema no es el número, es que el criterio
  sea de energía. Bajarlo o subirlo no cambia la naturaleza del error.
