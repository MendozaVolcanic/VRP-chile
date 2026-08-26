# "¿Hay problemas con nuestra réplica?" — sí, y por qué no los veíamos (S124)

Pregunta de Nicolás: *"si nuestros resultados son diferentes al reportar el
máximo, ¿hay problemas con la réplica? ¿pero no teníamos paridad? ¿qué es lo que
no estamos viendo?"*

Scripts reproducibles: `experiments/_s124_gap_decomp/0{1,2,3}_*.py`

## Respuesta: sí hay un problema, y la métrica de paridad lo tapaba

### Paso 1 — La banda que usamos no discrimina

`~memory/reference_paridad_mirova_umbrales.md` define **dos** bandas distintas:

| métrica | tolerable | razón documentada |
|---|---|---|
| ratio de **una detección** | 0,5 – 2,0 | el ±30 % de error que MIROVA declara |
| ratio **mediano por volcán** | **0,7 – 1,4** | *"más estricto porque mide tendencia central, no outliers. Mediana 2.0 = sesgo sistemático, no ruido"* |

**`scripts/auto_audit_weekly.py:80` aplica la banda floja (0,5-2,0) a la MEDIANA.**
Una banda 4× de ancho donde el criterio propio del proyecto pide 2×. Por eso dos
algoritmos que difieren 17 % (0,71 vs 0,83) "pasan" los dos.

### Paso 2 — Con la banda correcta, 4 de 11 están fuera, y todos sub-reportan

| volcán | n | vent_anchored | banda [0,7-1,4] |
|---|---|---|---|
| Lascar | 228 | 0,62 | **FUERA** |
| Isluga | 131 | 0,61 | **FUERA** |
| Lastarria | 95 | 0,47 | **FUERA** |
| Llaima | 2 | 0,36 | **FUERA** (n insuficiente) |
| Tupungatito | 76 | 0,74 | al borde |
| GLOBAL | 755 | **0,71** | **al borde** |

Los tres volcanes con más observaciones sub-reportan **35-50 %**. Con n de 95 a
228 noches, eso no es ruido.

### Paso 3 — NO es la selección de cluster (descartado con datos)

| volcán | primary_cluster | mejor cluster | **escena COMPLETA** |
|---|---|---|---|
| Lascar | 0,62 | 0,75 | **0,80** |
| Isluga | 0,61 | 0,68 | **0,76** |
| Lastarria | 0,47 | 0,54 | **0,69** |
| PlanchonPeteroa | 0,93 | 1,06 | 1,07 |
| Chaiten | 1,18 | 1,68 | 1,86 |

**Sumando toda la escena seguimos 20-31 % por debajo.** No perdemos VRP al
atribuirlo: no lo detectamos.

### Paso 4 — El déficit son PÍXELES FALTANTES

Ratio escena/MIROVA según cuántos píxeles anómalos detectamos esa noche:

| píxeles | Lascar | Isluga | Lastarria |
|---|---|---|---|
| 1 px | 0,59 (n=76) | 0,65 (n=63) | 0,41 (n=55) |
| 2 px | 0,69 (n=76) | 0,66 (n=36) | 1,15 (n=19) |
| **3-5 px** | **0,93** (n=32) | **0,91** (n=14) | **1,47** (n=19) |
| 6+ px | **99×** (n=44) | **12×** (n=18) | 2,4× (n=2) |

Monótono y consistente en los tres. **Cuando alcanzamos 3-5 píxeles estamos en
paridad. Cuando solo agarramos 1, medimos la mitad.**

### Paso 5 — En esas noches sólo UN píxel pasa el gate

Diagnósticos de las noches de 1 píxel (n = 273 / 287 / 181):

| campo | Lascar | Isluga | Lastarria |
|---|---|---|---|
| `diag_n_dnti_ctx_path` | 1 | 1 | 1 |
| `diag_n_bt_path` | 0 | 0 | 0 |
| `diag_n_nti_path` | 0 | 0 | 0 |
| `diag_n_second_pass_recapture` | 0 | 0 | 0 |
| `single_pixel_mode` activo | 259/273 | 287/287 | 181/181 |

El píxel entra **exclusivamente por el path dNTI contextual**, ningún vecino se
recaptura, y el pipeline pasa a `single_pixel_mode`. No es que algo recorte los
píxeles: **nunca disparan**.

## El hallazgo de fondo: la falla es BIMODAL y la mediana la promedia

- **Noches débiles (1-2 px, la mayoría)**: sub-integramos → 0,4-0,7.
- **Noches de campo difuso (6+ px)**: sobre-integramos → **12× a 99×**
  (el drift D9/A23 de path D, ya catalogado).
- **En medio (3-5 px)**: paridad real.

La mediana per-volcán de 0,62 no describe "estamos un poco bajos": describe el
promedio de **dos modos de falla opuestos**. Una banda de 4× de ancho aplicada a
esa mediana no podía detectarlo. Eso es lo que no estábamos viendo.

## Interpretación física

La fuente del cráter es real y está repartida en 2-4 píxeles. En las noches más
débiles sólo el núcleo supera el umbral y el resto queda apenas por debajo;
MIROVA integra ese halo y nosotros no. Cuando la señal sube lo suficiente para
que 3-5 píxeles crucen el umbral, coincidimos con MIROVA — que es exactamente lo
que muestra la tabla del Paso 4, y es la mejor evidencia de que la fórmula y los
coeficientes están bien (S14 los calibró a ±0,17 % contra OSF).

**El problema está en el gate de detección, no en el cálculo de VRP.** Coincide
con lo que la memoria de paridad ya anticipaba: *"si superamos la banda, el
problema NO es la fórmula/coeficiente — es detección: qué píxeles pasan el gate"*.

## Qué queda por establecer (no concluido acá)

1. **Por qué MIROVA sí captura ese halo.** Hipótesis a distinguir: (a) su umbral
   contextual es menos estricto en régimen débil; (b) integra un ROI fijo en vez
   de píxeles individuales; (c) su second-pass de adyacencia es más permisivo que
   el nuestro (que recaptura 0 en estas noches).
2. **Si tocar el gate para curar el modo débil empeora el modo difuso** — son
   los dos extremos del mismo parámetro. Cualquier cambio necesita A/B con
   criterio pre-registrado **estratificado por régimen** (A83), midiendo ambos
   modos a la vez.
3. **Llaima** (0,36 con n=2) no es concluyente; hace falta ventana más larga.

## Acciones inmediatas propuestas

| # | acción | riesgo |
|---|---|---|
| 1 | Corregir la banda de la mediana en `auto_audit_weekly.py`: [0,7-1,4] | nulo — es el criterio propio documentado |
| 2 | Reportar el ratio **estratificado por conteo de píxeles**, no sólo la mediana | nulo — es visibilidad |
| 3 | Investigar el gate en régimen débil (papers primero) | A45 si termina en cambio |

La (1) y la (2) son las que evitan que esto se vuelva a esconder. **No proponer
todavía ningún cambio de umbral**: primero hay que entender qué hace MIROVA en el
régimen débil, y cualquier movida ahí toca los dos modos a la vez.
