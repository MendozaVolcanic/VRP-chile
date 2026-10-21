# Inserta comentarios de marca A113 (S158 R2) encima de pruebas, sin tocar aserciones. Conserva CRLF.
# Se corre una sola vez; aborta si el ancla no aparece exactamente una vez o si la marca ya esta.
import sys
R = "docs/AUDIT_S158_R2.md, marca A113; experiments/_s158_audit_r2/a113/INFORME.md"
MARCAS = [
 ("tests/test_cluster_hotspots.py", '"""S27 — TDD para cluster_hotspots', [
  f"# ⚠️ S158 R2 ({R} n 1): la premisa del docstring cae. MIROVA no reporta",
  "# regiones contiguas: en VIIRS 750 cuenta pixeles (npix = numel(alert)) y el VRP suma todos los alertados sin",
  "# agrupar (MIROVA_VIIRS750_VRP.m l. 61 y 83 a 85); en el OSF v2.5 el fondo por unidad de Npix es plano con el",
  "# tamano en los tres sensores (m02_osf_npix.txt). cluster_hotspots sirve para nuestro marcador, no es paridad",
  "# con un n_hotspots de MIROVA. Las aserciones no cambian.",
 ]),
 ("tests/test_vrp_negative_clip.py", '"""S26 — TDD para clip', [
  f"# ⚠️ S158 R2 ({R} n 11): el «Fix universal ... Wooster physics» no es lo que",
  "# hace MIROVA en VIIRS 750: deltaL_MIR = sum(L_hot) - sum(L_bk) sobre todos los alertados, sin recorte por pixel",
  "# ni de la suma (MIROVA_VIIRS750_VRP.m l. 83 a 85). El OSF v2.5 no lo puede mostrar: esta filtrado por VRP minimo",
  "# por sensor (5 MW en VIIRS 750, m03). Para MODIS y VIIRS 375 no hay codigo (TRASLADADA). Ver D25.",
 ]),
 ("tests/test_unsuitable_filters.py", '"""S72 F1.2', [
  f"# ⚠️ S158 R2 ({R} n 12 y 9): en VIIRS 750 el codigo de MIROVA descarta solo",
  "# el contraste de NTI < -0,1 (MIROVA_VIIRS750_hotspot_detection.m l. 298); el contraste de ETI no se filtra",
  "# (l. 368 a 369). El paper (p. 5, renderizada) si nombra dNTI y dETI: para MODIS y VIIRS 375 el filtro de dETI se",
  "# sostiene. Y el K1 nocturno de VIIRS 750 en el codigo es -0,7, no -0,8 (l. 178). Las aserciones no cambian.",
 ]),
 ("tests/test_local_kernel_background.py", '"""Tests TDD para local kernel 3x3', [
  f"# ⚠️ S158 R2 ({R} n 5): «Coppola 2024 L1129 literal» no se sostiene. La",
  "# frase, renderizada (978-3-031-86841-2.pdf, p. impresa 337), es condicional y es del modelo de dos componentes,",
  "# no del fondo del VRP. En VIIRS 750 MIROVA aparta los vecinos adyacentes (dilatacion 3, 5 o 7) e interpola el",
  "# fondo con fillmissing2 (MIROVA_VIIRS750_VRP.m l. 63 a 81). Para MODIS el respaldo posible es Coppola 2016a p. 8",
  "# («arithmetic mean of all the pixels surrounding the active one»). Las aserciones no cambian.",
 ]),
 ("tests/test_local_kernel_modis.py", '"""Tests TDD para integracion ENABLE_LOCAL_KERNEL_BG', [
  f"# ⚠️ S158 R2 ({R} n 5, cita fuera de la tabla de F2): «Coppola 2024 L1129",
  "# literal» es una frase condicional del modelo de dos componentes (libro p. impresa 337, renderizada), no el fondo",
  "# del VRP. Para MODIS el respaldo posible es Coppola 2016a p. 8. Las aserciones no cambian.",
 ]),
 ("tests/test_drift1_test1_k1_saturation.py", '"""Tests Drift #1a', [
  f"# ⚠️ S158 R2 ({R} n 10): el Test 1 K1 no es «mascara de saturacion» ni",
  "# «literal» retirarlo del reporte. Coppola 2016a p. 6 (renderizada): los pixeles del Test 1 son «flagged as",
  "# 'active'» y salen de los pasos siguientes; en VIIRS 750 el codigo los publica como alerta directa",
  "# (MIROVA_VIIRS750_hotspot_detection.m l. 201 a 206 y 245) y los saca del fondo (l. 276 y 328). El flag ON de",
  "# estas pruebas aleja de MIROVA; OFF es lo fiel en el reporte. Las aserciones no cambian.",
 ]),
 ("tests/test_enable_exclude_zones_flag.py", '"""S27 T3', [
  f"# ⚠️ S158 R2 ({R} n 3): «MIROVA no usa mascaras geograficas» cae en forma",
  "# absoluta para VIIRS 750: el codigo admite pixeles excluidos (NaN en BOX) y dice que las ROI se adaptan por",
  "# volcan para excluir volcanes vecinos u otras fuentes termicas persistentes (l. 25 a 29 y 120 a 128). Si MIROVA",
  "# lo aplica en Chile es SIN DATO; «no en papers» no lo revise. Las aserciones no cambian.",
 ]),
 ("tests/test_second_pass_conditioned_s135.py", '"""S135 — el segundo pase condicionado', [
  f"# ⚠️ S158 R2 ({R} n 2): estas pruebas fijan la lectura del paper (p. 7,",
  "# renderizada), que es la vara para VIIRS 375. En VIIRS 750 el codigo de MIROVA corre el segundo pase siempre y",
  "# sobre toda la escena con los mismos umbrales (MIROVA_VIIRS750_hotspot_detection.m l. 223 a 235 y 389 a 399): la",
  "# condicion (a) es nula en efecto y la (b), adyacencia, no existe. Llevar el modo condicionado a VIIRS 750 seria",
  "# alejarse del codigo. Las aserciones no cambian.",
 ]),
 ("tests/test_detection_context.py", "def test_kernel_uses_arithmetic_mean_not_median():", [
  f"# ⚠️ S158 R2 ({R} n 7): la media aritmetica se sostiene; el «8 vecinos» no",
  "# en VIIRS 750, donde MIROVA promedia 3 x 3 con el central incluido (colfilt, l. 281 a 294 y 362 a 368). Para",
  "# MODIS y VIIRS 375 manda el paper (p. 5, renderizada: «eight neighbouring pixels»). La asercion no cambia.",
 ]),
 ("tests/test_rama_diurna_viirs_s151.py", "def test_umbrales_viirs_dia_es_la_tabla_1_diurna():", [
  f"# ⚠️ S158 R2 ({R} n 6): K1 = -0,6 es la Tabla 1 de MODIS. El codigo de",
  "# MIROVA para VIIRS 750 usa de dia K1 = -0,5 (C1 = 0,02 y C2 = 15 coinciden) y rechaza la escena con reflejo",
  "# solar bajo 12 grados (MIROVA_VIIRS750_hotspot_detection.m l. 83 a 89 y 188 a 199). Esta prueba fija una tabla",
  "# unica para 375 y 750; para 375 el -0,6 queda TRASLADADO, no refutado. La asercion no cambia.",
 ]),
]
for path, anchor, lines in MARCAS:
    b = open(path, "rb").read(); s = b.decode("utf-8")
    if "S158 R2" in s: print("ya tiene marca:", path); continue
    nl = "\r\n" if "\r\n" in s else "\n"
    n = s.count(anchor)
    if n != 1: sys.exit(f"ancla {n} veces en {path}")
    s = s.replace(anchor, nl.join(lines) + nl + anchor)
    open(path, "wb").write(s.encode("utf-8")); print("marcado:", path)
