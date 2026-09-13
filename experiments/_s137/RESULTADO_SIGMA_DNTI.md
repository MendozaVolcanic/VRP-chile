# S137 · La banda 21 fabrica el primer paso de MODIS: resultado del probe de sigma del dNTI

> Run 34706563697, 84 pares por granule (Láscar 40, Villarrica 44), pasadas nocturnas del 12 al
> 31 de agosto de 2026, cero fallas. Todos los números salen de `out_sigma/report.txt` y
> `out_sigma/sigma_dnti_4brazos.json` (regla S91). Script: `sigma_dnti_4brazos.py`.

## El fenómeno, primero

La banda 21 de MODIS es la de **ganancia baja**: está pensada para no saturarse sobre lava y llega
hasta unos 500 K. De noche, sobre roca y nieve a 250-270 K, trabaja en el fondo de su escala,
donde cada escalón digital es grueso. Ese escalonado aparece en la imagen como una textura
aleatoria de píxel a píxel, sin ningún significado físico.

El dNTI es justamente un detector de textura de píxel a píxel: le resta a cada píxel el promedio de
sus ocho vecinos. Sobre la banda 21 fría, entonces, amplifica el ruido de cuantización. La banda 22
mira la misma ventana espectral con **ganancia alta**, y su resolución fina está justo en ese rango
frío. El paper usa la 22 como primaria (`documentacion/sp426.5.pdf`, p. 3, banda L21ok: la 21 sólo
entra donde la 22 satura). Nosotros hacemos lo contrario.

## Lo medido

Medianas por volcán. "Veces C1" es cuánto supera el contraste `mu + 5 sigma` al piso de 0,003.
"1er paso" son los píxeles que pasan los Tests 2 y 3 en la escena.

| volcán | brazo | sigma dNTI | veces C1 | caída de sigma | 1er paso | escenas con 1er paso |
|---|---|---|---|---|---|---|
| Láscar | base (hoy) | 0,00790 | 13,2 | 1,00 | 62 | 39 de 40 |
| Láscar | banda 22 | 0,00169 | 2,8 | **4,69** | **0** | **1 de 40** |
| Láscar | remuestreo | 0,00894 | 14,9 | 0,88 | 57 | |
| Láscar | ambos | 0,00192 | 3,2 | 4,12 | 0 | |
| Villarrica | base (hoy) | 0,00705 | 11,8 | 1,00 | 54,5 | 44 de 44 |
| Villarrica | banda 22 | 0,00203 | 3,4 | **3,48** | **0** | **3 de 44** |
| Villarrica | remuestreo | 0,00812 | 13,5 | 0,87 | 50 | |
| Villarrica | ambos | 0,00235 | 3,9 | 3,00 | 0 | |

Control de que el instrumento no está roto: con banda 22 los 84 pares dan sigma finito, sin nulos;
la media del dNTI sigue en cero; y el NTI máximo se corre sólo una centésima (Láscar de -0,917 a
-0,928), que es lo esperable al cambiar de banda y no una escena vacía.

**Lectura.** Hoy, en prácticamente todas las escenas nocturnas de estos dos volcanes, unos 55 a 60
píxeles superan el piso de 0,003 en dNTI y en dETI a la vez. Con la banda del paper, esos píxeles
desaparecen en 80 de 84 escenas. Lo que los producía era la textura de la banda 21.

## Lo que esto refuta

1. **S136, "la banda 22 ofrece un factor 1,3 a 1,8, insuficiente contra 11,7".** Ese factor era el
   sigma del **fondo BT** que midió S133, no el sigma del **dNTI** que gobierna los Tests 2 y 3. Medido
   sobre el objeto correcto, la caída es 3,5 a 4,7. Es A93: el instrumento medía otra cosa.
2. **S136, "la banda 22 no puede mover la detección de MODIS".** Falso, **incluso bajo la conectiva
   `min` de hoy**. El argumento sólo miró el umbral (que bajo `min` es el piso y no depende de sigma)
   y no los valores que lo cruzan: con la banda 22 son los propios dNTI del ruido los que caen bajo el
   piso. El primer paso pasa de unos 60 píxeles a cero.
3. **Mi hipótesis del remuestreo.** Refutada. Remuestrear sube el sigma un 13-15 % y casi no toca el
   primer paso. No es palanca.
4. **Mi hipótesis de que la contradicción del paper se disuelve.** Sólo en parte. Con la banda 22 el
   contraste queda 2,8 a 3,9 veces el piso: la brecha entre `min` y `max` baja de unas 12 veces a
   unas 3, pero no desaparece.

Y una aparente contradicción que **no** es tal: S133 escribió que con la banda 22 "la detección casi
no se movió". Su criterio contaba cambios en `triggered_test1` (`experiments/_s133/analizar_ab_b22.py`,
l. 253-262), que es el camino del Test 1 integrado, sobre MIR absoluto. Nunca miró el primer paso de
los Tests 2 y 3, que es donde está el efecto.

## Lo que esto NO dice

- **Si todo lo que desaparece era ruido.** Los cúmulos publicados también caen: en Láscar de 40 a 9
  escenas con cúmulo, en Villarrica de 44 a 8. Eso puede ser curar la sobre-detección o perder señal
  real, y esta ventana no lo distingue: MIROVA publicó **una** alerta MODIS en Láscar (21 de agosto,
  0,4 MW) y **ninguna** en Villarrica entre el 12 y el 31 de agosto. Es el mismo límite que dejó
  indeciso el A/B de S133.
- **Que la configuración sea la de producción.** El probe llama `calculate_vrp` con
  `lbg_global_compatible=False` y `local_kernel_bg_compatible=False` en los cuatro brazos. La
  comparación pareada vale; los números absolutos del brazo base pueden no coincidir con los records
  publicados.
- **Nada sobre VIIRS.** La banda 22 es de MODIS.

## Lo que corresponde

El juez es la **batería del Apéndice A**, que es MODIS y trae seis escenas donde el autor detecta y
tres donde deliberadamente no. Su criterio ya está fijado desde S136 y no se mueve: un cambio sirve
si y sólo si **conserva los 6 positivos y cura los 3 negativos**.

Brazos a correr: banda 22 con la fórmula (`min`) y banda 22 con la prosa (`max`). Hoy la fórmula da
6 de 6 y 0 de 3, y la prosa 2 de 6 y 3 de 3.

Nota para leerla: el control de validez de la batería exige que el NTI de alguna pasada caiga a
±0,06 del que da el paper. El corrimiento por cambiar de banda es de una centésima, así que el
control sigue siendo aplicable.
