# Propuesta de re-sello del evaluador del piso (S199): cuatro defectos verificados antes de evaluar

Escrita por S199 el 2026-11-25 para Nicolás. **No cambia el evaluador ni el pre-registro**: `evaluar.py` y
`PREREGISTRO.md` siguen sellados (sus hashes no se tocan). Lo que se re-sella, y cómo, lo decides tú.

## Por qué ahora

El barrido del piso de la zona A corre por tandas mensuales (abril y mayo cerrados; junio en curso; julio a noviembre
detrás). Recién cuando estén todas se corre `evaluar.py calibrar`. La ronda 4 de la auditoría externa con Codex (frente
D, aislamiento y pre-registro del laboratorio) encontró defectos en ese evaluador, y un verificador Claude de contexto
limpio los reprodujo con el `calibrar` y el `tasas_barrido` reales sobre records reales de producción. Lo bueno primero:
**producción está aislada del laboratorio** (el perfil `mirova_equivalent` deja la zona A apagada en los 45 volcanes;
el workflow sólo empuja a `s196-lab-piso/<run_id>`). Los defectos están en cómo se juzgará el barrido. Conviene
decidirlos **antes** de mirar los resultados: después, cualquier ajuste sería a posteriori.

Fuente: `D:\codex-vrp\_salida\ronda4\fd_r4\INFORME.md` (Codex) y
`D:\codex-vrp\_salida\ronda4\fd_r4_verificacion\VEREDICTO.md` (verificador, instrumentos `i3`, `i5` e `i8`), fuera del
repo.

## Los cuatro defectos de gravedad 3

| ID | Qué pasa, como geólogo | Arreglo recomendado |
|---|---|---|
| R4FD-V201 | Desde el 2026-11-15 12:30 UTC producción guarda las pasadas MODIS de día y el laboratorio no. El control «el brazo de control cuenta lo mismo que producción» compara también los negativos de día, así que con la ventana sellada (hasta el último día) sale **INVÁLIDO por construcción**: un control perfecto da en MODIS 5.117 negativos contra 5.217 de producción con fin 2026-11-20. La noche, que es la unidad que decide, queda igual (127 de 1.522). Tal como está sellado, el barrido no puede dar ELEGIDO. | Contar producción con las mismas reglas de día que el laboratorio (descartar lo que su almacén rechazaría de día) antes de compararla con el control. Mantiene el control completo y no corta la ventana. |
| R4FD-101 | Si un brazo pierde noches que otro tiene (un trozo que muere a mitad de la lista de brazos, o un brazo que cae un día), la tasa por noche de ese brazo cambia y el piso elegido también, **sin que el evaluador lo invalide**. Caso medido: el brazo de 0,00175 pierde 17 noches que publican y se elige 0,00175 en vez de 0,002, con estado ELEGIDO. | Exigir que todos los brazos cubran exactamente el mismo conjunto de volcán y día (y, en ese conjunto, las mismas pasadas); si no, INVÁLIDO o se compara sólo la intersección, declarándolo. Va con R4FD-V202: `reproc_brazos.py` debe dejar escrito, en la cobertura del trozo, cada brazo que cayó y en qué día (hoy sólo lo imprime). |
| R4FD-102 | El control «donde la zona no actúa debe dar idéntico» se apoya casi entero en Cordón Caulle (3.140 de 3.144 records). Sin ese volcán, o con su archivo vacío, compara **cero records** y aun así dice idéntico. | Exigir un mínimo de records comparados por brazo (por ejemplo, el mismo umbral de poder que ya usa el pre-registro); con menos, SIN PODER, no idéntico. |
| R4FD-105 | El evaluador no comprueba que los brazos vengan del mismo código ni del mismo intento: juntar tandas de corridas distintas, o relanzar sólo algunos brazos, mezcla versiones sin aviso. Los records traen `regimen.codigo_sha` y `perfil`, pero `calibrar` no los mira. | Exigir el mismo `regimen.codigo_sha` en todos los brazos de una misma ventana (y declarar cada cambio de código entre tandas); si no, INVÁLIDO. |

Menores, en la misma pasada si se re-sella (gravedad 2): R4FD-104 (la recolección borra incidencias y el punto hasta
donde llegó el reproceso), R4FD-106 (la calibración baja dos veces la referencia de MIROVA y no guarda su procedencia;
bajarla una sola vez y guardar su hash), R4FD-108 (cero unidades NHI pareadas lanza excepción en vez de SIN PODER),
R4FD-111 (la calibración exige el JSON de Cordón Caulle aunque el pre-registro permite excluirlo) y R4FD-V202 (arriba).

## Lo que necesito de ti

Una decisión: **re-sellar ahora con estos arreglos** (recomendado: el barrido sigue juntando datos mientras tanto y
nadie ha visto un resultado; la noche, que decide, no cambia) o **dejar el sello** (entonces la evaluación final saldrá
INVÁLIDA por R4FD-V201 y habrá que decidir después, ya con resultados a la vista). Si dices que sí, el re-sello va como
PR aparte: evaluador corregido, pruebas que fallen con el evaluador de hoy en cada caso de esta tabla, hashes nuevos en
`PREREGISTRO.md` y una nota que diga qué cambió y que se hizo antes de evaluar.
