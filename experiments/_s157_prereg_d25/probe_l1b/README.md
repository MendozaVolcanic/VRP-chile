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
(`d25_rad`). Y el diagnóstico de selección sobre los vecinos 8-conexos no alertados del cúmulo publicado.

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
