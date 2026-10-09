# S150: las cinco "alertas fuertes" de Suomi NPP que `max` pierde son filas del OCR con la imagen de otra pasada

> Cierra el pendiente de `docs/S150_RESULTADO_MESES.md` §3 y de `docs/AUDIT_S150.md`: "mirar las cinco imágenes
> de MIROVA". Imágenes bajadas de Mirova-v1 (commit `2866830`) a `experiments/_s150_imagenes_snpp/imagenes/` con
> `bajar_y_comparar.py`; cabeceras leídas mirando cada imagen en esta sesión.

> ⚠️ **CORREGIDO S150, mismo día** (agente del arreglo del scraper, PR MendozaVolcanic/Mirova-v1#20; esta
> sesión no lo re-verificó): el **VRP** de las 5 filas SÍ es de su propia pasada (está en la celda de su hora en
> las imágenes Latest10NTI de MIROVA, siempre con cenit de 59° o más). Lo que viene de la pasada posterior es
> la **distancia y la clase ALERTA** (salen de la estrella de la imagen de distancias) y las imágenes guardadas.
> O sea: eran detecciones de MIROVA con VRP real pero **sin saber si estaban en el cráter**. No son alertas
> del cráter confirmadas, y tampoco artefactos probados. En el caso del 22 de agosto, MIROVA no llevó el
> 1,65 MW ni a su serie ni a latest.php.

## 0. En una línea

**En los cinco casos, la imagen que el scraper guardó con la hora de la pasada de Suomi NPP es, según su propia
cabecera, la imagen de una pasada POSTERIOR**, y en uno es literalmente el mismo archivo. El valor que el OCR
le atribuyó a cada fila no describe la pasada de Suomi NPP. Esas cinco no son alertas reales que `max` pierda.

## 1. El fenómeno

MIROVA publica por volcán una sola imagen viva, que se reemplaza cada vez que procesa una pasada nueva. Su
cabecera dice de qué pasada es ("Last Update", con el cenit del satélite en "Zen"). El scraper de Mirova-v1
baja esa imagen y la guarda con la hora de una pasada; el OCR lee después el valor. Si cuando el scraper la
baja MIROVA ya la reemplazó por la de la pasada siguiente, la fila queda con la hora de una pasada y la imagen
de otra. Es la misma familia que A106 ("MIROVA a veces vuelve a servir una imagen vieja bajo una hora nueva"),
vista desde el otro lado.

## 2. Lo medido

| fila del OCR (Suomi NPP) | VRP de la fila | cabecera de la imagen guardada | nuestro control (B) |
|---|---|---|---|
| Lastarria 2026-05-02 05:06 | 2,36 MW | "Last Update 02-May-2026 06:42:00", Zen 67° | 0,033 MW a 1,0 km |
| Isluga 2026-05-29 04:54 | 0,86 MW | "Last Update 29-May-2026 06:00:02", Zen 30° | 0,013 MW a 4,9 km |
| Láscar 2026-06-25 04:54 | 0,51 MW | "Last Update 25-Jun-2026 06:00:02", Zen 32° | 0,014 MW a 0,2 km |
| Láscar 2026-08-17 05:00 | 0,60 MW | "Last Update 17-Aug-2026 05:18:01", Zen 40° (es NOAA-20 de las 05:18) | 0,024 MW a 1,5 km |
| Láscar 2026-08-22 05:06 | 1,65 MW | "Last Update 22-Aug-2026 05:24:01", Zen 32°; **md5 idéntico** al archivo de las 05:24 | 0,018 MW a 0,3 km |

- La cabecera no coincide con la hora de la fila en **5 de 5**. Tres de los cinco casos son posteriores al
  2026-06-13, cuando el OCR ya medía distancia y geometría: la regla A119 (que descarta el OCR antes de esa
  fecha) no los cubre.
- La pasada que sí está en cada imagen (NOAA-20 o la siguiente de la noche) la publican los dos brazos del A/B
  (§3 de `S150_RESULTADO_MESES.md`).
- **SOSPECHA**, no medido: de dónde salen los valores altos. En la imagen de Isluga hay un triángulo negro (la
  leyenda de MIROVA lo define como detección a más de 5 km del cráter) cerca de 0,86 × 10⁶ W justo antes del
  último punto, y el verificador del resultado de mayo ya había encontrado que las pérdidas fuertes de mayo
  eran fuentes lejanas mal rotuladas. Leer el algoritmo del OCR diría cuál punto toma.
- El valor que nuestro control veía en esas pasadas (1 a 4 % de lo que dice la fila) deja de ser una anomalía:
  la fila no describía esa pasada.

## 3. Lo que cambia

1. **Las cinco "pérdidas fuertes" de `max` dejan de ser pérdidas.** El costo de `max` en recall de VIIRS 375,
   de abril a agosto, queda en las alertas débiles: bajo 0,10 MW. La decisión de recall que espera a Nicolás se
   reduce a esa pregunta.
2. **Una alerta de Suomi NPP que llega sólo por el OCR no es confiable como etiqueta positiva** mientras no se
   compruebe que la cabecera de su imagen coincide con su hora. Arreglo propuesto (repo Mirova-v1, del dueño):
   que el scraper lea la cabecera "Last Update" y rechace la fila si no coincide con `Fecha_Satelite_UTC`.
   Mientras tanto, los evaluadores pueden informar aparte las alertas "sólo OCR" de Suomi NPP, como ya hacen.
3. Cuántas filas "sólo OCR" de toda la referencia tienen este defecto **no está medido**: este documento revisa
   las cinco que decidían un veredicto, no la referencia completa.
