# Verificador con contexto limpio: propagación de K (S157)

Worktree leído: `D:\vrp-trabajo\s157-propagar-k` (rama `s157-propagar-k`, HEAD `57d18ad78`), sólo lectura. No
corrí pytest ni escribí nada dentro del worktree. Las marcas S157 las leí con `git diff origin/main`. Única
lectura del almacén de objetos: `git show efd1b8a9…:pipeline/profiles/mirova_equivalent.yaml` (árbol que dejó
`simular_revert.sh`).

## 1. Pasajes sin marca que contradicen a K (de más grave a menos)

1. **`CLAUDE.md:1859-1870`, sección «Estado».** Lista D11 bajo «**CERRADAS, no reabrir** (anti-A8)»: «D11 cara
   far→summit (⚠️ S125: … el "irreducible" vale para la vía espectral/de magnitud…)». Es el archivo que se lee
   primero y la única salvedad es la de S125. La marca S157 de D11 (catálogo) y la de A82 dicen que la condición
   del cierre (banda 21) ya no rige; acá sigue mandando «no reabrir» sin marca.
2. **D12, `docs/MIROVA_DIVERGENCES.md:1664`** («MODIS Láscar pierde ~70/79 alertas por `distance_class` del píxel
   Salar») y su eco en **`CLAUDE.md:1858`** («y **D12** (FN MODIS; … cierre formal pendiente»). Con K, MODIS publica
   en Láscar 39 de 39 protegidas y recall 60 de 65 (`experiments/_s153_fk_v2/v2.log:224`; C0: 6 de 39 y 7 de 65,
   l. 223). Las marcas de D12 son S125 y S146; ninguna menciona K. El mecanismo (etiqueta desde el píxel Salar) no
   está medido bajo K, pero el «pierde» presente queda contradicho.
3. **D11-bis, `docs/MIROVA_DIVERGENCES.md:1639-1641`**: «records cuya única fuente es el Test1 integrado
   (`final_hotspot_source='test1_roi'`) … En producción son **2365 records**», más un pendiente de tooltip.
   Bajo K: 0 records `test1_roi` desde la observación del 2026-09-18
   (`experiments/_s155_audit/frente_1_verif/v_fuente_hotspot_k.txt`: sólo `None`, `ctx_cluster`, `eruption`).
4. **`docs/FICHA_SDA_VRP_CHILE.md:7`, cabecera «Versión»**: «rige desde el merge del PR de adopción, cuya fecha y
   hora UTC muestran las tres vistas del tablero». La precisión S157 (iii) del cuerpo dice que en los datos rige
   desde la observación 2026-09-18, y `frontend/cambio_detector.js:24-26` dibuja la línea ahí. Encabezado que
   contradice al cuerpo (A113 d).
5. **`pipeline/process_viirs.py:7-8` y `:13`, cabecera FICHA**: «En regimen de muy baja energia recupera focos
   sub-pixel con anillo de fondo intermedio condicionado» y «T de fondo (anillo/intermedio)». El anillo intermedio
   sólo alimenta `effective_L_bg` (l. 1903-1924), que se consume sólo con `final_hotspot_source == "test1"`
   (l. 1935, 1949 y siguientes): inerte bajo K. La marca S157 de la l. 6 sólo rebaja «el 'ROI'».
6. **`docs/INDEX.md:74-75`, sección CANÓNICOS**: «Design frente **ABIERTO** fondo-local NTI» y «Design frente
   **ABIERTO** Test1-NTI co-validación». Frentes sobre un camino apagado en producción; sin marca.
7. **`docs/MISSION.md:168-171`**: «el operacional **hoy sí conmuta por volcán**: `enable_test1_lbg_global` está
   gateado por `lbg_global_compatible`…». Ese flag sólo toca el VRP del Test 1 (`process_modis.py:1365`,
   `process_viirs.py:1923`, `process_viirs_mod.py:1263`): bajo K no conmuta nada. La marca general de
   `MISSION.md:8-17` lo cubre sólo si el lector sabe que ese flag es del Test 1. (La conmutación por
   `local_kernel_bg` sí sigue viva.)
8. **`pipeline/process_modis.py:94-96`** (comentario de módulo junto al docstring): «NTI … computed per-pixel from
   Band 21 (MIR ~3.93 um)». Con K el MIR es la 22 (`process_modis.py:337-338`).
9. **`docs/MIROVA_DIVERGENCES.md:706`**, tabla «Roadmap»: «D4 | Recall sub-pixel summit | ✅ **Cerrado S27** [...]
   H_S27_1 confirmada categóricamente». La marca S157 de D4 está en l. 109, no acá. Baja: la tabla es de abril-mayo.

## 2. Marcas S157 con números o citas que no se sostienen tal como están escritas

- **`frontend/index.html:544`** (aviso visible): «Ninguna alerta de 1 MW o más quedó sin publicar». `v1.log:153`
  dice «VIIRS375 K … protegidas A 19 de 21»; las 2 son Tupungatito sólo-OCR de Suomi NPP (`v1.log:63-64`). La
  ficha v1.9 lo explica; el aviso del tablero lo afirma sin salvedad.
- **`frontend/index.html:1624`** (comentario): «en los 24 summit el marcador coincide con el cúmulo».
  `v_eruption_marcador.py` compara la **distancia radial** de `anomaly_pixels[0]` con `final_hotspot_dist_km`:
  ni posición (A93) ni cúmulo. Los conteos 52 y 24 sí se sostienen.
- **`docs/MISSION.md:24-25`**, marca (c): «aunque el perfil sí vuelve a C0 (… salida en `revert_hoy.out`)». La salida
  no imprime ese control (P2 del script). Lo comprobé aparte: en el árbol `efd1b8a9` están `enable_test1_path: true`
  (l. 263), `enable_modis_b22_primary: false` (l. 567) y no aparece `enable_tests_23_prose_branch` (default False,
  `profile.py:727`). El hecho es cierto; la evidencia citada no lo muestra.
- **`CLAUDE.md` A117**: «en V2 publica 6 de 39 … (`v2.log:223-224`)». La l. 223 es el brazo C0 del A/B, no los datos
  del laboratorio. La equivalencia C0 = laboratorio sale de S155 `v_flags.txt` (difieren sólo en los tres flags).
  Menor.

Verificado y correcto: `v1.log:178` (107 y 7 de 825), `v2.log:233` (242 y 18 de 2.173; PCC 158 en l. 242),
`v1.log:91` (16 de 194; C0 0, l. 90), `v2.log:148` (26 de 388), `v2.log:223-224`, `process_modis.py:337-338`,
`process_viirs.py:1876`, 0 de 3.687 (`v_fuente_hotspot_k.txt`), 0 de 3.661 (`efecto_k_en_datos.out`), conflictos
del revert en 3 archivos (`revert_hoy.out`), `34cea39e` = 2026-10-18 09:57:30 UTC, `5783192c1` (backfill
Villarrica), bloque de arranque S150 en `main` y S157 en `loop/activo`, cifras del aviso (239/260, 400/426, 28/42,
91/117, C0 32 y 95), precisiones (i) y (ii) de la ficha (`a61/INFORME.md` l. 126-148).

## 3. Dudosos

- **`CLAUDE.md:188`**: la marca general sobre «las reglas A-número» vive al inicio de «Reglas S14». A100, A114 y
  A117 están varias secciones abajo, así que quien entra directo no la ve (A113 c).
- **Marca S157 de A100**: «con K `keep_peak` no actúa». Vale para el keep-peak del Test 1 (`process_viirs.py:1880`),
  pero `FOCAL_CLUSTER_KEEP_PEAK` sigue corriendo en MODIS y V750 (`process_modis.py:1172`, `:1422`;
  `process_viirs_mod.py:1349`). Se presta a confusión.
- **`CLAUDE.md:1666-1668`**, glosario FN: «que MIROVA ve integrando ROI completo». Le atribuye a MIROVA el ROI
  integrado (D30). Defecto anterior a K.
- **`frontend/diario.html:93`**, rótulo visible: «Driver A + Driver B Phase 1 (Coppola 2016a Tabla 1)». No
  describe a K.
- **`frontend/cambio_detector.js:58-59`**: «…y los anteriores, del detector C0». Antes del 09-18 los datos no son
  un solo detector (marca S153 de A85: MODIS de enero a junio con gates intra-radio). Además, 26 records MODIS
  Terra posteriores al 09-18 no son K (marca S157 de MISSION).
- **`pipeline/process_viirs_mod.py:12`**: «amplifica el gradiente topografico crater-nieve (A69/A80)». No tiene
  marca de K, y el camino de A69 está apagado.
- **`docs/INDEX.md`**: l. 84 (AUDIT_S114 «irreducible», marca S146 + «Ver D11», sin K), l. 87-88 (D12 «NO
  ADOPTAR», «cerrable»), l. 67 («Diagnóstico vivo» A69), l. 92 (anillo [1.5,3], sólo Test 1).
- **`docs/MIROVA_DIVERGENCES.md:989`**: «Lascar 64% queda como límite físico aceptado». Cae dentro de H_S27_1 (lo
  cubre la marca S153 genérica), contra Láscar 39 de 39 con K.
- **`docs/MIROVA_DIVERGENCES.md:2734`** (D25): «…y todo el camino Test 1».
- **Ficha, «Texto original»**: «…mediante un anillo de fondo intermedio…» (inerte, como el punto 5). La marca
  v1.9 rebaja sólo el punto (4); la v1.7 dice «no describe del todo».
- **Fuera del alcance pedido, sin cambios en esta rama** (S155 F1-05, F1-07, F1-10, F1-11, V1-03):
  `mirova_equivalent.yaml` cabecera, `experimental.yaml:26-30`, `detection_context.py` cabecera y l. 935-939,
  `test1_integrated.py` cabecera, `process_modis.py:772` («B21 primary, B22 fallback»).

## 4. Cobertura sin problema

- `CLAUDE.md`: punto NTI (marcas S153 y S157), A69, A82, A100 y A117 con marca propia, A83/A84/A85 heredan, bloque
  de arranque.
- `MISSION.md`: marca de cabecera, D4, D11, vent-path, sección «literal pierde recall», H_S27_1.
- Catálogo: encabezados de D4, D10, D11, D19, D21, D24, D26 y D30; D22, D23, D31 y D32 no contradicen a K.
- `INDEX.md`: filas S157 (`_s153_fk_v2`, `_s137`, B22, D-4).
- `process_modis.py`: cabecera y docstring «Bands». `process_viirs.py`: cabecera «Lógica».
- `frontend/`: modal de `index.html`, `cambio_detector.js`, `diario.html` y `mosaico.html` (sólo comentarios
  `triggered_test1`, que valen para datos C0).
