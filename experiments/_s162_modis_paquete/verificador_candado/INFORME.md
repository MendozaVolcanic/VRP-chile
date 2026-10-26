# Verificación con contexto limpio del candado MOD-D (censo del paquete MODIS contra K)

Modelo y esfuerzo: Claude Fable 5.1, esfuerzo bajo el que corrió esta sesión (el fijado por quien la lanzó; no lo elegí yo).
Hora del servidor de GitHub al empezar: Mon, 26 Oct 2026 04:31:27 GMT. Material: worktree `C:\vrp-trabajo\s162-modd`,
rama `s162-modd-candado`, HEAD `b423316c2` = `origin/s162-modd-candado`, árbol limpio. Caminos de ruptura escritos antes
de abrir el código en `CAMINOS.md` de esta carpeta (sha256 al pie). Todo lo que afirmo abajo sale de un archivo que leí o
de un script que corrí en esta sesión; lo que no, va como SOSPECHA.

## En una pantalla

1. **Las reglas selladas están implementadas palabra por palabra** en `evaluar_paquete.py` (§4, §5, §6, §8 y adendas 1 a 3): lo leí regla por regla (tabla §2 de este informe) y lo medí con 9 pruebas extra que la batería no trae (9 de 9 pasan contra el evaluador real).
2. **Todo lo que se puede correr sin red se reproduce** en este computador: batería 19 de 19 (y 19 de 19 fallan por aserción contra el vacío), prueba del arnés 6 mutaciones de 6 atrapadas, diagnóstico S-1 OK, ensayo en seco número por número igual al guardado, los blobs sellados coinciden con el árbol y con sus commits de origen, la población es la sellada (5.465 pasadas, 1.232 gránulos, etiquetas exactas) y el árbol sólo difiere del main congelado `80b819828` en `experiments/` y dos workflows.
3. **Un hallazgo que sí toca una regla sellada (VCM-01)**: la adenda 3.6 saca del denominador más pasadas que el §8.5 (también «error del port» y «grilla incompleta»), y con eso una protegida que K publica y el port no pudo correr deja de vetar P1. Está listada junto al veredicto, pero el §4 la contaría como pérdida. Es un cambio de regla que la adenda dice no hacer.
4. **El candado no fija el arnés ni el evaluador (VCM-02)**: ningún hash protege `probe_paquete.py`, `evaluar_paquete.py`, `grillas.json` ni los módulos de MOD-B que reutilizan; «procedencia» sólo exige un commit único, no el del candado, y todavía no existe el tag.
5. **Veredicto: se puede despachar el humo con cambios chicos** (lista en §7). Ninguno exige tocar `pipeline/`.

## 1. Qué corrí y qué dio (todo en primer plano salvo las tandas de mutaciones, que esperé hasta su fin)

| qué | comando (desde `experiments/_s162_modis_paquete/`) | resultado | salida guardada |
|---|---|---|---|
| diagnóstico S-1 | `PYTHONIOENCODING=utf-8 python -I diagnostico_s1.py` | `PRUEBA DIAGNOSTICO S-1 OK`, borde ruidoso sube sigma 0,00041 a 0,00109 y la cumbre pierde su píxel (n2_g 1 a 0) con la ROI1 intacta | `verificador_candado/salida_diagnostico_s1.txt` |
| prueba del arnés | `python -I verificador_candado/rastrear_deps_probar_probe.py` (corre `probar_probe_paquete.main` y lista los paquetes de terceros cargados) | `RESULTADO: OK, atrapadas 6 de 6, caen 0, vivas 0`; terceros: numpy, scipy, pyproj, yaml (los cuatro del `pip install` del job `prueba`) | `salida_probar_probe_paquete.txt` |
| batería contra el real | `python -I probar_evaluar_paquete.py` | `pasan 19, fallan 0, caen 0 (de 19)`; duró 6 min (el material decía 3 a 4) | `salida_bateria_real.txt` |
| batería contra el vacío | `python -I probar_evaluar_paquete.py --modulo evaluar_vacio.py` | `pasan 0, fallan 19, caen 0`: las 19 fallan por aserción | `salida_bateria_vacio.txt` |
| ensayo en seco | `python -I ensayo_en_seco.py --ref D:/vrp-trabajo/temporales/s162_mxd03/ref` | `rc=0`; idéntico al guardado: 150 pasadas, INDECIDIBLE por cobertura y predicado, port_s159 OK 148 comunes y 91 con píxeles, PM P2 GANA neto -25 B 29, Chillán 7 pares 6 a favor SIN RESOLVER | `salida_ensayo_en_seco.txt` |
| pruebas extra (mías) contra el real | `python -I verificador_candado/pruebas_extra_verificador.py` | `pasan 9, fallan 0, caen 0 (de 9)` | `salida_pruebas_extra_real.txt` |
| pruebas extra contra el vacío | `... --modulo ../evaluar_vacio.py` | 6 de 9 fallan por aserción; **x03, x06 y x08 pasan contra el vacío**: son pruebas en negativo (exigen que algo NO ocurra) y sólo valen pareadas con la mutación que cazan (§3) | `salida_pruebas_extra_vacio.txt` |
| mutaciones propias (sobre copia) | `python -I verificador_candado/mutaciones_propias.py ...` | ver §3 | `salida_mutaciones_propias_g1.txt`, `_g2.txt` |
| muestra de las mutaciones originales | `python -I mutar_evaluar_paquete.py sin_info_entra_y_cuenta k_ignora_predicado p2_signo_invertido` | ver §3 | `salida_mutaciones_originales_muestra.txt` |
| nulo de los controles externos | `python -I verificador_candado/nulo_controles_externos.py --ref D:/...` | ver §4 | `salida_nulo_controles_externos.txt` |

Lo que NO se puede correr aquí: el arnés real (`probe_paquete.py`) y `recorrer_en_sha.py`, porque leen HDF con pyhdf (no
existe en Windows). Su prueba sin red sí corrió. Discos al terminar: C: 25 GB, D: 9,6 GB libres.

## 2. Cada regla sellada: dónde la implementa el evaluador y si coincide

Notación: `EP:n` = `experiments/_s162_modis_paquete/evaluar_paquete.py` línea n; `D25` = `evaluar_d25_ded217af4.py`
(blob `1dbabf65`, idéntico byte a byte al de `ded217af4`: `git diff` vacío, medido). «Prueba» = la de la batería que la
ejercita, o la mía (xNN) si la batería no la toca.

| regla sellada | implementación | ¿coincide? | prueba |
|---|---|---|---|
| §4 «publica» = predicado de `frontend/index.html` con node (A97) | `EP:121-129 predicado` llama `bp.correr_node` y toma `p[4]` (publica) y `p[3]` (`mirovaEqVrpDisplay`); mismo `slim` que el runner (`probe_etiquetas.publica`) | sí | t09 (predicado del runner distinto) |
| §4 P1 veto: protegidas que K publica y el brazo no | `EP:184-189` | sí, palabra por palabra | t02; x03 (K callado no veta) |
| §4 P1b: ambos publican, K ≥ 1 y brazo < 1 en magnitud mostrada; contraria se lista | `EP:192-203` (`>= 1.0 >` y `< 1.0 <=`) | sí | t07 (las dos direcciones) |
| §4 P2: S = bajo 1 MW sin publicar + publicaciones en negativos limpios, por bloque noche-volcán, `regla_signos_p2` | `EP:206-241`; signo +1 = error sólo del brazo (D-45: positivo es malo para el brazo); bloques `vol|noche` (`EP:175`); `D25:509-563` | sí; B cuenta bloques con alguna discordante incluidas las de suma 0, como dice el docstring de D-45 | t01, t03, t04, t05, t06; x01 (dos pasadas de una noche = un bloque); x04 (bajo 1 MW sin publicar) |
| §4 M: d = abs(log10(B/M)) − abs(log10(K/M)) en alertas que ambos publican, `regla_m`, sólo EMPEORA decide; d′ informa | `EP:244-274`; `D25:245-249 regla_m`, `D25:295 comparar_con_ganancia` | sí; magnitud = mostrada (adenda 3.5, equivalente a `pc.vrp_mw` en MODIS, ver §6) | t08 (EMPEORA decide, MEJORA no) |
| §4 curva de cenit, noches A94 | `EP:277-282`, `EP:322-331` | informan | ninguna (informativos) |
| §5.1 recuperadas | `EP:291-292` | sí | t13 (r4) |
| §5.2 pares y «más cerca» | `EP:293-300` | sí | t13 |
| §5.3 RESUELTO: mediana en [0,8; 1,25] y signos una cola p ≤ 0,05 | `EP:311` (`20 * num <= den`, exacto en enteros) | sí | t13 (7 de 7); x02 (6 de 7 = 0,0625 NO alcanza) |
| §5.4 ES DEL SENSOR: >30° bajo 0,8 y ≤30° en [0,8; 1,25] | `EP:313` | sí | t13 (r3); x06 (bajo 30 fuera de banda no cumple) |
| §5.5 SIN SUSTRATO <5 pares; empate exacto sale y se lista; grupo vacío no cumple regla 4 | `EP:300, 309, 305-308` | sí (pares = sin empate, adenda 3.8) | t13 (4 pares); x07 (empate); x08 (grupo vacío) |
| §5 precedencia 5, 3, 4, 6 | `EP:309-316` | sí | t13 |
| §6 orden 1 a 6 | `EP:520-535` | sí, fila por fila; `_rojo` trata todo estado distinto de OK como rojo (`INCOMPLETO` incluido) | t17, t02, t03, t04, t05, t07, t08, t06 |
| §6 atribución (¿PM-geo5 y PM-sens también la pierden?) | `EP:186` | sí | t02 |
| §8.1 K = producción (control_arnes de MOD-B + predicado del evaluador = del runner) | `EP:402-410` sobre `evaluar_mxd03.control_arnes` | sí | t09 |
| §8.2 PM = S159 (npix y VRP a 1e-6) en comunes; INDECIDIBLE si ninguna común tiene píxeles (adenda 3.11) | `EP:413-438` | sí | t10 (sólo VRP; npix sin prueba, ver VCM-03) |
| §8.3 placebo d′ = 0 | `EP:441-452` (`dprima_max_abs == 0` y ganancia 1,2 a 1e-9) | sí | t16; mutación `placebo_sin_ganancia` |
| §8.4 nulo del contador (a), (b) y +50 exactos (adenda 3.10) | `EP:455-498` | sí | t16; mutación `contador_sin_inyectar` |
| §8.5 cobertura: mismos gránulos, sin repetidas, no evaluables aparte | `EP:501-512` | **en parte**: lo que sale del denominador es más ancho que el §8.5 (VCM-01) | t11, t12; x05 (grilla incompleta) |
| §8.6 referencia y población: sha256 y re-etiquetado | `EP:590-607` (sha256_lf de los dos CSV contra `poblacion.json`; `poblacion_mxd03.py --sin-bajar` verifica el MANIFIESTO y re-etiqueta; `control_reetiquetado` compara lab, z, partida, vrp_mirova) | sí | ninguna de la batería (OK_EXT); ensayo (positivo) y mi nulo (§4) |
| §2 población y ventana | `poblacion.json`: 5.465 records, 1.232 gránulos, 2026-03-01 01:35 a 2026-10-16 08:15, protegida 50 / bajo1 42 / neg_limpio 5.110 / sin_info 253 / far_ref 10, 0 duplicados (vol, dt), checkout `80b819828` | sí, exacto al §2 | `unir` INDECIDIBLE si una fila del arnés no está en la población o trae otro lab/z (`EP:627-640`) |
| §2 `sin_info` y `far_ref` no deciden | filtro `lab not in (bajo1, neg_limpio)` en `EP:218` y `_error` en `EP:206-211`; P1/P1b/M filtran por `protegida`/`bajo1` | sí | t15; mutación `sin_info_entra_y_cuenta` |
| §3 brazos | arnés `probe_paquete.py:145-165`: K = `probe_mxd03_ab.brazo(..., latlon=None)` = `procesar_brazo` con la geolocalización de `_interp_geo` (producción); K33 = mismo brazo con `pm.ENABLE_MODIS_MIR_LAMBDA_POR_BANDA` parchado (único consumidor del flag: `process_modis.py:600-601`, A118 cumplida); PM = `probe_portes.procesar(sin_k=True)` con sólo `bajar_par` reemplazado por enlaces duros; variantes `fisica`, `fisica_geo5km`, `sensible`, `pixel`, `fisica_b21` | sí | prueba del arnés (M1 a M6) |
| adenda 1 soporte independiente (±6 h, otro sensor u otro satélite MODIS, cúmulo summit publicado; MIROVA en cualquier canal, regla SN) | `EP:338-359`; `contexto` indexa la referencia con `regla_minimas="SN"` (`EP:619`) | sí | t14; x09 (el mismo MODIS no cuenta) |
| adenda 3.7 mitades con hermana `sin_info` se cuentan y se informan | `EP:223` las marca `invisible` y las deja dentro | sí | ninguna |
| adenda 3.12 S-1, borde del gránulo, costura, K33 = K, cruce con MOD-B | `EP:362-398`, `EP:558`, `EP:643-658` | informan | t19 (borde); el resto sin prueba |

## 3. Mutaciones: las del candado y las que faltaban

**Las del candado.** Re-corrí tres de las 19 (`sin_info_entra_y_cuenta`, `k_ignora_predicado`, `p2_signo_invertido`):
identidad 19 de 19 y las tres ATRAPADAS por las mismas pruebas que en la salida guardada
(`salida_mutaciones_originales_muestra.txt`). No re-corrí las 19 (unas 2 h aquí). Dos notas sobre el instrumento:
(a) `mutar_evaluar_paquete.py` sale con 1 cuando se corre un subconjunto (exige `atr == len(MUTACIONES)`), así que el
código de salida de una corrida parcial no se puede leer como veredicto; la salida guardada v2 dice `[exited with code 0]`
para una corrida de 1 de 19, que por ese `if` no puede dar 0 (SOSPECHA sobre cómo se capturó esa línea; la tabla sí es
consistente con lo que yo obtuve). (b) Tras reemplazar las dos vivas por `sin_info_entra_y_cuenta` no se volvió a correr
la lista entera, sólo la nueva (el material lo declara).

**Las que faltaban.** Escribí 8 mutaciones en `mutaciones_propias.py` (sobre copia, misma batería, mismo criterio S156) y
9 pruebas en `pruebas_extra_verificador.py`. Resultado:

| mutación (regla que rompe) | contra la batería del candado | contra mis pruebas extra |
|---|---|---|
| `bloque_por_pasada` (§4: bloque noche-volcán) | **VIVA** | ATRAPADA por x01_bloque_noche |
| `chillan_p_flojo` (§5.3: p <= 0,10 en vez de 0,05) | **VIVA** | ATRAPADA por x02_chillan_6_de_7 |
| `p1_sin_mirar_k` (§4 P1: cuenta protegidas que K tampoco publica) | **VIVA** | ATRAPADA por x03_p1_k_calla |
| `error_bajo1_al_reves` (§4 P2: bajo 1 MW publicada cuenta como error) | **VIVA** | ATRAPADA por x04_bajo1_sin_publicar |
| `grilla_incompleta_cuenta` (adenda 3.6) | **VIVA** | ATRAPADA por x05_grilla_incompleta |
| `chillan_regla4_sin_bajo` (§5.4 sin la banda de <= 30 grados) | **VIVA** | ATRAPADA por x06_chillan_regla4_bajo |
| `soporte_mismo_modis` (adenda 1, A109) | **VIVA** | ATRAPADA por x09_soporte_mismo_modis |
| `p1b_contraria_decide` (control positivo del corredor) | ATRAPADA por t07_p1b | no probada (ya la caza la batería) |

Salidas: `salida_mutaciones_propias_g1.txt`, `_g2.txt` (contra la batería) y `salida_mutaciones_propias_vs_extras_g1.txt`, `_g2.txt` (contra las extras). Las 7 vivas caen 7 de 7 contra las pruebas extra, cada una por la prueba que la apunta.

Las 7 vivas NO son defectos del evaluador: las 9 pruebas extra pasan contra `evaluar_paquete.py` (9 de 9), o sea que hoy
esas reglas están bien escritas. Son reglas selladas sin vigilancia: una edición futura que las rompa pasaría la batería en
verde. Por qué la batería no las ve: `base()` tiene una pasada por noche (los bloques coinciden con las pasadas), ninguna
alerta bajo 1 MW donde sólo uno de los dos publica, ninguna protegida con K callado, Chillán sólo con 7 de 7 y con 4 de 7,
y ninguna fila con `port_grilla = grilla_incompleta`.

Honestidad sobre mis pruebas: 3 de las 9 (x03, x06, x08) PASAN contra el evaluador vacío porque exigen que algo NO pase
(no vetar, no ES DEL SENSOR); por S156 solas no prueban nada y valen únicamente pareadas con la mutación que cazan.

## 4. Nulo de los controles externos (A110, A116)

La batería recibe `blobs`, `predicado`, `procedencia`, `referencia`, `reetiquetado` y `union` ya en OK (`OK_EXT`), y el
ensayo en seco sólo mide el caso positivo. Medí si pueden ponerse en rojo (`nulo_controles_externos.py`, lote de S159
convertido como en el ensayo, tres corridas del evaluador real):
- A, referencia intacta: `referencia OK`, `reetiquetado OK` (control positivo del instrumento).
- B, copia de la referencia con UNA fila del consolidado cambiada de ALERTA a RUTINA (Láscar VIIRS 2026-10-23):
  `referencia INDECIDIBLE`, `reetiquetado INDECIDIBLE`, veredicto INDECIDIBLE.
- C, una segunda cabecera con otro commit: `procedencia INDECIDIBLE`.
Resultado: `NULO DE LOS CONTROLES EXTERNOS: PUEDEN FALLAR`. Los blobs se comprueban por igualdad de hash en el evaluador
(`EP:578-583`) y en el workflow (`:64-69`, `:113-118`); no les armé nulo aparte.

## 5. Hallazgos (lo peor primero)

### VCM-01. La adenda 3.6 saca del denominador más de lo que el §8.5 sellado permite, y con eso una protegida perdida por el port deja de vetar
- ARCHIVO:LÍNEA: `experiments/_s162_modis_paquete/evaluar_paquete.py:132-141` (`evaluable`), `:184-189` (`p1` sólo mira
  `_ev(filas)`), `:506-508`; `PREREGISTRO.md:154-155` (§8.5) contra `:237-239` (adenda 3.6).
- QUÉ PASA: el §8.5 sellado saca del denominador dos cosas, «volcán fuera del gránulo» y «escena inválida». `evaluable()`
  saca además todo `port_estado` distinto de «ok» (incluido `error: ...`, una excepción del port), `port` vacío y
  `port_grilla == grilla_incompleta`. Para una protegida que K publica y donde el port se cayó o le faltó media grilla, el
  §4 (P1: «protegidas que K publica y el brazo no») contaría una pérdida y el §6 daría NO CANDIDATO; el evaluador la lista
  en `protegidas_fuera_del_denominador` y sigue. La adenda dice «no cambia ninguna regla sellada» y en este punto sí la
  cambia. Tamaño esperable: en MOD-C fueron 10 no evaluables de 413 (8 «fuera del gránulo», 2 «escena inválida»; informe
  de MOD-C en `origin/claude/s162-modis-774bb0`), 2,4 %; con 50 protegidas cabe esperar del orden de una. El port usa una
  grilla de 51 km y K un anillo de 25 km, así que una protegida cerca del borde del gránulo es justo donde K puede
  publicar y el port no.
- CÓMO SE VE EN EL DASHBOARD: invisible (censo retrospectivo); en `resultado_paquete.json` queda como una fila de
  `protegidas_fuera_del_denominador` junto a un veredicto que puede decir CANDIDATO.
- CÓMO REPRODUCIRLO: `t12_fuera_del_denominador` de la batería lo exhibe (protegida con
  `port_estado=volcan_fuera_del_granulo` y veredicto CANDIDATO); para `grilla_incompleta`, mi `x05_grilla_incompleta`
  (pasa: la protegida sale del denominador y el veredicto es CANDIDATO).
- CONFIANZA: CONFIRMADO (leído y medido).
- GRAVEDAD: 3. Puede torcer NO CANDIDATO en CANDIDATO, aunque la fila listada lo deja a la vista de quien lea el JSON entero.
- Cambio chico posible (lo decide quien orquesta): o P1 cuenta como pérdida toda protegida publicada por K cuyo motivo de
  exclusión no sea uno de los dos del §8.5 (`volcan_fuera_del_granulo`, `escena_invalida`), o la adenda 3.6 se reescribe
  como lo que es, una ampliación del §8.5, y se vuelve a sellar. Una tercera salida: que el veredicto pase a DECIDE
  NICOLÁS si la lista no está vacía.

### VCM-02. El candado no fija el arnés ni el evaluador; «procedencia» sólo exige un commit único
- ARCHIVO:LÍNEA: `evaluar_paquete.py:84-86` (`BLOBS_SELLADOS`: sólo los 3 del port) y `:61` (D25); `:587-589`
  (`procedencia`: `len(commits) == 1`); `.github/workflows/probe-s162-modd.yml:64-69, 113-127` (hashes de los 3 del port
  y D25, más `git diff` contra el main congelado SÓLO en `pipeline scripts volcanoes.yaml frontend data/mirova_equivalent`);
  `PREREGISTRO.md:171-172` (§10.3 pide «blobs ... del arnés y del evaluador»).
- QUÉ PASA: ni el workflow ni el evaluador comprueban el hash de `probe_paquete.py`, `grillas.json`, `diagnostico_s1.py`,
  `probe_mxd03_ab.py`, `04_analizar.py`, `evaluar_mxd03.py` ni `evaluar_paquete.py`. El `git diff` contra el main
  congelado no cubre `experiments/`. Un disparo desde un árbol con un arnés editado pasaría todos los controles mientras
  los 4 blobs sellados y `pipeline/`, `scripts/`, `frontend/` sigan iguales; la cabecera guarda el commit, pero el
  evaluador sólo exige que las partes compartan uno, no que sea el del candado. Hoy además no existe tag ni rama de
  disparo (`git ls-remote`: sólo `s162-modd-candado`; ningún tag de MOD-D), lo esperable antes de la verificación.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `grep -n "6a1d797c\|c12f9df4\|3e4afa65" evaluar_paquete.py .github/workflows/probe-s162-modd.yml`
  (hashes de HEAD de `probe_paquete.py`, `evaluar_paquete.py`, `grillas.json`) devuelve 0 líneas.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2. No tuerce el veredicto por sí solo; deja sin candado la mitad del candado que el §10.3 prometió.
- Cambio chico: fijar en el paso «Instrumento» del workflow los hashes de `probe_paquete.py`, `grillas.json`,
  `diagnostico_s1.py`, `probe_mxd03_ab.py` y `04_analizar.py`, y en el evaluador exigir `commits == [sha del tag]` (o al
  menos imprimirlo al lado del veredicto para compararlo con el tag a mano).

### VCM-03. Siete reglas selladas sin ninguna prueba que las vigile (7 mutaciones vivas)
- SCRIPT:SALIDA: `verificador_candado/mutaciones_propias.py` → `salida_mutaciones_propias_g1.txt`, `_g2.txt` (tabla en §3).
- QUÉ PASA: la batería no distingue bloque de pasada, no exige p <= 0,05 en Chillán (acepta 0,10), no comprueba que P1
  exija que K publique, no tiene ninguna alerta bajo 1 MW donde sólo uno publique (el signo del error de `bajo1` puede
  invertirse sin que nada falle), no ejercita `grilla_incompleta`, no exige la banda de cenit bajo en la regla 4 de Chillán
  y deja que el mismo satélite MODIS cuente como soporte independiente. Hoy el evaluador las cumple (mis 9 pruebas pasan).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -I verificador_candado/mutaciones_propias.py` (48 min las 8) y
  `python -I verificador_candado/pruebas_extra_verificador.py`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2 hoy (el código está bien); 4 si alguien edita el evaluador antes del censo sin estas pruebas.
- Cambio chico: sumar las 9 pruebas extra a la batería (o las 7 mutaciones a la lista) antes del despacho.

### VCM-04. Control 2: `npix` sin prueba que lo vigile, y tolerancia 1e-6 MW con dependencias del runner sin fijar
- ARCHIVO:LÍNEA: `evaluar_paquete.py:429-432`, `:76` (`TOL_PORT_S159 = 1e-6`); `probe-s162-modd.yml:106-111`
  (`pip install` sin versiones); `t10_control_s159` sólo cambia `vrp_mw`.
- QUÉ PASA: quitar la comparación de `npix` (`igual = True and (...)`) sobreviviría a t10 (no la corrí: es la única de mi
  lista que no probé, lo digo). Y si numpy o scipy del runner del censo difieren de los del run 39712862945 y un píxel al
  filo del umbral cambia, el control 2 pone INDECIDIBLE a todo el censo (17 h) por una razón que no es del arnés.
  Precedente a favor: MOD-C reprodujo 13 de 13 pasadas de S159 en `npix` en otro runner (informe de MOD-C, tabla de
  controles).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: no se puede sin red; se sabrá en el humo (dos pasadas comunes con S159).
- CONFIANZA: SOSPECHA (la fragilidad); CONFIRMADO (la ausencia de prueba de `npix`).
- GRAVEDAD: 1. La dirección del fallo es segura (INDECIDIBLE), no un falso CANDIDATO.

### VCM-05. El grupo de concurrencia guarda un solo run pendiente: dos tandas empujadas seguidas se desplazan
- ARCHIVO:LÍNEA: `probe-s162-modd.yml:21-23` (`group: probe-s162-modd`, `cancel-in-progress: false`), `:9-10` (el
  comentario manda «una tanda a la vez»).
- QUÉ PASA: es la lección de S125/S126 del `CLAUDE.md` (GitHub mantiene un run pendiente por grupo). Si `s162-modd-t2` y
  `s162-modd-t3` se empujan mientras `t1` corre, una de las dos se pierde sin error. Hoy sólo lo protege el procedimiento.
- CÓMO SE VE EN EL DASHBOARD: invisible; en el evaluador se vería como `cobertura INDECIDIBLE` (faltan 8 partes).
- CONFIANZA: CONFIRMADO (leído; el mecanismo es el documentado en el proyecto, no lo reproduje).
- GRAVEDAD: 1 (fallo en dirección segura, cuesta tiempo).

### VCM-06. Detalles del instrumento (gravedad 1, todos CONFIRMADOS)
- K33 en `armar_tabla` (`EP:160-163`) usa la publicación del runner y `pc_vrp` del record, no el predicado del evaluador
  ni la magnitud mostrada como los otros brazos; informa, pero su P1b no es comparable con el de los demás (en el ensayo
  da 27 porque el ensayo pone K33 = None).
- `probe_paquete.blob` (`:68-71`) hashea bytes crudos y el del evaluador normaliza CRLF: en este worktree de Windows
  (`core.autocrlf=true`) los 4 archivos están en CRLF, así que el probe saldría con «blobs distintos» si se corriera aquí;
  en el runner (LF) no pasa. No es defecto; es otra razón por la que el arnés sólo corre en Linux.
- La batería tarda 6 min aquí, no 3 a 4; la corrida completa de mutaciones serían unas 2 h, no 70 min.
- El job `prueba` no corre `probar_evaluar_paquete.py` ni las mutaciones (se corren a mano); el criterio del humo (adenda
  3.14) depende de correr el evaluador localmente sobre los artefactos. Está dicho, pero el workflow no lo deja en un log.
- Observación del ensayo, no del candado: en el lote de S159 `PM-geo5` pierde 3 protegidas y `PM-b21` 28; son brazos
  informativos, pero conviene tenerlo presente al leer el censo.

## 6. VERIFICADO LIMPIO (qué no hace falta volver a mirar, y con qué comando)

- **Blobs sellados**: `git hash-object` de `probe_portes.py`, `mirova_port.py`, `mirova_v750_r2.py` y
  `evaluar_d25_ded217af4.py` = `8ec50e7b`, `96769a89`, `07da7010`, `1dbabf65`, iguales a los del evaluador, el arnés y el
  workflow; `evaluar_d25_ded217af4.py` es byte a byte el blob de `ded217af4:experiments/_s157_prereg_d25/evaluar_d25.py`
  (`git diff` vacío); `04_analizar.py` (`6560b927`), `probe_portes.py` y `mirova_port.py` son los mismos blobs que en
  `origin/s159-pruebas`.
- **Árbol = main congelado fuera de experiments/**: `git diff --name-only 80b819828 HEAD | grep -v ^experiments/` da sólo
  los dos workflows; 0 borrados. La rama parte de `origin/s162-mxd03-codigo` (`merge-base` = su HEAD `afb3fcdea`).
- **Población sellada**: `poblacion.json` con checkout `80b819828`, ventana 2026-03-01 a 2026-10-16, `regla_minimas SN`,
  5.465 records en 1.232 gránulos, 24 partes que suman 1.232, 0 duplicados, 0 `noche` o `z` vacíos; etiquetas
  50/42/5.110/253/10 exactas al §2; Chillán con 10 alertas (9 protegidas, 1 bajo 1 MW) como dice el §5.
- **Humo**: las 5 claves del workflow existen en la población con los papeles que dice la adenda 3.14 (Láscar 03-14 07:05
  bajo1 0,97 común con S159; Láscar 03-27 07:10 protegida 1,0; Chillán 10-10 07:40 protegida 3,95 expuesta; Chillán 10-16
  01:40 protegida 12,39 común con S159; Villarrica 04-30 03:00 negativo limpio). `--solo` filtra sobre todos los gránulos,
  no sólo la parte 0 (`probe_paquete.py:194-195`).
- **K es producción**: `probe_mxd03_ab.brazo(..., latlon=None)` → `probe_etiquetas.procesar_brazo` con `calculate_vrp` +
  `store.append_record` y la geolocalización de `read_modis_l1b` (`_interp_geo`), store en temporal; flags por
  `VRP_PROFILE=mirova_equivalent` (workflow `:72, :131` y `setdefault` en `probe_paquete.py:52`). K33 parchea el único
  consumidor del flag D33 (`grep ENABLE_MODIS_MIR_LAMBDA_POR_BANDA pipeline/`: `process_modis.py:173, 600, 601`; A118).
- **PM es el port sin tocar**: `PP.procesar(o, destino, outdir, sin_k=True)` con sólo `bajar_par` parchado (enlaces duros,
  borrados al salir); la prueba M3 exige identidad con `mirova_port.correr` directo (40,9754 MW en los dos). Las 5
  variantes se guardan; `port_estado`, `grilla_incompleta`, `saturados` y `motivo_vacio == escena_invalida` existen con
  esos nombres en `probe_portes.py:306-339` y `mirova_v750_r2.py:155`.
- **Predicado = tablero con node (A97)**: el evaluador y el runner arman el mismo `slim` (CAMPOS_JS + `anomaly_pixels`
  con lat, lon, vrp_mw, bt_k) y leen `p[4]`/`p[3]` de `banco_paridad.correr_node`; el control 1 exige que ambos den la
  misma publicación de K (`EP:406`); el sha256 de `frontend/index.html` viaja en la cabecera y se compara (`EP:584-586`).
  Para MODIS la magnitud mostrada es `pc.vrp_mw` (`index.html:1162-1183`; `mirovaEqVrpCore` devuelve `base` si el sensor
  no es VIIRS 375, `:1295-1305`), así que la elección 5 de la adenda 3 es equivalente a `pc.vrp_mw` hoy.
- **D-45 y D-28 tal cual**: `prueba_signos_p2` exacta con B <= 20 y 10.000 sorteos (semilla 162) sobre eso;
  `regla_signos_p2` SIN SUSTRATO con B <= 4, 5 % en enteros; `regla_m` intervalo 95 % de la mediana por bloques;
  `comparar_con_ganancia` redondea d′ a 12 decimales, por eso el placebo da exactamente 0 (ensayo: `placebo OK`, 78 pares).
- **Controles pueden fallar**: 19 de 19 pruebas fallan por aserción contra el vacío; 18 + 1 mutaciones del candado
  atrapadas (3 re-corridas aquí); `referencia`, `reetiquetado` y `procedencia` se ponen en rojo con datos alterados (§4).
- **Ensayo en seco**: reproduce número por número la salida guardada.
- **Dependencias del job `prueba`**: `numpy scipy pyyaml pyproj` son exactamente los paquetes de terceros que
  `probar_probe_paquete.py` carga (medido con `rastrear_deps_probar_probe.py`).
- **Workflow**: `"on":` entre comillas (A43), `set -o pipefail` con `tee` (S141), sólo `EARTHDATA_TOKEN` y falla al
  instante si viene vacío (A71, `probe_paquete.py:179-180` y `:97-101` del yml), `permissions: contents: read`, 24 partes
  con `max-parallel 8` y 240 min cada una (unas 228 pasadas por parte, A15 holgado), `if-no-files-found: error`.
- **Cobertura y duplicados**: una pasada sin fila, con `estado` distinto de ok o repetida en los artefactos da
  INDECIDIBLE (t11, `EM.control_cobertura`, `EM.control_duplicados`); `unir` da INDECIDIBLE si una fila trae otro lab o z
  que la población.
- **Mitades con hermana sin_info** se cuentan y se marcan `invisible` (adenda 3.7, `EP:223`), como el §4 manda.

## 7. Veredicto

**Se puede despachar el humo con cambios chicos.** Ninguno toca `pipeline/`; ninguno exige re-sellar reglas salvo que se
elija la segunda salida de VCM-01:
1. VCM-01: decidir, antes del humo, qué pasa con una protegida que K publica y el port no pudo evaluar por un motivo fuera
   de los dos del §8.5 (contarla en P1, o DECIDE NICOLÁS si la lista no está vacía, o re-sellar la ampliación).
2. VCM-02: fijar los hashes del arnés y de sus módulos en el paso «Instrumento» del workflow, y que el evaluador compare el
   commit de las cabeceras con el del tag (o lo imprima junto al veredicto).
3. VCM-03: sumar las 9 pruebas extra (`pruebas_extra_verificador.py`) a la batería o las 7 mutaciones vivas a la lista,
   para que el evaluador quede vigilado en esas reglas antes de que alguien lo edite.
Lo demás (VCM-04 a VCM-06) se informa y no bloquea.

Pendientes que no me correspondían y no hice: commit, push, tag, rama de disparo, despacho.
