# El 2×2 de la corona Eq.6 — veredicto, y la celda que nadie había corrido

> Números de `experiments/_s126_corona/01_veredicto.py` → `01_veredicto.json` (S91).
> Criterios fijados **antes** de correr en `docs/S126_CORONA_PREREGISTRO.md`. No se
> tocaron después de ver los resultados.
>
> Ventana 2026-06-25 a 2026-08-24, 5 volcanes, VIIRS 375 m. Un par por noche, máximo de
> ambos lados. 22 alertas diurnas de MIROVA descartadas (A76).

## Primero: el experimento por fin midió lo que decía medir

El A/B salió **inconcluso dos veces**. La segunda, la corona corría en 1.179 records y sólo
movía el número publicado en **15**, porque `apply_single_pixel_mode` la revertía con los
VRP por píxel del fondo viejo. Arreglado en #546 y **verificado sobre los datos nuevos**:

| | antes del fix | ahora |
|---|---|---|
| corona corrió (no degradada) | 1.179 | 1.179 |
| **cambió `pc.vrp_mw`** | **15** | **925** |
| de los que cambian, con `single_pixel_mode=True` | 0 | **910** |

Los 910 son exactamente la población que antes quedaba anulada. Y la corona **nunca
degradó**: 0 de 2.179 records cayeron al fondo regional, así que el fallback explícito no
se usó ni una vez.

## Veredicto: **NO ADOPTAR** el brazo corona

| volcán | n | control | **corona** | ctx_off | corona+ctx_off |
|---|---|---|---|---|---|
| Villarrica | 8 | 0,832 ✓ | 0,877 ✓ | 1,315 ✓ | 0,912 ✓ |
| Planchón-Peteroa | 13 | 1,036 ✓ | 1,000 ✓ | 6,636 ✗ | 2,631 ✗ |
| Láscar | 36 | 0,501 ✗ | 0,569 ✗ | 0,635 ✗ | **1,242 ✓** |
| Puyehue-Cordón Caulle | 22 | 0,728 ✓ | 0,726 ✓ | 1,141 ✓ | 1,036 ✓ |
| Nevados de Chillán | **3** | 1,543 ✗ | 1,167 ✓ | — | 16,467 ✗ |
| **volcanes en banda** | | **3/5** | **4/5** | 2/5 | 3/5 |

| criterio pre-registrado | resultado |
|---|---|
| 1. más volcanes en banda y ninguno se sale | **CUMPLE** (3/5 → 4/5, cero salidas) |
| 2. Villarrica **baja** la magnitud | **NO CUMPLE** (0,832 → 0,877) |
| 3. Láscar: 0 detecciones perdidas y caída ≤ 20 % | **CUMPLE** |
| 4. el evento NdC 06-16 sigue disparando (A79) | CUMPLE — *pero ver abajo* |
| 5. cero detecciones perdidas en total | **NO CUMPLE** (8) |
| 6. MODIS y V750 no se mueven | **CUMPLE** (0 movidos) |

**El veredicto se lee, no se interpreta.** Falla dos criterios escritos de antemano, así
que es NO ADOPTAR. Lo que sigue es contexto para decidir si alguno de esos criterios
merece revisarse — lo cual sería un **cambio de criterio explícito y documentado**, no una
lectura distinta de los mismos números.

## Los dos criterios que fallan, dimensionados

**Criterio 2 — Villarrica sube 0,045 en vez de bajar.** El criterio existía porque S126
estableció que la magnitud de Villarrica es **artefacto**: mide a 2,74 km del cráter
incluso en noches que MIROVA confirma, con el píxel 4,74 K *más frío* que el fondo. La
corona no lo desinfla; lo mueve 5 % hacia arriba. Ambos valores están dentro de la banda,
así que el efecto práctico es nulo — pero la corona **no resuelve el frente de Villarrica**,
que era una de las dos cosas que se esperaba de ella.

**Criterio 5 — 8 detecciones perdidas sobre 2.179 (0,37 %).** Desglosadas:

| volcán | noches | VRP del control | n_píxeles | ¿MIROVA confirma esa noche? |
|---|---|---|---|---|
| Villarrica | 2 | 0,021 · 0,027 | 1 | **no** |
| Planchón-Peteroa | 3 | 0,034 · 0,041 · 0,042 | 1 | **no** |
| Láscar | 1 | 0,040 | 1 | **no** |
| Nevados de Chillán | 2 | 0,033 · 0,035 | 1 | **no** |

Las ocho son **clústeres de un solo píxel, entre 0,021 y 0,042 MW, y ninguna cae en una
noche con contraparte en MIROVA**. Mecánicamente esto es la corona **haciendo exactamente
lo que se diseñó**: una fluctuación de terreno tiene vecinos a su misma temperatura, da
ΔL ≈ 0 y se desploma. No es señal volcánica que se pierde.

Aun así el criterio decía **cero**, y el pre-registro existe justamente para que un
resultado no se reacomode después de verlo.

## Dos cosas que hay que decir aunque incomoden

**El criterio 4 pasa por empate en cero.** El evento de NdC del 16-jun **no dispara en
ninguno de los dos brazos** (`dispara_control: false`, `dispara_corona: false`). O sea el
canario de A79 no está protegiendo nada: la corona no lo rompe porque ya estaba roto. Leer
ese CUMPLE como «la corona preserva el evento» sería falso.

**La predicción del pre-registro sobre Láscar se equivocó.** S126 anticipó que la corona
sola *«probablemente falle su propio canario»*, bajándole la magnitud ~20 % a un volcán al
que ya le falta. Lo contrario: Láscar **sube** 13,6 % (0,501 → 0,569) y **gana** 3
detecciones (377 → 380). La estimación read-only que daba corona/hoy = 0,717 no se
sostuvo cuando el cálculo corrió de verdad. Es A18 otra vez: el preview no predice el
reproceso real.

## La celda que nadie había corrido: el mecanismo de Láscar **se confirma**

Ésta es la información nueva de verdad. S126 razonó que bajo un fondo **local** un píxel
de terreno se autocancela, así que la corona *vuelve seguro incluir más píxeles* — que es
justo lo que a Láscar le falta (necesita ~2 y sumamos 1).

**Se cumple, y con margen**: Láscar pasa de **0,501 a 1,242** y entra en banda por primera
vez en todo el frente de magnitud. El mecanismo predicho era exacto.

**Pero no generaliza, y ahí está el problema:**

- **Planchón-Peteroa**: el filtro apagado lo dispara a 6,636; la corona lo amortigua a
  2,631 — dos tercios del daño, pero sigue fuera de banda. Su problema no es el fondo
  autorreferente sino el complejo multi-cráter (A22: el pipeline oscila entre aislar el
  cráter Peteroa y capturar el halo regional).
- **Nevados de Chillán**: 16,467, pero con **n = 3**. Es una muestra demasiado chica para
  concluir nada; se reporta y no se usa para decidir.

O sea: la corona **sí es el discriminante espacial que se pensó**, y cura a Láscar cuando
se le da el segundo píxel. Lo que no hace es curar a los volcanes cuyo exceso viene de otro
mecanismo.

## Lo que esto deja

1. **La corona sola no se adopta**, pero es el único brazo que **sube** el conteo de
   volcanes en banda (3/5 → 4/5) sin sacar a ninguno. Si Nicolás decide revisar el
   criterio 5 —cuya violación son 8 fluctuaciones de un píxel sin contraparte MIROVA— o
   el 2 —cuyo incumplimiento es un 5 % dentro de banda—, sería un cambio de criterio
   explícito y no una relectura.
2. **Láscar tiene por fin un camino**: corona + filtro contextual apagado. Falta acotarlo
   para que no rompa a Planchón, y eso pide separar los dos mecanismos, no un umbral más.
3. **Villarrica sigue abierta y la corona no la toca.** Su número no viene del cráter
   (S126: 2,8 km, píxel más frío que el fondo, VIIRS 375 no ve el lava lake). Es artefacto
   y por A72 se arregla en el algoritmo — pero no con esta palanca.
4. **El piso VRP ya puede decidirse**: S126 lo condicionó a leer este A/B. La corona no
   desinfló el artefacto de los nevados lo suficiente como para cambiar el análisis, así
   que la recomendación de S126 —quitarlo, y NO aplicarlo a `pc.vrp_mw`— sigue en pie.

## Lo que NO hay que concluir

- **No «la corona no sirve»**: mueve 925 records, nunca degrada, mejora el conteo en banda
  y cura a Láscar en combinación. Falla dos criterios, que no es lo mismo.
- **No «hay que apagar el filtro contextual»**: solo lo aguanta Láscar. En Planchón sigue
  siendo lo único que impide el 6,6×.
- **No usar Nevados de Chillán para decidir**: n = 3.
