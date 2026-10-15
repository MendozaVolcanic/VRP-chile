# Loop 1.5: el fondo por vecinos (D25) en VIIRS 750, medido primero sobre lo que hay en disco

Fecha: 2026-10-14. Sólo lectura. No toca `pipeline/` ni el perfil. Nada despachado.
Revisado por un verificador con contexto limpio (PR #790): arreglos D1 a D4 aplicados en esta versión.

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
  informe. Lista congelada: `lista_268_s149.json`.
- Hoy la misma definición da **271**, y las 268 siguen todas dentro (control C4). Los tres de más tienen
  dos causas distintas (atribución en `techo.json`): **Chaitén 2026-08-17 06:12 y Nevados de Chillán
  2026-06-29 06:24 son del arnés** (los JSON de S149 leídos con el cargador de Loop 0.1, #778, ya dan
  270); **Isluga 2026-09-21 05:42 es del corpus**: en S149 su cúmulo tenía 0,025 MW y hoy tiene 0,0
  (A90). El criterio del probe cuenta sólo las 268.

## Qué datos hay

- **Los records no guardan a los vecinos.** `anomaly_pixels` trae sólo píxeles alertados (lat, lon,
  dist_km, bt_k, vrp_mw); `diag_L_bg_local_w_m2_sr_um` existe en 21 de los records pero es nulo en los
  271. No hay ninguna temperatura ni radiancia de un vecino no alertado (`techo.json`).
- **No hay granules VIIRS 750 en disco.** Lo único en `experiments/` son dos `.npz` de VIIRS 375 (S104).
- **Ningún artefacto de GitHub sirve**: los probes de vecinos (S141) y las 12 noches (S143) son de
  VIIRS 375, y ningún A/B corrió jamás con `enable_vrp_bg_neighbor_mean_viirs750` encendido.
- `../mirova-tif-archive` guarda el producto de MIROVA, no nuestras temperaturas: no da los vecinos.

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

Bajo 10 MW **el tablero no pone ninguna barrera**: que D25 haga publicar a un negativo depende sólo del
**signo** del contraste del cráter contra sus vecinos, y ese signo vive en el granule.

**Escala** (conversión determinista, no una medición de D25): en 206 de los 271 con píxeles guardados, el
píxel del cráter está a una mediana de **1,81 K bajo el anillo** (201 de 206 bajo o igual). Un kelvin de
exceso en un píxel de 750 m vale **~0,08 MW**.

**Controles** (fijados antes de mirar): C1 identidad del predicado; C2 la población sin tocar publica 0 de
299; C3 el campo que se muta es el que decide (814 que hoy publican: intactas 814, con magnitud cero 0);
C4 contiene exactamente a las 268 y 28 de S149. Los cuatro pasan. `control_sintetico.py` valida la cadena
del fondo con cinco casos de respuesta conocida: pasan los cinco.

## Sello, piloto y enmienda (2026-10-15)

Nicolás selló el probe el 2026-10-15 (D-5, issue #793). **Piloto** Tupungatito, 10 pasadas, run 38678279921:
9 de 10 con los tres brazos y C-P1 en las 9; el cableado funciona (el control nunca llama al fondo por
vecinos). La décima falló porque NASA reprocesó el gránulo: el archivo exacto del record
(`VJ102MOD.A2026169.0542.021.2026169113420.nc`) ya no está y el buscador devuelve el de la misma adquisición
producido el día 174. Con la regla original de cobertura completa, cualquier reproceso así deja el probe
INDECIDIBLE sin que el instrumento esté mal.

**Enmienda, escrita antes de correr las 356 y sin mirar ninguna alerta** (las 10 del piloto son negativos en
cero, sin rescate posible que mirar): si el L1B exacto no existe, se usa el de la misma adquisición y la pasada
queda marcada `l1b_reprocesado`. El control C-P1 (que el brazo control reproduzca el record persistido) decide
si sirve, como para cualquier otra pasada, y el umbral de 90 % no cambia. El analizador informa cuántas pasadas
usaron un L1B reprocesado y cuántas de ellas pasan C-P1. Criterio, brazos y reglas 1 y 2 no cambian; la
autoprueba da la misma salida.

## El probe propuesto (escrito, NO despachado)

`probe_d25_v750.py` + `.github/workflows/probe-s151-d25-v750.yml`. Un job por volcán, **356 pasadas**:
271 negativos en cero, 28 alertas en cero, 40 pasadas al azar que ya publican y **17 alertas protegidas**
(VRP de MIROVA de 1 MW o más) que hoy publicamos y no cayeron en las 40 (otras 2 sí cayeron). Mismo
granule del record (nombre exacto), tres brazos en el mismo proceso:

- **control**: flag apagado. Debe reproducir el record (C-P1). Si falla en más del 10 %, INDECIDIBLE.
- **a, canon**: media de la radiancia de los vecinos no alertados (Coppola 2016a ec. 6), `max_half_px` 3.
- **b, variante**: a + sacar los vecinos con BT11 (M15) < 255 K. Es de Coppola 2014 (IJRS, p. 3412), no
  del canon 2016a (`docs/audit_s150/meta/VERIFICADOR_DATOS.md` D9).

Autentica sólo por `EARTHDATA_TOKEN` y falla si viene vacío (A71). Si `vols` trae un nombre mal escrito
sale con código 2 antes de autenticar (`prueba_probe_lista_vacia.py`: el código nuevo sale 2, el anterior
salía 7, o sea seguía de largo). Volumen de descarga y duración: SIN MEDIR.

**Piloto recomendado**: `vols = ["Tupungatito"]` o `["Isluga"]` con `max_pasadas = 10`, no Copahue (3
pasadas, ninguna en condición fría). Las 10 primeras de cada volcán son negativos en cero: el piloto sirve
para ver C-P1 y el cableado de los brazos, no para el veredicto.

**Criterio pre-registrado** (`analizar_probe.py`, alineado con el "Criterio de victoria de la réplica" de
`docs/MISSION.md`):
- **Regla 1**: si un brazo apaga una alerta protegida que el control publica, NO VALE.
- **Regla 2**: las 28 alertas son "Muy Bajo", así que rescate y falso pesan igual y se cuentan en
  **casos**. VALE sólo si el límite superior Wilson 95 % de los negativos que empiezan a publicar, por 268,
  queda bajo el límite inferior Wilson 95 % de las alertas rescatadas, por 28. Con 28 de 28 rescatadas
  el límite inferior es 24,6 casos, así que el brazo tolera a lo más unos 17 negativos nuevos.
- **Validez**: cobertura completa de las 356 pasadas (A108), C-P1 en 90 % o más, el control nunca llama al
  fondo por vecinos y cada brazo encendido sí.
- La autoprueba (`analizar_autoprueba_salida.txt`) exige: sólo alertas da VALE; alertas más todos los
  negativos da NO VALE; **28 rescatadas con 225 negativos nuevos da NO VALE** (el criterio anterior, por
  tasas, le daba VALE); apagar una alerta protegida da NO VALE por regla 1; una pasada menos da
  INDECIDIBLE; Wilson no se cae con conteos fuera de rango. Pasan las seis.

## Lo que el probe NO distingue

- **La variante b no separa nube de cumbre fría y despejada.** El umbral de 255 K saca a todo vecino
  frío, haya nube o no. En 56 de las 356 pasadas la mediana del anillo (`t_bg_k`, banda MIR M13, usada
  como aproximación de la de 11 µm) ya está bajo 255 K, 17 de 39 en Tupungatito. Ahí b deja al píxel sin
  vecinos útiles, cae al respaldo y se parece al control **por construcción**, no porque el fondo de
  vecinos falle.
- **Una alerta "rescatada" se cuenta sin comparar su magnitud con la de MIROVA** (regla 3 del criterio de
  victoria) **ni su posición** (A107: coincidir en radio no es coincidir en objeto). El probe guarda las
  dos cosas, pero el criterio no las usa.
- **Quedan fuera las 27 pasadas de rutina en noches con alerta** que están en la misma condición de
  cúmulo en cero (`techo.json`): una publicación ahí tampoco tiene alerta en su pasada.
- **C-P1 puede fallar de verdad**: 274 de los 356 records no tienen `processed_utc` (son las pasadas
  hasta el 2026-09-02; el primer `processed_utc` de la lista es del 2026-09-03), o sea que se
  procesaron con código más viejo que el de hoy, así que el código de hoy puede no reproducirlos aunque el
  probe esté bien. Si falla, primero hay que mirar si fue el código o el producto, antes de leer los brazos.

## Recomendación

**No gastar todavía el A/B.** Primero el piloto y después el probe: lee 356 granules en vez de reprocesar
meses, y contesta lo que el A/B dejaría sin aislar (el signo del contraste en esas pasadas). Si las dos
variantes dan NO VALE, D25 en VIIRS 750 se cierra con esta medición; si alguna da VALE, el A/B se corre
sólo para esa variante, y ahí sí con magnitud y posición contra MIROVA.
