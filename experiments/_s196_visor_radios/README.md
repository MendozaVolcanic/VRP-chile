# Visor de radios del edificio (S196)

**Para qué.** El laboratorio por áreas (`config/areas_laboratorio.yaml`, #1092) separa cada volcán en cráter, agua,
flanco y resto. El flanco es el anillo entre el cráter (radio interno de MIROVA, KML) y el borde del edificio. El ítem
P0 del plan del experimental (`docs/PLAN_EXPERIMENTAL_MEJORAS_S196.md`, #1103) vigila ese anillo aparte del cráter, para
que un calor conocido y constante (lacolito de Cordón Caulle, lago de lava de Villarrica, cráter de Láscar) no esconda
un foco nuevo en otra parte del volcán. Hoy el borde es 10 km provisional en todos. Por la decisión D-H del 2026-11-23,
Nicolás fija un radio por volcán desde la geología; este visor es para eso.

**Abrir.** Local: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s196_visor_radios\visor_radios.html`
(necesita la carpeta `fondos\` al lado e internet para cargar Leaflet). Publicado: Artifact
https://claude.ai/artifact/YaZuZ3pWuxfAZQG2UJY7PL (privado de Nicolás).

**Qué muestra.** Por volcán: imagen satelital o relieve sombreado con curvas de nivel (o la mezcla), el radio interno
de MIROVA (celeste), el provisional de 10 km (blanco punteado) y el radio que se elige (naranjo; deslizador, botones de
±0,5 km o arrastre del punto del borde). Encima, las casillas de 1 × 1 km donde la vía alertó de noche, en color por
número de noches, y el agua de `frontend/agua/<Volcan>.geojson`. El panel cuenta casillas y noches por área con el radio
elegido y lista las casillas recurrentes (3 noches o más) que quedarían fuera del edificio.

**Dónde queda lo elegido.**
- En el Artifact: base de datos del Artifact, colección `radios`, un documento por volcán (id = nombre de
  `volcanoes.yaml`) con `radio_flanco_km`, `cuando` (UTC), `criterio` (texto libre), `por_id` (id opaco de quien guardó),
  `es_dueno` (si fue el dueño del Artifact), `radio_provisional_km` e `inner_radius_km`. Cada guardado agrega además una
  fila a `historial`. El loop lo lee con `ArtifactData` (`action: list`, `collection: radios`) sobre la URL de arriba.
- Abierto desde el disco: sólo en ese navegador (localStorage), con aviso en la cabecera.
- En los dos: botón «Descargar YAML» o «Copiar YAML», con el formato de `config/areas_laboratorio.yaml` (en el Artifact
  se descarga como `areas_laboratorio.yaml.txt`, porque la plataforma no admite la extensión `.yaml`). Los volcanes que no
  están hoy en la partición (Cordón Caulle y los de la sombra) salen con un comentario: los de la sombra no tienen
  `inner_radius_km` en `volcanoes.yaml`, así que la partición no los puede leer tal cual.

**Cómo se rehace.**

```
python experiments/_s196_visor_radios/fondos.py          # imágenes de fondo (baja teselas; caché en D:\vrp-trabajo\temporales\s196_visor\teselas)
python experiments/_s196_visor_radios/datos_visor.py     # calor por casilla y agua -> datos_visor.json, datos_visor_salida.txt
python experiments/_s196_visor_radios/construir_visor.py # plantilla + datos -> visor_radios.html
```

**Datos (números sólo de `datos_visor.py`).** Records de la vía (`via_codigo_mirova: true`), pasadas nocturnas con el
criterio de `experiments/_s194_areas/particion.py::es_nocturna`, desde el 2026-03-01 (noche local; la primera noche
contada es la del 2026-02-28 porque una pasada antes de las 12 UTC pertenece a la noche anterior). Tier A desde
`data/mirova_equivalent/`; los demás desde `data/sombra_34/`, que corre la vía sólo desde el 2026-11-03 (unas 20
noches). Casillas de 1 km en coordenadas locales desde el cráter (`get_detection_anchor`), noches distintas por casilla
(A94). Resumen por volcán en `datos_visor_salida.txt`.

**Límites.**
- La casilla se asigna a un área por la distancia de su centro; la partición asigna cada píxel por su propio `dist_km`.
  Cerca de un borde los conteos del visor pueden diferir en una casilla de los de `particion.py`.
- El agua se marca por el centro de la casilla.
- Fondos: ESRI World Imagery (atribución Esri, Maxar, Earthstar Geographics) y Terrain Tiles de AWS Open Data. El
  modelo de elevación trae picos falsos muy negativos (Villarrica, -3.743 m): se recortan al percentil 0,5 antes de
  sombrear. Caja de ±30 km a zoom 12 en los Tier A y ±20 km a zoom 11 en los demás.
- El guardado desde la página publicada no se probó en un navegador con sesión de claude.ai; sí la escritura y lectura
  de la colección `radios` por `ArtifactData` y el guardado local con el YAML resultante (parsea y tiene las mismas
  claves que `config/areas_laboratorio.yaml`).
