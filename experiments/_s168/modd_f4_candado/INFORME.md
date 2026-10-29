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

## Lo que falta, en orden

1. **Esperar el cupo pesado.** Lo ocupa la lectura de V375-E (PID 15924, `leer_posicion_v375e.py`). Antes de lanzar,
   comprobarlo con `Get-CimInstance Win32_Process`. MOD-D tiene un solo cupo, y el medidor de V750-A ocupa el otro.
2. **Ensayo en seco.** Comando:
   `python experiments/_s166_modd_f4/ensayo_en_seco_f4.py > experiments/_s166_modd_f4/ensayo_en_seco_f4_salida.txt 2>&1`.
3. **Mutaciones reformadas**: 86 mutaciones más 4 controles, con `python mutar_evaluar_f4.py --paralelo 1`, `TMP` en
   `D:\vrp-trabajo\temporales\s168_mut` y el árbol quieto (sha256 antes y después). Duran unas 9 h, a unos 6 min por copia.
   **`mutar_evaluar_f4_salida.txt` es todavía el de la corrida de `314cec809`** (82 mutaciones, batería de 63): queda
   viejo hasta esta corrida.
4. Poner al día el §13 del pre-registro con la corrida nueva y regenerar el manifiesto
   (`manifiesto_candado_f4.py --escribir`). Después, el tag del candado y su verificador limpio.
5. El humo de unas 25 pasadas necesita el workflow en `main`, o sea un merge con una frase de Nicolás que nombre el
   merge. Nada se despachó.

## Riesgos que el humo tiene que mirar (declarados por quienes escribieron el arnés y la identidad)

- 518 records MODIS desde marzo en `data/` no traen `codigo_sha`. Si en alguno K difiere de lo guardado, no se puede
  re-correr en su sha y el control 8.1 queda en rojo.
- Si `data/` guardó la versión NRT y el arnés baja la estándar, una diferencia puede no reproducirse.
- El censo guardó sus grillas en float32. Si la identidad sale en rojo, el diagnóstico `con_grilla_runner_en_float32`
  dice si la causa es sólo esa precisión.
- El costo estimado es de unas 10 h de runner en tres tandas, sin medir: se mide en el humo.
