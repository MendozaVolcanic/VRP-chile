# S197: caja sensible de MODIS centrada en el cráter o en la grilla (pre-registro, escrito antes de correr)

Pedido de Nicolás (2026-11-23, respuesta a «¿acepto la pérdida de Chaitén 19-nov?»): «Medir la caja primero». Origen:
issue #1106 y `experiments/_s197_1106/INFORME.md` (PR #1107): en Chaitén MODIS 2026-11-19 02:30 la celda tibia que
parece haber alertado MIROVA queda una columna fuera de la caja sensible, que en MODIS está centrada en la grilla y no
en el cráter.

## El fenómeno y la pregunta

La caja sensible (5 × 5 km, umbral μ + 5σ con piso 0,003) es donde el detector busca calor débil; fuera de ella pide
μ + 10σ con piso 0,02. Si el cráter no está en la celda central de la grilla de MIROVA, una caja centrada en la grilla
deja parte del edificio en la zona conservadora y una parte del terreno sin volcán en la sensible. La pregunta es si
centrar la caja de MODIS en el cráter acerca la vía a lo que publica MIROVA, sin publicar más donde MIROVA no vio nada.

## Diseño

- Muestra: las 330 pasadas nocturnas MODIS procesadas por el A/B de D36 (run 44016042341, elegidas antes de mirar con
  semilla 190 en `experiments/_s190_d36/p1_seleccion.py`; 11 Tier A, desde el 2026-03-01 hasta el 2026-11-16), con sus
  recortes nativos (artefactos s190-d36-p1-0, 1 y 2, vigentes hasta el 2026-12-17). Local, sin red.
- Brazos: **A** = la vía de producción sin tocar (`calcular_vrp_granulo`, caja «def»); **C** = la misma vía con
  `tipo_roi="crater"` (la caja de 5 × 5 movida a la celda del cráter; `caja_roi`, sin código nuevo de detección).
- Volcanes donde la celda del cráter es la central (Copahue, Isluga, Lastarria, Llaima, Nevados de Chillán): C es A por
  construcción. Donde no (Cordón Caulle a 7 celdas, Tupungatito, Planchón-Peteroa, Villarrica, Láscar y Chaitén): C
  puede cambiar.

## Controles (si fallan, el resultado no se lee)

1. A local igual al brazo A guardado por el run de Actions (mismos campos de `slim`) en todas las pasadas, o las
   diferencias contadas y explicadas (A50 de S152: el orden de empates puede cambiar entre CPU).
2. C igual a A en las 5 volcanes de celda central, en todas sus pasadas.
3. El instrumento puede dar distinto de cero: en Chaitén 2026-11-19 02:30 (fuera de la muestra) la celda decisiva de C
   es la (27, 22) y la de A la (26, 23) (ya visto en `experiments/_s197_1106/cajas_5_pasadas_salida.txt`).

## Métricas (las de D36, `experiments/_s190_d36/p1_analisis.py`, con los brazos A y C)

- M1: noches con alerta protegida de MIROVA (≥ 1 MW) acertadas, y M1 con todas las alertas.
- M3: publicaciones en las pasadas negativas (MIROVA en 0), el costo.
- M4: pasadas cuyo valor publicado cambia, por volcán, con nuevo desde cero y a cero.

## Regla de decisión, fijada antes de ver datos

- **C mejora** si gana al menos una noche de M1 (todas), no pierde ninguna noche protegida y no agrega publicaciones
  en negativas. Entonces la recomendación a Nicolás es un A/B en Actions más grande antes de tocar producción (A45).
- **C empata** (no cambia M1 ni M3): no hay razón para mover la caja; se recomienda aceptar la pérdida de Chaitén.
- **C cuesta** (pierde protegidas o agrega negativas): no mover la caja; se informa el costo y se recomienda aceptar
  la pérdida.
- Cualquier otro caso (gana y cuesta) se informa con el detalle por volcán y la decisión es de Nicolás.
