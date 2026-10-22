# Verificador: estabilidad de la referencia de MIROVA (S159, 2026-10-21)

Verificador con contexto limpio del informe `C:\vrp-trabajo\s159-pruebas\experiments\_s159\referencia_estable\INFORME.md`.
Sólo lectura sobre `origin/main` (`d516b9d8c`) y sobre el repo del scraper por la API de GitHub (sin clon).
Scripts en `C:\vrp-trabajo\s159-pruebas\experiments\_s159\referencia_estable\verificador\`.

Desvío declarado: corrí una vez `git fetch origin --quiet` al empezar (escribe refs, la instrucción pedía sólo
`log`/`show`). `origin/main` quedó en `d516b9d8c`, el mismo sha que usó el informe, así que no cambia ningún número.

## Instrumentos y sus dos preguntas

| script | qué mide | ¿vería el defecto? | ¿instrumento muerto se ve distinto? | control positivo |
|---|---|---|---|---|
| `upstream_bisect.py` | presencia de filas en las versiones de Mirova-v1 (5 min) entre dos copias nuestras | sí: si sólo nuestra copia perdiera la fila, el upstream la mostraría presente | cada versión reporta n de líneas; una descarga caída da n = 0, no «ausente» | la fila está en la versión upstream de las 14:41 (n = 42.509) |
| `compara_upstream.py` | bajas, altas, duplicados y nombres no reconocidos por clave | sí | n y `no_tier` por versión | reproduce los 822 duplicados y 163 bajas de `81dd25ce3` |
| `impacto_s153.py` | filas que alguna vez existieron en las ventanas de S153 y faltan en su referencia congelada | sí | n por capa (42.614 / 794 / 11.316) | contra el CSV upstream del 18-oct sin unión faltan 207 (V1) y 507 (V2) filas |
| `union_cobertura.py` | bajas netas cubiertas por la unión | sí | las 163 que vuelven no deben contarse | 1.948 netas, no 2.111 |
| `ocr_contra_tabla.py` | pasadas con OCR = ALERTA y tabla = no alerta en la misma clave | sí | cuenta sobre dos fechas | copia del 2026-05-29: 34 (las 34 de la tanda 1) |

## Veredicto por afirmación

### 1. La tabla pierde filas y no las devuelve: CONFIRMADA en los números, PARCIAL en la atribución y en el efecto en el tablero

- Números: `union_cobertura.py` da 1.948 bajas netas en 6 tandas (202, 186, 207, 529, 194, 630), 14 protegidas, ninguna presente hoy.
- **La pérdida NO es de nuestra copia ni de MIROVA: es del CSV del scraper (Mirova-v1).** `compara_upstream.py`:
  el upstream `96cf680ee` (2026-10-18 17:41) ya tiene las mismas 630 bajas que nuestra `0c8848ff9`, y el `main`
  upstream de hoy también. Nuestra copia es un `curl` + `cmp` + reemplazo del archivo entero
  (`.github/workflows/sync-mirova-csv.yml`, pasos «Download fresh CSV» y «Check if changed»); no normaliza ni mezcla.
- Mecanismo, CONFIRMADO en parte: 11 min antes de la pérdida, el upstream `c292d6b26` (17:30) tenía **1.752
  claves duplicadas y 299 filas menos**; la siguiente (`96cf680ee`) quitó los duplicados y dejó 630 menos. Es la
  firma de H4, y nuestra copia horaria no la vio. Mirova-v1 tiene varios workflows en grupos de concurrencia
  distintos (`monitor-vrp`, `scraper-ocr`, `archivar-evidencia`, `generador-graficos`, ...) que hacen `git add
  monitoreo_satelital/` y `git pull --rebase -X ours` (main.yml l. 68, ocr_workflow.yml l. 135). Que la mezcla de
  líneas de un CSV reescrito entero sea la causa es SOSPECHA fuerte (lo mismo dice MendozaVolcanic/Mirova-v1#19).
- Clave estable, CONFIRMADO: 0 filas con nombre no reconocido en ninguna versión (`no_tier = 0`); las altas que
  coinciden con tandas son pasadas nuevas de 3,5 a 21,5 h, mientras las bajas cubren enero a octubre.
- Tablero, PARCIAL: de las 7 protegidas sin copia OCR, sólo **2 desaparecen del todo** (Láscar MODIS 2026-02-09 07:20,
  confirmado: está en `data/mirova/Lascar.json` de `5c55c0749` y no en `0c8848ff9` ni en `origin/main`; y Láscar MODIS
  2026-04-05 01:35). En las otras 5 (VIIRS) el tablero conserva la misma pasada en la otra resolución, con VRP menor
  (Láscar 03-21 05:06: queda VIIRS 750 de 1,45 MW; Puyehue 01-13: queda 1,07 MW; Láscar 01-15: queda VIIRS 375 de 0,85 MW).

### 2. La unión recupera 1.946 de 1.948: CONFIRMADA, con un matiz en el «atraso»

- `union_cobertura.py`: 1.946 en la unión del 19-oct (`2e1bc0e31`); faltan sólo Láscar y Tupungatito MODIS
  2026-10-16 01:45, RUTINA. La del 14-oct tenía 595 (las tandas de agosto y 6-oct, exactas).
- Matiz: el auto-audit regenera la unión en la misma corrida antes de evaluar (`audit-weekly.yml` l. 61 a 70), así
  que para él el atraso es 0. Los «hasta 50 días» son de agosto a la creación de la unión (14-oct), no atraso de
  regeneración.

### 3. El OCR reescribe 39 alertas: CONFIRMADA la reescritura, REFUTADAS «sin rastro» y la autoría implícita, PARCIAL la refutación de S139

- Las 39 son **correcciones manuales en el scraper, documentadas**: tanda 1 = `b88e7cb45f` (2026-06-15, «reclasificar
  47 eventos OCR mal ubicados», cruzados con `latest.php`) y `2a34d8e42e`; tanda 2 = `52ff007401` (2026-08-04,
  NMendoza, 5 filas del bug de la estrella del panel equivocado). No es MIROVA ni una recalibración automática.
- **Sí queda rastro en la fila**: 39 de 39 pasan `Editado` NO→SI (34) o NO→AUTO (5), `Confianza_Validacion`
  alta→baja y la nota agrega «RECLASIFICADO ...». Sólo `Ultima_Actualizacion` no cambia.
- Las correcciones hacen que el OCR **coincida con la tabla de MIROVA**: en la copia del 2026-05-29 las 34 de la
  tanda 1 ya eran FALSO_POSITIVO en la tabla con la misma clave; hoy hay 0 contradicciones OCR-alerta contra
  tabla-no-alerta (`ocr_contra_tabla.py`).
- S139 ya lo sabía: `docs/audit_s139/MAPA_BASES_MIROVA_V1.md:57` («nunca reescribe las viejas salvo
  `reconciliar_latest.py` ... y ediciones humanas») y `:164-165` (las 49 del 15-jun). El «no hubo reprocesos
  retroactivos» de `:142` habla de volver a capturar imágenes viejas. Lo que sí falta es la tanda del 4-ago y una
  frase sin ambigüedad en `:142`, `:340`, `scripts/calidad_referencia_mirova.py:26` y A119.
- Gravedad que propongo: 2, no 4. Nada cerrado desde septiembre la ve (ver abajo). Lo latente: `clase_mirova.py:65-75`
  cuenta como protegida toda `ALERTA_TERMICA_OCR` aunque la tabla diga FALSO_POSITIVO en la misma pasada.

### 4. Asentamiento: CONFIRMADA

Tabla: máximo 27,16 h, 17 llegadas sobre 24 h, ninguna alerta. OCR desde 09-21: protegidas 19,95 h (n = 33), sin
geometría 131,78 h. Son cotas superiores (hora de nuestro commit), y el OCR con geometría tiene n chico.

### 5. Versión corrupta `81dd25ce3`: CONFIRMADA

822 duplicados, 163 bajas, 0 protegidas; `0e2dff5b2` (19:52) vuelve a 33.420 sin duplicados.

## Evaluaciones cerradas

- **Veredicto de K (S153)**: usó la referencia congelada `_s151_prereg_fk_11/_congelado_v{1,2}/` (Mirova-v1
  `c5944c61`, 2026-10-14 14:26 UTC, con sha256 y copia) más unión y respaldo. `impacto_s153.py`: en V1
  (08-29 a 10-08, 7.284 claves vistas) y V2 (03-01 a 06-12, 15.927) **faltan 0 filas**, y la referencia de hoy da
  las mismas claves con los mismos tipos (0 diferencias). Las reescrituras OCR son anteriores. **No cambia.**
- **#864 (auto-audit del 2026-10-19)**: regeneró la unión en la misma corrida; las únicas filas que no recupera son
  las 2 RUTINA MODIS del 2026-10-16 01:45. A lo más sale un negativo limpio por volcán de MODIS; ninguna protegida.
  No lo re-corrí: SOSPECHA de efecto nulo.
- H6 del informe es PARCIAL: el congelado por hash que su recomendación 1 propone **ya existe** en
  `experiments/_s151_prereg_fk_11/_congelado_v1/MANIFIESTO.json`. Lo que falta es usarlo por defecto en `banco_paridad`.

## VERIFICADO LIMPIO

- Nuestra copia es igual al upstream en la pérdida del 18-oct: `python -I compara_upstream.py b2782fe68 c292d6b26 96cf680ee 1bf0da3a1 local:0c8848ff9 main`.
- 0 nombres de volcán no reconocidos en esas versiones (`no_tier 0`, mismo comando).
- Referencia de S153 sin huecos ni cambios: `python -I impacto_s153.py`.
- OCR coherente con la tabla hoy: `python -I ocr_contra_tabla.py` (0 hoy; control 34).
- Unión: `python -I union_cobertura.py` (1.946/1.948; u14 está contenida en u19).
