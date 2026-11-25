# Acta de cierre de la auditoría externa con Codex, ronda 4

Escrita a pedido de Nicolás Mendoza («Sí, escríbela», 2026-11-25) por la sesión S200. **Para aprobar:** las
decisiones de la tabla «Acta» son propuestas hasta que Nicolás las apruebe; el PR no se mergea antes.

## Por qué existe este documento

La ronda 4 (2026-11-24 y 2026-11-25) revisó lo que cambió después del Cierre II
(`docs/ACTA_CIERRE_AUDITORIA_CODEX_2026-11-24.md`) y nunca había sido frente propio: la continuidad del NRT cuando
NASA falla (A), las miniaturas por pasada (B), las lecturas de la regla D-9 (C), los 34 volcanes fuera del NRT y el
tablero de turno (E+F) y el laboratorio del piso del cráter (D), más un cierre informado. Codex eligió los frentes y su
presupuesto (`D:\codex-vrp\_salida\ronda4\_consulta\OPINION_RONDA4.md`). Cada frente tuvo pase ciego, confrontación con
las rondas anteriores y un verificador Claude de contexto limpio que selló su propio instrumento antes de leer a Codex.

El cierre informado de Codex no daba la ronda por terminada por una sola razón: los cuatro defectos de gravedad 3 del
laboratorio necesitaban una decisión durable de Nicolás y un responsable de implementarlos, distinto de quien decide.
Nicolás decidió re-sellar el 2026-11-25 y el arreglo entró en #1129. Esta acta registra eso y lo que queda abierto, con
la misma idea del Cierre II: **cerrada con límites explícitos**, no «todo está bien».

## Qué se cerró y sobre qué

| Qué | Valor |
|---|---|
| Copias auditadas por los frentes | A y B: `473bf0891ec81af17fb4ed6c9783faabd2dacb49` (ficha v1.95). C, E+F y D: `bfcef8406d9bbd087e2547f9864c93d5e3746dda` (ficha v1.98) |
| Copia del cierre informado | `9bd65c37f03f3a9315656425d49832817d036426` (ficha v1.103, tras #1126); sello de insumos `e8c5674446ef53a8594e0e0aa07f14561bd46d5f5cec380234497ce631a01da8` (945 insumos, `cierre\SELLO.json`) |
| Copia de la certificación (main tras el re-sello) | `003f035064b11e94ca3c6f811ed4f3ee581f7f16` (ficha v1.106, tras #1127, #1128 y #1129), más #1130 (v1.107, correcciones del verificador del re-sello) |
| Corpus de protegidas del cierre | 519 = 495 publicadas + 21 con record sin publicar + 3 sin record (2 son MODIS de día); SHA-256 de `cierre\protegidas_actuales.csv` `3c4d8fc651418e0cfcc8b37ebc1ea61ee5bfc6d9b66b79264f13affb6f0c3482` |
| Registro de hallazgos verificados | 402 filas (71 de la ronda 4), `D:\codex-vrp\_salida\ronda4\hallazgos_verificados.csv` (fuera del repo) |
| Informe del cierre y su verificación | `D:\codex-vrp\_salida\ronda4\cierre\INFORME.md` y `D:\codex-vrp\_salida\ronda4\cierre_verificacion\VEREDICTO.md` (14 de 14 afirmaciones CONFIRMADO) |
| Resumen para Nicolás | `D:\codex-vrp\_salida\ronda4\RESUMEN_R4_PARA_NICOLAS.md` |

Como en el Cierre II, los archivos de `D:\codex-vrp\` están fuera del repo a propósito. Si se pierden, esta acta y la
ficha conservan lo decidido, no la evidencia.

## Los doce gravedad 3, todos resueltos

| Hallazgo | Qué pasaba, como geólogo | Estado | Dónde |
|---|---|---|---|
| R4FB-104, R4FB-106 | El panel de miniaturas decía «Sin anomalía» en pasadas no medidas y en pasadas con una detección lejana | Corregido | #1121 (ficha v1.100) |
| R4FEF-109 | Un solo JSON cortado dejaba el tablero sin ninguna tarjeta | Corregido | #1126 (v1.103) |
| R4FEF-106 | El aviso de pasadas no medidas quedaba en caché toda la sesión: un hueco nuevo de NASA no aparecía en una página abierta, y una falla de lectura se veía como «todo medido» | Corregido | #1126 (v1.103) |
| R4FD-V201 | El control del barrido del piso salía inválido por construcción, porque producción guarda MODIS de día y el laboratorio no | Corregido con re-sello decidido por Nicolás | #1129 (v1.106) |
| R4FD-101 | Un brazo que perdía noches cambiaba el piso elegido sin invalidarse | Corregido con re-sello | #1129 |
| R4FD-102 | «Idéntico donde la zona no actúa» se declaraba comparando cero records | Corregido con re-sello | #1129 y #1130 |
| R4FD-105 | Brazos de código distinto se mezclaban sin aviso | Corregido con re-sello | #1129 |
| R4C-101 a R4C-104 | El cierre reitera R4FD-101, 102, 105 y V201 | Los mismos cuatro | #1129 |

El cierre informado comprobó que los cuatro del tablero están corregidos: quitando cada arreglo de una copia, su prueba
falla. El verificador del cierre lo repitió con siete inversiones. Para el re-sello (#1129): sus pruebas nuevas fallan
10 de 12 con el evaluador sellado antes; las mutaciones que apagan cada arreglo quedan atrapadas 8 de 8, y las del
control de S196, 25 de 25. **Implementador:** la sesión S200 (Claude). **Decisión:** Nicolás, 2026-11-25.
**Verificador independiente del re-sello:** un Claude de contexto limpio (2026-11-25,
`D:\vrp-trabajo\temporales\s200\verif_1129\VEREDICTO.md`, fuera del repo) que selló su propio instrumento antes de
leer las pruebas y corrió `calibrar` de main y del evaluador sellado antes en 28 escenarios con el `tasas_barrido` real
del S194: los cinco arreglos CORREGIDOS y lo que el pre-registro fija, intacto (mismos sha256). Sobre los 74.694 records
de producción, el filtro de día quita las 228 pasadas MODIS de día desde el 2026-11-15 12:30 UTC y ninguna de noche.
Tres efectos no buscados que dejó (SIN PODER tapaba un INVALIDO, el poder contaba records fuera de la ventana y el
filtro tardaba unos 82 minutos) se corrigieron en #1130 (v1.107), con pruebas que fallan con el evaluador de #1129; los
demás quedan declarados en el §5b del pre-registro.

## Regresiones comprobadas

Los arreglos que entraron después de los frentes no rompen lo que las rondas 2 a 4 dieron por bueno (cierre informado
§2 y su verificador):

- **Pasadas no medidas, aviso de fondo no estimado, rótulos de miniaturas y carga tolerante del tablero.** Pasan sus
  casos positivos, negativos y de recuperación. El censo del cierre leyó 80.348 records: 57 marcas de cráter sin medir
  y 14 de fondo no estimado, sin discrepancias entre Python y JavaScript.
- **Marca «sin ángulo».** No cambia ningún record con ángulos válidos. Ninguno de los 298.342 records de la vía pasaría
  a «sin ángulo». 33 escenas sintéticas por el código real salen idénticas byte a byte (verificador) y 48 dan cero
  diferencias (Codex). Con un ángulo malo, la marca sí actúa en 12 de 12 controles.

## Acta: lo que queda abierto (gravedad 2 o menos)

Conteo del registro (`hallazgos_verificados.csv`, filas de la ronda 4): gravedad 2, 6 en A, 5 en B, 2 en C, 11 en E+F, 7
en D y 1 del cierre; gravedad 1, 27 en total. Ya cerrados entre ellos: R4FB-105 y R4FB-V202 y R4FEF-101 (#1121), la
primera mitad de R4FEF-107 (#1126) y la segunda (#1128, v1.105), R4C-106 (#1128) y R4FD-106 (#1129). Los de gravedad 1
quedan en el registro sin acción.

| Grupo | Qué pasa, como geólogo | Decisión propuesta | Responsable |
|---|---|---|---|
| **R4FD-107 (barrido del piso)** | La fecha de fin con que se evalúa el barrido no está fija: con las mismas carpetas, fin 2026-05-31 elige 0,0025, fin 07-31 elige 0,00225 y fin 11-20 elige 0,002. Quien evalúa podría elegir el fin mirando el resultado | **Fijar el fin en el pre-registro antes de correr `calibrar`**: el último día de la última tanda despachada (2026-11-23), sin mirar nada | Nicolás aprueba; la sesión del loop lo escribe |
| R4FA-109 (NRT) | Cuando NASA publica el producto estándar, el record NRT se reemplaza entero y podría perder una alerta o una anotación del NRT | Medir, sólo lectura: cuántos reemplazos cambiaron la alerta o la marca de una pasada | Sesión del loop |
| R4FA-101, 102, 104, 107, V201 (NRT) | El reintento y la cobertura pueden subcontar fallas (geolocalización, artefacto parcial, corte antes del final, producto estándar parcial) y un paso cortado pierde lo procesado. Lo que no se ve lo recoge el NRT de los 8 días cada 2 horas o el barrido de los domingos: atrasa, no pierde | Aceptar declarados | Sesión del loop, si reaparecen |
| R4FB-101, 102, 107 (miniaturas) | Si el cálculo de una miniatura falla, la pasada queda sin record y la corrida en rojo; imagen y record podrían ser de versiones distintas del mismo gránulo; un record borrado podría seguir en un índice viejo. Ninguno cambia un número publicado | Aceptar declarados | Sesión del loop |
| R4FC-101, 102 (D-9) | Fallan sólo si ocurre una excepción que hoy no ocurre; ninguno calla (uno abre issue y el otro deja la corrida en rojo) | Aceptar declarados | Sesión del loop |
| R4FEF-V201 (sombra de los 34) | Una noche sin pasadas en la sombra se muestra como «datos atrasados», sin la marca «no medida» de los 11, porque `data/cobertura/` cubre sólo los 11 (la noche perdida del 24-nov fue un corte del catálogo de NASA) | Aceptar mientras los 34 sean preliminares; extender la cobertura a la sombra antes de publicarlos | Sesión del loop |
| R4FEF-102 a 105, 108, 111, 112, 114 (rótulos del tablero) | Rótulos que en una vista engañan y que la misma página da bien en otra (tabla, tarjeta o evolución); R4FEF-111 latente (0 de 330 casos) | Aceptar declarados; arreglar cuando se toque esa vista | Sesión del loop |
| R4FD-104, V202 (barrido del piso) | No queda escrito qué brazo cayó y en qué día; con el re-sello un brazo caído ya invalida, aunque el informe no diga por qué | Aceptar declarados (pre-registro §5b) | Sesión del loop |
| R4FD-108 (vara S194) | Cero unidades NHI pareadas lanzan una excepción en vez de SIN PODER | Aceptar declarado: está en la vara sellada del S194, que no se toca sin re-sellarla | Nicolás, si se re-sella el S194 |
| R4FD-111 | La calibración exige el JSON de Cordón Caulle aunque el pre-registro permite excluirlo; hoy todos los brazos lo traen | Aceptar declarado | Sesión del loop |
| R4FD-110 (SIN DATO) | La resubida de artefactos al relanzar podría fallar; depende del servicio de GitHub | Vigilar en el barrido | Sesión del loop |
| R4C-V201 | La copia de Codex no traía todos los `experiments\` que citan dos pruebas; los dos instrumentos sí están en main | Sin acción: no afecta ningún veredicto | |

## Qué reabriría qué parte

Tabla del cierre informado (§3), copiada para que viva en el repo. Un cambio de la columna izquierda obliga a repetir la
parte de la derecha antes de volver a decir que la ronda 4 vale para el sistema de ese momento.

| Cambio futuro | Repetición mínima |
|---|---|
| Búsqueda, descarga, cobertura, barrido, reintento o commit del NRT | A: caída y recuperación, parcial, geolocalización, antigüedad y duplicación; E+F: «no medida» en las tres vistas. Un corpus nuevo requiere sello |
| Miniatura, índice, gránulo, sensor o callback | B: neutralidad en los tres sensores y caso de error; identidad record e imagen; rótulos, falta del almacén, lejanas y cumbre |
| Ángulos, remuestreo, detector, ROI, área, coeficiente o fondo | Escenas en los tres sensores, ángulo válido y ausente, radiancia; neutralidad de B; marcas de E+F; publicación y protegidas de C. El frente 3 físico afectado |
| Referencia, D-9, denominador, pareo, regla radiante o día | C: cinco lecturas, protegidas, ausencias, mínimas, día y noche, exclusiones; E+F si cambia la publicación. Comparar claves y corpus |
| JSON, caché, sondeo, predicado o display | E+F: falla aislada, recuperación, frescura y marcas; rótulos de B; C si cambia el predicado |
| Evaluador, pre-registro, perfiles, brazos o recolección del laboratorio | D: re-sello, pasadas iguales, poder no vacío, procedencia, referencia fija, día y noche, aislamiento; B si toca la vía compartida |
| Nueva evidencia o un control que pierde poder | Sólo el SIN DATO afectado y su cadena, con antes y después sellados. Un cero sin control no cierra |

## SIN DATO que el cierre deja escrito

L1B, ejecución remota y frecuencia real de JSON rotos o de errores de imagen; el código anterior exacto de cada arreglo
(se reconstruyó invirtiendo líneas, no desde git); la rasterización real de los gráficos del tablero; seis diferencias
exactas entre el corpus del frente C y el del cierre (29.536 contra 29.530 pasadas medibles, con los mismos 3.038
publicados); y el efecto real de los defectos del laboratorio en las tandas ya corridas, que el re-sello vuelve
irrelevante porque el barrido todavía no se evaluó.
