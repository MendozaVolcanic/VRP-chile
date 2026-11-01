# Caminos por los que cada afirmación podría estar mal (escrito ANTES de leer el informe)

Hora del servidor (header Date de api.github.com): Mon, 26 Oct 2026 01:45:10 GMT
Commit medido: 014a1ab61 (origin/s162-v375-protegidas-snpp). Regla #903: 719e9c32e (origin/instrumento/clase-pasada).

sha256 de los artefactos del informe al momento de escribir esto:
```
59239ecee2e2e77d56dee17ed8f80252d1e441589f628080e61bd673251ce8c9  00_md5_png.txt
f8e7940dd9dc48ae599271455068af430a7a968d8cb039853c3de79b3ae2bf68  01_records_produccion.json
9c638127974401dfb2e391e7347427cc4debd8141094d9dc8aa496721d4c9925  01_records_produccion.py
0bff415b32bf5691724bf14cb8c488b9146b75710fce586d19a9b4b177d51d12  01_records_produccion_salida.txt
f76de5a627c8697e7217b3da238e04eb3ee52914d6b657850322aac972a910df  01b_hotspots_otras_pasadas_salida.txt
889591caf31bdcb425f7f49e649917fd889b771c92bc30eb993580e7786413e9  02_regla_903.json
f38be24442914b423cbee7d2864f9faa69a5005016b59f9a5166403e5137d1de  02_regla_903.py
59e5d4c7f91a8e1a49fed8d13ff3d01f4e154d5f6f276a4b9b6d51e2c29b3900  02_regla_903_salida.txt
99c83e6de411b37d451d6efa5fbc1018974e1c870c0660c0e4b209ab0ac24996  03_evidencia_por_pasada.json
b5b7e477b760bd4f1267588387dee0762daae46bc04db534cfb199025411fea9  03_evidencia_por_pasada.py
0104dc42a5d9cada3cb8dedd1f629c43d5e8215c9a05d6b35bf533be9bc6a334  03_evidencia_por_pasada_salida.txt
e48aef11531dc84bafb651b36ed99c180d8625df7fa6421a783d278987db428e  03b_regla_distancia_port.py
b210745761a74240dea0397cf2bc2f1eac7a49a3aca0478f5a6769ad336a0273  03b_regla_distancia_port_salida.txt
94c9af85b2a4074f65d8c52c1530531bcdff0a7a9c69e8eb848b323cf53bc961  INFORME.md
6e55c90bd5f17cf20edaa541f1806b8605e57b8702358c59e792809c015597eb  _clase_mirova_903.py
```

## Afirmación 1 (0 de 6 protegidas de cráter con #903; motivo ocr_snpp_antes_del_hito; latest.php no trae ninguna)
- C1a. `_clase_mirova_903.py` es una copia distinta de `scripts/clase_mirova.py` de 719e9c32e (copiada de otro commit, editada a mano, o de una versión posterior/anterior del PR).
- C1b. El script la aplica con otros parámetros (fecha del hito, umbral 1 MW, radio) o con la fila mal parseada (sensor, satélite, fecha UTC vs local).
- C1c. El motivo `ocr_snpp_antes_del_hito` es circular: la regla excluye por construcción toda fila OCR de SNPP antes del hito, así que «0 de 6» no aporta evidencia física, sólo que la regla se aplicó. Distinguir «la regla dice» de «no es cráter».
- C1d. Las 6 filas no son las 6 que los brazos pierden (selección distinta, otra ventana, otros volcanes).
- C1e. «latest.php no trae ninguna» medido contra una copia atrasada del consolidado o con alias de nombre de volcán mal (A14) o ventana horaria demasiado estrecha.
- C1f. Si el instrumento estuviera muerto (la regla siempre devuelve no-cráter) daría también 0: falta control positivo (protegidas que sí salen de cráter).

## Afirmación 2 (cabecera Last Update de la imagen es de pasada posterior, 18 a 102 min)
- C2a. La imagen leída es de otro volcán (nombre de archivo, alias) u otra hora (la hora del nombre no es la de la imagen, A106).
- C2b. La cabecera se leyó mal (OCR del propio verificador, zona horaria UTC vs local, AM/PM).
- C2c. El md5 repetido entre imágenes es coincidencia o es una imagen genérica (placeholder) y no implica imagen de otra pasada.
- C2d. La imagen «guardada con la hora de la fila» no es la que usó el OCR para producir esa fila (el scraper pudo leer otra).
- C2e. Que la cabecera sea posterior no prueba que la distancia/clase sean de otra pasada si MIROVA mantiene el mismo VRP y distancia en la cabecera.
- C2f. Rango 18 a 102 min transcrito a mano y no reproducible.

## Afirmación 3 (VRP de cada fila es de su pasada y calza con píxeles a 8,7 a 29 km)
- C3a. Pareo VRP-píxel por azar: con muchos píxeles y combinaciones, alguna suma calza con cualquier VRP (falta nulo).
- C3b. El granulo del port/K no es el de la pasada de la fila (hora distinta).
- C3c. Las distancias están medidas desde otro punto (centro de grilla vs cráter, A3) o confunden radio con posición (A93).
- C3d. Coeficiente/area distinta entre port y K que cambia el calce.
- C3e. «VRP de su pasada» puede ser circular si la única evidencia es que calza con algo en esa pasada.

## Afirmación 4 (las 3 que K publica, por píxel débil del cráter 0,008 a 0,041 MW)
- C4a. K publica por otro cúmulo (lejano) y el píxel de cráter es secundario.
- C4b. Los records de producción usados no son los de K (otro detector, régimen previo a K o reproceso, A104).
- C4c. «Del cráter»: distancia desde el vent o desde centro de grilla; inner_radius distinto.
- C4d. Rango 0,008 a 0,041 transcrito, campo equivocado (pc.vrp_mw vs f5_core_vrp_mw, A10).

## Afirmación 5 (128 de 234 protegidas A de VIIRS 375 son sólo OCR anteriores al 2026-10-09)
- C5a. Otra ventana (toda la referencia vs ventana del A/B), otra lectura (A vs B), otra copia del CSV.
- C5b. «Sólo OCR» definido distinto (OCR sin fila CONS en la misma pasada vs en la noche).
- C5c. 128 cuenta todos los satélites y no sólo SNPP, o al revés; o incluye diurnas.
- C5d. Corte de fecha UTC vs local; filtro de 1 MW con >= vs >.
- C5e. Denominador 234 de otra corrida (A90).
