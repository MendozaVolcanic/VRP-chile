# Probe del L1B de Nevados de Chillán, 2026-10-18: fondo D25 y selección, sobre K

> Escrito el 2026-10-20 (S157, sesión lateral de la tarea 1.29) **antes de correr**. Sólo lectura: no toca
> `pipeline/` ni los perfiles, no escribe en `data/`. Workflow `.github/workflows/probe-s157-d25-chillan.yml`, 2 jobs,
> grupo de concurrencia propio, autenticación sólo por `EARTHDATA_TOKEN` (A71). El resultado, cuando exista, va en
> `resultado/` con el número de run y lo lee `analizar_probe.py`.

## Por qué

La sesión de magnitud de Chillán (PR #869) separó nuestro déficit contra MIROVA en recorte del tablero (F_rec) y un
resto G que mezcla tres cosas: el **fondo** que restamos (anillo regional de 5 a 25 km contra vecinos, D25), la
**selección** (vecinos tibios del foco que MIROVA sumaría y nosotros no alertamos) y el **área del píxel** (D17). Sin
el L1B sólo pudo acotar el fondo con sensibilidades (vecinos 5 y 10 K más fríos, fondo cero). Este probe mide, en 10
gránulos de la misma mañana con pasadas casi a nadir (05:42 y 06:00) y en el borde del barrido (05:06 a 49° y 06:48 a
68°), lo que hace D25 de verdad y por qué los vecinos tibios quedaron afuera.

## Qué corre

Ver el docstring de `probe_chillan.py`. Por gránulo, en el mismo proceso: control (K tal cual), nulo (camino de D25
encendido con el fondo de hoy), D25 con ventana hasta 7x7 (`h3`, el valor del perfil) y sólo 8 vecinos (`h1`). En
MODIS no hay flag D25 (PREREGISTRO.md §2): se usa el camino opt-in del kernel local que ya existe en
`process_modis`, con la media de temperatura en 3x3 (`kernel3`) y con un envoltorio que promedia radiancia como D25
(`d25_rad`). Y el diagnóstico de selección sobre los vecinos 8-conexos no alertados del cúmulo publicado, con el dNTI,
el dETI y los umbrales del primer pase y del segundo (con K el segundo pase corre sin condicionar, sin compuerta de
temperatura y con los activos fuera de la media: es la etapa que decide; hallazgo H11 del verificador del
pre-registro). `prueba_probe.py` compara la reconstrucción del segundo pase con `second_pass_adjacent` en 20 escenas
sintéticas: 60 píxeles nuevos, 0 discrepancias; reconstruyendo con `min` en lugar de `max`, 1.867.

## Controles (fijados antes)

C-P1 (el control reproduce el record persistido), C-N (el nulo da exactamente el control), C-A (el fondo se llamó en
los brazos y nunca en el control), C-K (k·A reproduce el VRP del píxel más caliente con el anillo). Una pasada que
falla C-P1 se informa y su factor no se interpreta.

## Predicciones (escritas antes de correr; números de `experiments/_s157_magnitud_chillan/a_pasadas_salida.txt`, PR #869)

- **PL-0, del instrumento.** El factor de D25 sobre la suma de nuestros alertados dentro del inner (S_in) no puede
  pasar el techo del fondo cero de #869 (G con fondo 0 sobre G): VIIRS 375 1,26 (05:06), 1,24 (06:00), 1,31 (06:48);
  VIIRS 750 1,55 (05:06), 1,37 (05:42), 1,36 (06:00), 3,2 (06:48); MODIS 2,8 (01:20), 1,86 (07:50), con los mismos
  píxeles. Pasarlo es defecto del probe, no hallazgo.
- **PL-1, VIIRS 375.** D25 sube la magnitud publicada menos de ×1,31 en las cuatro pasadas, así que a las 06:48 la
  razón contra MIROVA queda bajo 0,5 (hoy 0,35). Si sube más, el fondo pesa más de lo que #869 acotó y su techo
  estaba mal calculado.
- **PL-2, VIIRS 750 a las 06:48.** Aun con D25 la razón publicada queda bajo 0,5 (hoy 0,12): el recorte del tablero
  (F_rec 0,42) no depende del fondo.
- **PL-3, regla de lectura de la selección.** Si en una pasada la potencia de los vecinos tibios no alertados
  (sumados restando el anillo) es menor que lo que le falta a D25 para llegar a MIROVA, la selección tampoco puede
  cerrar esa pasada y el resto queda para el área u otro efecto del ángulo (D17). Si es mayor, la selección queda
  como candidata y el probe dice qué prueba (dNTI, dETI o la compuerta de temperatura) dejó afuera a esos vecinos.
  No es un veredicto sobre D17: es lo que este probe puede decir con 10 gránulos de una mañana.

## Lo que este probe NO decide

No adopta nada ni decide el A/B: con 10 gránulos de un volcán y una mañana, es el caso, no la muestra. Alimenta el
criterio de magnitud del pre-registro (`../PREREGISTRO.md`) y la decisión entre D25 y D17 (tareas 1.29 y 1.36).

## Reproducir

```bash
python experiments/_s157_prereg_d25/probe_l1b/prueba_probe.py            # prueba sintética, sin red
python experiments/_s157_prereg_d25/probe_l1b/analizar_probe.py resultado  # lee los JSON del artefacto
```

## Resultado (run 39428997189, 2026-10-20 13:16 UTC, código `b72434243`)

Primer intento, run 39408156347 (10:29 UTC): los 10 gránulos fallaron en la búsqueda con
`{"errors":["An Internal Error has occurred."]}` de CMR (HTTP 500); el script salió con código 2 y el job quedó rojo,
no verde vacío (S141). Segundo intento al volver CMR: **10 de 10 gránulos, los dos jobs en verde**. Artefactos en
`resultado/` (JSON por gránulo y logs); tabla en `analizar_probe_salida.txt` (`analizar_probe.py`, escrito antes de
ver datos) y selección con fondo de vecinos en `seleccion_fondo_vecinos_salida.txt` (enmienda post hoc, declarada).

**Controles.** C-P1, C-N, C-A y C-K en verde en los 10: el control reproduce el record persistido, el nulo da
exactamente el control, el fondo se llamó en cada brazo y nunca en el control, y k·A reproduce el píxel más caliente.

**Qué hace D25 sobre la magnitud publicada** (factor del brazo sobre el control; razón contra MIROVA antes y después):

| gránulo | cenit | factor D25 | razón K → D25 |
|---|---|---|---|
| VIIRS 375, 05:42 | 20,5° | 1,082 | sin vara: MIROVA sólo en `ALERTA_SIN_GEOMETRIA_OCR` (11,03), que no decide |
| VIIRS 375, 06:00 | 22,3° | 1,093 | 0,72 → 0,79 |
| VIIRS 375, 05:06 | 48,6° | 1,094 | 0,46 → 0,50 |
| VIIRS 375, 06:48 | 67,6° | 1,086 | 0,35 → 0,38 |
| VIIRS 750, 05:42 | 20,5° | 1,143 | 0,67 → 0,77 |
| VIIRS 750, 06:00 | 22,3° | 1,130 | 0,72 → 0,81 |
| VIIRS 750, 05:06 | 48,7° | 1,138 | 0,41 → 0,47 |
| VIIRS 750, 06:48 | 67,6° | 2,162 | 0,12 → 0,27 |
| MODIS (análogo `d25_rad`), 07:50 | 23,1° | 1,319 | 0,49 → 0,64 |
| MODIS (análogo `d25_rad`), 01:20 | 37,6° | 2,449 | 0,24 → 0,59 |

**Contra las predicciones.**
- **PL-0 (instrumento): se cumple.** Ningún factor sobre la suma de alertados pasa el techo del fondo cero de #869 (el
  más cercano, VIIRS 750 05:06: 1,21 contra 1,55).
- **PL-1 (VIIRS 375 sube menos de ×1,31): se cumple**, con margen: ×1,08 a 1,09 en las cuatro pasadas, sin
  dependencia con el cenit. A las 06:48 la razón queda en 0,38, bajo 0,5.
- **PL-2 (VIIRS 750 06:48 queda bajo 0,5): se cumple** (0,27), aunque D25 más que duplica esa pasada: sus píxeles
  tienen poco exceso (276 a 288 K) y el fondo pesa.
- **PL-3 (selección).** Los vecinos 8-conexos no alertados del cúmulo están entre 261 y 269 K, de 6 a 12 K **más
  fríos** que el anillo (272 a 277 K): es la cumbre nevada alrededor del cráter. Ninguno pasa los Tests 2 y 3 del
  segundo pase. Con el anillo, su potencia es 0 en los 10. Con el fondo de los vecinos (post hoc, cota generosa que
  supone que MIROVA los alerta a todos), 0,06 a 0,70 MW, contra 2 a 17 MW que faltan. **La selección no cierra
  ninguna pasada**: según la regla pre-registrada, lo que queda (sobre todo en las oblicuas: a las 06:48 faltan 16 MW
  en VIIRS 375 y 17 en VIIRS 750 después de D25) va al área u otro efecto del ángulo (D17, tarea 1.36) o a la
  saturación de I4 (#869, sin verificar).

**Para las decisiones del pre-registro.**
- **§8 b, ventana de vecinos: `h1` y `h3` dan magnitudes idénticas en los 10 gránulos** (los píxeles alertados siempre
  tienen vecinos no alertados a 1 píxel). Por la regla del §8 b, **sólo D**.
- **§8 c, MODIS:** el análogo de D25 sube la magnitud de Chillán ×1,32 y ×2,45 (razón 0,49 → 0,64 y 0,24 → 0,59), y
  el kernel 3x3 en temperatura que ya existe en `process_modis` da lo mismo a 0,1 % (`kernel3` contra `d25_rad`). En
  MODIS, D25 sí movería la magnitud de Chillán; escribir el flag es decisión de Nicolás (A45).

**Lo que no dice.** Diez gránulos de una mañana de un volcán: es el caso, no la muestra. El factor de D25 sobre los
focos débiles de otros volcanes, que es donde puede pasarse, lo mide el A/B.
