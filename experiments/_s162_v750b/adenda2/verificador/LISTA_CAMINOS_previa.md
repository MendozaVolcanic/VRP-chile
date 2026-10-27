# Lista previa de caminos por los que la adenda 2 de V750-B podria estar mal

Escrita ANTES de abrir ADENDA2_V750B.md o cualquier script de adenda2. Hora del servidor (header Date de
`gh api -i repos/MendozaVolcanic/VRP-chile`): Tue, 27 Oct 2026 22:44:47 GMT. HEAD del worktree: 83405c557.
Solo conozco el encargo (que la adenda suma pasadas de fuente lejana al run y agrega un lector de posicion).

## A. La lectura sellada de V750-B ve algo distinto
A1. La lista suplementaria se mezcla en objetivos_v750b.json o en el mismo artefacto y el analizador sellado
    (analizar_v750b.py) la cuenta como poblacion (denominadores, negativos limpios, recall cambian).
A2. El workflow cambia (matriz, inputs, nombres de artefactos, timeouts) y la lectura sellada pierde o duplica gránulos.
A3. Los gránulos suplementarios solapan con los sellados (mismo granule/fecha) y se duplican en los resultados.
A4. La separacion de resultados (separar_resultados) asigna mal un record al conjunto sellado o suplementario
    (clave de cruce incompleta: volcan, fecha, hora, sensor; colisiones; pasadas sin clave).
A5. El run suplementario consume el presupuesto/limites de bajada (1.300 granulos) y recorta la poblacion sellada.
A6. Cambio silencioso de orden/ordenamiento que altere la seleccion de la poblacion sellada.

## B. La lista suplementaria no es la poblacion que dice
B1. Definicion de "fuente lejana" (far_ref): umbral de distancia, que referencia (CONS vs OCR, A119), que fechas
    (ventana, A104 #535, A119 hitos), que sensor (V750 = M-band, convencion de nombres A48).
B2. Incluye/excluye pasadas FALSO_POSITIVO_OCR, RUTINA, alertas con VRP<=0,05 (regla D-9) segun lo declarado.
B3. Denominador/ventana temporal no declarados o distintos de los del texto; conteos transcritos a mano.
B4. Interseccion con la lista sellada no vacia (una pasada en ambas) o hueco (ni una ni otra).
B5. Diferencias de zona/fecha UTC vs local; el dia de la pasada vs la noche; hora redondeada.
B6. Deriva entre el script de poblacion de origin/main (01_poblacion.py, banco_paridad.py) y lo que reimplementa el generador.
B7. Volcanes: nombres variantes (A14), 11 Tier A vs 45; radio inner_radius_km distinto por volcan.

## C. Los brazos no miden lo que dicen
C1. "radiante" / "cercano" / "pico" definidos de forma que dos brazos son identicos o uno es subconjunto trivial.
C2. Distancias medidas desde el punto equivocado (centro de grilla vs crater vs vent, A3/A93/A107): una cota escalar de radio no es posicion.
C3. Comparacion contra MIROVA via Distancia_km sin acimut (A93): un radio no identifica el objeto.
C4. Unidad: km vs m, grados vs km; haversine vs aproximacion plana.
C5. Un brazo usa campos que en V750 no existen (pc_lat/pc_lon, geo_class) o con fallback silencioso.
C6. Empates, NaN, None tratados como 0 (distancia 0 = "acierta").
C7. Los tres brazos se evaluan sobre universos distintos (denominadores distintos) y se comparan.

## D. Metricas extraidas con ast no son las selladas
D1. ast extrae funciones del analizador sellado y las ejecuta en un entorno distinto: dependencias omitidas, constantes
    globales no importadas (los valores se cambian), versiones del analizador (tag vs archivo actual).
D2. Se extrae la funcion por nombre y una homonima o una version posterior pisa a la sellada.
D3. Hash del analizador no verificado contra el tag/sha declarado.
D4. Parametros por defecto distintos al llamar.

## E. Controles que no pueden fallar
E1. Control positivo construido con el mismo codigo que mide (circular).
E2. Control negativo que no puede dar positivo (nulo no medido, A110).
E3. Fixtures sinteticos que ya traen la respuesta; verdes por construccion.
E4. Tests que comparan por subcadena (A92), NaN con != (S132), assert siempre verdadero.

## F. Bateria / nulo pasan por la razon equivocada
F1. Mutaciones "atrapadas" por caida (excepcion/import error) y no por aserción (S152).
F2. Mutaciones equivalentes o que mutan comentarios/literales sin efecto.
F3. Un mutante no aplicado (patron no encontrado) cuenta como atrapado/sobreviviente mal.
F4. El conteo "13 de 13" / "18/18" no coincide con lo que realmente corre (A112: arbol en movimiento).
F5. La bateria se corre contra un evaluador distinto (--evaluador) al del tag sellado; sha no verificado.
F6. Mutaciones solo en un archivo; no cubren lector, generador y separador por igual.

## G. Despacho propuesto rompe el workflow
G1. Comando gh workflow run con inputs inexistentes o un input mal nombrado; el yml sellado no los acepta.
G2. Fechas/tamaños que exceden el limite de matriz (256 jobs) o timeouts de 50 min / 6 h.
G3. `"on":` quoting (A43), concurrency group, push a main (A47) por el workflow; secretos (EARTHDATA_TOKEN, A71).
G4. Despacho antes de merge a main (HTTP 422, workflow_dispatch solo en default branch).
G5. Disco del runner / artefacto demasiado grande; retencion.

## H. El texto afirma lo que el codigo no hace
H1. Numeros del texto (20 pasadas, 5.841, 62/62...) no reproducibles o transcritos a mano (A91 integridad).
H2. Afirmaciones "no toca pipeline/", "no cambia la lectura sellada", "lee en solo lectura" falsas.
H3. Referencias file:line envejecidas (A101).
H4. Dice que reproduce la lectura sellada pero cambia criterio (P-valor, umbrales, regla D-9, regla SN).
H5. Lenguaje: voseo, guiones largos (grep -c — debe dar 0), rutas relativas.
H6. Promesas de pre-registro: criterio decidido ANTES del resultado; la adenda agrega criterios post-hoc o
    deja libertad (garden of forking paths) en la lectura de posicion.

## I. Cuestiones de proceso
I1. El diagnostico de posicion para V750-A (lector) usa campos de V750-B sin equivalente o con otra definicion.
I2. Archivos de salida *_salida.txt no corresponden al codigo actual (editados despues, hora de modificacion posterior).
I3. Windows: CRLF/autocrlf, md5 de archivos, encoding cp1252 en salida (A116 etc.).
I4. Dependencias de rutas absolutas del autor (C:\vrp-trabajo...) que no existan en el runner.
I5. Que el modo de falla del generador (sin red, sin gh) produzca lista vacia silenciosa que parezca "0 pasadas".
