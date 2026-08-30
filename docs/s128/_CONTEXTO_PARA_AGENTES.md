# Contexto S128 para los agentes de lectura de papers

Proyecto: **VRP Chile** — clon literal del sistema MIROVA NRT (Coppola et al.) para 11
volcanes chilenos Tier A. Repo: `C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile`.

## Qué hace nuestro pipeline hoy (para poder contestar "¿nos contradice?")

- **Magnitud MIR (Wooster 2003)**: `VRP = A_pix · k · ΔL_MIR`, con
  `WOOSTER_COEFF` = 18.9 (MODIS B21/22, `pipeline/process_modis.py:82`),
  19.7 (VIIRS M13 750 m), 18.0 (VIIRS I04 375 m, `pipeline/process_viirs.py:74`).
  **Área de píxel NADIR FIJA** para los tres sensores (sin corrección sec³ por ángulo
  de vista) — adoptado S102/S103 (`ENABLE_NADIR_FIXED_PIXEL_AREA_*`).
- **Detección**: NTI/ETI contextual de Coppola 2016a (SP426.5). Dual-ROI con N·σ
  = 5 (summit) / 10 (scene) de noche, 15 de día; dNTI con C1 = 0,003 summit /
  0,010 scene; Tests 2∧3 con rama OR `min(C1, μ+C2·σ)`; σ global por imagen;
  second-run que excluye activos y recomputa μ/σ; ETI por regresión cuadrática;
  kernel de 8 vecinos con media aritmética. Más `Test 1` = energía MIR integrada
  sobre el ROI (`compute_test1_mir`).
- **VRP TIR**: Stefan-Boltzmann puro (σ = 5,67e-8), ref. Coppola 2024 cap. Springer
  Eq.16 + Aveni 2024 RSE Eq.5.
- **Sólo nocturno** (elevación solar), MIR contaminado de día.
- **Máscara de nube: APAGADA** (`cloud_mask=0.0`, decisión S127/D14 — recupera 176
  de 181 noches ciegas).
- **Publicamos por PASADA**, no el máximo diario.
- **No calculamos `c_rad` ni TADR** (verificado: `grep c_rad pipeline/` da cero).
- **Piso VRP**: hoy es un no-op; la decisión de quitarlo o aplicarlo está abierta.
- **`inner_radius_km` por volcán** (3-20 km) sólo clasifica summit/far; NO filtra.
  `radius_km = 25 km` uniforme.

## Nuestros frentes ABIERTOS (contra los que hay que leer)

1. **Piso VRP / régimen sub-MW.** Nuestro artefacto topográfico vive en 0,04-0,06 MW.
   Laiolo 2026 dice que MIROVA considera <0,1 MW probablemente nube o mala geometría,
   citando Coppola 2014 y 2016.
2. **Fondo local vs regional.** Descubrimos (S126) que el fondo autorreferente
   (el píxel caliente entra en su propio fondo) subestima la magnitud; el filtro
   contextual está ON y cuesta señal.
3. **Geometría de grilla y resampleo.** MIROVA resamplea a grilla UTM ~51×51 km;
   nosotros NO replicamos la grilla (D17: `get_grid_center()` existe y no tiene
   llamador; `ENABLE_UTM_REGRID` OFF). En el archivo de TIF los tres sensores
   comparten el **borde oeste** idéntico, no el centro.
4. **Filtrado de nube.** Lo apagamos. ¿Qué test usaría MIROVA si filtrara?
5. **Umbrales N·σ y NTI.** Origen del NTI = Wright 2002 (no lo tenemos).
6. **Agregación temporal.** Laiolo 2026: MIROVA usa el **máximo diario** para mitigar
   nube y geometría. Nosotros publicamos por pasada. Sin implementar.
7. **Saturación y calibración cruzada** entre sensores.
8. **Señal difusa vs foco discreto** (A69/D11/A82): en nevados el gradiente
   topográfico contamina los paths que usan MIR **absoluto**; el NTI lo cancela.
   Llamamos "artefacto topográfico" a esa señal difusa. Girona et al. 2021 (Nature
   Geosci) la llamaría posiblemente "unrest térmico de gran escala".
9. **Incertidumbre declarada**: Laiolo 2026 declara ±30 % para el MIR-method sobre
   emisores >600 K. Nuestra banda de paridad es [0,5-2,0].

## Reglas de reporte (obligatorias)

- **Las SEIS preguntas** deben quedar contestadas:
  1. Qué mide y con qué fórmula — ecuación numerada + constantes, **verbatim entre
     comillas, con página**.
  2. Qué decisiones de diseño toma **y por qué** — el CRITERIO, no el resultado.
  3. Qué dice sobre nuestros frentes abiertos (lista de arriba).
  4. **En qué NOS CONTRADICE.** Es la parte que más rinde y la que más se omite.
  5. Qué cita que no tenemos (su bibliografía es un mapa) — con DOI si lo trae.
  6. **Qué NO dice**, contra lo que se le atribuye. Leer el PÁRRAFO, no la frase.
- Cada afirmación fuerte = **cita verbatim + página**. Sin eso no está leído: está hojeado.
- **A48**: no inventes convenciones del proyecto. Si concluís algo de "alto impacto"
  sobre nuestro código, verificalo vos con un `grep`/`sed` de 30 segundos antes de
  escribirlo, y decí con qué lo verificaste (archivo:línea).
- **A9 — canon**: MIROVA = Torino + Firenze + Sapienza Roma (Coppola, Laiolo,
  Massimetti, Campus, Aveni, Cigolini). **NO son MIROVA** aunque sean italianos:
  INGV Catania (Del Negro, Corradino, Di Bella, Torrisi) ni CNR-IMAA Potenza
  (Marchese, Pergola, Genzano, Filizzola). No los cites como autoridad metodológica.
- Escribí en **español de Chile** (nada de voseo rioplatense).

## Cómo leer los PDF

`Read` acepta PDFs con el parámetro `pages` (máx 20 por llamada). Para PDFs grandes,
convertí primero a texto y grepeá:
`python -c "import pypdf,sys; r=pypdf.PdfReader(sys.argv[1]); print('\n'.join((p.extract_text() or '') for p in r.pages))" ARCHIVO.pdf > /tmp/x.txt`
(si `pypdf` no está, probá la skill `markitdown`). Varios ya tienen `.md` o `.txt`
extraído al lado — usalo si existe, es mucho más barato.
