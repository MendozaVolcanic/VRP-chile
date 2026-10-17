# Selector de noche o rango en el tablero (opción B), diseño y plan

Aprobado por Nicolás el 2026-10-17 («Sí, implementa la opción B: selector de noche o rango en las tres vistas, clic en
la barra, y el mapa con los mismos filtros y el criterio del gráfico»). Fuente: auditoría del tablero de S153
(`C:\Users\nmend\AppData\Local\Temp\claude\audit_tablero\INFORME.md`, sin versionar).

## Por qué

El geólogo de turno pregunta «¿qué pasó la noche del 1 de octubre en Chillán y dónde?». Hoy el tablero sólo ofrece
ventanas móviles desde «ahora» (24 h a «Todo») en `index.html`, y ventanas fijas en `diario.html` (90 días) y
`mosaico.html` (30 días). Además el mapa del detalle no muestra lo mismo que el gráfico: ignora el conmutador de
sensores y dibuja cualquier record con `vrp_mw > 0`, mientras el gráfico usa el criterio de publicación (`eqVrp`). En
Villarrica, 30 días, hay 18 detecciones que el gráfico cuenta y el mapa no dibuja.

## La unidad: la noche, rotulada en UTC

Una noche chilena (21 a 06 local, UTC−3 o UTC−4) cae entera en una sola fecha UTC, la de la mañana: de 11.584 records
de 100 días, 11.571 están entre 00 y 08 UTC (auditoría §2.1). El selector pide fechas UTC, filtra
`[desde 00:00 UTC, hasta 23:59:59 UTC]` y rotula «16 oct UTC (noche del 15 al 16 en Chile)».

## Diseño

1. **`frontend/periodo.js`, funciones nuevas solamente** (`window.Periodo`, y `module.exports` para probarlo con
   node): leer y escribir el período en la URL (`?dias=N` o `?desde=AAAA-MM-DD&hasta=AAAA-MM-DD`), intervalo en ms,
   filtro de records, si hace falta la historia completa, rótulos, desplazar una noche y fecha UTC de un punto del
   gráfico. Los ayudantes del predicado (`isValidDetection`, `mirovaEqVrp`, etc.) **no se mueven**: `banco_paridad.py`
   y los guards los leen desde `index.html`.
2. **Por defecto se ve lo mismo que hoy**: 30 días en `index.html`, 90 en `diario.html`, 30 en el mini gráfico de
   `mosaico.html`. Sin parámetros en la URL, nada cambia.
3. **`index.html`**: el desplegable gana «Noche o rango…», que muestra dos fechas, «◀ noche» y «noche ▶». El período
   va a la URL con `history.replaceState`. Una franja visible dice el período cuando no es el de por defecto y
   recuerda que las tarjetas, la barra de estado y los iconos del mapa general muestran el **estado actual (48 h)**.
   Si el período sale de los últimos 90 días, se baja la historia completa con el mecanismo que ya existe.
4. **Clic en una barra del gráfico principal**: fija el período a esa noche y redibuja (gráfico, mapa, tabla).
5. **Mapa del detalle con el criterio del gráfico**: dibuja sólo records con `eqVrp(r) > 0` y `isSensorVisible(r)`.
   La capa «Anomalías» del mapa general respeta «Sólo cráter» y muestra la magnitud del tablero (`mirovaEqVrpDisplay`),
   no `r.vrp_mw` (A10).
6. **Rótulos que dicen la verdad**: «máx 30 d» y el tooltip de métricas usan el rótulo del período.
7. **Tabla NRT**: obedece el conmutador de sensores y se redibuja al cambiar «Sólo cráter» y los sensores.
8. **`diario.html`**: selector de rango en la barra superior; reemplaza `WINDOW_DAYS` y los textos «90 d».
9. **`mosaico.html`**: el mini gráfico acepta el período de la URL; el clic de tarjeta pasa a enlace que lleva el
   período a `index.html`; enlaces cruzados entre las tres vistas.

Fuera de este PR (segundo PR): tabla de la última noche por volcán, celular, accesibilidad, preferencias comunes.

## Restricciones

- G8 (`tests/test_guard_declarado_vs_efectivo_s131.py:153`) fija la línea de `isValidDetection` en `index.html`, y el
  `CLAUDE.md` del proyecto la cita: toda línea agregada antes obliga a remapear en el mismo PR
  (`scripts/remapear_citas.py`, A101).
- `tests/test_guard_predicado_tres_vistas_s147.py` y `tests/test_guard_region_s132.py`: no se toca el predicado.
- Verificación en navegador con zona horaria `America/Santiago` (lección del bug de zona horaria, PR #250) y R8 sobre
  la URL pública después del despliegue.

## Plan

1. `periodo.js` con su prueba en node (`tests/test_periodo_js_s153.py`): casos de URL, intervalo, filtro en el borde
   de las 00:00 y 23:59 UTC, rótulos, desplazar y fecha desde un punto del gráfico. La prueba falla antes de escribir
   el módulo.
2. `index.html`: carga del módulo, control, franja, URL, filtro, clic en barra, mapa, capa Anomalías, tabla NRT,
   rótulos. Remapear G8 y la cita del `CLAUDE.md`.
3. `diario.html` y `mosaico.html`.
4. Suite completa; navegador local (`/frontend/`) con zona horaria de Chile: período por defecto idéntico al de hoy,
   noche elegida, clic en barra, URL compartida, mapa contra gráfico en Villarrica.
5. PR, CI, merge; R8 sobre `https://mendozavolcanic.github.io/VRP-chile/`.
