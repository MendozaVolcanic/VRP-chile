# A/B de magnitud S125 — resultado

> Criterio fijado **antes** de correr: `docs/S125_AB_MAGNITUD_PREREGISTRO.md`.
> Números recomputados y persistidos por
> `experiments/_s125_magnitud/02_veredicto_ab.py` → `02_veredicto.json`
> (regla S91: ninguno transcrito a mano).
>
> Tag defensivo: `pre-s125-magnitud-ab`. **No se tocó `mirova_equivalent`.**

## Veredicto: NO ADOPTAR todavía — 2 de 4 criterios fallan

| criterio pre-registrado | resultado |
|---|---|
| 1. Más volcanes dentro de banda | **NO CUMPLE** — 3/4 antes, 3/4 después |
| 2. Ningún volcán en banda se sale (control interno) | **CUMPLE** |
| 3. IC bootstrap que **no** se solapen | **NO CUMPLE** — se solapan en los 4 |
| 4. Cero falsos negativos nuevos | **CUMPLE** |

Piloto: 4 volcanes, 25-jun a 24-ago, brazo **C** (las dos reducciones apagadas +
fondo por corona de Eq. 6 encendido) contra el control.

## Pero el mecanismo es real

| volcán | control | brazo C | IC 95 % control | IC 95 % C | cierra del hueco |
|---|---|---|---|---|---|
| Villarrica | 0,725 | **0,860** | [0,437 – 0,900] | [0,670 – 0,908] | 49 % |
| Planchón-Peteroa | 1,067 | 1,100 | [0,828 – 1,425] | [0,921 – 1,633] | (ya sobre 1) |
| Láscar | 0,480 | **0,566** | [0,430 – 0,586] | [0,480 – 0,674] | 17 % |
| Puyehue-Cordón Caulle | 0,734 | **0,878** | [0,526 – 1,018] | [0,645 – 1,133] | 54 % |

**La magnitud sube en los 4 de 4**, en la dirección que predice la hipótesis y
sin perder ninguna detección. Que los cuatro se muevan al mismo lado no es
casualidad estadística: es el efecto esperado de dejar de recortar la suma del
cluster.

Lo que falla no es la dirección sino el **tamaño y la certeza**:

- Cierra entre el 17 % y el 54 % del hueco, no el hueco entero.
- Con n de 15 a 57 noches, los intervalos son anchos y se solapan con el control.
  Por el criterio propio, eso no decide.
- **Láscar sigue muy fuera de banda** (0,566 contra un piso de 0,7) y es el de
  mejor muestra (57 noches). Ahí hay otra cosa además de las dos reducciones.

## La distribución, no la mediana (T3)

La mediana esconde que el problema no es un sesgo parejo:

| volcán | control (suben/bajan) | rango | brazo C |
|---|---|---|---|
| Villarrica | 2 / 13 | 0,03 – 1,18 | 3 / 12, máx **3,73** |
| Planchón-Peteroa | 8 / 7 | 0,52 – 4,40 | 8 / 7, máx **5,10** |
| Láscar | 9 / 48 | 0,051 – **19,1** | 10 / 47, máx **20,8** |
| PCC | 11 / 20 | 0,037 – 3,23 | 13 / 18, máx **5,95** |

Dos lecturas que importan:

1. **Láscar no sub-reporta parejo**: 48 de 57 noches por debajo, pero con
   outliers de hasta 19× por arriba. Son dos poblaciones mezcladas, no un factor
   de escala único. Un ajuste global de magnitud no puede arreglar eso.
2. **El brazo C empuja los máximos hacia arriba** (Villarrica 1,18 → 3,73; PCC
   3,23 → 5,95). Descontar el recorte también destapa las noches donde ya
   sobre-estimábamos. Es coherente con que las dos reducciones nacieron como
   parche a un sesgo real hacia arriba del fondo.

## Qué falta antes de decidir

El piloto probó el paquete completo (R1 + R2 apagadas **y** corona encendida).
No sabemos cuánto aporta cada parte, y eso importa: si el brazo **B** (apagar los
parches sin encender la corona) ya diera lo mismo, la corona sobra.

1. **Correr los brazos A y B** — es lo que el diseño de 4 brazos existe para
   contestar, y sin eso no se puede atribuir el efecto.
2. **Ampliar la muestra** para que los IC decidan: más volcanes y/o ventana más
   larga. Con 15 noches no se separa nada.
3. **Láscar aparte**: su distribución bimodal es un problema distinto del
   recorte de la suma, y no lo resuelve este frente.

## Lo que NO hay que concluir

- No "la corona no sirve": la dirección es consistente en 4/4 y sin FN. Lo que
  no alcanza es la evidencia, no el mecanismo.
- No adoptar "porque va en la dirección correcta": ese fue exactamente el error
  que las auditorías de S124 tumbaron. El criterio se fijó antes y no se cumple.
