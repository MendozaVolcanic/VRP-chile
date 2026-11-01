# Verificador con contexto limpio: vigilancia de la sombra de K (commit 0026eb816)

Worktree de sólo lectura `D:\vrp-trabajo\worktrees\s156-sombra-verif` (quedó sin cambios: `git status` vacío al final).
Referencia: `D:\vrp-trabajo\temporales\s156_sombra\ref\` (sin tocar). Scripts y salidas en
`D:\vrp-trabajo\temporales\s156_sombra\verificador\`.

## Veredicto por afirmación

| | Afirmación | Veredicto | Evidencia (script, salida) |
|---|---|---|---|
| B1 | El script implementa fielmente el paso 9 | **PARCIAL** | La reversión, la persistencia y el disparador de negativos siguen la letra, y `COTAS_AB` coincide número por número con la sección 6 de `v1.log` y `v2.log` (detector K, lectura A). Tres diferencias: (a) la **duración** cuenta protegidas anteriores a la adopción y queda «cumplida» el primer día (hallazgo 1); (b) el disparador **(i)** se calcula por volcán **y sensor**, cuando la regla dice «por volcán» con una sola cota (V1, 16 de 194); además las cotas de MODIS y VIIRS 750 que agrega el código miden otra cantidad (hallazgo 3); (c) las cotas del A/B son con la etiqueta original (sin D-9) y sin las filas «solo OCR Suomi NPP», mientras que la vigilancia aplica SN. `v4_muy_bajo_letra.py` → `v4_muy_bajo_letra.out`; `v3_instrumento_propio.out` §3; `out\sombra_latest.json` |
| B2 | Producción = sólo records de K; sombra = `experimental_v2`; mismo predicado con node | **CONFIRMADO** | Los 13 `codigo_sha` de producción en la ventana son el commit de adopción `34cea39e` o posteriores (`git log`, ancestros de 0026eb816). Quedan fuera 26 records sin marca, y sacar el filtro no cambia nada (`v6_mutaciones_main.out`, C). El predicado se aplica igual a los dos: misma `correr_node`, mismo `inner`. Matiz: ~75 % de los records de la sombra no tiene marca de régimen (`v2_cobertura.out`), así que «sombra = C0» se apoya en el historial del perfil y no en el dato. Para el record de PCC está verificado: lo escribió el commit `117236c08` (2026-10-10 18:39 UTC), después del congelamiento #771 del 2026-10-09, con `enable_test1_path: true` |
| B3 | Primera corrida: una candidata (PCC VIIRS 750 2026-10-10 05:54), más las otras cuatro protegidas, y 61 vistas | **CONFIRMADO** | Instrumento propio que no importa `vigilancia_sombra` (lee los CSV directo, de día y de noche, CONS y OCR, todas las filas ALERTA* y FALSO_POSITIVO, pareo a ±120, ±600 y ±1.800 s): **ninguna otra** protegida A en que la sombra publique y K calle, con ninguna tolerancia; las mismas cuatro protegidas restantes; 61 vistas; las mismas Muy Bajo (1 de 6, 1 de 21, 1 de 1, 1 de 9, 1 de 2). La sombra publica de verdad (cúmulo V750 de 1,886 MW a 0,153 km del vent, 4 píxeles calientes, Test 1 integrado activo) y K no tiene **ningún** píxel en ese gránulo (el mismo archivo `VJ202MOD.A2026283.0554.021…`). El resultado no cambia con tolerancias de 30 o 3.600 s ni sin el filtro de sha (`v6`). `v1_caso_pcc.out`, `v3_instrumento_propio.out`, `v8_pixeles_pcc.out` |
| B4 | La cabecera de MIROVA confirma la alerta | **CONFIRMADO** | Las dos imágenes dicen «Last Update: 10-Oct-2026 05:54:02», «Thermal anomaly: LOW», «VRP = 1 MW», con título «[VIIRS]» (la página de 750 m). La miniatura más nueva de la tira es la de 05:54:02, con ZEN = 23°, que coincide con el ángulo cenital de nuestro record de NOAA-21 (23,6°). Las vecinas también calzan (05:12:01 con ZEN 45° es NOAA-20, nuestro 45,2°; 04:54:00 con ZEN 62° es Suomi NPP, nuestro 62,8°). «1 MW» corresponde a la fila de VIIRS 750 (1,19), no a la de VIIRS 375 de la misma pasada (0,39 MW, Muy Bajo). La fila es de la **tabla CONS**, no del OCR, y el satélite es NOAA-21, así que el problema de la imagen de otra pasada (OCR de Suomi NPP antes del 2026-10-09) no aplica |
| B5 | Las 9 pruebas fallarían si el defecto volviera | **PARCIAL** | En una copia fuera del worktree probé 17 mutaciones. Con el nulo (sin mutación) la suite pasa. **8 quedan atrapadas** por un aserto y **0 caen** por excepción; **9 sobreviven**: tolerancia de 3.600 s, `all` en vez de `any`, Muy Bajo que incluye protegidas, negativos con cualquier etiqueta, cotas de MODIS y VIIRS 750 cambiadas, «cumplida» sólo por días, ventana sin filtro y diurnas sin saltar. Además `main()` no tiene prueba: si la sombra se lee de producción (olvidando `data=SOMBRA`), el veredicto pasa a **VERDE en silencio**, sin aviso (`v6`, B). La lógica central de la reversión sí está protegida (M1, M2, M16). `v5_mutaciones.py` → `v5_mutaciones.out`; `v6_mutaciones_main.out` |
| B6 | El parámetro `data` de `banco_paridad` no altera a los demás consumidores | **CONFIRMADO** | `cargar_nuestros(coords, inner, win)` da resultados idénticos en el commit y en su padre (3.698 records, mismos campos, mismo `pub`). Ningún llamador pasa un cuarto argumento posicional. Los 4 scripts que parchean `bp.DATA` siguen funcionando, porque `DATA` se sigue leyendo en el momento de la llamada. Las 8 suites que importan `banco_paridad` dan 169 aprobadas y 7 omitidas. `v7_banco_aditivo.out` |

## Hallazgos propios, por gravedad

1. **(Media-alta) La duración queda «cumplida» el primer día.** `duracion.protegidas_vistas_en_sombra` = 61 y
   `cumplida: true`, pero las 61 son anteriores a la adopción (2026-10-18 09:57 UTC). Contadas sólo después de la
   adopción, hay **0** (`v3_instrumento_propio.out` §3). El contador arranca en la frontera de los datos
   (2026-09-18), mientras que los 120 días corren desde la adopción. Leída al pie de la letra («29 protegidas o 120
   días, lo que ocurra primero»), la vigilancia aparece terminada antes de haber vigilado un solo día de K en
   producción. Además, 2026-10-02 a 2026-10-08 está dentro de la ventana de V1, que ya se adjudicó. Hay que decidir
   (Nicolás) si la vigilancia es retrospectiva, prospectiva o las dos, y separar los contadores.
2. **(Media) `main()` sin prueba.** El cableado que decide qué es producción y qué es sombra no lo ve ninguna prueba.
   La mutación «sombra leída de producción» convierte REVERSION_CANDIDATA en VERDE sin ningún aviso (la «sombra»
   tiene datos de hoy). Sugerencia: una prueba que exija que la ruta de la sombra sea distinta de `banco_paridad.DATA`,
   y que la sombra difiera de producción en al menos un record.
3. **(Media) El disparador (i) no es la letra y sus cotas no miden la cantidad vigilada.** La regla dice «por
   volcán», con la cota V1 de 16 de 194 (0,1298). El código parte por sensor y, para MODIS y VIIRS 750, usa como cota
   las «Muy Bajo perdidas» **absolutas** de K. Lo que vigila es la tasa **diferencial** (la sombra publica y K
   calla). En V375 las dos coinciden, porque C0 no perdió ninguna. En MODIS no: C0 perdió 4 de 4 en V1 y 25 de 26 en
   V2, así que el diferencial del A/B es 0 de 4 y como mucho 1 de 26. La cota del código (0,954) contra la máxima
   posible (0,490) deja el disparador de MODIS inalcanzable en la práctica. Leída según la letra, hoy tampoco dispara
   (`v4`), así que esto no cambia el veredicto de hoy. Lo mismo, más suave, para (iii): la vigilancia aplica SN
   (más pasadas pasan a negativo limpio) y la cota es con la etiqueta original. Hoy da Wilson [0,0217; 0,0499]
   contra una cota de 0,0501, con la superior casi en el borde.
4. **(Media, contexto para la decisión, no cambia la letra) La pérdida es de sensor, no de noche.** En la misma pasada
   de NOAA-21 de las 05:54, K publica VIIRS 375 con 0,688 MW sobre los mismos píxeles del cráter (0,08 a 0,55 km del
   vent, los mismos 4 que la sombra), y esa noche K publica PCC 5 veces. Lo que K pierde es la versión de 750 m, que
   en C0 entraba por el Test 1 integrado: justo el mecanismo que la regla quería vigilar. Por radio, el cúmulo de la
   sombra (7,3 a 7,8 km del punto de `volcanoes.yaml`) es coherente con los 7,83 km de MIROVA. Es sólo radio (A93):
   la posición le toca al agente a61. La regla, al pie de la letra, igual la cuenta como reversión: la unidad es la
   pasada y el sensor (A94).
5. **(Baja) Casos ≥ 1 MW fuera de la lectura A que el script no puede ver.** Copahue VIIRS 375, 2026-10-16 06:18,
   `ALERTA_SIN_GEOMETRIA_OCR` de 1,34 MW. La sombra publica 0,043 MW a 2,9 km y K tiene un cúmulo de 1,238 MW a
   6,5 km, rotulado `far`. Lo más probable es que sea otro objeto y no una pérdida de K. La exclusión es correcta por
   V31.1, pero un caso así no aparece en ningún listado de la vigilancia. Cuatro FALSO_POSITIVO a más de 23 km con la
   sombra publicando no vienen al caso (otro objeto).
6. **(Baja) Tupungatito 2026-09-28 y 2026-09-29** se listan como protegidas que K no publica, sin la marca «solo OCR
   Suomi NPP antes del 2026-10-09» que V1 sí les puso («no decide»). Caen dentro de la ventana ya adjudicada de V1.
7. **(Baja) La sombra no tiene marca de régimen** en ~75 % de sus records. Una sombra que dejara de ser C0 por un
   cambio del perfil no se detectaría desde el dato.

## ¿Cambia la conclusión «hay una candidata a reversión»?

No. La candidata se reproduce con un instrumento independiente, resiste la tolerancia de pareo y el filtro de
régimen, y la cabecera de MIROVA corresponde a esa pasada y a ese sensor. Sí cambian dos cosas que Nicolás debe saber
antes de decidir. La primera: la pérdida es sólo a 750 m, porque K publicó la misma pasada a 375 m sobre el mismo
cráter (hallazgo 4). La segunda: el «29 de 29 cumplido» del script **no** significa que la vigilancia terminó
(hallazgo 1).

## Lo que no verifiqué

- La tasa diferencial exacta de Muy Bajo en el A/B (el `v1.json`/`v2.json` no guarda el detalle por pasada): sólo la
  acoté. **SIN VERIFICAR** el valor exacto.
- La posición del objeto de MIROVA (no trae acimut): tema del agente a61.
