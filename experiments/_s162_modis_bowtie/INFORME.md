# S162 MOD-E: el bow tie de MODIS (D28) dentro del código de MIROVA, ablación local sin red

2026-10-24, 16:02 UTC (hora del servidor de GitHub). Sesión hija de MODIS (loop `tasks/LOOP_MODIS.md`), modelo Opus 5.5.
Sólo lectura: nada en `pipeline/`, `data/` ni `frontend/`. Insumos: el lote del port de S159 (run 39712862945,
artefactos en `D:\vrp-trabajo\temporales\s159_portes\run_39712862945\`), `objetivos_portes.json` y `mirova_port.py` de
la rama `s159-pruebas` (copia de lectura en el scratchpad de la sesión), el oráculo de VIIRS 750
(`experiments/_s158_audit_r2/oraculo/mirova_v750_r2.py`). **Pendiente: verificador con contexto limpio.**

## En una pantalla

1. **La ablación real no se puede hacer con lo que hay en disco**: las grillas guardadas del port ya están remuestreadas
   a 51 × 51 y no traen los píxeles nativos ni su línea y su frame, que es lo que hace falta para quitar un duplicado.
   La hará el lote de MOD-C, que guarda los recortes nativos (`experiments/_s162_modis_negativos/`, §8).
2. **En los datos, el port sube respecto de MIROVA con el cenit**: 0,964 bajo 25°, 1,052 de 25 a 40°, 1,115 de 40 a
   50° (89 alertas; Spearman ρ 0,29, p 0,005), y lo mismo **dentro de Láscar solo** (ρ 0,295, p 0,008; 0,959 bajo 25°
   contra 1,057 desde 25°). No es composición de volcanes.
3. **En el sintético, quitar los duplicados del bow tie no cambia nada hasta 45° de ángulo de barrido** (unos 52° de
   cenit; mediana de sin-duplicados sobre con-duplicados 1,000 a 1,005 a 1 y 3 MW), y **sobre 50° (58° de cenit) baja
   la magnitud un 25 %** (0,754, n 19, a 3 MW) y quita algunas detecciones (24 a 20 de 40).
4. **Lectura**: D28 no explica la subida de Láscar entre 25 y 48° de cenit (ahí el sintético da efecto nulo); sí puede
   inflar el port respecto de MIROVA en las pasadas muy oblicuas, del orden de 1,3 veces, que es justo donde está
   Chillán (2026-10-15 01:05, 57,6°: port/MIROVA 1,734). Por eso MOD-D lleva el brazo PM-sin_dup.
5. Es un sintético con modelo geométrico simple (sin PSF, foco puntual, fondo uniforme con ruido): sirve para el signo
   y el orden de magnitud del mecanismo, no para corregir números.

## El fenómeno

MODIS barre de lado a lado con 10 detectores, y cada barrido avanza 10 km sobre el suelo. En el nadir cada detector ve
1 km y los barridos se tocan sin pisarse. Hacia el borde la distancia al suelo crece, la huella de cada detector se
estira a lo largo de la traza (1,36 km a 40° de barrido, 1,70 km a 50°, 2,0 km a 55°) y los barridos vecinos se
traslapan: el mismo suelo aparece dos veces, en el último detector de un barrido y en el primero del siguiente. MIROVA
identifica y elimina esos duplicados antes de remuestrear a su grilla de 1 km (D28: Coppola et al. 2013, 2023 y Aveni et
al. 2023, citados en el catálogo). El port de S159 remuestrea con todos.

Un foco sub-píxel en la zona de traslape queda medido dos veces. Con remuestreo lineal sobre los centros, las dos
copias calientes ensanchan la región caliente de la grilla: la suma de los alertados crece. Quitar una copia la achica.

## Hallazgos

### E-1. Sin píxeles nativos en disco: la ablación real espera el lote de MOD-C
- **SCRIPT:SALIDA**: lectura de los `.npz` del lote (`grilla_000.npz`: claves `mir`, `tir`, `mir_b21`, `mir_geo5`,
  `tir_geo5`, todas de 51 × 51 float32); `probe_portes.py` (s159-pruebas) l. 352 guarda sólo eso.
- **QUÉ PASA**: para quitar un duplicado hay que saber a qué barrido y detector pertenece cada píxel nativo; la grilla
  remuestreada ya los mezcló.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 2 (bloquea la medición real, no una alerta).

### E-2. El port sube respecto de MIROVA con el cenit, también dentro de Láscar
- **SCRIPT:SALIDA**: `razon_por_cenit.py` → `razon_por_cenit_salida.txt`; `razon_por_cenit_volcan.py` →
  `razon_por_cenit_volcan_salida.txt`.
- **Las dos preguntas del instrumento**: (1) si el port fallara sobre 40°, la razón por tramo lo vería; K, al lado, cae
  de 0,631 a 0,209 (control positivo de que el tramo separa). (2) n por tramo impreso; una pasada sin resultado no entra.
- **QUÉ PASA**: razón port/MIROVA (variante `fisica`) en las alertas que el port publica:

  | tramo de cenit | n | mediana | IC 95 % (bootstrap de pasadas) | K/MIROVA |
  |---|---|---|---|---|
  | 0 a 25° | 53 | 0,964 | 0,916 a 1,023 | 0,631 |
  | 25 a 40° | 22 | 1,052 | 0,922 a 1,172 | 0,384 |
  | 40 a 50° | 10 | 1,115 | 0,930 a 1,385 | 0,218 |
  | 50 a 90° | 4 | 1,088 | 0,837 a 1,734 | 0,209 (n 1) |

  Spearman sobre las 89: ρ 0,291, p 0,0054 (5.000 permutaciones). Láscar solo, n 78: ρ 0,295, p 0,0078. Chillán, n 10:
  ρ 0,285, p 0,42 (sin poder). Ventana: MODIS nocturno 2026-03-01 a 2026-10-21 sin el 17 al 20 de octubre, muestra
  estratificada de S159.
- **Lectura**: la subida es chica (de 0,96 a 1,06 en Láscar) y cabe dentro de la banda de [0,8; 1,25] de la regla de
  PORTES, pero es real. Causa: SIN DATO (candidatas: la grilla de MIROVA en MODIS, que es SOSPECHA; la geolocalización
  MxD03 contra la de MIROVA; el bow tie sólo sobre 50°, E-3).
- **Hallazgo lateral**: las dos protegidas de Chillán a 58° que K y K con MxD03 no detectan (2026-10-12 07:20 y
  2026-10-15 01:05, frente M H4) **el port sí las detecta** (razón 0,837 y 1,734).
- **CÓMO SE VE EN EL DASHBOARD**: invisible hoy (el port no está en producción).
- **CONFIANZA**: CONFIRMADO (medido). **GRAVEDAD**: 2.

### E-3. Quitar duplicados no cambia nada hasta ~45° de barrido y baja la magnitud ~25 % a 50° o más (sintético)
- **SCRIPT:SALIDA**: `ablacion_sintetica.py` → `ablacion_sintetica_1MW_salida.txt`, `ablacion_sintetica_3MW_salida.txt`
  (y sus `.json` con cada realización).
- **Las dos preguntas del instrumento**: (1) control negativo exigido: en el nadir los dos brazos dan exactamente lo
  mismo (OK en las dos corridas); (2) la fracción de focos detectados y la razón medido / verdadero se informan por
  brazo y ángulo: en el nadir la razón es 0,993 (1 MW) y 1,005 (3 MW), el código conserva la energía del foco.
- **QUÉ PASA**: foco de 1.000 K con 1 o 3 MW verdaderos, 40 posiciones al azar por ángulo (±1 km a lo ancho, ±5 km a
  lo largo), fondo de 265 / 262 K con 0,3 K de ruido, remuestreo lineal a la grilla de 51 × 51 y `mirova_port.correr`
  variante `fisica`. Brazo TODOS (como el port) contra SIN_DUP (cada barrido conserva sólo los detectores cuyo centro
  cae en su franja nominal de 10 km; es una de las dos lecturas del método de MIROVA, la otra no está localizada,
  SOSPECHA):

  | ángulo de barrido (cenit) | huella a lo largo | detecta T/S (3 MW, de 40) | S/T mediana (3 MW) | p10 a p90 |
  |---|---|---|---|---|
  | 0° (0°) | 1,00 km | 40/40 | 1,000 | 1,00 a 1,00 |
  | 20° (22°) | 1,07 | 39/39 | 1,000 | 1,00 a 1,00 |
  | 30° (34°) | 1,18 | 38/37 | 1,000 | 0,99 a 1,15 |
  | 40° (46°) | 1,36 | 24/24 | 1,000 | 0,82 a 1,25 |
  | 45° (52°) | 1,50 | 20/20 | 1,005 | 0,94 a 1,09 |
  | 50° (58°) | 1,70 | 24/20 | **0,754** (n 19) | 0,46 a 1,01 |
  | 55° (66°) | 2,01 | 3/4 | 0,789 (n 2) | 0,61 a 0,96 |

  A 1 MW el efecto mediano es nulo en todos los ángulos donde detecta (hasta 45°; sobre eso no detecta nada a 1 MW).
- **Lectura**: el bow tie no explica E-2 entre 25 y 48° de cenit. Sobre ~55° de cenit sí puede: conservar los
  duplicados infla la suma del orden de 1,3 veces respecto de quitarlos, en la dirección en que el port quedaría sobre
  MIROVA. La pérdida de energía del código con el ángulo (razón medido / verdadero 0,95 a 20°, 0,27 a 50°) es la misma
  en los dos brazos: es del remuestreo y de los umbrales, no de los duplicados, y en los datos reales no se ve contra
  MIROVA porque MIROVA pierde igual (programa §1, punto 6).
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CONFIANZA**: CONFIRMADO como medición del modelo sintético; que el modelo represente bien el bow tie real (PSF,
  rotación de la huella, dientes de sierra de la geolocalización) es SOSPECHA hasta la ablación real. **GRAVEDAD**: 3
  (decide si MOD-D lleva el brazo PM-sin_dup: sí).

## Qué se recomienda

- **MOD-D**: correr el brazo PM-sin_dup (lo pide este informe; adenda fechada en MOD-D antes del despacho), con el
  método de filas de borde y, si se localiza, el de Coppola 2010.
- **Ablación real**: con los recortes nativos del lote de MOD-C, repetir E-3 sobre los gránulos reales de las alertas y
  de los negativos (y sobre los 4 casos de E-2 sobre 50°).
- **E-2** queda como divergencia chica a explicar dentro del paquete (no la causa D28).

## VERIFICADO LIMPIO

- Control negativo del sintético: brazos idénticos en el nadir en las dos corridas (`control negativo ... OK`).
- La razón por tramo suma 89 alertas, igual que la R4 de PORTES para MODIS (`04_analizar_salida.txt` de S159: n 89).
- Las sumas por volcán dan el n agrupado (89).

## SIN DATO

- La ablación real (E-1). El método exacto de MIROVA para quitar duplicados (D28: Coppola 2010 contra Liu et al. 2008,
  SOSPECHA). La causa de E-2.
