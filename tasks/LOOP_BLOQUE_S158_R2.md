# Bloque S158 R2 para el loop (propuesto el 2026-10-21; lo incorpora la sesión dueña del loop en `loop/activo`)

> Origen: `docs/AUDIT_S158_R2.md` (§0, §10), PR #888. Nicolás pidió el 2026-10-21 que el loop siga «con todo lo que
> estamos desarrollando». Este archivo **no** es el estado del loop: la sesión dueña lo copia a §4 de
> `tasks/LOOP_OBJETIVOS.md` en `loop/activo` y lo borra de aquí. Reglas del loop (§1) intactas: el loop no adopta
> nada en producción, cada palanca va pre-registrada, sellada por Nicolás y con verificador limpio.

Orden de la cola, por lo que destraba:

- [ ] **R2.1 Instrumentos antes de cualquier A/B** (tag defensivo; `pipeline/fetch.py` y `scripts/run_pipeline.py`).
  (a) Que una búsqueda con cero gránulos en un día con pasadas esperadas, y un L1B sin su geolocalización, se registren
  como falla de cobertura y no como «completa» (R2-9, VB-1; reproducción sin red en
  `experiments/_s158_audit_r2/rb/03_cero_granulos_cobertura.py` y `verificador/vb/v02_*`). (b) Que todo pre-registro
  nuevo con métrica de magnitud traiga un brazo placebo de ganancia constante como control obligatorio (R2-8). (c) El
  default `CALIB_MODO = "sellada"` de `experiments/_s157_prereg_d25/evaluar_d25.py:79` contradice la adenda sellada
  (VB-2): corregir sólo por adenda y con Nicolás (el pre-registro está sellado).
- [ ] **R2.2 A/B de D25**: no leer su veredicto. El 2026-10-18 y el 19 no se pueden reponer mientras CMR no los sirva
  (R2-13: 0 gránulos de VIIRS y MODIS el 18-oct a las 17:35 UTC del 21-oct). Decisión para Nicolás (issue
  `decision-nicolas`): evaluar sin esos días o repetir en otra ventana; y agregar un brazo con el fondo del código.
  Vigilar en cada vuelta si CMR vuelve a servir el 18 y el 19 (búsqueda pública `granules.json`, sin credenciales).
- [ ] **R2.3 Pre-registro: fondo y suma del código en VIIRS 750, junto con quitar la compuerta de 3 K del primer
  pase** (VA-1: los ceros de cumbre salen del segundo pase en los tres sensores, hay que medir las dos piezas juntas).
  Fondo interpolado bajo los alertados (`MIROVA_VIIRS750_VRP.m` l. 63-85), sin recorte, suma de todos los alertados, sin
  `single_pixel_mode`. Métricas en las dos caras: alertas de MIROVA de la misma pasada recuperadas (pareo a 8 min, no a
  60) y negativos limpios despegados del cero. Sello de Nicolás antes de despachar.
- [ ] **R2.4 D17 fase 0, probe de gránulos ampliado** (workflow de sólo lectura, rama de disparo, sólo
  `EARTHDATA_TOKEN`). Reusar `experiments/_s158_audit_r2/granulos/probe_granulos.py` sobre unas 40 pasadas VIIRS 750
  (alertas débiles de cumbre y RUTINA), con las variantes de grilla (±375 m) e interpolador (lineal, vecino más cercano)
  pre-registradas, para identificar la grilla de 750 m y el interpolador de MIROVA antes de escribir el remuestreo.
- [ ] **R2.5 ROI de MIROVA en Cordón Caulle y Tupungatito**: medirla en sus TIF y en la `Distancia_km` cuantizada (D15)
  antes de proponer umbrales de cumbre fuera del cráter (la alerta de PCC a 7,8 km sólo aparece con anillo sensible).
- [ ] **R2.6 Geolocalización MODIS desde MOD03** (R2-2): pre-registro y A/B en Actions (pyhdf no corre en Windows);
  cambia posiciones y clases cumbre/escena.
- [ ] **R2.7 Marcas A113 pendientes**: las de §8 de `docs/AUDIT_S158_R2.md` bajo A45 (en el PR que toque cada archivo)
  y las U1 a U13 del meta-auditor (`experiments/_s158_audit_r2/m1/INFORME.md` §3) que siguen sin marca.
- [ ] **R2.8 Pendientes de Nicolás sin tarea del loop**: D-10 (VIIRS diurno; la rama apagada usa K1 -0,6 y no tiene
  filtro de reflejo solar, VB-3) y la revisión visual del §9 de `docs/AUDIT_S158_R2.md`.
