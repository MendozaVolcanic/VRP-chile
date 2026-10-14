# Loop 1.5: el fondo por vecinos (D25) en VIIRS 750, medido primero sobre lo que hay en disco

Fecha: 2026-10-14. Sólo lectura. No toca `pipeline/` ni el perfil. Nada despachado.

## El fenómeno

En una cumbre nevada, de noche, el píxel de 750 m del cráter queda más frío que la mediana del anillo
regional de 5 a 25 km, que está lleno de valle tibio. El exceso sale negativo, el código lo recorta a cero
y el cráter queda "detectado pero mudo" (0,0 MW). MIROVA (Coppola 2016a, p. 8, ec. 6) resta como fondo la
media de los vecinos inmediatos del píxel alertado. Con ese fondo el cráter se compara con su propio
entorno, y la pregunta es si eso despega a las 28 alertas que hoy perdemos sin despegar también a las
pasadas en que MIROVA no vio nada.

## De dónde salen los 268

`docs/audit_s149/plan_final/VERIFICADOR_MAGNITUD_CERO.md` §5, script
`experiments/_s149_audit/verificador_magnitud_cero/v3_negativos.py`: VIIRS 750, nocturnas, ventana
2026-06-01 a 2026-09-21, negativo limpio (MIROVA listó la pasada como RUTINA con VRP 0 y no alertó esa
noche en ese sensor), cúmulo primario `summit` con `vrp_mw = 0` dentro del inner del tablero.

- `reconstruir_268.py` rehace el cálculo con el arnés, los JSON, la referencia y el `index.html` del
  commit de S149 (`d46b7ec`): **3.118 negativos limpios, 268 en la condición, 28 alertas**, idénticos al
  informe. Con el arnés de hoy da 271 (tres pasadas nuevas en la condición, por el cargador de Loop 0.1,
  #778); las 268 siguen todas dentro. Lista congelada: `lista_268_s149.json` y `pasadas.json`.

## Qué datos hay

- **Los records no guardan a los vecinos.** `anomaly_pixels` trae sólo píxeles alertados (lat, lon,
  dist_km, bt_k, vrp_mw); `diag_L_bg_local_w_m2_sr_um` existe en 21 de los records pero es nulo en los
  271. No hay ninguna temperatura ni radiancia de un vecino no alertado (`techo.json`).
- **No hay granules VIIRS 750 en disco.** Lo único en `experiments/` son dos `.npz` de VIIRS 375 (S104).
- **Ningún artefacto de GitHub sirve**: los probes de vecinos (S141) y las 12 noches (S143) son de
  VIIRS 375, y ningún A/B corrió jamás con `enable_vrp_bg_neighbor_mean_viirs750` encendido (sólo los
  perfiles `_s142_*` encienden el flag, y es el de 375).
- `../mirova-tif-archive` guarda el producto de MIROVA, no nuestras temperaturas: no da los vecinos de
  nuestro píxel.

Conclusión: **la magnitud que D25 le daría a los 268 es SIN MEDIR con lo que hay en disco.**

## Lo que sí se midió (`listar_y_techo.py`, salida en `techo.json` y `listar_y_techo_salida.txt`)

**Techo con el predicado real del tablero** (node sobre `frontend/index.html`): si el fondo nuevo le diera
a cada pasada cualquier magnitud positiva, ¿publica?

| magnitud forzada | de los 268 negativos publican | de las 28 alertas publican |
|---|---|---|
| 0,001 MW | 268 | 28 |
| 0,1 MW | 268 | 28 |
| 1 MW | 268 | 28 |
| 10,5 MW | 161 (corta `isCirrusArtifact`) | 20 |

O sea: bajo 10 MW **el tablero no pone ninguna barrera**. Que D25 haga publicar a un negativo depende sólo
del **signo** del contraste del cráter contra sus vecinos, y ese signo vive en el granule.

**Escala** (conversión determinista con las constantes del pipeline, no una medición de D25): en 206 de
los 271 con píxeles guardados, el píxel del cráter está a una mediana de **1,81 K bajo el anillo** (201 de
206 bajo o igual). Un kelvin de exceso en un píxel de 750 m vale **~0,08 MW**, así que bastaría que los
vecinos estuvieran 2 a 3 K más fríos que el cráter para darle 0,2 MW, el orden de lo que MIROVA publica en
las 28 alertas (0,2 a 0,75 MW).

**Controles** (fijados en el docstring antes de mirar):
- C1 identidad del predicado: pasa.
- C2 la población sin tocar publica 0 de 299: pasa.
- C3 el campo que se muta es el que decide: en las 814 pasadas que hoy publican, intactas publican 814 y con
  la magnitud en cero publican 0: pasa.
- C4 la población de hoy contiene exactamente a las 268 y 28 de S149: pasa.

`control_sintetico.py` valida la cadena del fondo (la función del pipeline más la variante de nube de
`variantes.py`) con cinco casos de respuesta conocida (nulo uniforme, cráter frío, nube a medias, todo
nublado cae al respaldo, formas distintas fallan): los cinco pasan.

## El probe propuesto (escrito, NO despachado)

`probe_d25_v750.py` + `.github/workflows/probe-s151-d25-v750.yml`. Un job por volcán, 339 pasadas en
total (271 negativos en cero, 28 alertas en cero, 40 pasadas que ya publican como control), el MISMO
granule del record (nombre exacto), tres brazos en el mismo proceso sobre la misma descarga:

- **control**: flag apagado. Debe reproducir el record (C-P1: `pc.vrp_mw` a max(1e-3 MW, 1 %), mismo
  número de píxeles, centroide a 0,01 km). Si falla en más del 10 %, el resultado es INDECIDIBLE.
- **a, canon**: media de la radiancia de los vecinos no alertados (Coppola 2016a ec. 6), `max_half_px` 3.
- **b, variante**: a + sacar los vecinos con BT11 (M15) < 255 K. Es de Coppola 2014 (IJRS, p. 3412), no
  del canon 2016a (`docs/audit_s150/meta/VERIFICADOR_DATOS.md` D9): se informa como variante.

Autentica sólo por `EARTHDATA_TOKEN` y falla si viene vacío (A71). Borra cada granule al terminar su
pasada. Volumen de descarga y duración: SIN MEDIR (una pasada es un L1B y un GEO de 750 m).

**Criterio pre-registrado** (`analizar_probe.py`): una variante VALE EL A/B si el límite inferior de
Wilson 95 % de alertas rescatadas (de 28) supera al límite superior de negativos que pasan a publicar
(de 268). Si los intervalos se cruzan, el fondo por vecinos publica igual con alerta que sin ella y el A/B
no se gasta. La autoprueba del analizador (`--autoprueba`, salida en `analizar_autoprueba_salida.txt`)
da VALE para un caso construido para valer y NO VALE para uno construido para no valer.

## Recomendación

**No gastar todavía el A/B.** Primero el probe: lee 339 granules en vez de reprocesar meses, y contesta
exactamente lo que el A/B dejaría sin aislar (el signo del contraste en esas pasadas). Si el probe da NO
VALE en las dos variantes, D25 en VIIRS 750 se cierra con esta medición; si da VALE en alguna, el A/B se
corre sólo para esa variante.
