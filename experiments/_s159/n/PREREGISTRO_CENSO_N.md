# Pre-registro del censo de F en negativos limpios (S159, frente N, adenda al PREREGISTRO_N.md)

> Escrito y commiteado ANTES de despachar el censo. Aprobado por Nicolás el 2026-10-21: «Sí: despacha el censo de ~120
> pasadas (los 60 cúmulos de cumbre en 0 MW, los 59 far e Isluga 10-12) para cerrar el efecto de F en negativos, con
> el mismo workflow de sólo lectura.» Origen: `verificador/INFORME.md`, afirmación 1, que refutó el estimador
> ponderado de F (152,3 encendidos estimados contra un techo físico de 119).

## Población del censo (`06_censo.py`, salida `06_censo_salida.txt`, lista `objetivos_censo.json`)

Sobre `poblacion_completa.json` sin el 2026-10-18 ni el 19, con las definiciones del verificador (`v3`, `v5`):

| clase | definición | n |
|---|---|---|
| cumbre_0mw | negativo limpio, producción no publica, `distance_class` summit, `pc.vrp_mw` 0,0 | 60 |
| far | negativo limpio, producción no publica, `distance_class` far | 59 |
| isluga_1012 | Isluga 2026-10-12 05:48 (única pasada de Isluga ese día; alerta de MIROVA bajo 1 MW, cúmulo de cumbre en 0,0 MW, SIN DATO en el lote) | 1 |
| reintento_1012 | Chillán 2026-10-12 05:18 (protegida) y 05:54: las otras SIN DATO del mismo día; reintento declarado, fuera del conteo de negativos | 2 |

Lectura de «Isluga 10-12»: no es ambigua (una sola pasada); la lectura inclusiva agrega sólo los dos reintentos de
Chillán del mismo día, que no cambian el conteo de negativos.

## Qué cuenta como encendido

- «Publica» = el predicado del tablero ejecutado con node desde `frontend/index.html` (`banco_paridad.correr_node`)
  sobre el record que escribe `store.append_record` para el brazo; **el mismo para K, C, F y FC**.
- Negativo **encendido por F** = F publica y K no. **Apagado** = K publica y F no.
- Control antes de leer: K tiene que publicar igual que producción (`pub_prod`) y con el mismo `pc.vrp_mw` a 0,001 MW
  en todas las pasadas ok del censo; F tiene que dar la misma detección que K (mismo `n_hot` y mismo número de píxeles
  del cúmulo). Si F cambia la detección en alguna pasada, la premisa del techo cae y se dice.

## Qué reemplaza

El resultado **reemplaza al estimador ponderado de F en esa población**: los negativos que F enciende se cuentan, no se
estiman. Fuera del censo, los 5.303 negativos sin ningún píxel alertado no pueden encenderse con F (F no cambia la
detección, premisa medida en 391 de 391 y que se vuelve a medir aquí), y los 54 que producción publica siguen
publicados con F (censo del lote, 54 de 54).

`ΔE_F (censo) = encendidos_F(cumbre_0mw + far) − apagados_F(neg_pub) − alertas bajo 1 MW ganadas + perdidas`, con las
ganadas = 48 del lote (censo de `pos_nopub`) más Isluga 2026-10-12 si F la publica, y las perdidas = 0 (0 en el censo de
protegidas y 0 de 36 en la muestra de `pos_resto`; esta última parte sigue siendo muestra, se declara). Denominador de
negativos: 5.476 de la población sin el 18 y 19 de octubre. Las pasadas del censo que queden SIN DATO se informan aparte
con su clase y ΔE se da como rango (como si F las encendiera todas y ninguna).

## Predicción del verificador (para comparar después, no es criterio)

Si F publica todo cúmulo de cumbre en 0,0 MW (55 de 55 en el lote): 60 encendidos en `cumbre_0mw`, ΔE ≈ +11 (con 49
ganadas); cota baja de la tasa (Clopper-Pearson) 32 encendidos, ΔE ≈ −16; los 59 `far`: SIN DATO, de 0 a +59, techo
de ΔE +71.

## Oráculo

Corre sin costo en las mismas pasadas. Se informa **aparte** y con el predicado del tablero aplicado a un record
sintético armado desde la salida del oráculo (`primary_cluster` con VRP, número de píxeles y distancia del centroide de
los alertados al centro de la grilla; `distance_class` summit si esa distancia es a lo más `inner_radius_km`;
`t_max_k` = temperatura de brillo M13 del alertado más radiante; sin `store`). No entra al veredicto de F.
