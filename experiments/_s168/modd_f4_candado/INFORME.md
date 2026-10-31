# Candado del §11 de MOD-D fase 4: estado de la entrega

Rama `claude/s168-modd-f4-sello`. El pre-registro está sellado: tag `s168-modd-f4-sellado`, commit `3768e9431`.
Nicolás aceptó VS-02, es decir, M70 cuenta como atrapada por la aserción explícita de E53. Lo transmitió la
coordinadora S168. Con eso, S168 encargó armar el candado. **El candado todavía no tiene tag.** El sha del commit
que contiene este informe se lee con `git ls-remote origin refs/heads/claude/s168-modd-f4-sello`.

Rutas relativas a `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\`.

## Qué está escrito (en `experiments/_s166_modd_f4/` salvo que se diga otra cosa)

| pieza del §11 | archivos | qué se corrió y qué salió |
|---|---|---|
| 1. población | `poblacion_f4.py`, `poblacion_f4.json`, `poblacion_f4_salida.txt`, `contrato_poblacion_f4.py` y su salida | 5.709 pasadas: 5.465 de C y 244 de E. 5.321 pasadas tienen `grilla_censo`, todas de C. 56 protegidas de la tabla: 50 de C y 6 de E. 2 etiquetas de C cambian contra el censo. `sin_pasada_nuestra` vacía. El contrato calza con `control_cobertura` y `control_identidad` |
| HEAD de los días de E (§4) | `head_e.py`, `head_e.json`, `head_e_salida.txt` | 106 de 106 URL de E responden 200, sin credenciales (LAADS devuelve 303 hacia una URL firmada). Ningún día excluido |
| 8.7, referencia y re-etiquetado | `reetiquetado_f4.py` y su salida, `externos_referencia.json` | Los sha256 de la referencia coinciden con los de S165. Dos corridas dan lo mismo. Con la referencia del censo, 0 distintas en 5.465 |
| 2. arnés | `probe_f4.py`, `probar_probe_f4.py` y su salida, `humo_f4.txt` | Batería del arnés: 18 de 18. Mutaciones del arnés: 16 de 16 atrapadas por aserción, ninguna con caídas. Controles: identidad VIVA, caída CAE, rota ROTA |
| 3. identidad | `identidad_f4.py`, `probar_identidad_f4.py` y su salida | 8 de 8 escenarios sobre 101 grillas reales del censo, cruzados con `control_identidad` |
| 4. externos y manifiesto | `externos_f4.py`, `manifiesto_candado_f4.py`, `MANIFIESTO_CANDADO_F4.json` y su salida | El manifiesto registra 64 archivos, con el tag y el commit en `null` |
| 5. workflow | `.github/workflows/probe-s168-modd-f4.yml` | Clave `"on"` entre comillas, sólo `workflow_dispatch`, autenticación sólo con `EARTHDATA_TOKEN`, sin push. Modos head_e, humo, t1, t2 y t3. Las cuatro pruebas de guardia de workflows pasan |
| ensayo en seco | `ensayo_en_seco_f4.py` | **No corrido**: pasa más de 27.000 records por node y no cabe en lo liviano mientras el cupo pesado está ocupado |

Hallazgos VS del tercer verificador cerrados en la batería y el medidor, sin tocar las reglas de `evaluar_f4.py`:
- VS-01: ATRAPADA exige que ningún escenario caiga. Hay una clase nueva, ATRAPADA_CON_CAIDAS, que no cuenta, y un control de caída con `ValueError`.
- VS-02: el `except` de E53 queda acotado al mensaje `math domain error`.
- VS-03: escenario E62 y prueba del medidor `probar_mutar_f4.py` (5 de 5), que ejerce la salida «NO VALE» con código 1.
- VS-04: aserción sobre `N_GRILLAS_CENSO` en E41.
- VS-05: escenario E63.
- VS-06: escenario E64.
- VS-08: `--traza` agregado a argparse.
- M83 a M86: mutaciones nuevas.

La batería pasa 66 de 66. Contra el evaluador vacío, 66 de 66 fallan por aserción y ninguno cae.

## Estado al tag (2026-10-30)

**Tag `s169-modd-f4-candado`** (el commit lo da `git rev-parse s169-modd-f4-candado^{commit}`). Antes del tag se hizo:
- Ensayo en seco: ensayo 1 PROPONER ADOPCIÓN sin controles en rojo; ensayo 2 INDECIDIBLE por procedencia, como debe
  (`ensayo_en_seco_f4_salida.txt`).
- Mutaciones del evaluador reformadas: 86 de 86 atrapadas por aserción sin caídas, cuatro controles como deben, árbol
  quieto (`mutar_evaluar_f4_salida.txt`; §13 del pre-registro).
- Arreglos de la auditoría S169 (VC169-01, P2-01, P2-02, P2-03 con VF2-02, P2-07 y P2-08) con sus pruebas:
  `probar_descarga_f4_salida.txt` 5 de 5, `probar_externos_f4_salida.txt` 4 de 4, `probar_probe_f4_salida.txt` 23 de
  23 escenarios y 20 de 20 mutaciones del arnés por aserción sin caídas. VF2-01 explicado en el §13. Lo declarado, en
  el §13 ter.
- Manifiesto regenerado sobre el commit del tag: 71 archivos, `--comprobar` OK (`MANIFIESTO_CANDADO_F4.json`).

Falta, después del domingo 2026-11-01 12:00 UTC (uso mínimo de tokens hasta entonces):
1. Verificador limpio del candado.
2. PR a `main` del workflow nuevo: P2-08 fijó versiones y su sha256 LF es `4047c55a64ef855b13ebdf6f56aadba7b5bdb4ef223cd64770b81a04886489a7`.
   El de `main` (#927) es el anterior. Merge sólo con una frase de Nicolás.
3. Humo de unas 25 pasadas (`humo_f4.txt`) con `--ref s169-modd-f4-candado`, y recién entonces el A/B completo.

## Riesgos que el humo tiene que mirar (declarados por quienes escribieron el arnés y la identidad)

- 518 records MODIS desde marzo en `data/` no traen `codigo_sha`. Si en alguno K difiere de lo guardado, no se puede
  re-correr en su sha y el control 8.1 queda en rojo.
- Si `data/` guardó la versión NRT y el arnés baja la estándar, una diferencia puede no reproducirse.
- El censo guardó sus grillas en float32. Si la identidad sale en rojo, el diagnóstico `con_grilla_runner_en_float32`
  dice si la causa es sólo esa precisión.
- El costo estimado es de unas 10 h de runner en tres tandas, sin medir: se mide en el humo.

## Humo (S170, run 41164864021, tag `s170-modd-f4-candado`, 2026-10-31)

Lectura: `leer_humo_f4.py` y su salida `leer_humo_f4_salida.txt`; identidad con `identidad_f4.py` sobre el artefacto
(`identidad_humo.json`, `identidad_humo_salida.txt`); tiempos de los jobs en `humo_run_41164864021.json`.

- Procedencia: la cabecera trae el commit `d65fd231d` y el ref del tag; los cuatro jobs terminaron en verde. La prueba
  previa en el runner corrió el arnés, el evaluador, el evaluador vacío y el manifiesto.
- Cobertura: 25 de 25 pasadas de `humo_f4.txt`, sin faltantes, sobrantes ni repetidas. 25 en estado `ok`.
  Villarrica 2026-04-30 03:00 sale con «volcán fuera del gránulo», un motivo sellado legítimo: el censo tampoco lo
  cubrió (`grilla_censo` falso).
- Gránulos: 25 de 25 bajados por nombre (L1B y MxD03 pedidos iguales a los usados), 0 `otro_granulo`, 0
  `CMR/descarga fallo` en `probe_0.log`.
- K igual a producción: `k_difiere_de_guardado` falso en 25 de 25. Ninguna re-corrida en su sha, `pub_runner` con K en
  25 de 25, la marca de la vía verdadera en 25 de 25 y el cenit tomado del MxD03 en las 25.
- Identidad: 23 pasadas comparables (las de C con grilla del censo), 23 iguales: mismo gránulo, misma máscara, VRP a
  0,001 MW y misma clase. La máxima diferencia de radiancia es 4,8e-7, la precisión de float32 del censo. Las otras dos
  pasadas son la de E (Chillán 2026-10-25) y la Villarrica fuera del gránulo.
- Tiempo: 2,41 s de mediana por pasada (máximo 2,81).
- Señal física, que informa y no decide: Chillán 2026-10-25 07:20 (58° de cenit, la tercera pérdida MODIS del #915)
  queda K 0 y V 2,553 MW en la cumbre, y las del 09-29, 10-12 y 10-15 también las publica V y K no. Láscar 2026-03-30
  07:25 sigue como `far` en K y en V.

**Veredicto del humo: APTO para t1.** Estimación (en la salida): 238 pasadas por parte, unos 9,6 min de pasadas más
3,8 min fijos por parte, y unos 18 min por tanda contando la prueba previa, sin colas del runner ni re-corridas en su
sha. Es una cota alta en descargas: el humo bajó casi un gránulo por pasada, y C tiene unas 4,4 pasadas por gránulo.

Hallazgos de gravedad 1 del verificador de S170 (`D:/vrp-trabajo/temporales/ver_s170_modd/INFORME.md`):
- VS170-MODD-01, cuatro módulos de VIIRS y del Test 1 cargados en la lectura están fuera del manifiesto. Queda
  declarado: no son de MODIS. Antes de la lectura de t1 a t3, comprobar que no cambiaron con
  `git diff s170-modd-f4-candado -- pipeline/process_viirs.py pipeline/process_viirs_mod.py pipeline/test1_contextual_filter.py pipeline/test1_spatial_core.py`.
- VS170-MODD-02, versiones sueltas (node, el parche de Python, las acciones). Queda declarado: la cabecera registra
  Python 3.11.17, numpy y scipy, y node se lee en el log de «Dependencias» de cada job. Al leer t1 a t3, comparar esas
  versiones entre tandas.
- VS170-MODD-03, una descarga lenta no cuenta para el tope. Queda declarado: en el humo no hubo ninguna falla de
  descarga y la pasada más lenta tardó 2,81 s. Falla cerrado, porque la parte vence el timeout y la cobertura queda en
  rojo.
- VS170-MODD-04, las grillas del censo sin sha. Queda cerrado para la lectura: `grillas_censo_sha256.txt` tiene el
  sha256 de las 5.321. Antes de correr la identidad de t1 a t3, comprobarlo con
  `cd D:/vrp-trabajo/temporales/s162_modd/censo && sha256sum -c <ruta>/grillas_censo_sha256.txt`.

## Tanda t1 (S170, run 41166033637, tag `s170-modd-f4-candado`, 2026-10-31)

Lectura con `leer_tanda_f4.py` (salida `leer_t1_salida.txt`), identidad en `identidad_t1_salida.txt` y tiempos de los
jobs en `t1_run_41166033637.json`.
- Las 8 partes salieron completas contra la partición del arnés: 1.891 de 1.891 filas, sin faltantes, sobrantes ni
  repetidas, todas en `ok`. Hay 0 `otro_granulo`, 0 pasadas en que K difiere de producción y la marca de la vía es
  verdadera en las 1.891.
- Todas las cabeceras traen el commit y el tag, y las versiones del runner son una sola en las 8 partes (VS170-MODD-02).
- Identidad: 1.746 de 1.746 iguales. Las grillas del censo coinciden con su sha256 (VS170-MODD-04) y los módulos de
  VIIRS y del Test 1 no cambiaron desde el tag (VS170-MODD-01).
- Tiempo: unos 17 minutos por parte y 25 en total.
- **Defecto de regla para la lectura (no del runner).** 24 pasadas tienen grilla del censo y el runner las saca como
  `escena_invalida`. El port del censo llegó al mismo motivo en las 24, y en todo el censo son 45
  (`selladas_con_grilla.py` y su salida). La regla N-01 del §8.2 supone que una pasada con grilla del censo es una
  pasada que el censo cubrió, y por eso cuenta como «sellada sin explicar» toda pasada con grilla que el runner saque por
  un motivo sellado, salvo que la identidad la declare de otro gránulo. Con esa regla, la identidad queda en rojo y el
  veredicto sale INDECIDIBLE. Arreglarlo cambia una regla del evaluador: pide una adenda sellada, por ejemplo que una
  pasada así cuente como acuerdo cuando el censo llegó al mismo motivo con la misma grilla. Lo decide Nicolás.

## Tanda t2 (S170, run 41168080181, 2026-10-31)

Lectura `leer_t2_salida.txt`, identidad `identidad_t2_salida.txt`, jobs `t2_run_41168080181.json`.
- Partes 8 a 15 completas: 1.922 de 1.922 filas, sin faltantes, sobrantes ni repetidas, todas en `ok`. Hay 0
  `otro_granulo`, 0 pasadas con K distinto de producción, la marca de la vía en las 1.922, el mismo commit y tag, y
  las mismas versiones que en t1.
- Identidad: 1.789 de 1.789 iguales, y las grillas del censo coinciden con su sha.
- Hay 11 pasadas con grilla del censo que salen como `escena_invalida`; el censo llegó al mismo motivo en las 11
  (`selladas_con_grilla_t2_salida.txt`). Con la regla sellada quedan 11 sin explicar; con la candidata de la adenda, 0.
