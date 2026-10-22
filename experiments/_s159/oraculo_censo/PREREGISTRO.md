# Pre-registro: censo del oráculo de MIROVA en todos los negativos limpios de VIIRS 750 (S159)

> Escrito y commiteado ANTES de despachar el censo (2026-10-21). Escala aprobada por Nicolás («tenemos tokens, tiempo y
> podemos probarlo todo»): todas las pasadas de la población del frente N. Origen: `experiments/_s159/n/verificador/INFORME.md`,
> afirmación 3 (el oráculo cambia la detección, así que su efecto en negativos no tiene techo por censo parcial; cota
> con la muestra 2,6 %, unos 139 negativos, ΔE hasta +34; y la comparación de N mezclaba el predicado del agente con el
> del tablero).

## 1. Población

`objetivos.json`, armado por `01_objetivos.py` (salida `01_objetivos_salida.txt`) desde
`experiments/_s159/n/poblacion_completa.json`: VIIRS 750 nocturno, 2026-04-01 a 2026-10-21 **sin el 18 ni el 19 de
octubre** (CMR no los sirve), pareo a 120 s, regla D-9 SN, lectura A de protegidas, records de `origin/main` 533398f8f,
referencia Mirova-v1 (consolidado `7ea275df`, OCR `4ddd5481`). **5.746 pasadas en 1.297 gránulos**:

| clase | n |
|---|---|
| negativos limpios | 5.476 |
| alertas que deciden | 256 (79 protegidas, 177 bajo 1 MW) |
| alertas sólo OCR antes del 2026-06-13 (no deciden, A119) | 14, se informan aparte |

Tramo A119: la etiqueta que decide antes del 13 de junio es la de la tabla; los 14 sólo OCR no entran a la suma de
errores. 508 de las 5.746 ya las midió el frente N (lote y censo de F): son las del control 2.

## 2. Qué corre (`probe_censo.py`, reusa `experiments/_s159/n/probe_n.py` sin cambiar su lógica)

Por pasada, sobre el mismo gránulo que listó MIROVA (el de nuestro record): **K** (producción tal cual, record pasado
por `store.append_record` en carpeta temporal) y el **oráculo** (código entero de MIROVA, port validado contra Octave,
en la grilla UTM de 67 × 67 celdas de 750 m con la esquina de GEO e interpolador lineal) con **dos cajas declaradas
ahora**:

- **O-def**: la caja por defecto de N (`PG.caja_mirova()`): cumbre de 7 × 7 celdas con umbrales de cumbre y anillo de
  21 × 21 con umbrales de escena.
- **O-sens**: el recuadro sensible de N: las 21 × 21 celdas con umbrales de cumbre (`caja(sensible_anillo=True)`).

No corren K2, C, F, FC ni las variantes vecino, cúbico o R2. Se guarda la cobertura del gránulo en la grilla (celdas
sin dato en el 67 × 67, en el 21 × 21 y en la cumbre de 7 × 7) y la distancia del píxel del gránulo más cercano al
centro.

## 3. Qué cuenta como «publica» (el MISMO predicado para K y para el oráculo)

`publica = isSummitDetection(r) && isValidDetection(r) && !isThermalArtifact(r, inner) && mirovaEqVrpDisplay(r, inner) > 0`,
las funciones extraídas de `frontend/index.html` y ejecutadas con node (`scripts/banco_paridad.correr_node`), con
`inner` = `inner_radius_km` de la lista `VOLCANOES` del mismo archivo (`banco_paridad.inner_desde_html`). Es el
predicado de la tabla del frente N y de su verificador.

Campos que ese predicado lee para un record de VIIRS 750 (leídos en `frontend/index.html`, `mirovaEqVrp` l. 1162,
`isCirrusArtifact` l. 1336, `isDiffuseFieldArtifact` l. 1355, `isValidDetection` l. 1595, `isSummitDetection` l. 1609;
el núcleo F5 sólo actúa en VIIRS 375): `primary_cluster.vrp_mw`, `primary_cluster.centroid_dist_km`,
`primary_cluster.n_pixels`, `distance_class`, `vrp_mw`, `vrp_mir_mw`, `discarded_reason`, `triggered_test1`,
`vrp_vent_mw`, `t_max_k`, `sensor`.

**Record de K**: el que escribe `store.append_record`, con esos campos (igual que N).

**Record sintético del oráculo** (la función `record_oraculo` de `experiments/_s159/n/07_censo_analizar.py`, copiada sin
cambios), una por caja:

- sin píxeles alertados: `{sensor, vrp_mw: 0, primary_cluster: null, distance_class: null}` (no publica);
- con píxeles: `sensor` = el de la pasada (`VIIRS_*_750`); `vrp_mw` = `primary_cluster.vrp_mw` = VRP total del oráculo
  (suma de TODOS los alertados de la caja, como MIROVA; no un cúmulo conexo como producción), redondeado a 3
  decimales como los records; `primary_cluster.n_pixels` = número de alertados; `centroid_dist_km` = distancia del
  centroide sin pesos (media de filas y columnas de los alertados) a la celda central (33, 33), × 0,75 km, o sea al
  **centro del TIF de MIROVA**; `distance_class` = `summit` si esa distancia es a lo más `inner`, si no `far`;
  `t_max_k` = temperatura de brillo M13 del alertado más radiante (`ORA.radiancia_a_temperatura`);
  `triggered_test1` = false; sin `discarded_reason` ni `vrp_vent_mw`.
- Sensibilidad declarada (no es variante): la distancia medida desde la coordenada de `volcanoes.yaml` en vez del
  centro del TIF. Sólo pesa en Planchón-Peteroa (1,83 km de desfase, inner 3) y Tupungatito (2,85 km, inner 7);
  los otros nueve están a 0,09 a 0,23 km (`01_objetivos_salida.txt`).

## 4. Qué se cuenta

Por caja, sobre las pasadas ok (sin pesos, todo es censo):

- negativos limpios publicados por el oráculo / 5.476, y por K / 5.476; encendidos (O publica y K no) y apagados;
- alertas que deciden: protegidas perdidas (K publica, O no) y ganadas; bajo 1 MW no publicadas por cada uno;
- `E = alertas bajo 1 MW que deciden sin publicar + negativos limpios publicados`; **ΔE = E_O − E_K** (regla 2 de
  MISSION). Las protegidas perdidas van aparte (regla 1: una sola perdida pesa más que cualquier ΔE).
- Desglose por volcán y por cenit (estratos ≤ 40° y > 40° de la población, y tramos 0-20, 20-40, 40-50, 50-60, > 60).
- **Pasadas partidas**, medidas en el propio gránulo (no con `diag_n_bg_anillo`): *fuera* = el píxel del gránulo más
  cercano al centro está a más de 5 km (la pasada no mira el volcán); *sin cráter* = alguna celda sin dato en la cumbre
  de 7 × 7; *partida con cráter* = celdas sin dato en el 67 × 67 pero no en la cumbre; *entera* = ninguna. El conteo
  principal usa las 5.476; se da también sin *fuera* ni *sin cráter*.
- **SIN DATO** (la pasada no bajó o falló K o el oráculo): se cuentan por clase y motivo, y ΔE se da como rango
  (negativos SIN DATO todos publicados o ninguno; alertas SIN DATO todas ganadas o ninguna). *Fuera* no es SIN DATO:
  es una pasada que no miró el volcán.

Etiqueta descriptiva por caja (no decide adopción, eso es la ola 3): 0 protegidas perdidas y todo el rango de ΔE
bajo 0, **GANA EN EL CENSO**; todo el rango sobre 0, **PIERDE**; el rango toca el 0, **SIN RESOLVER**; alguna
protegida perdida, **PIERDE PROTEGIDAS** sea cual sea ΔE.

## 5. Controles (se leen ANTES que el resultado)

1. **K = producción**: en toda pasada ok, K publica igual que producción (`pub_prod`) y con el mismo `pc.vrp_mw` a
   0,001 MW. Si falla en alguna, se listan y el resultado queda condicionado a explicarlas.
2. **Oráculo = N**: en las pasadas que N midió y que están ok en las dos corridas, mismo número de píxeles y VRP a
   1e-6 MW en O-def y O-sens que en `experiments/_s159/n/run_39682867040` y `run_39693661527`.
3. **Nulo del instrumento** (fuera de línea, sobre los records reales del censo): (a) a cada record del oráculo que
   publica se le pone `primary_cluster.vrp_mw = 0` y deja de publicar; (b) a cada uno se le pone `distance_class: far`
   y deja de publicar; (c) a 50 negativos que no publican (semilla 159) se les inyecta un cúmulo de cumbre de
   0,3 MW a 0,5 km con 290 K y pasan a publicar. Si alguno no cambia, el contador no ve lo que dice ver.
4. **Control positivo del oráculo**: detecta las alertas de MIROVA (N: 145 de 181 con O-def, 175 con O-sens; razón
   O/MIROVA 0,999). Se mide sobre las 256 que deciden.

## 6. Predicción del verificador (referencia, no criterio)

Del frente N (predicado del agente en el lote, del tablero en el censo de F): O-def publica 4 de los 54 negativos que
publica K más 1 de los 119 del censo de F, **≈ 5**, y pierde 6 protegidas de Cordón Caulle; O-sens 8 + 4, **≈ 12**, y 0
protegidas. En los otros 5.303 negativos el oráculo publicó 0 de 140 muestreados: cota superior 2,6 %, **hasta ~139
más**. ΔE del lote ponderado: O-def −72,6, O-sens −105,0, con ΔE posible hasta **+34** por esa cota.

## 7. Qué NO cambia

Nada en `pipeline/`, `data/` ni `frontend/`. El workflow (`probe-s159-oraculo-censo.yml`, copia en esta carpeta) es
de sólo lectura, autentica sólo con `EARTHDATA_TOKEN`, deja el resultado como artefacto y se dispara con un push a la
rama auxiliar `s159-oraculo-disparo`, que no se mergea.
