# Pre-registro: D36 punto 1, umbrales nocturnos de MODIS en la vía (S190, 2026-11-17)

Escrito antes de despachar el A/B y antes de ver cualquier resultado de los brazos. La lista de pasadas
(`p1_pasadas.json`) salió de `p1_seleccion.py` con semilla 190 sobre main `13af35186`.

## Pregunta

La vía MODIS usa de noche K1 = -0,7 y piso de dNTI fuera de la cumbre (zonas 0 y 1 de la caja) = 0,02, los números del
`.m` de VIIRS 750. La Tabla 1 de Coppola et al. 2016a (p. 7, leída renderizada en S190) dice para MODIS de noche K1 =
-0,8 y C1 = 0,003 en ROI1 y 0,01 en ROI2. ¿Cuánto cambia lo que publicamos, y nos acerca o nos aleja de MIROVA?

## Brazos (`brazos.py`)

A = vía de hoy (-0,7; 0,02). B = Tabla 1 (-0,8; 0,01). B1 = sólo K1 -0,8. B2 = sólo piso 0,01. Todo lo demás igual.

## Controles (si uno falla, el resultado no se lee)

1. `control_copia_igual`: A == prod en el 100 % de las pasadas procesadas.
2. `probar_local.py` verde en el runner (copia idéntica en 40 escenas sintéticas; el instrumento puede dar distinto de
   cero en B1 y B2).
3. `control_produccion`: prod contra el record guardado. Se informa la proporción igual; una diferencia con otro
   `codigo_sha` no invalida el A/B (A y B corren con el mismo código), pero se dice.

## Métricas (por brazo, total y por volcán; valor publicado = `mirovaEqVrp` del tablero)

- M1 recall de alertas protegidas MODIS de MIROVA (VRP >= 1 MW, nocturnas, consolidado u OCR), por noche (noche =
  fecha UTC de la hora menos 12 h), acierto = alguna pasada MODIS nuestra a ±60 min con valor publicado > 0, sobre las
  pasadas del estrato `mirova`. También para todas las alertas MODIS (> 0 MW).
- M2 razón de magnitud nuestra/MIROVA en la misma pasada (a 10 min o menos, fuente consolidado): mediana y mediana de
  |log razón|.
- M3 sobre-publicación: fracción de pasadas del estrato `negativa` con valor publicado > 0.
- M4 cuánto cambia: pasadas con valor publicado distinto de A, y suma de |Δ valor publicado| en MW, en todos los
  estratos; y en cuántas aparece una alerta nueva lejos de la cumbre (`dc` = far).

## Regla de decisión (fijada antes de mirar)

- **Adoptar B (proponer a Nicolás, con A45 y su sí)** sólo si a la vez: M1 de B no pierde ninguna alerta protegida que
  A acierta y acierta al menos una más; M3 de B no supera a A en más de 1 pasada de 165; mediana de |log razón| de B no
  peor que la de A en más de 0,01.
- **Dejar documentado (no cambiar)** si B cambia el valor publicado en menos del 2 % de las pasadas de los estratos
  `mirova` y `nuestra` juntos y M1 y M3 no cambian: el costo de la divergencia es medible y chico, y se escribe en
  D36 y la ficha con su cifra.
- **Mantener A y documentar el costo** si B pierde alguna protegida o sobre-publica más que el margen.
- Cualquier otro caso: **medir más**, diciendo qué falta.
B1 y B2 sólo atribuyen el efecto a una de las dos piezas; no deciden.

## Límites conocidos antes de correr

- Ventana desde 2026-03-01 (tabla de MIROVA comparable, A119); la referencia MODIS incluye OCR, que no sirve para
  magnitud (M2 usa sólo consolidado).
- La muestra de negativas es de 15 por volcán: una tasa de sobre-publicación de 1 % no se distingue de 0 con n 165.
- Sólo noche: la vía MODIS no tiene records diurnos en los 11 Tier A.
