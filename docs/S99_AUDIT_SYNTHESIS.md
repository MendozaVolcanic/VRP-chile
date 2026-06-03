# S99 — Síntesis de auditoría (Tupungatito 19× + PCC >1000 MW + Núcleo/Cluster)

Auditoría pedida por Nicolás (A62 adversarial: insistencia del experto = señal).
4 ramas en paralelo, evidencia en `experiments/_s99_audit/`. NADA de pipeline tocado
(gate de diseño / brainstorming). Ningún número transcrito a mano (S91): todos de
scripts reproducibles citados.

## Pregunta 1 — ¿Tupungatito cambió porque modificamos algo? → NO (input estacional)
Evidencia: `experiments/_s99_audit/git_forensics.md`.
- La misma versión de código (rama `s98-detection-anchor`, reproc S98) procesó marzo
  Y abril. Si difieren con el mismo binario, no es código.
- El código viejo S65 (`9d727787`, ancla y lógica distintas) muestra el **mismo**
  crecimiento de píxeles mar→abr→may. El crecimiento es invariante al código → input.
- Ningún commit a path D / clustering / single_pixel en la ventana feb–abr cambió
  comportamiento para Tupungatito; flags del perfil idénticos ambos meses.
- **Corrección de premisa**: "marzo 1.04×" era un SINGLE record citado en MEMORY, no
  la mediana mensual. La realidad es una **rampa estacional monótona**:
  feb 9.4× → mar 7.1× → abr 8.6× → may 12.5× → jun 25.4× (empeora hacia el invierno).

## Pregunta 2 — Mecanismo real del halo (corrige "path D")
Evidencia: `experiments/_s99_audit/tupun_mechanism.md` (verify.py: doc==JSON, 15/15 PASS).
- **CORRECCIÓN (A48/A62)**: los píxeles de más NO vienen del first-pass dNTI
  contextual (path D), como decía el handoff. En los 258/258 records VIIRS375 con
  cluster grande: `triggered_test1=True`, `diag_n_first_pass_pixels=0`, dNTI-ctx
  mediana=2. Domina **Test 1 integrado-ROI** (impl. S25). *Pendiente confirmar en
  código antes de cualquier fix que lo toque.*
- **Espacial (A61)**: marzo (chico) = 1 px a 0.09–0.29 km del cráter, foco compacto =
  MIROVA. Abril/mayo (grande, n≈183) = ~100 px en **disco/halo 0.1–3.0 km**, mediana
  2.14 km, BT 250–274 K (glaciar frío). Es **anillo nival difuso, no foco**.
- **Gate por t_bg REFUTADO con datos**: 91% de los records grandes tienen t_bg<270K,
  PERO los records chicos CORRECTOS de marzo también tienen t_bg 270–271 K. t_bg solo
  NO discrimina halo de foco (el fondo es frío todo el invierno). Coincide con A54/S86.
  **El discriminante es ESPACIAL, no térmico.**
- **Núcleo 0.75 km es físicamente correcto**: solo ~7.3% de los px del cluster grande
  caen <0.75 km; ~90% es halo lejano. El recorte elimina el anillo nival y conserva el
  foco peri-cratérico; marzo sobrevive intacto. Valida la dirección F5'-Núcleo como
  mitigación. Fix candidato = **recorte espacial del cluster**, NO gate térmico ni
  co-validación por path.
- TIF MIROVA (A24 reconfirmado): el TIF es el campo de radiancia de toda la grilla
  51×51 km (escena/topografía), ~17,900 px positivos, pico a 13–35 km del cráter. NO
  es ground truth per-píxel. MIROVA reporta ~0.2 MW por selección de cluster compacto
  invisible en el TIF.

## Pregunta 3 — ¿Núcleo o Cluster se asemeja más a MIROVA? ¿Por qué mantener los dos?
Evidencia: `experiments/_s99_audit/nucleo_vs_cluster.md`.
- Solo **VIIRS375** tiene ground truth MIROVA en la ventana (216 matcheados). MIROVA no
  publica VIIRS750 (0) y casi nada MODIS (12, ninguno matcheó) → la pregunta "por
  sensor" solo es medible en VIIRS375; en MODIS/V750 el Núcleo = Cluster por diseño.
- **Cluster** mediana global 1.16×, 67% en banda [0.5,2] → mejor tendencia central,
  PERO cola catastrófica (picos 58–90× en glaciar/campo frío).
- **Núcleo** mediana 1.53×, 57% en banda → doma la cola (Tupun 18.9→2.28×) pero
  sobre-corrige los sanos (Chaitén 1.49→2.99×, PCC 1.24→2.01×, PP 1.50→2.31×).
- **Veredicto**: no hay ganador único. Cluster = mejor en volcanes sanos (Láscar,
  Isluga, PCC, PP, Chaitén calibran bien crudos); Núcleo = imprescindible para domar
  el peor caso (Tupun). Por eso se mantienen ambos. Recomendación: Núcleo default
  (cura el peor caso operacional) + toggle Cluster siempre disponible.

## Pregunta 4 — PCC >1000 MW + ancla del lacolito
Evidencia: `experiments/_s99_audit/pcc_investigation.md`.
- **Qué es el ">1000 MW"**: NO es la tarjeta (usa pc.vrp_mw, máx 342 MW). Es el
  **popup del marcador del mapa** (`frontend/index.html:2455`) que imprime la suma
  scene-wide cruda `vrp_mw ?? vrp_mir_mw` (máx 981/1093 MW). 188 records >100 MW, todos
  MODIS. → **Es un bug de display del popup**, además de la sobre-estimación de fondo.
- **Mecanismo**: MODIS 1km, 78–290 px anómalos/pasada, path D dominante, t_bg 270–288K,
  campo difuso warm-scene (A23/A18). VRP=suma del campo → cientos de MW. MIROVA reporta
  mediana 0.37 / máx 5.45 MW (lacolito sub-píxel vía VIIRS375). Sobre-estimación ~180–200×.
- **Ancla del lacolito CORRECTA**: post-S98 el centroide cae a ~0.84–2.07 km del
  lacolito (vent_lat), no a 7.6 km en mirova_center. El radio del mapa nace del lugar
  correcto. El centroide del TIF completo cae cerca de mirova_center pero es artefacto
  (A24: TIF=fondo). MIROVA reporta ~7.83 km del GVP = el lacolito = nuestro vent_lat. ✓
- **¿Mismo problema que Tupungatito?** Comparten la raíz profunda (VRP=suma de campo
  amplio sobre fondo frío/heterogéneo vs selección compacta de MIROVA) pero se
  manifiestan distinto: Tupun era **ubicación** (curado por ancla S98); PCC es
  **magnitud** (suma de campo difuso MODIS) con ancla ya correcta. El fix de ancla S98
  NO toca los cientos de MW de PCC (siguen post-fix).

## Conclusión integrada
Dos modos de falla, una raíz común: **sumamos radiancia sobre un conjunto amplio de
píxeles marcados en fondo frío/heterogéneo, mientras MIROVA reporta una selección
compacta sub-píxel.** El discriminante correcto, confirmado con datos, es **ESPACIAL**
(foco compacto vs halo/campo amplio), NO térmico (t_bg refutado) ni por path.
- Tupungatito (VIIRS375): anillo nival peri-cratérico → recorte espacial (Núcleo) es
  el fix físicamente correcto.
- PCC (MODIS): campo difuso + popup del mapa muestra la suma cruda (>1000 MW).
