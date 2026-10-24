# Tercer verificador: sonda S150 de los tres campos (correcciones a V2)

**Objeto.** Commit `aae4a4ed0` de la rama `s150-sonda-tres-campos`, diff `5eda5b942..aae4a4ed0` (8 archivos:
`evaluar.py`, `prueba_local.py`, `prueba_local_salida.txt`, `sellar.py`, `sonda.py`, `DISENO.md`, el yml y el informe
V2). Las correcciones responden a `docs/audit_s150/VERIFICADOR2_SONDA_TRES_CAMPOS.md`.

**Límites que respeté.** Sin checkout, commit ni push en el árbol (sigue en `main`). Extraje con `git archive aae4a4ed0 <rutas>` a
`C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\ec53cbb6-245a-4ae2-837c-847d5aeff298\scratchpad\verif3\`
y `5eda5b942` a `...\scratchpad\verif3old\` (con el `prueba_local.py` nuevo encima, para correr P7b contra el código
viejo). En `verif3` hice un `git init` propio para P8 y copié el mismo TIF de Chaitén de la ronda anterior para P4. Sin
despachos, sin sello, sin NASA, sin credenciales. Los scripts quedan en `verif3`: `solo_p7b.py`, `ataques.py`,
`ataques2.py`, `ataques_v3.py` (con `ataques_v3_salida.txt`), `candado.sh` y `plan.sh`.

## Veredicto

**Todavía no, pero falta poco.** Las doce correcciones hacen lo que dicen, y lo medí. Pero el 5 % por grupo abrió un
camino a CONFIRMA (N2, gravedad 3). Quedan además tres huecos chicos: D22 leída en M con un M muerto, la tabla H3
que deja leer D22 cuando D22 está frenada, y un piloto que puede correr los 35 lotes. Los cuatro viven en `evaluar.py`
o en el yml, que quedan sellados. Si se dejan para después del piloto, §10 bis exige otro verificador. Conviene
cerrarlos antes de sellar: son unas veinte líneas y cuatro casos de prueba.

## 1. Los 12 casos de P7b: fallan en `5eda5b942`, pasan en `aae4a4ed0`

VERIFICADO con `solo_p7b.py`, que corre P3 (la salida sintética) y después sólo `p7b_segundo_verificador` sobre cada
árbol:

| caso | `5eda5b942` | `aae4a4ed0` |
|---|---|---|
| V2-1 M muerto | FALLA: `REFUTA (R_L 0.00 ...)` | OK: `INDETERMINADO POR INSTRUMENTO: M no publica las alertas de MIROVA...` |
| V2-2 `nativo|min` publica `negativo_b_no_publica` | FALLA: `CONFIRMA (... brecha 0.973)` | OK: reproducción, 42 de 42 |
| V2-2 `nativo|max` publica 30 % del residual | FALLA: `CONFIRMA (... brecha 0.224)` | OK: reproducción, 27 de 84 |
| V2-2 brecha contra el A/B | FALLA: `KeyError: 'gates_h1'` | OK: 0,330 contra 0,330 |
| V2-3 lote 1 sin piloto | FALLA (escribe la tabla) | OK |
| V2-3 clones en todo | FALLA (escribe la tabla) | OK |
| V2-3 candado del yml | FALLA: `no/1` sale 0 | OK: `{no/1: 1, no/: 0, si/: 1, si/1: 0}` |
| V2-4 σ en el piloto | FALLA (`None`) | OK: avisa 12 de 12 distintas |
| V2-5 duplicadas | FALLA: `CONFIRMA (R_L 0.70 sobre 60 ...)` | OK: `INDETERMINADO POR INSTRUMENTO: pasadas duplicadas` |
| V2-6 D22 con 11 | FALLA: `SELECTIVO: recupera 1.00 de 11` | OK: `INDETERMINADO POR COBERTURA` |
| V2-7 log de la sonda | FALLA: 1 print con detección | OK: 0 de 9 |
| V2-10 σ NaN | FALLA: `CONFIRMA` | OK: `INDETERMINADO POR INSTRUMENTO` |

Resultado: 12 de 12 fallan en el viejo y 0 de 12 en el nuevo. El caso del candado que falla en el viejo es justamente
`piloto = no, lotes = 1`, el que V2-3 pedía cerrar.

**`prueba_local.py` completo** sobre `aae4a4ed0`: `RESULTADO: 120 comprobaciones, 0 saltadas, TODO OK`, `exit 0`, en
mi máquina. La salida es idéntica a `prueba_local_salida.txt` salvo la línea del aviso de perfil, que en mi corrida va
por stderr. VERIFICADO con `diff`. Sin el TIF en disco, P4 ahora dice «se omiten las 5 comprobaciones» y el resumen
da `115 comprobaciones, 5 saltadas`: el pendiente que dejé en V2 quedó resuelto.

## 2. Mis ataques de `verif2` contra el código nuevo

VERIFICADO (`ataques.py`, `ataques2.py` y la primera mitad de `ataques_v3.py`):

| ataque | `5eda5b942` | `aae4a4ed0` |
|---|---|---|
| T1 clones en todo | INDETERMINADO | INDETERMINADO (ahora por reproducción también en los negativos) |
| T2 M muerto | REFUTA | INDETERMINADO POR INSTRUMENTO |
| T3b / T3c nativo que no reproduce los negativos | CONFIRMA / CONFIRMA | INDETERMINADO POR INSTRUMENTO / ídem |
| T4 lote 1 sin piloto | tabla y D22 escritos | `h3` y `d22_d26.nativo`: «NO SE ESCRIBE» |
| T5 duplicadas | CONFIRMA | INDETERMINADO POR INSTRUMENTO |
| T6 σ NaN | CONFIRMA | INDETERMINADO POR INSTRUMENTO |
| T7 D22 con 11 | SELECTIVO | INDETERMINADO POR COBERTURA |
| T8 claves del piloto | sin σ ni gránulo | con `sd_dnti_nativo_vs_record_ab`, `sd_dnti_falla`, `mismo_granulo_que_ab`, `duplicadas_falla` |
| T9 gate de registro r_L 0,85 / 0,95 | INDETERMINADO / CONFIRMA | igual (sin cambio, correcto) |

`ataques.py` se cae en T4 con `TypeError: string indices must be integers`, porque `res["h3"]` ahora es un texto: es
la corrección funcionando, no un error del evaluador.

## 3. Caminos nuevos

### N2. Los desvíos que tolera el 5 % por grupo convierten un INDETERMINADO en CONFIRMA. Gravedad 3

**El mecanismo.** El gate tolera hasta 2 de 42 en `negativo_b_no_publica` y 4 de 84 en `residual_apagado` donde el
nativo no reproduce al A/B. Esos mismos desvíos siguen dentro de FP(nativo, max), que es la línea base de ΔFP y de
la brecha. Si todos van en la dirección de inflar FP(nativo, max) y M no los acompaña, ΔFP baja más de lo que baja
la tolerancia (¼ de la brecha).

**Evidencia (VERIFICADO, `ataques_v3.py` N2).** Con M que reabre el 30 % del residual apagado:
- nativo sano: `INDETERMINADO (R_L 0.81 sobre 32; dFP 0.106, brecha 0.330 ...)`;
- nativo con 2 desvíos en `negativo_b_no_publica` y 4 en `residual_apagado`, todos dentro del máximo, con 0 fallas
  sobre el máximo en el gate: `CONFIRMA (R_L 0.81 ...; dFP 0.060, brecha 0.283)`.

Con 40 % de reapertura sigue en INDETERMINADO. El corrimiento está acotado: el techo de reapertura sube de un 25 % a
cerca de un 35 % del residual. Pero es un CONFIRMA que el criterio §6 no daría con el nativo sano. Que pase de verdad
es poco probable, porque el gate de σ en pie deja poco espacio a desvíos en masa. La corrección es barata y quita el
problema de raíz.

**El cálculo de la brecha mínima (unos 0,27) es correcto.** Repetí el peor caso a mano:
0,330 − 0,0306 − 0,0314 − 0,0013 ≈ 0,267. El máximo es ≈ 0,362. La guarda `brecha ≥ 0,10` ya no puede dispararse
mientras el gate de reproducción esté en pie, como dice el corrector.

**Corrección.** Contraste pareado: ΔFP, la brecha y R_K se calculan sólo sobre las pasadas que el nativo reproduce
(las dos corridas iguales al A/B), igual que R_L ya se calcula sólo sobre las pérdidas reproducidas. Con eso
FP(nativo, max) y FP(nativo, min) son exactamente los del A/B en esa muestra, y los desvíos tolerados dejan de
mover la cota. Un caso en P7b con el diseño de N2.

### N3. D22 leída en M da «NO RECUPERA» con un M muerto. Gravedad 2

V2-1 se cerró en H1 pero no en D22 leída en M. VERIFICADO (`ataques_v3.py` N3): con los `tif_*` sin publicar nada,
H1 da `INDETERMINADO POR INSTRUMENTO: M no publica...`. Pero `D22_D26_tif_lin` da `NO RECUPERA (0.00 de 14 ...)` en
las cuatro variantes. **Corrección:** cuando `campo != "nativo"`, agregar a `f_i` la misma falla de V2-1
(`rk_m < rk_n − 0,10`).

### N1. Con D22 frenada y H1 en pie, la tabla H3 deja leer la variante sin compuerta. Gravedad 2

VERIFICADO (`ataques_v3.py` N1): con `nativo|min` sin publicar una pérdida D22, D22 da
`INDETERMINADO POR INSTRUMENTO: control positivo...` y H1 da CONFIRMA. La tabla H3 se escribe entera, con
`nativo|max_sin_compuerta` y su recall en pérdidas confiables `(0.4375, 32)`: el número de D22 que el gate acaba de
frenar. Es lo mismo que V2-3, por otra puerta. **Corrección:** si los gates de D22 de un campo fallan, la tabla H3 no
escribe las filas `<campo>|max_sin_compuerta`.

### N5. Un «piloto» puede correr los 35 lotes. Gravedad 2

El candado (probado en Git Bash con `bash` y `sh`, sobre el texto exacto del paso extraído del yml) se comporta como
se pide en los cuatro casos de P7b. Pero `lotes = " "` o `lotes = ","` con `piloto = si` pasan el candado
(`-z` no los ve vacíos). El plan después los limpia y corre **todos**: `lotes: [0, 1, 2, ...]` (VERIFICADO, los dos
shells dan lo mismo). No sale ningún veredicto equivocado: el evaluador corre con `--piloto`. Lo que sí pasa es que
se gasta un despacho completo como piloto, que después hay que repetir entero, y quedan 90 días de artefactos con
todas las decisiones por pasada. No verifiqué si la interfaz de GitHub recorta los espacios del input ni si `gh workflow run`
lo hace (SIN VERIFICAR). **Corrección:** en «Plan de lotes», si
`PILOTO = si` y la lista limpia queda vacía, error. Mejor aún, que el piloto acepte un solo lote.

Lo que en Actions puede diferir de Git Bash: el runner usa `bash --noprofile --norc -eo pipefail {0}`. Mi prueba usó
`bash -e`, y el script del candado no usa tuberías. No veo diferencia que importe. Sigue SIN VERIFICAR en el runner.

### El 5 % con grupos chicos: no abre nada

`floor(0,05 · n)` da 0 para n < 20. Pero ningún grupo baja de 38 sin que antes caiga el gate de cobertura (≥ 90 %
de 42). Con cobertura mínima en `residual_sobrevive` (38 de 42) el máximo es `floor(1,9) = 1` y el evaluador sigue
confirmando el diseño sano (VERIFICADO, `ataques_v3.py` N4). El redondeo hace el gate más estricto, nunca más laxo.
Las pérdidas no confiables (10) sólo informan, como dice el código. La muestra D22 se revisa por grupo primario
(71 + 9 dentro de `residual_apagado`), y en los dos grupos lo esperado es lo mismo (F 0, B 1), así que no hay doble
criterio.

### Consecuencia de diseño de V2-1, no defecto

Ahora REFUTA por recall sólo sale si M conserva las conservadas y pierde las pérdidas. Un suavizado que mate todas
las alertas débiles da INDETERMINADO, no REFUTA. Es coherente con la razón de V2-1: MIROVA vio esas conservadas, así
que un campo que no las ve no es el suyo. Conviene que §6 lo diga en una línea.

## 4. ¿El piloto filtra números de detección?

**El evaluador, no.** VERIFICADO: en `--piloto` la salida sólo trae `identidad`, cobertura por grupo,
`sd_dnti_nativo_vs_record_ab`, `mismo_granulo_que_ab`, duplicadas, `operativo`, la validación contra el TIF y el
control del predicado con sus siete casos fijos (que no miran datos de la sonda). Ninguno es publicación ni decisión
sobre las pasadas. El piloto ahora también importa `banco_paridad` y corre node, así que sí ejercita las dependencias
(cierra V2-9).

**El log de la sonda, tampoco.** VERIFICADO: los 9 `print` de `sonda.py` llevan conteos de gránulos, flags, n_roi, σ,
identidad, tiempos y errores. El encabezado `=== clave [grupo]` muestra el grupo, que es dato de `pasadas.json`, no
de la sonda.

**Lo que sí queda,** y está dicho en §10 bis: los json por pasada del artefacto traen `decision` y los records.
Sumo N5: un piloto mal escrito deja esos json para las 365 pasadas.

**V2-8 en el runner no compara nada.** Con `fetch-depth` 1 no hay historia, y lo dice («sin sello anterior distinto
en la historia disponible»). §10 bis lo reconoce: la comparación sirve en local, al re-sellar. VERIFICADO por
lectura.

## 5. Cambios mínimos antes de sellar

1. `evaluar.py`: contraste pareado para ΔFP, brecha y R_K, sobre las pasadas que el nativo reproduce (N2).
2. `evaluar.py`: la falla de V2-1 también frena D22 leída en M (N3).
3. `evaluar.py`: sin filas `<campo>|max_sin_compuerta` en la tabla H3 cuando D22 de ese campo está frenada (N1).
4. yml: el piloto necesita al menos un lote válido después de limpiar la lista (N5).

Cada uno con su caso en P7b, que falle con `aae4a4ed0`. Después, volver a correr `prueba_local.py`. Con eso no veo
otro bloqueo para sellar y despachar el piloto.
