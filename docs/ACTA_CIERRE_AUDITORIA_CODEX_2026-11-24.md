# Acta de cierre de la auditoría externa con Codex (rondas 2 y 3)

Aprobada por Nicolás Mendoza el 2026-11-24 a las ~18:20 UTC («Sí, apruebo el acta»). Llevada al repo en S199.

## Por qué existe este documento

La auditoría externa con Codex (GPT, rondas 2 y 3, del 2026-11-16 al 2026-11-24) revisó el sistema en 12 frentes, un
Cierre I, una segunda vuelta de los frentes 9, 3 y 5 y un Cierre II. Cada hallazgo lo verificó después un Claude de
contexto limpio. El Cierre II no certificaba el cierre por una sola razón: para cada defecto grave que seguía abierto
faltaba escrito si se acepta, quién responde o cuándo se arregla. Esta acta es ese registro. Con ella la auditoría queda
**cerrada con límites explícitos**: no promete que todo esté bien, promete que ninguna pérdida excluida queda
invisible y que cada gravedad alta abierta tiene responsable.

## Qué se cerró y sobre qué

| Qué | Valor |
|---|---|
| Copia auditada por el Cierre II | `4eeda1b37fe93ae9761a617b87db7580840d2cb9` (ficha v1.91) |
| Copia de la certificación (main al llevar el acta al repo) | `473bf0891ec81af17fb4ed6c9783faabd2dacb49` (ficha v1.95, tras #1114, #1115, #1015 y #1116) |
| Corpus de protegidas nocturnas desde 2026-03-01, del cierre | 517 filas = 493 publicadas + 21 no publicadas + 3 sin record; SHA-256 `f907ec64aff9da4c2c25d424d69412840c6cbf60441bfdba5c259f9c4d87136f` |
| Corpus anterior (rondas 3, frentes 9, 3 y 5) | 516 filas = 492 + 21 + 3; SHA-256 `195c190070c18f146ddcd77e8e86d9ba5798519b9823c88002baeec4451b31dc`. El de 517 conserva las 516 sin cambios y agrega Nevados de Chillán MODIS_TERRA 2026-11-24 02:30 (7,99 MW de MIROVA, publicada) |
| Registro de hallazgos verificados | 331 filas, `D:\codex-vrp\_salida\ronda3\hallazgos_verificados.csv` (fuera del repo) |
| Informe del Cierre II y su verificación | `D:\codex-vrp\_salida\ronda3\cierre2\INFORME.md` y `D:\codex-vrp\_salida\ronda3\cierre2_verificacion\VEREDICTO.md` |
| Adaptaciones de reproducción conservadas | `D:\codex-vrp\_salida\ronda3\cierre2\` (`reproducir.py`, `cotejar_reproduccion.py`, `actualizar_cotejo.py`, `exclusiones_medicion.py`, `diurnas_publicacion.py` y sus salidas) |

Los archivos de `D:\codex-vrp\` están fuera del repo a propósito: la copia de Codex es de sólo lectura y lleva
material que no se publica. Si se pierden, esta acta y la ficha conservan lo decidido, no la evidencia.

## Las pérdidas que quedan, contadas

En el corpus de 517 protegidas nocturnas, las 24 que no se publican están todas nombradas: 12 por la regla de posición
«radiante» (el grupo más radiante está lejos del cráter), 8 por la distancia que da la lectura de imágenes de MIROVA
(aceptadas por Nicolás el 2026-11-24, D8'), 3 sin record nuestro (hueco de gránulos) y Chaitén MODIS 2026-11-19
(aceptada). Las 162 protegidas diurnas quedan fuera del criterio de victoria por alcance; una MODIS de día de Nevados de
Chillán (2026-11-22 20:40 UTC, 6,07 MW) sí se publica.

## Acta

| Grupo abierto | Qué pasa, como geólogo | Decisión | Responsable |
|---|---|---|---|
| F6-104, F6-112, F6-114 (NRT verde sin medir; pasada fallida sin fila; pérdida a los 8 días) | Una caída de NASA dejaba noches sin medir que se veían como noches tranquilas | **Corregida en main** (#1114); falta verla funcionar en Actions y la fila «no medida» por pasada fallida (F6-112) | Sesión del loop; F6-112 como PR siguiente |
| F7-318 (D-9 sólo en una lectura) | El conteo de falsas alarmas débiles depende de cómo se lea la regla; las protegidas no cambian | **Corregida** en el banco (#1115) y extendida a la auditoría semanal, la comparación vía/K y la clasificación de la referencia (#1116) | Sesión del loop |
| F8-107 y F3-102 (escena sin ángulo solar) | Si falta el ángulo del sol, la escena se trata como de día con brillo solar y queda en 0 | **Aceptar con marca**: hoy 0 records en ese caso; marcar «sin ángulo» como escena no medida cuando aparezca (toca la vía: A45) | Nicolás decide; la sesión prepara el PR |
| F1V-115 (garantía histórica de saturación sin cierre documental) | Que descartar píxeles saturados no pierde alertas está afirmado sin prueba citable | **Aceptar como límite declarado** en la ficha y medirlo cuando haya L1B saturados | Nicolás |
| R3F3-104 y C2-V201 (23 escenas históricas sin marca «no medido») | 23 noches viejas se ven tranquilas aunque el cráter no se pudo mirar; ninguna es protegida | **Declarar** en la ficha y en D36; reprocesar sólo si Nicolás lo pide (A45) | Nicolás |
| Tres protegidas sin record (corpus) | Tres alertas de MIROVA de las que no tenemos pasada (dos de Láscar 2026-03-11) | **Aceptar** como hueco de gránulos ya documentado; revisar si el barrido de huecos las recupera | Sesión del loop |
| Fondo perdido sólo en parte en MODIS (resto del grupo del fondo nulo) | Si una parte del fondo no se puede estimar, la potencia puede inflarse sin aviso; hoy 0 casos | **Aceptar** mientras siga en 0; vigilar con la marca que ya existe | Sesión del loop |

Correcciones del verificador al conteo de Codex, aceptadas con el acta: F6-113 sí tiene caso ejecutado (6 de 6 pruebas,
3 caen sin el arreglo); el fondo nulo ya tenía decisión de Nicolás del 2026-11-20 (`docs/MIROVA_DIVERGENCES.md` D36),
salvo el caso MODIS de fondo perdido sólo en parte, que es la última fila del acta.

## Qué reabriría qué parte

Tabla del informe del Cierre II, copiada para que viva en el repo. Un cambio de la columna izquierda obliga a repetir la
parte de la derecha antes de volver a decir que la auditoría vale para el sistema de ese momento.

| Cambio futuro | Parte mínima que debe repetirse |
|---|---|
| Detector, remuestreo, bandas, ROI, constantes, área o fondo | Frente 3 afectado por sensor y casos sintéticos, incluido fondo total o parcial, huecos y saturación; luego paridad por pasada del frente 9 y publicación de los mismos casos del frente 5 |
| Referencia, lector, corpus, potencia, distancia, satélite o hito OCR | Frente 9: nueva identidad, lectura A, grupos de 120 s, tres sin record y exclusiones; repetir pareo y predicado en los frentes 3 y 5 para las claves que cambien, preservando la serie anterior |
| Exclusión, aceptación de pérdida, variante D-9, regla radiante o encendido diurno | Pregunta 2 del Cierre II y contrato del frente 9, con costo dentro y fuera y dueño explícito; el día habilitado requiere banco diurno, no sólo el corpus nocturno |
| Predicado o display de index, diario, mosaico, comparación o módulos compartidos | Frente 5 sobre las mismas claves, valores y advertencias; repetir métricas del frente 9 si cambia publicación o sensor |
| Vigilancias, ventanas, filtros, claves de pareo, caché, aviso o workflow | Pregunta 4 y regresiones de guardia sin record, ambos callan, falta de K, cron y separación de estado de regla y aviso; si cambia el denominador, también el frente 9 |
| Reversión a K o reposición o reproceso de historia | F11-102, F11-104, F11-V201, AF-0354, AF-0356, C1 y frente 5; antes debe existir decisión de Nicolás sobre la historia; verificar marcas en ambos sentidos y no mezclar regímenes |
| Nueva evidencia L1B, imágenes de MIROVA, censo faltante o falla de un control | Sólo el SIN DATO o hallazgo afectado y su cadena de publicación; sellar antes y después. Un cero cuyo control falla impide usar ese instrumento como cierre |

Entre la copia auditada (`4eeda1b37`) y la de la certificación entraron #1114 (workflow de reintento y barrido), #1115 y
#1116 (variantes D-9 en informes), y #1015 (miniaturas por pasada, que toca `pipeline/mirova_v750_codigo.py` y el
tablero). Según esta tabla, piden repetir la pregunta 4, la pregunta 2 y el frente 5, y comprobar que el cambio en el
código de la vía no mueve detecciones. Esa repetición es la ronda 4 de la auditoría (S199), no una condición de esta
acta.

## Qué declaró este PR

- Ficha SDA, «Evaluaciones de impacto / sesgos»: los límites de R3F3-104 y C2-V201 (historia sin reprocesar) y de
  F1V-115 (saturación en K).
- `docs/MIROVA_DIVERGENCES.md` D36: la historia de la vía sin reprocesar tras #1078 (R3F3-104 y C2-V201). F1V-115 no va
  a D36 porque es del método K (hoy la guardia), no de la vía.
