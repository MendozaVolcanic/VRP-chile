# MOD-A: qué dice Coppola et al. 2026 (Scientific Data) sobre MOD03 (S162, sesión del instrumento, 2026-10-24)

Tarea MOD-A del programa por sensor (`docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md` §5 y §10:
«MIROVA usa MOD03», en disputa hasta MOD-A).

## Fuente y método

- PDF: `documentacion/Coppola_2026_SciData_Global_VRP_Dataset_s41597-026-08100-7.pdf` (carpeta fuera de git en la raíz
  del repo), sha256 `2b157f4868f6771107f4eb04f99053e60192f65c882d0461fd977a5e5018f398`, 25 páginas, versión «ARTICLE IN
  PRESS» (sin número de página impreso en esta hoja).
- Lectura: la página se **renderizó a imagen** con PyMuPDF (`page.get_pixmap(dpi=200)`, índice 3, cuarta página del
  PDF) y se leyó la imagen, no la capa de texto (A95). El render queda fuera del repo público (regla S158), en el
  scratchpad de la sesión: `C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile--claude-worktrees-s162-instrumento-021324\6969e0b5-2fb5-4304-a5de-456246cedf2d\scratchpad\modA\p_idx3.png`.
  Para reproducirlo: `python -I -c "import fitz; fitz.open(r'<pdf>')[3].get_pixmap(dpi=200).save('p4.png')"`.
- Búsqueda en las 25 páginas: MOD03 y MYD03 aparecen **sólo** en esa página (capa de texto, como localizador; la
  lectura es la de la imagen).

## Qué dice (p. 4 del PDF, primer párrafo, encima de la figura 1)

1. Para el período MODIS (2000 a 2025) se usaron los productos de radiancia calibrada de nivel 1B, `MOD021KM` y
   `MYD021KM`, «together with the corresponding MOD03 and MYD03 Terrain-Corrected Geolocation products».
2. Para VIIRS (2012 a 2025), los productos de 750 m (`VNP02MOD`, `VJ102MOD`) y de 375 m (`VNP02IMG`, `VJ102IMG`),
   acoplados a sus geolocalizaciones con corrección de terreno (`VNP03MOD`/`VJ103MOD` y `VNP03IMG`/`VJ103IMG`).
3. Los productos se obtuvieron por los sistemas de distribución LANCE y LAADS de NASA.

## Qué NO dice (límites de la cita)

- **No dice cómo se usa la geolocalización**: ni si se lee la latitud y longitud de cada píxel desde MOD03, ni si se
  interpola desde los puntos de amarre, ni cómo entra en el remuestreo a la grilla. «Se usaron junto con» no es «cada
  píxel se ubica con MOD03».
- **Describe el archivo, no el NRT**: es el data paper del conjunto 2000 a 2025 (OSF v2.5). A105 ya marcó que el OSF
  es un producto filtrado y distinto del canal de tiempo casi real que clonamos. Que el NRT de hoy use MOD03 es
  coherente con el texto pero **no está escrito** ahí.
- No nombra NOAA-21 (`VJ202MOD`, `VJ202IMG`): el archivo termina en 2025.

## Sobre «P1 y P3 discrepan»

El programa dice que P1 y P3 discrepan, sin citar dónde lo hace P3. Encontré la afirmación de P1
(`tasks/LOOP_OBJETIVOS.md:502`, R2.6: «Coppola 2026 Sci Data p. 4 dice que MIROVA usa MOD03 con corrección de
terreno») y no localicé por `git grep` en `origin/main` (docs, experiments, tasks) un texto de P3 que la niegue.
Lo más probable es que la discrepancia sea entre «insumo» y «método», que es justo lo que separa el veredicto de abajo;
queda como SOSPECHA hasta que la coordinadora indique el texto de P3.

## Veredicto sobre la disputa

- «MIROVA usa MOD03 con corrección de terreno» como **insumo declarado del archivo**: **CONFIRMADO** (p. 4, párrafo 1,
  leído en imagen). Coincide con lo que decía `tasks/BLOQUE_ARRANQUE_S159.md:74` y con `docs/BEYOND_MIROVA_EXTENSIONS.md:327`.
- «MIROVA ubica cada píxel MODIS con MOD03 en su cadena NRT»: **SIN LOCALIZAR** en este paper. Lo que sí es medido es
  nuestro lado: hoy `pipeline/process_modis.py` interpola las coordenadas de 5 km y baja MxD03 sin usarlo
  (`experiments/_s152_paper_revision/INFORME_CAMBIOS_PAPER_v1.md:111`, memoria `project_modis_geo_interp_offset`).
- Consecuencia para MOD-B (MxD03 sobre K, D-19, tarea 1.30): la cita respalda **que** MIROVA tiene MOD03 a mano; la
  forma de usarlo sigue siendo una elección nuestra que el pre-registro debe declarar como tal, no como copia de
  MIROVA. La rebaja «en disputa» de §10 del programa puede pasar a: confirmado como insumo, sin localizar como método.
