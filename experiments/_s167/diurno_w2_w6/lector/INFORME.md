# Lectura del A/B diurno sobre K, W2 a W6 (tarea 1.32, D-10, issue #813), S167

Lectura hecha el 2026-10-28 (consulta CMR a las 21:46:17 UTC) con el procedimiento sellado: pre-registro v3.1 más la
adenda 1 (§11, regla a y b'), opción del caso e **e-ii**. Nada del repo se editó, commiteó ni despachó. Todo corrió
fuera del repo, en `D:\vrp-trabajo\temporales\s167_diurno_lectura\`, con `python -I` (Python 3.12.10, scipy 1.17.1,
numpy 2.4.4, node v22.16.0).

## 1. Veredicto (tal como lo imprime el evaluador)

```
VIIRS375: P2 EMPATE (neto +0, B 9, p_gana 0.6094, p_pierde 0.6094) | protegidas 9 de 26 | alertas<1MW 5 de 10 | negativos 5 de 2246 (Q_d 0.0022) | Q_n 0.0367 (1606) | D True (14 de 36 alertas) | neg>=1MW 2 | pub en «otra» 0 | razón mag 0.9329905239687848
   -> ADOPTAR (caso b, opción e-ii)
VIIRS750: P2 SIN SUSTRATO (neto +0, B 0, p_gana 1.0000, p_pierde 1.0000) | protegidas 2 de 6 | alertas<1MW 0 de 0 | negativos 0 de 2416 (Q_d 0.0000) | Q_n 0.0093 (2375) | D True (2 de 6 alertas) | neg>=1MW 0 | pub en «otra» 2 | razón mag 1.0701747569672098
   -> ADOPTAR (caso b, opción e-ii)
GLOBAL (principal): DECIDE NICOLÁS
VARIANTES: {'tabla': 'DECIDE NICOLÁS CON M4', 'sin_W2': 'DECIDE NICOLÁS', 'sin_reflejo': 'DECIDE NICOLÁS', 'otra_como_negativo': 'DECIDE NICOLÁS CON M4'}
VEREDICTO FINAL (§6.4): DECIDE NICOLÁS
```

- **VIIRS 375: ADOPTAR, caso b** (neto 0 ≤ 0, P = 9 ≥ 1, D cumple).
- **VIIRS 750: ADOPTAR, caso b** (neto 0, P = 2, D cumple con Q_d = 0).
- **Global y final: DECIDE NICOLÁS.** Motivo según la regla sellada (§6.3, `veredicto_global`): VIIRS 750 en ADOPTAR
  manda a DECIDE NICOLÁS porque para VIIRS 750 manda el código de MIROVA (K1 diurno -0,5 y filtro de reflejo de 12°) y
  la rama diurna usa la Tabla 1 (K1 -0,6). El §6.3 dice que adoptarlo pide antes llevar la rama de VIIRS 750 al código
  o separar el flag por sensor. Como el principal no es ADOPTAR ni NO ADOPTAR, el §6.4 no agrega motivo (la salida trae
  `motivo` vacío), pero dos variantes caen en el caso e (abajo).
- R1 (protegidas que el control publica y el brazo no): **0**.

### Cifras que sostienen el veredicto (principal)

| | VIIRS 375 | VIIRS 750 |
|---|---|---|
| protegidas diurnas recuperadas (P / observadas) | 9 / 26 (las 9 con 1 MW o más) | 2 / 6 (las 2 con 1 MW o más) |
| alertas bajo 1 MW recuperadas | 5 / 10 | 0 / 0 |
| publicaciones en negativos diurnos limpios | 5 / 2.246 (Q_d 0,22 %) | 0 / 2.416 (Q_d 0) |
| de ellas con 1 MW o más | 2 | 0 |
| Q_n (control, negativos nocturnos) | 3,67 % (de 1.606) | 0,93 % (de 2.375) |
| P2 diurno | EMPATE: neto 0, 10 discordantes en 9 bloques, exacto, p 0,61 / 0,61 | SIN SUSTRATO: 0 discordantes |
| D | cumple (14 de 36 alertas) | cumple (2 de 6, Q_d 0) |
| publicaciones en «otra» | 0 | 2 |
| razón de magnitud brazo / MIROVA (mediana, informativa) | 0,93 | 1,07 |
| negativos publicados por elevación solar | 0 a 30°: 3; 30 a 60°: 2 | ninguno |

### M4 (transcrito de la salida; §6.5 lo pide para el caso e, que aparece en dos variantes)

Por ventana (P = protegidas recuperadas, amb = alertas bajo 1 MW, neg = negativos publicados):

| ventana | VIIRS 375 P | amb | neg | VIIRS 750 P | amb | neg |
|---|---|---|---|---|---|---|
| W2 | 0 / 11 | 0 / 1 | 1 / 485 | 0 / 1 | 0 / 0 | 0 / 605 |
| W3 | 0 / 1 | 1 / 2 | 2 / 386 | 0 / 0 | 0 / 0 | 0 / 404 |
| W4 | 3 / 5 | 2 / 4 | 0 / 490 | 0 / 2 | 0 / 0 | 0 / 505 |
| W5 | 1 / 4 | 1 / 2 | 1 / 525 | 0 / 1 | 0 / 0 | 0 / 522 |
| W6 | 5 / 5 | 1 / 1 | 1 / 360 | 2 / 2 | 0 / 0 | 0 / 380 |

Protegidas recuperadas, VIIRS 375: Nevados de Chillán 2026-10-01 18:42, 10-08 19:30, 10-10 18:18, 10-10 18:54,
10-11 19:36; Puyehue-Cordón Caulle 08-20 17:30; Villarrica 08-17 19:06, 08-21 18:54, 09-18 19:06.
VIIRS 750: Nevados de Chillán 10-01 18:42 y 10-10 18:18.

Protegidas no publicadas, VIIRS 375 (17): Chaitén 09-11 18:12; Isluga 07-25 17:24, 08-31 17:30, 09-14 18:42; Láscar
06-15 17:24, 06-24 17:36, 06-24 18:00, 06-28 17:30, 06-28 18:24, 08-27 17:42, 09-19 17:30; Lastarria 06-15 17:24,
06-28 17:30, 06-28 18:06, 06-28 18:24, 06-29 17:42, 06-30 17:24. VIIRS 750 (4): Isluga 06-21 18:36 y 09-04 18:30;
Planchón-Peteroa 08-14 17:42; Tupungatito 08-20 17:30. (Lo que sigue es un cruce de listas, no una interpretación: 13
de las 17 de VIIRS 375 y las 4 de VIIRS 750 están en la lista de reflejo probable del estudio 1.13 que usa la variante
sin_reflejo; ver §3.)

Negativos diurnos publicados, VIIRS 375 (5): Nevados de Chillán 10-09 19:12; Puyehue-Cordón Caulle 06-13 18:00,
07-29 18:36, 07-29 19:24; Villarrica 09-17 18:48. VIIRS 750: ninguno.

Filtro de reflejo de 12° (informativo, §7): apaga 0 publicaciones diurnas; 0 sin ángulos; con el filtro, los dos
sensores siguen en ADOPTAR (caso b). Instrumento 1.13 a) sobre lo nuestro: VIIRS 375 25 consistentes, 5
desproporcionadas, 1 aislada; VIIRS 750 5 consistentes.

## 2. Compuertas de instrumento (§5)

`COMPUERTAS: inválido 0, indecidible 0`.

- **I1** (cableado de K): por log, 110 logs (22 por ventana), los 110 con línea `FLAGS_BRAZO`, sin problemas; por
  record, ninguno con Test 1 ni fuente `test1`/`test1_roi` y `regimen.codigo_sha` igual al tag en todos. Comprobación
  propia aparte: 27.519 records de los dos brazos, los 27.519 con `codigo_sha` = `68687d2d4b...`, 0 con
  `triggered_test1`.
- **I2** (la palanca actuó): sin problemas.
- **I3** (cobertura nocturna contra la referencia, sólo records nocturnos): COBERTURA OK; 7.300 pasadas por lado,
  7.254 observadas, 0 con falta de cobertura, 46 no observadas iguales en los dos brazos.
- **I4** (cobertura diurna): VIIRS 375, 0 de 2.547 pasadas diurnas sin record del brazo; VIIRS 750, 17 de 2.499 (falla
  desde 22 según el §5, p_sup 0,0059). Ninguna alerta diurna sin record (I4a) ni volcán-día vacío (I4b). Las 17 de
  VIIRS 750 son todas RUTINA de la tabla, 0,0 MW, entre 19:06 y 20:12 UTC (listadas en
  `informativo\detalle_variantes_salida.txt`).
- **I5** (noches intactas): 0 records nocturnos en un solo brazo; 0 records nocturnos con otros campos distintos.
- **I6** (placebos): VIIRS 375 placebo a y b SIN SUSTRATO (2 bloques), placebo c 0 falsos y 0 GANA de 40; VIIRS 750 a y
  b SIN SUSTRATO (0 bloques), c 0 y 0. Es el límite declarado en el §5 (V9): con un brazo callado el placebo a no tiene
  sustrato.

Cobertura de cada corrida (`cobertura.txt`, leída antes del veredicto): las cinco dicen «COBERTURA NOCTURNA PAREJA y día
como se espera».

| ventana | run | commit de salidas | noche por brazo | faltan / sobran | diurnas V375 / V750 del brazo |
|---|---|---|---|---|---|
| W2 | 40379112237 | `9e997518bf80` | 2.154 | 0 / 0 | 863 / 853 |
| W3 | 40496903128 | `5631255c702f` | 1.429 | 0 / 0 | 561 / 559 |
| W4 | 40545948109 | `633779107472` | 2.266 | 0 / 0 | 906 / 898 |
| W5 | 40617142287 | `d835531baeb1` | 2.386 | 0 / 0 | 949 / 937 |
| W6 | 40681454167 | `e70c3146a80f` | 1.593 | 0 / 0 | 672 / 665 |

Los cinco números nocturnos coinciden con la bitácora. W2 tuvo un solo intento (run 40379112237, 23 de 23 jobs según
la bitácora de S165 vuelta 1); no hubo unión de intentos. El padre de los cinco commits de salida es `68687d2d4`.

## 3. Robustez (§6.4) y variantes informativas

| variante | global | VIIRS 375 | VIIRS 750 |
|---|---|---|---|
| tabla sola | **DECIDE NICOLÁS CON M4** | caso e-ii: neto +1, P 6 de 6, amb 4 de 7, neg 5 de 2.271, D cumple (10 de 13) | ADOPTAR b: P 2 de 2, neg 0 de 2.422 |
| sin W2 | DECIDE NICOLÁS | ADOPTAR b: neto -1, P 9 de 15, neg 4 de 1.761 | ADOPTAR b: P 2 de 5 |
| sin reflejo probable (17 pasadas) | DECIDE NICOLÁS | ADOPTAR b: P 9 de 13, neg 5 de 2.246 | ADOPTAR b: P 2 de 2 |
| «otra» como negativo | **DECIDE NICOLÁS CON M4** | ADOPTAR b: neg 5 de 2.509 | caso e-ii: neto +1, P 2 de 6, neg 1 de 2.475 (Nevados de Chillán 10-10 18:54, de 1 MW o más) |

El global de cada variante es el que imprime el evaluador sellado; el detalle por sensor sale de
`informativo\detalle_variantes.py`, que no está sellado y no decide: repite las mismas llamadas de `evaluar_completo` y
reproduce exacto el principal sellado (mismo global, mismas cifras), lo que sirve de control de que repite bien.

Variantes de la regla de mínimas (informativas, `docs/MISSION.md` punto 5): SE, original y SN 0,04 dan DECIDE NICOLÁS;
con el filtro de 12°, DECIDE NICOLÁS. La salida dice que ninguna cambia el veredicto principal.

Lo que el §6.5 dice que hay que mirarle a M4 (para Nicolás): M4 por sensor y por ventana con la lista de pasadas de
cada lado (§1), la cuenta de publicaciones de 1 MW o más en negativos (2 en VIIRS 375, 0 en VIIRS 750; 1 en VIIRS 750
en la variante «otra como negativo»), las variantes del §6.4 (tabla de arriba) y la informativa con el filtro de 12°
(no apaga nada).

## 4. Días excluidos (adenda 1)

**Ninguno.** `dias_excluidos_nasa.py` consultó CMR a las 2026-10-28T21:46:17Z sobre la caja -72,5 -39,5 a -67,5 -23,0:
los seis productos (`VNP02IMG`, `VJ102IMG`, `VJ202IMG`, `VNP02MOD`, `VJ102MOD`, `VJ202MOD`) tienen gránulos todos los
días de W2 a W6, así que la condición (a) no se cumple ningún día y `excluir_dias = []`, evidencia vacía. Informativo,
regla (b) original: tampoco excluye nada; el control pierde pasadas nocturnas de MIROVA de VIIRS 750 el 2026-06-17,
07-24, 08-13, 09-09, 10-05, 10-10 y 10-12, pero sin día vacío en CMR. Coincide con lo que el §11 anticipaba.

## 5. Código, referencia y comprobación de sha256

- Commit sellado del pre-registro (tag `s163-diurno-k-sellado` y `s163-diurno-k-codigo`, los dos apuntan a él):
  `68687d2d4b73bb0527da18a2c886a6dcc241a0ac` (objetos de tag `0ce05f81...` y `6025f28c...`, comprobados con
  `git ls-remote`). Es el `--sha-codigo`.
- Commit de la adenda 1: `4b86059706d9fd52c8bf166f485446a0e40652b5`; su sello vigente es
  `objetivos_adenda1_sha256.txt` del commit `af5af6a17` (que sólo cambia ese archivo respecto de `4b86059`). Ojo: el
  mismo archivo dentro de `4b86059` es la versión anterior (apunta a `038c6904b`) y con él 4 de 7 no calzan; el
  vigente es el de `af5af6a17`, igual al de `origin/main` (`ac967ead6`), y con él calzan 7 de 7.
- Árbol de código: `git -c core.autocrlf=false archive 4b86059 <las 29 rutas> <las 7 de la adenda> <los dos
  objetivos>` más `objetivos_adenda1_sha256.txt` de `af5af6a17`, en `codigo\`.
- **Sello original** (`objetivos_sha256.txt`, 29 rutas): los 29 blobs de `68687d2d4` calzan (29 de 29). En `4b86059`
  calzan 28; el que no es `PREREGISTRO.md`, que la adenda cambió y re-selló. Los archivos extraídos: 28 de 28 iguales
  (más el PREREGISTRO de la adenda). `evaluar_diurno_k.py` = `d6eb25b5...` (igual en `origin/main`).
- **Sello de la adenda** (7 rutas): 7 de 7 contra los blobs de `4b86059` y contra los archivos extraídos.
  `PREREGISTRO.md` = `44c3b011...`, igual al de `origin/main`.
- Referencia congelada: `congelar_referencia.py --commit 047bd5692319569a9404ac5d1b41dc5359510a6d` (de
  `sustrato_k.json`, `commit_referencia`), en `ref\`; los 4 CSV dan OK contra `sustrato_k.json` (consolidado
  `4057e2f0...`, OCR `44576c52...`, filas perdidas `c6ef10ea...`, respaldo `183aff7f...`). El evaluador vuelve a
  comprobarlos y no se negó.
- Salidas de las corridas: `git archive` de `experiments/_s151_ab_diurno/salidas/<run>` de cada rama
  `s151-ab-diurno/<run>`, en `corridas\` (22 JSON y 22 logs por ventana).

## 6. Comandos exactos (Git Bash; `W=D:/vrp-trabajo/temporales/s167_diurno_lectura`, `S=$W/corridas/experiments/_s151_ab_diurno/salidas`)

```
GIT_DIR="C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/.git" python -I $W/codigo/experiments/_s163_diurno_k/congelar_referencia.py --commit 047bd5692319569a9404ac5d1b41dc5359510a6d --salida $W/ref

python -I $W/codigo/experiments/_s163_diurno_k/dias_excluidos_nasa.py --raiz $S/40379112237 --raiz $S/40496903128 --raiz $S/40545948109 --raiz $S/40617142287 --raiz $S/40681454167 --ref $W/ref --salida $W/dias_excluidos_W2_W6.json

python -I $W/codigo/experiments/_s163_diurno_k/evaluar_con_exclusion.py --raiz $S/40379112237 --raiz $S/40496903128 --raiz $S/40545948109 --raiz $S/40617142287 --raiz $S/40681454167 --ref $W/ref --sha-codigo 68687d2d4b73bb0527da18a2c886a6dcc241a0ac --opcion-e e-ii --excluidos $W/dias_excluidos_W2_W6.json --salida $W/evaluacion_W2_W6.json
```

Los tres con rc 0 (3 min y 4 min 40 s los dos últimos). `GIT_DIR` hace falta porque `congelar_referencia.py` llama a
`git -C <raíz del árbol>` y el árbol extraído no es un repositorio.

## 7. Archivos de salida (stdout y stderr enteros)

| archivo | sha256 |
|---|---|
| `D:\vrp-trabajo\temporales\s167_diurno_lectura\congelar_referencia_salida.txt` | `880288ce...` |
| `D:\vrp-trabajo\temporales\s167_diurno_lectura\dias_excluidos_salida.txt` | `f0c57672...` |
| `D:\vrp-trabajo\temporales\s167_diurno_lectura\dias_excluidos_W2_W6.json` | `8bb05abc...` |
| `D:\vrp-trabajo\temporales\s167_diurno_lectura\evaluar_con_exclusion_salida.txt` | `9aa96cd5...` |
| `D:\vrp-trabajo\temporales\s167_diurno_lectura\evaluacion_W2_W6.json` | `1211f927...` |
| `D:\vrp-trabajo\temporales\s167_diurno_lectura\informativo\detalle_variantes.py` (no sellado) | `75a86ed1...` |
| `D:\vrp-trabajo\temporales\s167_diurno_lectura\informativo\detalle_variantes_salida.txt` | `5155cafb...` |

## 8. Lo que no se comprobó o merece mirarse

- No re-corrí la batería ni las mutaciones del evaluador ni de la adenda: sólo comprobé que los blobs son los sellados.
- No comprobé que los commits de salida de cada run sean los que produjo el workflow (confío en que la rama
  `s151-ab-diurno/<run>` es la del run; el padre de los cinco es el commit sellado, y I1 por record da el sha del tag
  en los 27.519 records).
- La lectura se apoya en una consulta a CMR hecha hoy, no en la hora de las corridas; el catálogo podría haber cambiado
  entre una y otra (SIN DATO). Como ningún día queda vacío, no cambiaría la lista salvo que NASA hubiera borrado
  gránulos.
- El global principal es DECIDE NICOLÁS por la regla de VIIRS 750 del §6.3, y no CON M4; el caso e aparece sólo en las
  variantes tabla (VIIRS 375) y «otra como negativo» (VIIRS 750). Lo dejo dicho sin interpretarlo.
- El evaluador sellado no guarda el detalle por sensor de las variantes; el que doy en §3 sale del script informativo
  no sellado (que reproduce el principal exacto).
- El cálculo y la consulta a CMR los hizo una sola instancia; falta el verificador limpio de otro modelo que pide la
  bitácora.
