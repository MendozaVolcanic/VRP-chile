# Dónde está la paridad con MIROVA, y qué queda por revisar (S145)

> Medido por `scripts/banco_paridad.py` el 2026-09-20, salida en
> `experiments/_s145_paridad/banco_s145.json`. Ningún número escrito a mano (S91).
> Ventana **2026-09-01 a 2026-09-20**: el régimen actual empieza con el PR #571
> (2026-08-31, retiro del piso VRP). Una ventana que cruce #535 o #571 mezcla dos
> regímenes y no se puede leer (A104). Publicar = predicado del dashboard ejecutado
> con node (A97), con su control de identidad en verde.

## 1. Los números

2285 records nocturnos de los 11 Tier A. Etiquetas: 162 **pos** (MIROVA alertó), 1433
**neg_limpio** (MIROVA miró esa pasada y no vio nada), 32 **far_ref**, 658 **sin_info**.

| sensor | recall por pasada | n | recall por noche | n | publica en negativos limpios (pasada) | n |
|---|---|---|---|---|---|---|
| MODIS | 1,000 | 1 | 1,000 | 1 | 0,114 | 438 |
| VIIRS 375 | 1,000 | 143 | 1,000 | 75 | **0,863** | 373 |
| VIIRS 750 | 0,722 | 18 | 0,929 | 14 | 0,214 | 622 |
| **cualquiera** | **0,969** | 162 | **1,000** | **78** | **0,352** | 1433 |

⚠️ El `n = 1` de MODIS no permite leer una tasa: es una sola pasada con alerta en la
ventana. Su `publica en negativos` sí tiene 438 casos y es legible.

**Controles del instrumento** (sin ellos los números de arriba no valen): identidad del
predicado en verde; AUC de lo real contra lo barajado, por volcán, entre 0,809 y 1,000
frente a 0,47-0,53 del barajado. El instrumento discrimina y no es azar.

## 2. Qué dicen

**El recall está resuelto.** Por noche, que es la unidad en que el operador vive el
sistema (A94), detectamos **78 de 78**. No hay una sola noche en que MIROVA haya alertado
y nosotros no publiquemos nada. Por pasada, 96,9 %.

La única grieta de recall es **VIIRS 750 por pasada: 13 de 18**. Las 5 que faltan son
exactamente las de `docs/audit_s143/PERDIDAS_V750.md`, todas por el mismo mecanismo (D25,
el cráter con magnitud recortada a cero), y **las 5 caen en noches que otra pasada cubre**.
Por eso el recall por noche de ese sensor es 13 de 14 y no 13 de 18.

**La brecha es de sobre-publicación, y está concentrada en VIIRS 375.** En el 86,3 % de las
pasadas donde MIROVA miró y no vio nada, nosotros publicamos. Por noche, en ese sensor, el
100 %. Esto confirma A98 con datos de hoy y coincide con la línea base de S142 (87,1 %
después de #571).

**Pero "publicar de más" no es lo mismo que "estar mal".** La auditoría S86 midió que el
95,4 % de esos extras son anomalías térmicas **físicamente reales**: lava lake de
Villarrica, lacolito de Cordón Caulle, campo fumarólico Lazufre, cráteres secundarios. Son
señal sub-umbral que MIROVA no publica por alcance operacional, no ruido nuestro.

## 3. El problema real: los dos objetivos comparten una sola salida

`docs/MISSION.md` declara dos objetivos:

1. **Clon literal de MIROVA NRT** (primario algorítmico): reproducir su comportamiento.
2. **Extensión volcánica documentada** (secundario, de reporte): publicar lo que el
   algoritmo de Coppola captura y MIROVA no informa.

Y dice cómo deben separarse: *"La distinción (1) vs (2) vive en el campo derivado
`pc.classification` (diseño S87 Bloque 3) + en el frontend que separa visualmente las
categorías"*.

**Ese campo no existe.** Verificado el 2026-09-20 recorriendo los 11 JSON: ni un solo
record tiene `classification`, ni en la raíz ni dentro de `primary_cluster`. En
`pipeline/` la palabra aparece sólo en comentarios sobre el radio interno.

Esa es la raíz de por qué el 86 % se lee como un defecto. Medido contra el objetivo 1, cada
una de esas publicaciones es una divergencia. Medido contra el objetivo 2, son el producto.
Sin el campo que las distingue, **toda métrica de paridad castiga al objetivo 2 por existir**,
y cualquier intento de "mejorar la precisión" corre el riesgo de destruir categoría b, que
es justo lo que A54 y A72 prohíben.

## 4. Qué queda por revisar, en orden

| # | frente | por qué importa | estado |
|---|---|---|---|
| 1 | **Implementar `pc.classification`** | sin él los dos objetivos son indistinguibles y ninguna métrica de precisión es interpretable | diseñado S87, **nunca implementado** |
| 2 | **D19 `keep_peak`** | gravedad 5 por verificador limpio; S144 midió que publica un sitio tibio **estable**, no un evento | abierta, decisión del dueño pendiente |
| 3 | **D21 y D22** (banda 21 primaria, compuerta de 3 K) | son fidelidad literal al paper y **condicionan** el cierre de D11: mientras sigan abiertas, el "irreducible" de S114 vale sólo bajo la configuración de hoy | abiertas, ningún brazo cumple la batería |
| 4 | **D17 y D28** (grilla UTM, bow tie) | el remuestreo a 1 km del paper no está replicado; S130 midió que el ratio cae 2,7× con el ángulo aun con área nadir | abierta |
| 5 | **D13** (la cerca del frontend apaga el 31 % de la magnitud) | es display, y toca directamente lo que el operador ve | abierta, documental |
| 6 | D23, D24, D25 (MODIS), D26, D29 | fidelidad literal, impacto menor o nulo medido | abiertas |

Fuera del catálogo, dos cosas con fecha: el **token de Earthdata vence el 2026-10-03**, y el
**correo a Coppola** sigue sin enviarse, con 13 preguntas redactadas de las que al menos la
4 (fondo por vecinos y recorte a cero) es hoy la palanca de un frente vivo.

## 5. La lectura en una frase

Detectamos todo lo que MIROVA alerta, publicamos bastante más que MIROVA, y **no tenemos
cómo decirle al operador cuál de las dos cosas está mirando**. Lo primero es un logro, lo
segundo es el valor agregado del proyecto, y lo tercero es el trabajo pendiente que hace
que los otros dos se confundan.
