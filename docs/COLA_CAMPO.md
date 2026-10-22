# Cola de validación en campo (abierta en S160)

Casos que ninguna auditoría puede cerrar desde el código ni desde los records: hay que mirarlos con los ojos (el
tablero, una lámina de MIROVA, una imagen SWIR) o esperar a que pase algo en el mundo. Cada auditoría declara cuántos
ítems aporta y cierra los que pueda; un ítem cerrado no se borra, se marca con la fecha y el resultado.

Abierta por la síntesis de la auditoría S160 (`docs/AUDIT_S160.md` §6), según el plan `docs/PLAN_AUDITORIA_S160.md` §7.
Dónde vive y quién la mantiene es decisión de Nicolás (plan §9, decisión 4); esta ubicación es la recomendada.

| ID | qué mirar | qué decide | qué desbloquea | de dónde sale | estado |
|---|---|---|---|---|---|
| C-01 | Láscar, 2026-10-08 05:42 UTC, VIIRS 750: lámina de MIROVA contra tablero contra figura del oráculo | si el fondo nuestro apaga un píxel que MIROVA publica | D25 (fondo) y el hallazgo 203 de S160 | `docs/AUDIT_S158_R2.md` §9 caso 1 (enlaces y qué ver ahí) | abierto |
| C-02 | Nevados de Chillán, 2026-10-10 05:54 UTC, VIIRS 750: cuántos píxeles abarca la mancha de MIROVA | si la diferencia de magnitud viene del conteo de píxeles | D32 y F1-H6 de S158 (verificado en S160, gravedad 4) | `docs/AUDIT_S158_R2.md` §9 caso 2 | abierto |
| C-03 | Cordón Caulle, 2026-10-10 05:54 UTC, VIIRS 750: rumbo del píxel de MIROVA | si la ROI de MIROVA (caja de su grilla) explica lo que no publicamos | D17 y V2-09 de S160 (caja de cumbre 7 × 7) | `docs/AUDIT_S158_R2.md` §9 caso 3 | abierto |
| C-04 | Tupungatito, 2026-09-28 05:18 UTC, VIIRS 375: distancia del marcador de MIROVA en «Last Month» | si la alerta de MIROVA era del cráter | issue #864 | `docs/AUDIT_S158_R2.md` §9 caso 4 | abierto |
| C-05 | MODIS a más de 40° de cenit en Láscar o Isluga: punto del tablero contra la lámina | si la geolocalización MODIS se corre hacia el nadir | `project_modis_geo_interp_offset` (memoria) | `docs/AUDIT_S158_R2.md` §9 caso 5 | abierto |
| C-06 | El 2026-11-02 después de las 13:00 UTC: ¿el tablero o algún aviso muestra que Suomi NPP dejó de llegar? | si la vigilancia por plataforma funciona en el mundo real | hallazgos 241 y 242 de S160 y PR #892 | `experiments/_s160_audit/f3/` y `v3/` | abierto (fecha fija) |
| C-07 | Nevados de Chillán, Suomi NPP VIIRS 750, 2026-10-01 06:00 UTC: lámina de MIROVA (OCR dio 10,0 MW) contra nuestros 11,08 MW | si una alerta protegida quedaría topada en 5 MW con el K1 del código de MIROVA (-0,7) | V0b-01 de S160, antes de adoptar el K1 del código | `experiments/_s160_audit/f0b/v0b_02_ndc_tope_k1.py` | abierto |
| C-08 | Una pasada VIIRS 750 de la ventana K con cúmulo de cumbre en 0,0 MW y alerta de MIROVA (hay 7): lámina de MIROVA | si MIROVA ve calor donde nuestro recorte a cero lo borra | hallazgo 203 de S160 (gravedad 5) | `experiments/_s160_audit/v2/v_203_cero_salida.txt` (lista de pasadas) | abierto |
| C-09 | Lastarria, VIIRS 375, 2026-04-18 04:42 UTC: imagen de MIROVA de la fila OCR de 1,29 MW | si es una alerta del cráter o un objeto a 20 km mal leído; hoy cuenta como protegida en todo evaluador con el combinado | hallazgo 162 de S160 y V1a (filas 811, 813 y 815 de `registro_vrp_ocr.csv`) | `experiments/_s160_audit/v1a/` | abierto |
