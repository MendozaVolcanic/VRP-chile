# Frente F (S146): materiales de la auditoría de fidelidad de VIIRS

Informe: [`docs/audit_s146/FRENTE_F_FIDELIDAD_VIIRS.md`](../../../docs/audit_s146/FRENTE_F_FIDELIDAD_VIIRS.md).
Sólo lectura: nada de acá modifica `pipeline/`, `frontend/`, perfiles, `data/` ni `tests/`.

## Scripts

Todos leen `data/mirova_equivalent/*.json` y no escriben nada. Salida conjunta guardada en
`salida_cruda.txt` (corrida del 2026-09-20).

| script | qué mide | sostiene |
|---|---|---|
| `test1_ruido_vs_resolucion.py` | El valor de reposo del Test 1 integrado con ruido puro, predicho por sensor y medido contra `test1_k_observed` | **F-01** |
| `f01_prueba_por_angulo.py` | Prueba independiente de F-01: `test1_k_observed` contra el ángulo cenital, que hace crecer el píxel y achica N_ROI | **F-01b** |
| `c1_vs_sigma_por_sensor.py` | Cuánto vale el piso absoluto C1 = 0,003 en desvíos del propio sensor, y con qué frecuencia gobierna la rama OR | **F-02** |
| `cierre_f02_f04.py` | Las dos refutaciones: tasa de píxeles marcados por píxel evaluado, y proxy de publicación por tramo de ángulo cenital | **F-02** (refutación), **F-04b** |
| `perfil_por_sensor.py` | Perfil comparado de los tres sensores sobre todos los diagnósticos persistidos | contexto de F-01 y F-02 |
| `umbral_vrp_tabla1_scidata.py` | Cuánto de lo que publicamos sobrevive a los pisos de VRP de la Tabla 1 de Coppola 2026 | **F-06** |

## Páginas renderizadas (`paginas/`)

Sólo se conservan las que sostienen un hallazgo. Todas fueron miradas como imagen, que es el único
modo válido de leer una fórmula o una tabla en este proyecto (A95): la capa de texto de estos PDF
corrompe operadores, y el `.txt` del capítulo Springer entrega la Tabla 1 **escrita al revés**.

| archivo | fuente y página impresa | qué sostiene |
|---|---|---|
| `campus2024_p1..p5.png` | Campus et al. 2024, Bull Volcanol 86:25, pp. 2 a 6 | bandas I4/I5, remuestreo UTM 50 × 50 km, Eqs. 1 a 3, A_pix 140.625 m², k_MIR 18,0, fondo por vecinos (**F-03**), suma de alertados (**F-05**), 17,22 % de frecuencia de alerta en Vulcano |
| `campus2022_p5.png` | Campus et al. 2022, Sensors 22:1713, p. 6 | Tabla 1: bandas M13/M15, rangos espectrales, T_MAX 634 K y 343 K |
| `campus2022_p6.png` | ídem, p. 7 | §3.2: grilla UTM 51 × 51 km a 750 m y matriz 67 × 67 (**F-04**), Eq. 1 con 1,97 × 10⁷ y A_pix 0,5625 km², Eq. 2 con el fondo por vecinos (**F-03**), y *"the same used for MODIS"* |
| `scidata2026_p4..p7.png` | Coppola et al. 2026, Sci Data, págs. idx 4 a 7 | remuestreo UTM por sensor (**F-04**), *"All resampled pixels ... were retained"* y la suma de todos los alertados (**F-05**), regla de preferencia 750 sobre 375 (**F-07**), Tabla 1 con k_MIR y pisos de VRP (**F-06**) |
| `coppola2025cap11_p334_impresa331.png` | Coppola 2025, cap. 11, p. 331 | Tabla 1: saturación MIR 353 K y TIR 343 K en la banda I (**F-12**) |
| `coppola2025cap11_p339_impresa336.png` | ídem, p. 336 | Tabla 2 con K1 = −0,8 / −0,6; Eqs. 11 a 13 con la suma sobre N_pix (**F-05**) y el fondo de los píxeles vecinos (**F-03**) |
| `coppola2025cap11_p340_impresa337.png` | ídem, p. 337 | Eq. 17 del VRP y la trampa de lectura `A_pix = 0,75 × 10⁶ m²` (**F-14**) |
| `coppola2025cap11_p352_impresa349.png` | ídem, p. 349 | §4.1.4: *"Similar percentages were also obtained for MIROVA (~5%)"* (**F-13**) |
| `aveni2024_p0.png` | Aveni et al. 2024, RSE 315:114388, portada | el título y el resumen dicen banda TIR única y ~1,8 % de falsos positivos (**F-10**, **F-13**) |
