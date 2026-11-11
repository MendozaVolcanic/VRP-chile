# S179: las 5 alertas «sólo OCR» que la posición «radiante» de VIIRS 375 no publica

Fecha: 2026-11-11. Pedido de Nicolás («Sí, revísalas»), tras la decisión 1 de `docs/AUDIT_S179.md`. Lectura del
orquestador (Opus 5.5) y lectura ciega e independiente de un verificador Fable 5.2 a `high`, que vio sólo las imágenes
y las cinco filas, sin la conclusión del orquestador. Las dos coinciden.

## La pregunta

Con la regla de posición «radiante» (la que publica hoy el código de la vía, `pipeline/mirova_v750_codigo.py` l. 670 a
726 en `438a60a1e`), la vía no publica cinco alertas de VIIRS 375 de 1 MW o más que K sí publica. Las cinco existen
sólo en el OCR del scraper Mirova-v1; la tabla `latest.php` de MIROVA no las trae. Si MIROVA las vio en el cráter,
encender B1 con «radiante» pierde alertas reales. Si MIROVA las vio lejos, no pierde nada.

## Lo que muestran las imágenes de MIROVA

En los gráficos de MIROVA cada pasada con anomalía lleva una potencia (VRP) y una distancia al volcán; las de menos de
5 km van en rojo y las de más de 5 km en negro. Para octubre está la página «Latest» con la hora exacta de cada pasada;
para marzo no hay imágenes de esos días y se usa el panel «Last Month» de una captura de comienzos de abril, que cubre
marzo (la distancia de cada pasada sigue dibujada en capturas posteriores, regla del S151).

| Pasada (UTC, Suomi NPP) | OCR | MIROVA: color y distancia (verificador) | La vía: cúmulo y distancia | Confianza |
|---|---|---|---|---|
| Isluga 2026-03-20 05:06 | 2,21 MW, dist. 0,0 | negro, 18,6 km, VRP fuera de escala (mayor que 2,18) | 2,199 MW a 18,94 km | ALTA: el otro marcador de esa noche es rojo de 0,45 MW |
| Isluga 2026-03-24 05:30 | 1,51 MW, dist. 0,0 | negro, 23,5 km, 1,51 MW | 1,214 MW a 23,27 km | ALTA: el otro marcador de esa noche es rojo de 0,12 MW |
| Láscar 2026-03-15 05:00 | 1,54 MW, dist. 0,0 | negro, 14,1 km, 1,55 ± 0,07 MW | 1,198 MW a 12,99 km | MEDIA: en la misma noche hay un rojo de 1,74 MW; se identifica sólo por magnitud |
| Isluga 2026-10-03 05:18 | 1,62 MW, dist. 0,95 | negro, 22,7 km, 1,62 MW (escrito en «Latest» bajo la miniatura de 05:18:00) | cúmulo a 22,78 km | ALTA |
| Láscar 2026-10-01 05:18 | 1,20 MW, dist. 1,22 | negro, 20,1 km, 1,20 MW (escrito en «Latest» bajo la miniatura de 05:18:02) | cúmulo a 18,99 km | ALTA |

Fuentes (repos públicos propios): `MendozaVolcanic/Mirova-v1`, `monitoreo_satelital/imagenes_satelitales/Isluga/2026-10-03/05-18-00_Isluga_VIIRS375_{Latest,Dist,VRP}.png`,
`.../Lascar/2026-10-01/05-18-02_Lascar_VIIRS375_{Latest,Dist,VRP}.png`, `.../Isluga/2026-04-04/05-24-00_Isluga_VIIRS375_{Dist,VRP}.png`,
`.../Lascar/2026-04-01/05-00-01_Lascar_VIIRS375_{Dist,VRP}.png`; y `MendozaVolcanic/mirova-tif-archive`, `data/png/` (capturas
posteriores de octubre). Los GeoTIFF del archivo cubren sólo del 2026-05-09 al 2026-09-22: ninguna de las cinco
pasadas tiene TIF. Distancias de la vía: `experiments/_s179_audit/c/c05_ocr_solo_cercano_salida.txt` (marzo) y
`experiments/_s179_audit/vd/vd3_filas_ocr_cinco_salida.txt` (octubre). Scripts del verificador (miden ejes y
marcadores con PIL): `verificador/medicion_final.py` y los de apoyo en la misma carpeta.

## Lectura

1. **MIROVA dibuja las cinco pasadas a más de 5 km**, entre 14 y 24 km, y la vía las ubica a la misma distancia (entre
   13 y 23 km) con casi la misma potencia. Son la fuente lejana que aparece en negro durante todo el año en los
   gráficos de Isluga y Láscar, no el cráter.
2. **El OCR les pegó la distancia de otra pasada.** En octubre, la estrella verde del gráfico de distancia es la pasada
   siguiente (05:36 en Isluga, 0,26 MW; 06:18 en Láscar, 0,09 MW), que sí está en el cráter; el OCR leyó la estrella y
   la asignó a la pasada de las 05:18. En marzo el OCR v21 dejó distancia 0,0. Es el defecto ya conocido del S150
   (`reference_ocr_imagen_de_otra_pasada` en la memoria): VRP real, ubicación de otra pasada.
3. **Con «radiante» la vía no pierde ninguna alerta del cráter en estas cinco.** Hace lo mismo que MIROVA: las clasifica
   lejos. «Cercano» las publicaba porque elige el cúmulo próximo al cráter; eso no es lo que hizo MIROVA.
4. **Salvedad física.** En las miniaturas de las 05:18 hay también un punto en la cumbre, además del lejano. MIROVA
   asigna a la pasada un solo VRP y la dibuja entera en negro, así que las imágenes no dicen cuánto de los 1,62 y 1,20 MW
   viene de la cumbre. Las pasadas vecinas que sólo ven la cumbre dan 0,26 MW (Isluga) y 0,09 MW (Láscar): la cumbre,
   esas noches, estaba bajo 1 MW.
5. **Observación aparte.** Las dos pasadas de octubre desaparecen de MIROVA en capturas posteriores del mismo día
   (Isluga a las 07:44 UTC, Láscar a las 12:37 UTC): ya no están en «Latest» ni en los gráficos. MIROVA retira pasadas
   después de publicarlas. No se investigó por qué.

## Para la decisión 1 de la auditoría

La pérdida de «5 de 72» del hallazgo 551 es un artefacto de la etiqueta del OCR, no una pérdida de alertas del cráter.
Recomendación: encender B1 con la posición «radiante», que es la de MIROVA, y escribirlo en el cuerpo de #974 (VD-03),
citando este informe. Queda MEDIA la identificación de Láscar 2026-03-15; las otras cuatro, ALTA.
