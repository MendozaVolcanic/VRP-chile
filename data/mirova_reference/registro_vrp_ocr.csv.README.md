# registro_vrp_ocr.csv — OCR universe expansion (S70-0 T5)

## Origen
- **Path origen**: `C:\Users\nmend\OneDrive\Escritorio\claude\Automatizacion web\Automatizacion web\Mirova-v1\monitoreo_satelital\registro_vrp_ocr.csv`
- **Fecha del archivo origen**: 2026-03-28 11:00 (mtime)
- **Recuperado al repo**: S70-0 T5 (2026-05-20) tras auditoría pre-S70 detectar que vivía solo en el scraper local y no en `origin/main` del repo VRP-chile.
- **Scraper origen**: `Mirova-v1` (módulo `scraper_ocr.py` + `ocr_utils.py`) corriendo OCR sobre PNGs MIROVA, complementa el scrape del consolidado.

## Contenido
- **Filas totales**: 235
- **Tipos de registro**:
  - `ALERTA_TERMICA_OCR`: 216
  - `FALSO_POSITIVO_OCR`: 19
- **Cobertura temporal** (timestamps epoch UTC):
  - Min: 2026-01-20T05:12:00Z
  - Max: 2026-03-28T07:50:00Z
- **Vols cubiertos** (top con conteo):
  - Lascar: 98
  - Isluga: 33
  - Puyehue-Cordon Caulle: 29
  - Lastarria: 27
  - PlanchonPeteroa: 18
  - Tupungatito: 13
  - Chaiten: 7
  - Villarrica: 5
  - Nevados de Chillan: 3
  - Copahue: 2
- **Columnas**: `timestamp`, `Fecha_Satelite_UTC`, `Fecha_Captura_Chile`, `Volcan`, `Sensor`, `VRP_MW`, `Distancia_km`, `Tipo_Registro`, `Clasificacion Mirova`, `Ruta Foto`, `Fecha_Proceso_GitHub`, `Ultima_Actualizacion`, `Editado`, `Color_Punto_Dist`, `Confianza_Validacion`, `Requiere_Verificacion`, `Metodo_Validacion`, `Nota_Validacion`, `Version_OCR`

## Por qué importa
Las calibraciones operacionales adoptadas en S62-S63 usaron este universo expandido (consolidado + OCR) para llegar a las ratios reportadas:
- **Lastarria** 1.07× (S62, adoptado `local_kernel_bg: true`)
- **Chaiten** 2.23× (S63, adoptado)
- **PCC** 0.29× (S63, adoptado)
- **Lascar** 1.37× natural (sobre 525 ALERTAS combinadas CONS+OCR, confirmado clon literal)

Sin este CSV en el repo, las ratios reportadas no eran reproducibles externamente. Esta recuperación cierra el gap de reproducibilidad detectado en la auditoría pre-S70.

## Discrepancia vs memoria S62
La memoria S62 menciona "~457 ALERTAS_TERMICA_OCR adicionales" sobre el consolidado. Este snapshot (28/03/2026) tiene 216 ALERTAS_TERMICA_OCR. Posibles explicaciones:
- El conteo de memoria incluía ALERTAS de PNGs subsiguientes (post-snapshot) que el scraper procesó después.
- "~457" puede haber referido al delta combinado de CONS+OCR vs CONS solo, no solo a ALERTAS_TERMICA_OCR.
- Es el snapshot estable disponible en el scraper local al momento del rescate; si el scraper genera nueva versión, sobreescribir y subir un commit nuevo.

Para las auditorías S70+, este es el universe OCR consultable.

## Cómo regenerar si se actualiza el scraper
1. Correr Mirova-v1 OCR pass: `python "C:\...\Mirova-v1\scraper_ocr.py"` (ajustar al script real).
2. Copiar `monitoreo_satelital\registro_vrp_ocr.csv` al mismo path en este repo.
3. Actualizar el conteo de filas y el rango de fechas en este README.
4. Commit como `S<N>: refresh CSV OCR universe (NN filas, YYYY-MM-DD → YYYY-MM-DD)`.

## Excepción de `.gitignore`
El archivo está explícitamente whitelisted en `.gitignore` (regla S70-0 T5) junto con su README, anulando el catch-all `data/mirova_reference/*` que evita commitear los 98 MB de la OSF v2.5.
