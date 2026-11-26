# Acta de cierre de la auditoría externa con Codex, ronda 5

**Propuesta, pendiente de la aprobación de Nicolás Mendoza.** Escrita por la sesión S202 (2026-11-26) a partir del
cierre informado de Codex, su verificador Claude de contexto limpio y las dos decisiones de Nicolás del 2026-11-26. Las
decisiones de la tabla «Acta» son propuestas hasta que Nicolás apruebe esta acta.

## Por qué existe este documento

La ronda 5 (2026-11-25 y 2026-11-26) revisó lo que cambió después del acta de la ronda 4
(`docs/ACTA_CIERRE_AUDITORIA_CODEX_RONDA4_2026-11-25.md`): el evaluador re-sellado del laboratorio del piso (frente
A), la historia de los 32 volcanes fuera de MIROVA (B), las vigilancias de la guardia K y la auditoría semanal (C+D),
las declaraciones públicas de la ficha, el modal y la página de comparación (E), más un cierre informado. Cada frente
tuvo pase ciego de Codex, confrontación con las rondas anteriores y un verificador Claude de contexto limpio.

**Ningún hallazgo quedó en gravedad 3 o más tras verificar.** El cierre de Codex no daba la ronda por terminada por una
sola razón (R5C-101): al bajar el piso, la validez de una escena depende del brazo, y el evaluador comparaba brazos
sobre muestras distintas sin que ningún control lo viera. El verificador lo dejó en gravedad 2, juzgó que la ronda
puede terminarse sin repetir frentes y pidió dos cosas: una decisión escrita de Nicolás sobre el arreglo, re-sellada
antes de calcular ninguna tasa del barrido, y anotar en el manifiesto la aceptación del rescate de t2. Las dos están
hechas (abajo). Como las actas anteriores: **cerrada con límites explícitos**, no «todo está bien».

## Qué se cerró y sobre qué

| Qué | Valor |
|---|---|
| Copia auditada | main `3354563c3` (ficha v1.109) |
| Registro de hallazgos verificados | 461 filas (61 de la ronda 5), `D:\codex-vrp\_salida\ronda5\hallazgos_verificados.csv` (fuera del repo) |
| Informe del cierre y su verificación | `D:\codex-vrp\_salida\ronda5\cierre\INFORME.md`, `PROPUESTA_CIERRE.md` y `D:\codex-vrp\_salida\ronda5\cierre_verificacion\VEREDICTO.md` |
| Resumen para Nicolás | `D:\codex-vrp\_salida\ronda5\RESUMEN_R5_PARA_NICOLAS.md` |
| Decisiones de Nicolás | «Sí, acepta el rescate» (t2 de marzo, 2026-11-26 ~00:50 UTC); «Sí, re-séllalo así» (arreglo (a) de R5C-101, ~03:50 UTC) |

Los archivos de `D:\codex-vrp\` están fuera del repo a propósito. Si se pierden, esta acta y la ficha conservan lo
decidido, no la evidencia.

## Conteo del registro (filas de la ronda 5)

| Frente | Gravedad 2 | Gravedad 1 |
|---|---|---|
| A, evaluador del piso | 10 | 4 |
| B, historia de los 32 | 5 | 7 |
| C+D, guardias y auditoría semanal | 5 | 8 |
| E, declaraciones públicas | 2 | 6 |
| Cierre | 5 | 7 |
| Otras filas del registro (frentes «4» y «10»; la de gravedad 2 es la del informe S190) | 1 | 1 |
| **Total** | **28** | **33** |

## Lo que ya quedó cerrado

| Hallazgo | Qué pasaba, como geólogo | Dónde |
|---|---|---|
| R5C-101, R5FA-105 | Con el piso bajo, un foco débil pegado a un hueco de datos queda sin fondo y la vía guarda la escena MODIS como «no medida» sólo en ese brazo: los brazos se comparaban sobre muestras distintas | Re-sello S202, #1136 (abajo) |
| R5C-V201 (nuevo del verificador) | Al revés en VIIRS 375: una escena que el control no midió se vuelve válida y publicada con el piso bajo | El mismo re-sello |
| R5C-102 | El rescate de t2 de marzo estaba en el manifiesto sin decisión | Decidido por Nicolás («Sí, acepta el rescate») y anotado en el manifiesto, #1135 (ficha v1.112) |
| R5FA-101, 102, 112 | Duplicados o escenas inválidas daban «poder» al control de fuga o escondían un código contradictorio; graves sólo si la unión de tandas no elimina duplicados | La unión estricta (#1133, v1.110) se detiene ante cualquier duplicado que difiera en algo más que la hora de proceso |
| R5FE-101, R5FE-105 | La ficha decía «sólo de noche» con MODIS diurno activo desde la v1.71; la página de comparación presentaba el histograma de distancias como prueba de alineamiento espacial | #1134 (v1.111) |
| R5 sin ID (informe S190) | El informe S190 decía que la conectiva «or» del paper es lo mismo que el máximo del `.m` | Ya marcado como falso en `experiments/_s190_d36/INFORME.md` (F4-117) |

### El re-sello S202 (R5C-101)

**Decisión.** A la pregunta «¿Re-sello el evaluador excluyendo de todos los brazos la escena inválida, con frenos?»,
Nicolás respondió «Sí, re-séllalo así» (2026-11-26). Tras el verificador, a la pregunta «¿Cómo cierro el sesgo hacia
pisos más bajos del re-sello antes de mergear #1136?», respondió «Agregar freno 3» (2026-11-26).

**Qué hace.** Toda escena inválida en alguno de los nueve brazos y válida en otro sale de los nueve y de producción
antes de contar, y la salida la declara. INVÁLIDO si una excluida decide su noche (cambia si la noche entra al
denominador, en algún brazo o en producción), si las excluidas pasan del 1 % de las noches negativas del control, o si
las publicaciones que la exclusión quita cambian el piso elegido (freno 3). Detalle en el §5c de
`experiments/_s196_lab_piso/PREREGISTRO.md`.

**Lo que se vio al hacerlo.** La única escena así de marzo a agosto (Llaima, MODIS Terra 2026-05-30 02:55) no es sólo
«no medida» en seis pisos: en 0,00275 es válida con 9,685 MW y el tablero la publicaría (en el control, 0 MW; contra la
tabla real de MIROVA es un falso positivo, según el verificador). La exclusión le quita a ese brazo esa noche publicada;
su noche tiene otras pasadas limpias, así que no cambia de denominador. El verificador mostró además (R202V-1, gravedad
2) que, con los dos primeros frenos en verde, lo único que la exclusión mueve son publicaciones quitadas, así que el piso
elegido sólo podía quedar igual o bajar: en dos casos sintéticos bajaba con todo en verde. El freno 3 lo cierra.
**Implementador:** la sesión S202 (Claude). **Decisión:** Nicolás. **Verificador independiente:** un Claude de
contexto limpio, dos pasadas (2026-11-26, `D:\vrp-trabajo\temporales\s202\verif_resello\VEREDICTO.md`, fuera del
repo), que escribió sus caminos de falla antes de abrir el código y corrió el `calibrar` real con casos propios: la
exclusión llega a los nueve brazos y a producción con la misma clave, los tres frenos hacen lo que dicen, la noche real
de Llaima queda confirmada contra la tabla real de MIROVA y sus dos casos de R202V-1 dan ahora INVÁLIDO por el freno
3. Recomendó mergear. Dejó dos observaciones de gravedad 1: R202V-5 (con los tres frenos la muestra común nunca mueve
la elección: el resultado es el del sello anterior o INVÁLIDO, declarado en el §5c) y R202V-6 (faltaba una prueba de
que el freno 3 compara también el estado; agregada con su mutación).

**Pruebas.** `tests/test_lab_piso_resello_s202.py`: 17 pruebas con el `calibrar` real (el conteo, el banco y el
predicado del tablero originales; sólo la referencia de MIROVA es sintética); 13 fallan con el evaluador del sello
S200c (en los casos de Codex ese evaluador elegía en silencio) y las dos del freno 3 fallan sin él. Incluyen la noche
real de Llaima en los nueve brazos. Mutaciones (`experiments/_s196_lab_piso/mutar_resello_s202.py`): 15 de 15 atrapadas,
contando como atrapada sólo una falla por aserción (R5FA-110), con un control de caída en ejecución que sale no
atrapado; las 13 del re-sello S200 siguen atrapadas.

## Acta: lo que queda abierto (gravedad 2)

Los de gravedad 1 quedan en el registro sin acción.

| Grupo | Qué pasa, como geólogo | Decisión propuesta | Responsable y disparador |
|---|---|---|---|
| R5C-103, R5FA-V201, R5FA-108 (carpeta y brazo) | Nada ata la carpeta que se le pasa a `calibrar` al piso que dice ser: la misma carpeta para dos pisos, o la de otro perfil, da ELEGIDO. El mismo código no certifica el perfil | Antes de correr `calibrar`, un chequeo externo (sin tocar el evaluador sellado) lee `regimen.perfil` de cada carpeta y exige `_s196_lab_<brazo>` del brazo que dice ser; la salida del chequeo va junto al resultado | Sesión del loop, al correr `calibrar` sobre el barrido |
| R5C-106 (unión de tandas) | La unión no liga los trabajos del último intento al commit de la rama que lee; medido sin efecto en t3 y t4 (verificador de #1133, pasada 2) | Aceptar declarado; repetir la medición en t8, que tuvo relanzamientos | Sesión del loop, al agregar t8 al manifiesto |
| R5FA-106, 107, 109, 110 (controles del evaluador) | Las cuentas agregadas no ven a producción alertar en otra noche con las mismas cuentas; la muestra queda identificada pero no fijada; sobreviven mutaciones de coordenadas y de dos clases de fuga; el contador de mutaciones contaba caídas como capturas | R5FA-110 corregido para el re-sello S202 (el contador exige fallas por aserción y tiene un control de caída en ejecución); los demás, aceptar declarados: exigen un archivo armado a mano o un error al escribir la línea de comandos | Sesión del loop; reabrir si se re-sella el evaluador por otra causa |
| R5FB-101 (historia de los 32) | El tablero no carga la historia de los 32 volcanes fuera de MIROVA, ni pidiendo la historia completa; la serie empieza el 3-nov. No muestra calma falsa (el panel lo rotula) | Tarea propia si se van a publicar los 34 | Nicolás decide si se publican; la sesión del loop la hace |
| R5FB-102 | San Pedro tiene 278 records de historia con la grilla anterior a la corrección de S190 y la sombra 10 records en 5 volcanes; sólo uno cambia de lado del umbral de 5 km (Antillanca, 0,19 MW) | Aceptar declarado (ya en la ficha); reprocesar San Pedro si se publican los 34 | Sesión del loop, con R5FB-101 |
| R5FB-105 (CSV del tablero) | La exportación CSV pierde el motivo de escena vacía y la marca preliminar, también en los 11 principales | Arreglar cuando se toque la exportación; no cambia ningún número publicado | Sesión del loop |
| R5FB-106, R5FB-110 (sombra en el tablero) | El mapa general muestra los preliminares sin su rótulo; la sombra no tiene el aviso persistido de pasadas no medidas (ya aceptado en la ronda 4, R4FEF-V201) | Aceptar mientras los 32 sean preliminares; arreglar antes de publicarlos | Sesión del loop, con R5FB-101 |
| R5FCD-101 (pareo a 120 s) | El pareo de pasadas a 120 s podría tapar una protegida callada o fabricar una candidata a volver a K; con las plataformas de hoy no ocurre (0 pares a 120 s o menos en 74.694 records; gránulos a 5 o 6 min) | Aceptar declarado; reabrir si entra una plataforma o un duplicado de la misma pasada | Sesión del loop |
| R5FCD-102, 104, 107, V202 (vigilancias y auditoría semanal) | La vigilancia tolera tres días sin guardia; MODIS mezcla día y noche en una razón de magnitud; una excepción histórica de subbanda quedó obsoleta y taparía una caída futura; si se revierte MODIS a K, una protegida que K calle ese mismo día no llega a la lista semanal (la diaria sí la ve) | Aceptar declarados; R5FCD-107: quitar la excepción cuando se toque la auditoría semanal | Sesión del loop |

## Qué reabriría qué parte

Se mantiene la tabla de la ronda 4. Para el laboratorio del piso, además: cualquier cambio del evaluador, del
pre-registro, de la unión de tandas o de los brazos obliga a repetir las pruebas de los re-sellos S200 y S202 y sus
mutaciones antes de correr `calibrar`.

## SIN DATO que queda escrito

La frecuencia de escenas de validez distinta en septiembre a noviembre (se medirá con
`D:\vrp-trabajo\temporales\s201\r5c101\medir_invalidas_por_brazo.py` cuando terminen sus tandas); el efecto real del
re-sello sobre la elección, que nadie conoce porque `calibrar` no se ha corrido sobre el barrido; y si la historia de
los 32 se va a publicar.
