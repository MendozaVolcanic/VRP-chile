# Verificacion de la investigacion de VIIRS 750 en Nevados de Chillan (cenit), S173

## 1. Encabezado

- Fecha y hora del servidor (header `Date` de `gh api -i repos/MendozaVolcanic/VRP-chile`): **Tue, 03 Nov 2026 00:56:07 GMT** al empezar; **Tue, 03 Nov 2026 01:10:56 GMT** al terminar las mediciones.
- Commit sobre el que medi: la copia `repo/` del auditor es `git archive` de **5de08ebf62d1ea092c485c0a030f323f2cbdcf2a** (`v750/repo/COMMIT.txt`), que es `origin/main` de hoy (`git rev-parse origin/main` = 5de08ebf..., medido al arrancar). El worktree local `VRP Chile/` esta en `loop/activo` (ddd83c5b9) y NO lo use para medir; de el solo lei, con `git show origin/main:`, el documento `docs/s131/REMUESTREO_LEY_DE_AREA.md` (copia en `ref_s131_ley_de_area.md`).
- Modelo y esfuerzo reales: **Claude Fable 5.1 (claude-fable-5-1)**, esfuerzo de razonamiento **bajo** (el que trae la sesion; no se me paso uno explicito). Lo declaro porque la regla de S172 (`feedback_s172_esfuerzo_explicito_agentes`) pide esfuerzo alto para auditores.
- CARPETA: `C:/Users/nmend/vrp-wt/s173_cenit/ver_v750/`. `repo/`, `insumos/` y `src/` son **junctions** (lectura en la practica) a las carpetas homonimas del auditor en `C:/Users/nmend/vrp-wt/s173_cenit/v750/`; sus scripts `s01` a `s04` estan copiados aca y se re-corrieron aca (las salidas quedaron aca, la carpeta del auditor no se toco: sus archivos siguen con hora 21:4x-21:5x del 2 de noviembre).
- `caminos.md` escrito ANTES de abrir ningun script del auditor; sha256 y hora al final del archivo (no se volvio a editar).
- Disco al cerrar: C: 32 GB libres, D: 4,7 GB (no escribi nada en D:).
- Lo que NO mire: el `INFORME.md` del auditor (a proposito); los informes de otros verificadores (`src/s162/verificador_*.md`, `src/s172/v750c_VERIFICADOR.md`: no abiertos); el pipeline del worktree `loop/activo`; MODIS y VIIRS 375; el codigo `.m` de MIROVA (no esta en el repo: no verifico que el port de R2 sea fiel al `.m`, solo que el modulo de ablacion reproduce al port y que el brazo O da razon ~1 contra MIROVA); los granulos nativos (no estan en disco: las grillas de `D:/vrp-trabajo/temporales/s159_n` son el unico insumo de imagen, y los brazos nativos K, C, F y FC vienen ya calculados en los JSON de resultados del runner de S159, corridos el 2026-10-21 en la rama `s159-n-disparo`, commits e646d11e y 4a25e8bb, no en main; el control que los ata a main es que el K del runner coincide con el K publicado en main en los 26 que publican, s03 «K main distinto de K del runner: 0»).

## 2. En una pantalla

1. Las seis afirmaciones se sostienen en lo central: los cuatro scripts del auditor corren y dan salidas **byte a byte identicas** a las suyas (s01 a s04, CSV y JSON), y por un camino propio sin sus helpers (pareo al minuto desde `data/mirova_equivalent` y los CSV del scraper) la caida de K con el cenit en Chillan reaparece: 31 pasadas con alerta en su ventana (Spearman -0,652 con ceros, -0,774 sin), 53 hasta el 31 de octubre (-0,743 / -0,826), y **dentro de la misma noche** (mismo estado del volcan) la razon cae en 23 de 27 pares de cenit distinto (p 0,0003) y en 41 de 45 con la ventana larga.
2. En la grilla, el fondo de anillo es la pieza: dentro de la noche O_fanillo y X_fanillo_rec caen en 21 de 25 pares (p 0,0003) y «todo K salvo el fondo» (X_todoK_fcodigo) no (16 de 9, p 0,23). Matiz: la compuerta en los dos pases (O_comp) tambien cae en 21 de 25, pero no es la de K (`second_pass_adjacent` no recibe `bt_sanity_k`) y su tamano es un tercio.
3. En el granulo nativo, F conserva 0,587 de la caida logaritmica de K (no «la mitad»: 0,505 contra 0,313 en medianas; dentro de la noche 18 de 25, p 0,043). La SOSPECHA «resto = area/remuestreo» pasa la condicion necesaria: el crecimiento de area que F requiere (1,3 / 1,9 / 2,2x a 30 / 45 / 62 grados) cabe bajo el 4,39x del ATBD y F por sec(z) queda plano; el que K requiere (6x) no cabe.
4. Lo que cae es nuestro factor, no el denominador: el VRP de MIROVA es plano con el cenit (Spearman -0,098, dentro del barajado) y el pc de K cae solo (-0,469, fuera).
5. Defectos propios del instrumento, todos de gravedad 1 o 2: la ventana efectiva son 20 dias de una erupcion (12 noches), no abril a octubre; el universo son los objetivos de N (28 de 31 alertas); el F del 2026-10-01 05:24 esta topado por D9 (5,0 MW) y el auditor lo dejo como «|dif| max 1,21» sin veredicto; el control positivo de s01 no puede fallar; y el placebo «+1 dia» depende del subconjunto.

## 3. Hallazgos (ordenados por gravedad)

### VV750-01
- TÍTULO: La ventana efectiva de la medicion son 20 dias de una sola erupcion (12 noches) y el universo son los objetivos de N, no las pasadas de Chillan: 28 de 31 alertas; el «2026-04-01 a 2026-10-31» de s02 sobredeclara
- ARCHIVO:LÍNEA: `v750/s02_razon_por_cenit.py:128` (`ventana = ("2026-04-01", "2026-10-31")`), `v750/s02_salida.txt` («ventana de los positivos: 2026-09-28 04:42 a 2026-10-17 06:18 | noches: 12»); SCRIPT:SALIDA `v01_pareo_propio.py:v01_salida.txt` (ventana corta: «records nocturnos: 82 | minutos con alerta MIROVA V750: 33 | ... positivos: 31»)
- QUÉ PASA: MIROVA no publico ninguna alerta de VIIRS 750 en Chillan entre abril y el 27 de septiembre, asi que los 19 negativos de abril a septiembre no aportan razon y toda la estadistica vive en la erupcion del 28-sep al 17-oct. Ademas el frente N eligio 53 objetivos de Chillan; mi pareo propio encuentra 31 pasadas con alerta en esa ventana: faltan 2026-10-12 05:18 (8,44 MW, protegida, `sin_granulo_VJ202MOD`), 2026-10-12 05:54 (0,40 MW, sin granulo VNP02MOD) y 2026-10-09 06:12 (0,82 MW, que no es objetivo de N). No cambia el veredicto (con 31: -0,652 con ceros / -0,774 sin; con 53 hasta el 31-oct: -0,743 / -0,826), pero «47 pasadas nocturnas» y la ventana de seis meses hacen parecer mas ancho el sustrato.
- CÓMO SE VE EN EL DASHBOARD: invisible (es del instrumento).
- CÓMO REPRODUCIRLO: `cd C:/Users/nmend/vrp-wt/s173_cenit/ver_v750 && python -B v01_pareo_propio.py` (Chillan, ventanas 2026-04-01 a 2026-10-31 y 2026-09-28 a 2026-10-17).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### VV750-02
- TÍTULO: El record del brazo F del 2026-10-01 05:24 esta topado por D9 (pc 5,0 MW, `d9_capped` True; sin tope 6,214 MW) y el auditor lo dejo como «|dif| max 1,2137» sin veredicto; un record K de main (2026-10-24 05:30) tambien esta topado
- ARCHIVO:LÍNEA: `v750/s03_salida.txt` («F record pc vs F_pc_central: n 27 | |dif| max 1.2137»); `insumos/n/run_39682867040/.../resultados_02.json` id 319 brazo F (`primary_cluster.vrp_mw` 5.0, `d9_capped` true); `repo/data/mirova_equivalent/NevadosDeChillan.json` record 2026-10-24 05:30 VIIRS_SNPP_750 (pc 5.0, `d9_capped` true, z 37,36); SCRIPT:SALIDA `v02_dentro_de_la_noche.py:v02_salida.txt` seccion (c).
- QUÉ PASA: el tope de 5 MW del camino D (A23, D9) se arma con el fondo de escena bajo 270 K sin ningun pixel por temperatura ni NTI absoluto; en una noche fria de Chillan recorta la magnitud del brazo F de 6,21 a 5,00 MW (MIROVA 9,0 MW: razon 0,690 en vez de 0,556). Es 1 de 28 y del tramo z<30 (27,9 grados): la mediana del tramo no cambia (1,033 con los dos valores). El auditor imprimio la diferencia como control de lectura y no dijo que es el tope.
- CÓMO SE VE EN EL DASHBOARD: en main, el record K del 2026-10-24 05:30 (MIROVA 7,14 MW) publica 5,0 MW por el tope: el operador ve una magnitud recortada en una alerta protegida.
- CÓMO REPRODUCIRLO: `cd C:/Users/nmend/vrp-wt/s173_cenit/ver_v750 && python -B v02_dentro_de_la_noche.py` (seccion c) y el comando de la bitacora «D9» mas abajo.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2 (en el eje de esta verificacion; el tope en produccion es el frente D9, fuera de mi eje).

### VV750-03
- TÍTULO: La condicion necesaria de la SOSPECHA «resto = area/remuestreo» se cumple para F y no para K: el crecimiento de area que F requiere cabe bajo el disponible del ATBD y F por sec(z) queda plano; K requiere 6x
- ARCHIVO:LÍNEA: SCRIPT:SALIDA `v03_area_y_placebo.py:v03_salida.txt` secciones (2) y (2 bis); `ref_s131_ley_de_area.md` l. 106-116 (tabla del ATBD, fila M13: 4,39x).
- QUÉ PASA: al borde del barrido un pixel de M-band cubre hasta 4,39 veces el area de nadir (ATBD 423-ATBD-002 tabla 2.2-1, segun `docs/s131/REMUESTREO_LEY_DE_AREA.md` l. 112, TEXTO: «M13 → fila M6/M8 (VIIRS750) | 0,742 × 0,776 | 1,60 × 1,58 | 2,16× | 2,04× | **4,39×**»); K usa area nadir fija (`ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS` True, leido de `pipeline.profile`), asi que un pixel caliente oblicuo cuenta menos energia que la que MIROVA suma en sus 2 a 3 celdas. Medido: f requerido de F = 1,28 / 1,88 / 2,20 en los bines 25-35 / 35-50 / 50+ (cenit mediano 29,5 / 44,8 / 62,5 grados) contra 1,59 / 1,90 / 2,93 que S131 midio en I-band; F x sec(z): med<30 1,057, med>=30 0,858, Spearman -0,258 dentro del barajado, signos dentro de la noche 13 de 12. K requiere 5,96 en 50+, mas que el 4,39 disponible, y K x sec(z) sigue fuera (-0,712). No es prueba: sec(z) no es la ley del ATBD (que tiene saltos por zona de agregacion) y sec^2(z) sobrecorrige F (+0,532 fuera).
- CÓMO SE VE EN EL DASHBOARD: invisible por si mismo; es la mitad residual de la magnitud oblicua que el operador ve baja.
- CÓMO REPRODUCIRLO: `cd C:/Users/nmend/vrp-wt/s173_cenit/ver_v750 && VRP_PROFILE=mirova_equivalent python -B v03_area_y_placebo.py`.
- CONFIANZA: CONFIRMADO (la condicion necesaria); la atribucion sigue SOSPECHA.
- GRAVEDAD: 2.

### VV750-04
- TÍTULO: Dentro de la misma noche, O_comp (compuerta de temperatura en los dos pases) cae en 21 de 25 pares (p 0,0003), con un tercio del tamano del fondo de anillo; no es la compuerta de K, que solo rige el primer pase y el test absoluto
- ARCHIVO:LÍNEA: SCRIPT:SALIDA `v02_dentro_de_la_noche.py:v02_salida.txt` seccion (b bis); `repo/pipeline/detection_context.py:822-835` (firma de `second_pass_adjacent`: no tiene `bt_sanity_k`); `repo/pipeline/process_viirs_mod.py:916` (`bt_sanity_k=NTI_BT_SANITY_K` solo en `first_pass_tests_2_and_3`); `src/s162/oraculo_ablacion.py:17-19`.
- QUÉ PASA: una compuerta `bt > t_bg + 3 K` aplicada tambien al segundo pase apaga vecinos tibios que de noche oblicua se enfrian relativo al anillo (mediana de log10(alto/bajo) -0,106, contra -0,319 del fondo de anillo). El auditor lo mide como «O_comp cae pero no es la de K»: confirmo las dos partes. O_comp1 (la de K) da 18 de 25 (p 0,043) con mediana -0,023: cae en signo, no en tamano.
- CÓMO SE VE EN EL DASHBOARD: invisible (O_comp no corre en produccion).
- CÓMO REPRODUCIRLO: `cd C:/Users/nmend/vrp-wt/s173_cenit/ver_v750 && python -B v02_dentro_de_la_noche.py`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

### VV750-05
- TÍTULO: El control positivo (4) de s01 no puede fallar mientras el codigo corra, y el placebo «referencia corrida +1 dia: 0 de 47» depende del subconjunto (9 de 82 records de la misma ventana dan par a +1 dia)
- ARCHIVO:LÍNEA: `v750/s01_ablacion_chillan.py:112-117` (multiplica por 1,10 la M13 de los alertados y recalcula el VRP con la misma mascara); `v750/s02_razon_por_cenit.py:149,163-164`; SCRIPT:SALIDA `v01_pareo_propio.py:v01_salida.txt` («P2 placebos ... +1 dia 9») y `v03_area_y_placebo.py:v03_salida.txt` seccion (1) («pares con +1 dia: 0 de 47»).
- QUÉ PASA: subir 10 % la radiancia de los pixeles alertados con el fondo intacto sube el VRP por construccion: el control solo detecta codigo muerto, no mide que el instrumento vea un cambio fisico pequeno. Y el +1 dia da 0 en los 47 objetivos de N, pero sobre los 82 records de Chillan de la misma ventana da 9 pares (la erupcion tuvo alertas diarias a horas parecidas), asi que el 0 no es una propiedad del pareo sino de ese subconjunto; los placebos +-50 min (otra plataforma) dan 0 en los dos conjuntos y si valen.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `cd C:/Users/nmend/vrp-wt/s173_cenit/ver_v750 && python -B v01_pareo_propio.py && VRP_PROFILE=mirova_equivalent python -B v03_area_y_placebo.py`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

### VV750-06
- TÍTULO: El placebo «VRP de MIROVA barajado» no es nulo por construccion aqui: sale FUERA (-0,430) en la ventana larga porque el pc de K cae solo con el cenit (-0,469 FUERA) mientras MIROVA es plano (-0,098 dentro)
- ARCHIVO:LÍNEA: SCRIPT:SALIDA `v01_pareo_propio.py:v01_salida.txt` («PLACEBO MIROVA barajado ... Spearman -0.430 ... FUERA», ventana larga) y `v02_dentro_de_la_noche.py:v02_salida.txt` seccion (a).
- QUÉ PASA: es un hallazgo sobre mi propio instrumento (A110) y a la vez un dato: el factor que depende del cenit es el numerador (nuestro pc), no el denominador (MIROVA). El barajado del cenit del auditor (permuta z, no vM) si es el nulo correcto; el barajado dentro de cada noche de v02 da 0,509 y 0,501 de signos negativos, como debe.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `cd C:/Users/nmend/vrp-wt/s173_cenit/ver_v750 && python -B v01_pareo_propio.py && python -B v02_dentro_de_la_noche.py`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

### VV750-07
- TÍTULO: Los 3 positivos con VRP solo del OCR traen el VRP truncado a entero (10,00 / 9,00 / 7,00 MW), sesgo de hasta 1 MW en la razon de esas pasadas
- ARCHIVO:LÍNEA: `repo/data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv` (nota «VRP truncado por MIROVA en VIIRS: real ∈ [28, 29) MW» en la fila del 2026-11-02 06:18:01; las filas OCR pareadas con CONS en la ventana dan 2,0 contra 2,03, 7,0 contra 7,86, 21,0 contra 21,94); SCRIPT:SALIDA `v01_salida.txt` («fuente: {'CONS': 28, 'OCR': 3}»); comprobacion de las filas dobles en la bitacora.
- QUÉ PASA: el banner de MIROVA que lee el OCR trae el VRP entero; en las pasadas donde la tabla no tiene fila (2026-10-01 05:24 y 06:00, 2026-10-05 06:24) la razon usa ese entero y queda sesgada hacia arriba hasta 1/VRP. El auditor ya corrio s04 (a) con solo la tabla (K -0,887 FUERA): el veredicto no depende de esas 3.
- CÓMO SE VE EN EL DASHBOARD: invisible (es la vara).
- CÓMO REPRODUCIRLO: ver bitacora «filas dobles»; `python -B v01_pareo_propio.py`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

## 4. Veredicto por afirmacion del auditor

| # | Afirmacion | Veredicto | Lo que yo medi |
|---|---|---|---|
| 1 | 47 pasadas nocturnas de Chillan en las grillas; 28 pareadas por pasada con alerta (7 bajo 30, 21 a 30 o mas) | **CONFIRMADA EN PARTE** | s01 y s02 re-corridos: 47 con grilla, 28 con alerta, cenit 7 / 21, identico. Nocturnas: `dayflag == 0` en el runner y `solar_zenith_deg > 90` en los 2.724 records V750 de Chillan de main. Pareo por pasada: `banco_paridad.parear` a +-120 s desde `clase_mirova.VENTANA_S` (l. 112); mi pareo propio al minuto da los mismos 28 mas 3 (VV750-01). La parte que no se sostiene: el universo son los objetivos de N y la ventana efectiva es del 28-sep al 17-oct, no «47 pasadas de abril a octubre». |
| 2 | Controles: identidad 47/47, O = runner 47/47, control positivo 29/29, referencia +1 dia 0/47 | **CONFIRMADA EN PARTE** | Los cuatro numeros se reproducen (s01 identico). Identidad y O = runner si pueden fallar (dos implementaciones, s01 l. 100-107). El control positivo no puede fallar (VV750-05) y el +1 dia es sensible al subconjunto (VV750-05); los +-50 min que agregue dan 0 en los 47 y en los 82. |
| 3 | K reproduce la caida (0,910 / 0,285; Spearman -0,864 fuera del barajado) | **CONFIRMADA** | s03 identico (con ceros). Camino propio: 31 pasadas 0,877 / 0,353, -0,652 con ceros, -0,774 sin; 53 hasta el 31-oct 0,798 / 0,368, -0,743 / -0,826; dentro de la noche 23 de 27 pares (p 0,0003) y 41 de 45; jackknife por noche -0,828 a -0,582. Cenit: el del `final_hotspot` (o vent) del record (`process_viirs_mod.py:1524-1528`), igual al del centro de la grilla salvo 0,86 grados (s01), y coincide con el `Zenith_Sat_deg` del OCR en 3 de 3 (27,9/27; 11,1/11; 44,8/44). Por plataforma: NOAA-20 -0,896 fuera, NOAA-21 -0,455 y SNPP -0,143 dentro (n 12 y 6). |
| 4 | En la grilla solo el fondo de anillo de K reproduce la caida (0,791 / 0,373, -0,486, 12/12 sacando una noche); las demas piezas juntas quedan planas (+0,061) | **CONFIRMADA EN PARTE** | s03 y s04 identicos. El anillo del modulo (`oraculo_ablacion.py:222-223`, inner 5 a 25 km, mediana de M13) es el de K (`process_viirs_mod.py:570` con `BG_INNER_KM` 5 / `BG_OUTER_KM` 25 de `pipeline.profile`, `detection_context.py:1083` mediana de BT, Planck despues en `:1072`; mediana y Planck conmutan salvo conteo par). Dentro de la noche: O_fanillo 21 de 25 (p 0,0003), X_fanillo_rec 21 de 25, X_todoK_sinrec 21 de 25; X_todoK_fcodigo 16 de 9 (p 0,23), O_todoK_sincomp 12 de 13, O_rec, O_sinhalo, O_8vec, O_umbK, caja: planos. La parte que matizo: «unica» no es exacta, O_comp tambien cae con significancia (VV750-04), aunque no es la de K y pesa un tercio; y «plana +0,061» es el Spearman de X_todoK_fcodigo, que dentro de la noche da -0,023 de mediana: plana en tamano. |
| 5 | En el granulo nativo con fondo y suma de MIROVA (F), queda cerca de la mitad logaritmica de la caida (-0,662); que sea area/remuestreo es SOSPECHA | **CONFIRMADA EN PARTE** | -0,662 identico (s03 con ceros). «Mitad»: F conserva 0,587 de la caida logaritmica de medianas (log10 0,505 = -0,296 contra log10 0,313 = -0,505) y 0,45 dentro de la noche (mediana log -0,203 contra -0,455; 18 de 25 pares, p 0,043, contra 22 de 25). Un F de 28 esta topado por D9 (VV750-02; no mueve la mediana). La SOSPECHA pasa la condicion necesaria (VV750-03) y sigue siendo SOSPECHA: no hay granulos nativos en disco ni ley del ATBD por angulo. |
| 6 | Medir la razon solo donde el brazo da VRP positivo esconde la caida | **CONFIRMADA** | O_fanillo: sin ceros n 22 Spearman -0,352 dentro del barajado; con ceros n 28 -0,523 FUERA; los 6 negativos estan en 31,1 / 55,8 / 64,3 / 65,5 / 68,0 / 68,0 grados, todos a 30 o mas (v02 seccion c). Matiz a favor del auditor: dentro de la noche la caida se ve incluso sin ceros (O_fanillo > 0: 11 de 13 pares, p 0,02), asi que lo que esconde la caida es el Spearman con n 22 y 200 barajados, no el fenomeno. |

Duplicados fundidos: ninguno (no tengo otros auditores que fundir; los IDs CV750-01 a 05 del auditor se cruzan arriba, no se renumeran).

## 5. SEGUIMIENTOS (fuera de mi eje)

- **Tope D9 en un K publicado de Chillan**: `repo/data/mirova_equivalent/NevadosDeChillan.json`, record 2026-10-24 05:30 VIIRS_SNPP_750, `primary_cluster.vrp_mw` 5,0 con `d9_capped` true, MIROVA 7,14 MW (razon 0,700). Es el frente D9 / A23 (hoy 183 cumulos sobre 5 MW en main segun la marca S160 de A23). Confianza CONFIRMADO (leido en el JSON). Comando en la bitacora «D9».
- **Corridas del runner de N con `conclusion: failure`**: los tres runs (39680724047, 39682867040, 39693661527) terminaron en `failure` (6 de 8 jobs del primero usado, 3 de 3 del segundo); por el docstring de `src/probe_n.py` l. 21-23 el job sale 2 cuando alguna pasada queda sin estado «ok», asi que puede ser esperado, pero A108 pide contar las pasadas por brazo antes de leer un veredicto; aqui las 47 de Chillan tienen `estado ok`, y faltan 6 objetivos (s01 «estados de los que quedan fuera»). SOSPECHA de cobertura parcial en otros volcanes, no en Chillan.
- **VRP entero en el OCR** (VV750-07): defecto de la vara en Mirova-v1 (el banner trunca); afecta a todo analisis que use filas solo OCR como magnitud. CONFIRMADO en el CSV.
- **Docstring de s02 (`v750/s02_razon_por_cenit.py:21`)** dice «Ventana: la de las grillas de Chillan (s01: 2026-04-15 a 2026-10-17)» y la l. 128 pone 2026-04-01 a 2026-10-31: inconsistencia menor de documentacion; los positivos reales son del 28-sep al 17-oct.

## 6. VERIFICADO LIMPIO

- **Los scripts del auditor corren y reproducen sus salidas byte a byte** (contra la vara «misma entrada, misma salida»): `cd C:/Users/nmend/vrp-wt/s173_cenit/ver_v750 && python -B s01_ablacion_chillan.py && python -B s02_razon_por_cenit.py && python -B s03_nativos_y_extra.py && python -B s04_robustez.py` y luego `diff s0N_salida.txt ../v750/s0N_salida.txt` (N = 1..4), `diff s01_por_pasada.csv ../v750/s01_por_pasada.csv`, `diff s02_por_pasada.csv ...`, `diff s03_por_pasada.csv ...`, `diff s02_resumen.json ...`: todos sin diferencias (bitacora). Nota: reproducir no valida; lo que valida son los caminos propios de abajo.
- **El cenit es el del volcan en esa pasada** (contra la vara «record del pipeline» y, por otro camino, el `Zenith_Sat_deg` del OCR): `process_viirs_mod.py:1524-1528` (geometria en el `final_hotspot`, o el vent si no hay), 0 de 2.724 records V750 de Chillan sin `sensor_zenith_deg`, |record - centro de grilla| max 0,86 (s01), 3 de 3 coincidencias con el OCR a 1 grado (v01).
- **El pareo es por pasada**: `clase_mirova.VENTANA_S = 120` (l. 112) importado por `banco_paridad.TOL_S` (l. 63, 78); `parear` (l. 253-261) toma filas a +-120 s. Mi pareo propio a +-60, +-120 y +-300 s da los mismos 31 / 53 pares (ninguna pasada cambia con la tolerancia); las 8 pasadas con 2 filas son CONS + OCR de la misma pasada y se toma la CONS (`s02:117-123`).
- **La vara**: CSV del snapshot con ultima fila 2026-11-02 06:18:01 (fresco); `aplicar_regla_minimas` SN solo actua sobre `SENSORES_MINIMA = ("VIIRS375",)` (`clase_mirova.py:108`): en V750 no cambia ninguna fila, y no hay alertas V750 de Chillan de 0,05 MW o menos en la ventana (v01). Los hitos A119 (OCR mal calibrado hasta 2026-06-11, sin distancia hasta 06-13, Suomi NPP hasta 10-09) no tocan la razon: la razon usa solo el VRP y la ventana de positivos es posterior; A104 (#535, 2026-08-28) tambien es anterior a todos los positivos.
- **K del runner = K de main**: s03 «K del runner (s01) distinto de N K pc: 0» y «K main (tablero) distinto de K del runner pc (|dif| > 0,006 MW) entre los que publican: 0»; K2 = K en 28 de 28 (nulo del runner).
- **El brazo O reproduce a MIROVA en Chillan** (vara: VRP del scraper, por pasada): mediana 0,998 [0,973, 1,046] n 28, plana con el cenit (+0,053), y x2 dobla la mediana (1,996): el port en la grilla es un instrumento vivo y calibrado para esta pregunta.
- **Flags de produccion leidos de `pipeline.profile`** (no del YAML): `ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750` False (el fondo de K en V750 es la mediana del anillo 5-25 km), `ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS` True, `ENABLE_UTM_REGRID` False, `NTI_BT_SANITY_K` 3.0, `ENABLE_SINGLE_PIXEL_SUB_MW_MODE` True, `FOCAL_CLUSTER_KEEP_PEAK` True, `BG_INNER_KM` 5.0, `BG_OUTER_KM` 25.0; `inner_desde_html()['NevadosDeChillan']` = 5.0 (bitacora).
- **La caida dentro de la noche no es confusion de fecha ni de plataforma**: 23 de 27 pares de la misma noche con 10 grados o mas de diferencia (16 de 1 con 20 grados o mas); nulo barajando dentro de cada noche 0,509; control positivo razon x (1 - z/90) 24 de 27 (v02).

## 7. SIN DATO

- Los granulos nativos de las 47 pasadas no estan en disco: no re-corri los brazos K, C, F ni FC; sus numeros vienen de los JSON del runner (2026-10-21, rama `s159-n-disparo`), atados a main solo por el control K runner = K main.
- La ley de area por angulo del ATBD (423-ATBD-002 tabla 2.2-1 con las zonas de agregacion): `experiments/_s131_remuestreo/ley_atbd.py` no esta en `origin/main` (`git ls-tree` no lo lista); use sec(z) y sec^2(z) como cotas crudas. Por eso VV750-03 es condicion necesaria y no prueba.
- Fidelidad del port de R2 al `.m` de MIROVA: fuera de mi alcance y sin el `.m` en disco.
- Las dos pasadas del 2026-10-12 (8,44 y 0,40 MW): sin granulo en el runner; no se si K las ve.

## 8. FUERA DE ALCANCE

- MODIS y VIIRS 375 (otros verificadores); la decision de que palanca tirar (fondo o remuestreo); el `.m` de MIROVA; el frente D9 en produccion; la cobertura de los runs de N en los otros 10 volcanes.

## Bitacora de mediciones (orden cronologico; cada una con sus dos preguntas)

1. **Arranque** (00:56 GMT): sha256 del prompt d7739b84... confirmado; `origin/main` = 5de08ebf = `repo/COMMIT.txt`; discos C: 32 GB, D: 4,7 GB. `caminos.md` escrito y sellado (sha256 8b9d509e...) a las 00:57:27 GMT.
2. **Runs del runner de N** (`gh api .../actions/runs/{id}` y `/jobs`): los tres en `s159-n-disparo`, 2026-10-21, `conclusion: failure`; 39682867040 jobs probe(4) y probe(7) success, los otros 6 failure; 39693661527 3 de 3 failure. 8 llamadas a la API de GitHub en total en la sesion (de 40).
3. **v01_pareo_propio.py** (P1: si la caida no existiera, Spearman dentro del barajado; P2: placebos +1 dia, +-50 min, vM barajado): salida `v01_salida.txt`, positivos en `v01_positivos_0928_1017.json`. Resultados en VV750-01, -05, -06 y la tabla de veredictos.
4. **s01 a s04 del auditor re-corridos** (uno a la vez, s01 61 s): `s01_run.log`, `s02_run.log`, `s03_run.log`, `s04_run.log`, stderr en `s0N_stderr.txt`; salidas identicas a las del auditor (diff vacio) en los 4 txt, 3 CSV y el JSON.
5. **Flags y radios** (`VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; ..."` desde `repo/`): valores en VERIFICADO LIMPIO.
6. **D9** (`python -I -c` sobre `insumos/n/run_*/**/resultados_*.json` y `repo/data/mirova_equivalent/NevadosDeChillan.json` buscando `pc.vrp_mw == 5.0 or d9_capped`): id 319 brazo F 2026-10-01 05:24 (5,0, capped) y main 2026-10-24 05:30 (5,0, capped, z 37,36).
7. **v02_dentro_de_la_noche.py** (P1: control positivo razon x (1 - z/90) tiene que dar signos negativos; P2: razon barajada entre pasadas y dentro de cada noche tiene que dar ~50 %): `v02_salida.txt`. Factores por separado, pares dentro de la noche para K propio (31 y 53) y para los 18 brazos del auditor (28), F_pc_central y «mitad logaritmica» (0,587).
8. **v03_area_y_placebo.py** (`VRP_PROFILE=mirova_equivalent`; P1: si el area explicara F, F x ley quedaria plano, y K x ley no; P2: la misma ley sobre O, que ya es plano, no se corrio: O no tiene area que corregir): `v03_salida.txt`. f requerido, dos leyes crudas, multiplicador realizado (1,33 → 3,0 celdas por pixel nativo; F x multiplicador -0,189 dentro).
9. **Filas dobles y universo de N** (`python -B -c` con `v01_pareo_propio`): las 8 pasadas con 2 filas son CONS + OCR; 2026-10-09 06:12 no es objetivo de N; las dos del 10-12 son `reintento_1012` sin granulo.
10. **hallazgos.csv** escrito con `v04_hallazgos_csv.py` (modulo csv).
11. Hora del servidor al cerrar las mediciones: Tue, 03 Nov 2026 01:10:56 GMT.
