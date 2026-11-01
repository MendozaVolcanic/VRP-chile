# F6: ¿cuánto se le puede creer al código publicado de MIROVA (VIIRS 750)?

S158, 2026-10-21. Auditoría de sólo lectura. Nada fuera de esta carpeta se tocó. Todos los scripts corren con
`python -B` desde `D:\vrp-trabajo\temporales\s158_d17` y dejan su salida cruda al lado (`*_salida.txt`). El OSF v2.5
se leyó de `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv`
(615.470 filas; V750 = 100.641 filas, 2012-01-19 a 2025-12-31). Código de MIROVA citado como `H` =
`experiments/_s158_d17_diseno/osf_codigo_mirova/MIROVA_VIIRS750_hotspot_detection.m` y `V` = `.../MIROVA_VIIRS750_VRP.m`.

## Respuesta corta

El código publicado **sí** describe partes de la cadena que produjo el archivo OSF v2.5 y de la que corre hoy: la
grilla de 67 × 67 celdas de 750 m centrada en la cumbre, el rechazo por sun-glint bajo 12°, y la fórmula del VRP
(1,97e7 × 0,5625 × ΔL sumado sobre todos los alertados) **con cenit del satélite de 50° o menos**. Pero el archivo
publicado por el mismo autor muestra **dos pasos de producción que no están en el código ni en el paper**: un cambio
del VRP de VIIRS 750 que se activa exactamente sobre 50° de cenit (H1) y un corte de las alertas a 30 km de la cumbre
en los tres sensores (H2). Y los umbrales de detección (K1, mínimos, σ, día) **no tienen ningún contraste con un
resultado publicado**: el único caso reproducido (Etna) no los ejercita y el OSF sólo trae pasadas de 5 MW o más de
noche (50 MW de día), mientras que el 97,7 % de las alertas VIIRS 750 de MIROVA en Chile están bajo 5 MW (H3).
Conclusión práctica: para VIIRS 750 el código es una buena autoridad sobre **la estructura** y sobre la fórmula del VRP
**hasta 50° de cenit**; sobre los números de detección es palabra del autor, y sobre el VRP con cenit mayor a 50° está
desmentido por su propio archivo.

## Clasificación de cada parte del código

| parte | dónde | contraste | evidencia |
|---|---|---|---|
| grilla 67 × 67 de 750 m centrada en la cumbre | entrada, H:125 | **resultado publicado** (OSF y NRT 2026) | M6: 100.641 de 100.641 `Max_Dist` = 0,75 km × √(i²+j²), control celda 0,70 km: 0,71 %; M12: 291 de 291 `Distancia_km` del scraper 2026 (azar 6,4 %); TIF V750 de 67 × 67 float64 (M11) |
| rechazo por sun-glint < 12° | H:87 | **resultado publicado** | M9: 0 de 17.859 filas diurnas con glint < 10° contra 1,89 % esperado al barajar; 34 entre 10,9° y 12° (error de hora del gránulo) |
| VRP = 1,97e7 × 0,5625 × Σ(L − L_bk) | V:88-91 | **resultado publicado con cenit ≤ 50°; desmentido sobre 50°** | M1, M3, M16 (H1) |
| suma de todos los alertados | H:241, V:83-85 | resultado publicado (cenit ≤ 50°) y Coppola 2026 | identidad exacta en 66.391 filas |
| segundo pase con recálculo | H:228-235 | resultado publicado, **una pasada** | Etna: 4 píxeles en el pase 1 y 1 en el pase 2, todos clase 2 (M15) |
| media de 3 × 3 con el central | H:281-287 | palabra del autor (paper dice 8 vecinos) | Etna no la distingue (mutación del oráculo) |
| fondo por dilatación 3/5/7 e interpolación | V:68-81 | resultado publicado, **una pasada** (0,07 %) | el OSF no tiene poder para ver los cortes 4/5 y 30/31 (M8) |
| sin recorte de ΔL | V:83-85 | **no contrastable** en el OSF (piso de 5 MW); en el NRT nunca aparece ΔL ≤ 0 | H4 |
| Test 1 con K1 = -0,7 como alerta directa | H:178, 245 | **palabra del autor** | Etna: 0 alertas absolutas (M15) |
| umbrales de la región conservadora (10σ, 0,02 / 0,01) | H:180-187 | **palabra del autor** | Etna: 0 alertas en clases 0 y 1 (M15) |
| umbrales de cumbre (5σ, 0,003) | H:180-187 | paper (Coppola 2016a Tabla 1, de MODIS) + Etna (pase 2 en el piso 0,003 de ETI) | M15 |
| umbrales diurnos | H:189-198 | palabra del autor | ningún caso diurno reproducido |
| filtro BT M15 ≤ 200 K y escena con mitad NaN | H:150-167 | palabra del autor | |
| constantes de Planck antiguas | H:410-412 | palabra del autor | no observable en agregados |
| dominio de detección (BOX) | ejemplo `.mat` | **desmentido** en las esquinas | H2 |

## Hallazgos (peor primero)

### H1. Sobre 50° de cenit el VRP publicado de VIIRS 750 no es el que da el código publicado
- **SCRIPT:SALIDA**: `m1_identidad_osf.py` (`m1_identidad_osf_salida.txt`), `m3_fuera_vs_cenit.py`, `m16_escalon_50.py`,
  `m7_chile_y_dia.py`, con salidas al lado.
- **QUÉ PASA**: en pasadas muy oblicuas MIROVA publica para VIIRS 750 un VRP menor que el exceso de radiancia
  medido por sus propios píxeles: en vez de 1,97e7 × 0,5625 × (Tot_Lmir_hot − Tot_Lmir_bk), el archivo trae entre 0,03
  y 0,95 de eso (mediana 0,51). Pasa en **8.239 de 34.250 filas con cenit > 50° (24,1 %)** y en **0 de 66.391 filas
  con cenit ≤ 50°**. Es un escalón, no una rampa: con ΔL·k > 100 MW, **0 de 119** filas entre 49,5° y 50,0° contra
  **106 de 122** entre 50,0° y 50,5° (M16); el cenit mínimo de una fila afectada es 50,013°. Sólo en VIIRS 750: las
  252.374 filas de 375 m y las 262.455 de MODIS cumplen su identidad con su propio k a 1e-6 (control positivo de M1:
  con el k de 750 fallan las 514.829). Ni el código (V:83-91), ni el README, ni Coppola 2026 (sección «Volcanic
  Radiative Power computation»: «pixel-level VRP values are subsequently summed») describen este paso. Se activa más
  con radiancia y extensión grandes (en cenit > 50°: 2 de 12.048 filas con k·ΔL ≤ 20 MW, 4.050 de 4.111 sobre
  500 MW; Npix mínimo 4; `Max_Dist` mínimo 1.061 m), pero no requiere píxeles lejanos: Villarrica 2023-11-27 06:18 UTC,
  cenit 50,51°, Npix 17, todos a 1,68 km o menos de la cumbre, publica 77,1 MW donde el código da 153,9 MW (r = 0,501).
  El mecanismo no se pudo identificar con agregados: no es el VRP de la fila de 375 m (1 de 8.239 tiene fila
  coincidente, y Coppola 2026 dice que la de 375 se descarta cuando coincide), no es determinista con el cenit
  (desviación estándar de r entre 0,15 y 0,21 dentro de cada grado), y no es un tope de magnitud.
- **CÓMO SE VE EN EL DASHBOARD**: en la magnitud de VIIRS 750. Si el proyecto adopta `MIROVA_VIIRS750_VRP.m` como
  la autoridad del VRP, en una pasada oblicua de un evento fuerte publicaríamos del orden del doble que MIROVA. Además
  pega en D17: `docs/DISENO_D17_REMUESTREO_UTM.md` §3.6 mide que MIROVA VIIRS 750 en Chile cae a 0,51 sobre 50° y lo
  atribuye al remuestreo; este paso es un candidato alternativo, al menos en parte (SOSPECHA: en el OSF casi no actúa
  bajo 20 MW, y bajo 5 MW no hay datos).
- **CÓMO REPRODUCIRLO**: `python -B experiments/_s158_audit/f6/m16_escalon_50.py <ruta OSF csv>`. Fila de control:
  OSF id 562337 (índice 562336), Villarrica, 27/11/2023 06:18, Satellite 3, Tot_Lmir_hot y Tot_Lmir_bk de la fila
  contra su VRP.
- **CONFIANZA**: CONFIRMADO que existe y dónde actúa; SOSPECHA el mecanismo y si corre en el NRT de hoy.
- **GRAVEDAD**: 4. Cambia la magnitud publicada de un evento fuerte observado en oblicuo y la lectura de la pendiente
  con el cenit, que es la firma con que D17 decide adoptar.

### H2. Ninguna alerta del archivo está a más de 30 km de la cumbre, en ningún sensor; el ejemplo permite hasta 33,9 km
- **SCRIPT:SALIDA**: `m6_max_dist_grilla.py`, `m10_max_dist_sensores.py`.
- **QUÉ PASA**: con la grilla de 67 × 67 sin el marco (H:102), las esquinas de la escena quedan entre 30 y 33,9 km
  de la cumbre, y la matriz de ejemplo no las excluye (BOX: 4.090 celdas clase 0, 0 NaN). Un incendio o una fuente
  caliente en esa esquina sería alerta en el código publicado. En el archivo, `Max_Dist` (distancia de la cumbre al
  píxel alertado más lejano) vale como máximo **exactamente 30.000 m** en VIIRS 750 (n = 100.641), VIIRS 375
  (n = 252.374) y MODIS (n = 262.455), con 0 filas por encima. No es por falta de geometría: en VIIRS 750 hay 201
  filas con el píxel más lejano entre 38 y 40 celdas, y la corona de 40 a 45,3 celdas tiene 144 celdas contra 136 de
  la corona de 38 a 40. Que el corte sea igual en tres sensores con grillas distintas apunta a un paso común
  posterior o a un dominio circular de 30 km en el BOX operacional, que el ejemplo no trae. No está ni en el código ni
  en Coppola 2026 (que habla de un recorte de 50 × 50 km).
- **CÓMO SE VE EN EL DASHBOARD**: invisible en la cumbre; cambia la suma del VRP de la pasada (el código suma todo lo
  alertado) cuando hay una fuente en las esquinas, y cambia la población de μ y σ de toda la escena (H:303-304) si el
  dominio real es el círculo.
- **CÓMO REPRODUCIRLO**: `python -B experiments/_s158_audit/f6/m10_max_dist_sensores.py <ruta OSF csv>`.
- **CONFIANZA**: CONFIRMADO el corte; SOSPECHA si es un BOX circular o un filtro de píxeles (o de filas) posterior.
- **GRAVEDAD**: 2.

### H3. Los umbrales de detección de VIIRS 750 no tienen contraste con ningún resultado publicado
- **SCRIPT:SALIDA**: `m15_etna_caminos.py`, `m7_chile_y_dia.py`, `m13_scraper_vrp_salida.txt`.
- **QUÉ PASA**: el único caso que el oráculo reproduce (Etna, 2023-05-19 00:54) entra entero por la caja de cumbre:
  **0 alertas absolutas, 0 en clase 0 o 1, 4 en el pase 1 y 1 en el pase 2, las 5 en clase 2**. Así que K1 = -0,7, el
  Test 1 como alerta directa, los 10σ y el mínimo de 0,02 de dNTI fuera de la cumbre y todos los números diurnos
  quedan sin probar. El OSF no puede suplirlo: su VIIRS 750 tiene piso de **5,00005 MW de noche y 50,0028 MW de día**
  (el piso de la Tabla 1 de Coppola 2026), y no trae M15. En cambio el NRT de MIROVA en Chile vive debajo: **298 de 305
  alertas VIIRS 750 del scraper bajo 5 MW, mediana 0,57 MW** (2026-01-11 a 2026-10-14). La frase del README del
  oráculo «Eso prueba también que el código publicado es el que corrió en producción en esa pasada»
  (`experiments/_s158_oraculo_mirova/README.md`) dice más de lo que el control mide: prueba que el resultado de esa
  pasada es compatible con el código, y H1 y H2 muestran que la producción tiene pasos que el código no trae.
- **CÓMO SE VE EN EL DASHBOARD**: si se adoptan K1 = -0,7 y el mínimo de 0,02 fuera de la cumbre «porque lo dice el
  código», cambia qué alertas débiles de VIIRS 750 se publican, sin ninguna medición que lo respalde.
- **CÓMO REPRODUCIRLO**: `python -B experiments/_s158_audit/f6/m15_etna_caminos.py experiments/_s158_oraculo_mirova experiments/_s158_d17_diseno/osf_codigo_mirova/Example/VIIRS750_example.mat`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 3. La decisión «el código manda sobre el paper» para VIIRS 750 se apoya en este caso.

### H4. El código no recorta ΔL, pero MIROVA nunca publica una alerta con VRP nulo o negativo
- **SCRIPT:SALIDA**: `m13_scraper_vrp_salida.txt`; código V:83-91.
- **QUÉ PASA**: con fondo interpolado, un píxel alertado débil puede quedar con fondo mayor que su radiancia y el código
  devuelve ΔL y VRP negativos sin recorte. En el OSF no se puede ver (piso de 5 MW). En el NRT de Chile, de 305 alertas
  VIIRS 750, ninguna tiene VRP ≤ 0 y la mínima es 0,09 MW (VIIRS 375: 0 de 1.244, mínima 0,01). O la combinación nunca
  pasa, o hay un filtro posterior que la saca. No está medido cuál.
- **CÓMO SE VE EN EL DASHBOARD**: si se copia el «sin recorte» literal, podrían aparecer alertas de VRP negativo o
  casi nulo que MIROVA no publica.
- **CÓMO REPRODUCIRLO**: leer `registro_vrp_consolidado.csv` filtrando `Sensor == VIIRS`, `Tipo_Registro == ALERTA_TERMICA`.
- **CONFIANZA**: SOSPECHA (que exista el filtro).
- **GRAVEDAD**: 2.

### H5. La función de VRP probablemente falla, en vez de devolver NaN, cuando la detección rechazó la escena
- **ARCHIVO:LÍNEA**: V:42 y V:50; H:81 (`alert = []`) con los `return` de H:88 y H:166.
- **QUÉ PASA**: cuando la escena se rechaza (sun-glint o escena incompleta) la detección devuelve `[]` de 0 × 0. El
  `validateattributes(alert, ..., {'vector', ...})` de V:42 corre antes del `isempty` de V:50, y un 0 × 0 no es vector
  en MATLAB, así que el «VRP_MW = NaN» documentado sólo se alcanzaría con un vacío de 0 × 1 (sin alertas en una escena
  aceptada). El oráculo devuelve NaN en los dos casos, o sea que es más permisivo que el original en ese camino.
- **CÓMO SE VE EN EL DASHBOARD**: invisible (afecta al ejemplo y al oráculo, no a nuestro pipeline).
- **CÓMO REPRODUCIRLO**: en MATLAB, `MIROVA_VIIRS750_VRP(S.ZI_M13, [])`. No tengo MATLAB.
- **CONFIANZA**: SOSPECHA (depende de cómo trata `validateattributes` un 0 × 0; no se ejecutó).
- **GRAVEDAD**: 1.

### H6. El README describe otro empaquetado que el depositado
- **ARCHIVO:LÍNEA**: `README.txt:15-18, 30, 102`.
- **QUÉ PASA**: lista `example/`, `CITATION.cff` y `LICENSE`; en OSF están `Example/`, `CITATION.txt` y `LICENSE.txt`
  (log de OSF del 2026-07-24 08:58 a 08:59, `osf_logs_p1.json`). El `load('example/...')` del README falla en un
  sistema de archivos que distingue mayúsculas; `run_example.m` sí funciona porque arma la ruta con `fileparts`.
  Indica que el README se escribió para otra distribución (por ejemplo un repositorio con `.cff`) y no se regeneró.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 1.

### H7. Algunos comentarios afirman efectos que el código no tiene
- **ARCHIVO:LÍNEA**: H:427-443 y H:111-118.
- **QUÉ PASA**: (a) el comentario dice que el 3,14 se conserva «to maintain numerical consistency», pero
  `temperatureToRadiance` multiplica por 3,14 (H:434) y divide por 3,14 (H:443): se cancela salvo redondeo de punto
  flotante, no puede cambiar ningún píxel. (b) H:111 llama a la clase 1 «central» y H:115 a la clase 2 «extended»;
  en la matriz de ejemplo la clase 2 es la caja de 7 × 7 centrada (filas y columnas 30 a 36 en base 0) y la clase 1 un
  anillo de 21 × 19 (filas 22 a 42, columnas 24 a 42), descentrado una fila. Ya estaba en `docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md` §2; lo
  confirmo. Lección para el proyecto: los comentarios de este archivo no son evidencia sobre el operacional.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 1.

### H8. La dilatación del fondo también agranda los huecos que ya trae M13, y los TIF de MIROVA traen huecos
- **ARCHIVO:LÍNEA**: V:76-81; `m11_tif_vrp.py` (metadatos), `m14_tif_duplicados_salida.txt`.
- **QUÉ PASA**: `imdilate(isnan(ZI_M13masked))` dilata todo NaN, no sólo los alertados. Los 5 TIF VIIRS 750 de MIROVA
  que leí (67 × 67 float64, `TIFFTAG_SOFTWARE = MATLAB R2024b, Mapping Toolbox 24.2`) traen entre 14 y 70 celdas NaN.
  Si esas matrices son el `ZI_M13` operacional (SOSPECHA), el fondo de MIROVA también aparta un halo alrededor de cada
  celda faltante. El README sólo habla de los alertados.
- **CÓMO SE VE EN EL DASHBOARD**: invisible salvo que haya huecos junto al cráter.
- **CONFIANZA**: CONFIRMADO lo que hace el código; SOSPECHA que los TIF sean `ZI_M13`. **GRAVEDAD**: 1.

## VERIFICADO LIMPIO

- **La copia local es la publicada y no cambió desde que se subió.** Los 6 archivos tienen el mismo sha256 que la API
  de OSF, cada uno con una sola versión, creados el 2026-07-24 entre 08:58:50 y 08:59:20 UTC y sin modificación
  posterior; el nodo sólo cambió después en citas y nombres de carpeta (`osf_metadatos_codigo.txt`, `osf_logs_p1.json`).
  Vara: API de OSF.
- **Cronología**: el CSV v2.5 se subió el 2026-03-05 y el código el 2026-07-24 (log de OSF). El archivo es anterior al
  código; que salieran de la misma versión es supuesto, apoyado sólo por Etna y por las identidades de H1. Vara: log OSF.
- **Grilla de 750 m centrada en la cumbre**: 100 % de las 100.641 distancias del OSF y de las 291 del NRT 2026 caen en
  0,75 km × √(i²+j²) (M6, M12; controles 0,71 % y 8,9 % con celda de 0,70 km). Vara: resultado publicado.
- **Coeficientes por sensor**: 375 m = 2.531.250 y MODIS = 18,9e6 exactos en el 100 % de sus filas; 750 m =
  11.081.250 exacto en el 100 % con cenit ≤ 50° (M1). Vara: OSF v2.5.
- **Rechazo por sun-glint < 12°**: confirmado contra el OSF (M9). El cálculo de sol se validó contra el ejemplo
  (116,28° y 31,02° contra 115,90° y 31,89° del `.mat`, diferencia atribuible a la hora de inicio del gránulo). Vara:
  resultado publicado.
- **Convención de ángulos**: el `SatAzi` del OSF para Etna 2023-05-19 00:54 (-77,463219) es el `sat_azi` del ejemplo;
  `Satellite = 4` es NOAA-20 (VJ1). Vara: OSF contra `.mat`.
- **Sin duplicados en la lista de alertas**: las absolutas quedan en NaN en la población del pase 1 (H:276), las del
  pase 1 en la del pase 2, y las máscaras de clase son disjuntas, así que el «sin UNIQUE» (H:239) no duplica píxeles
  ni infla `npix`. Vara: lectura del código.
- **Umbral de escena**: `floor(4489/2) = 2244`, como dice H:162. Vara: aritmética.
- **El ejemplo es Etna, NOAA-20, de noche y casi a nadir** (cenit 7,75°, dayflag 0, glint 113,1°). Vara: `.mat` y OSF.

## Lo que no pude medir

- **El mecanismo de H1.** Los agregados por pasada no lo identifican; haría falta la lista de píxeles de una pasada
  afectada. La forma barata de saberlo es preguntarle al autor (va bien en el correo del Anexo A de
  `docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md`): «¿qué se aplica al VRP de VIIRS 750 cuando el cenit supera 50°?», con la
  fila de Villarrica del 2023-11-27 06:18 como ejemplo.
- **Si H1 y H2 corren en el NRT de hoy.** El scraper no trae radiancias ni Npix. El intento de recalcular el VRP de
  latest.php desde el TIF M13 con la función publicada (M11) no fue informativo: sin M15 no se puede correr la detección,
  el barrido de k píxeles calientes dio 2 de 7 coincidencias contra 1 de 7 del control, y además el script cruzó mal
  los TIF de volcanes distintos con el mismo nombre de archivo (filas de Isluga y Tupungatito leyeron el TIF de
  Láscar). No lo cuento como verificación en ningún sentido.
- **Los cortes de la dilatación (4/5 y 30/31 píxeles).** El salto del fondo por píxel en 4→5 (-0,018, z = -2,9) no se
  distingue de los vecinos 3→4 (-0,030) y 5→6 (-0,027), y en 30→31 (-0,123, z = -3,1) los placebos vecinos dan +0,07 y
  40→41 da +0,105 (z = +2,2): sin poder (M8).
- **Umbrales de detección, filtro de 200 K, constantes de Planck, día**: ningún resultado publicado los restringe (H3).
  Lo que los restringiría: una pasada débil con resultado publicado y las matrices de entrada. El OSF jepv6 (Vulcano)
  es VIIRS 375 y no aplica a este código.
- **MATLAB**: no está instalado, así que H5 y el comportamiento exacto de `fillmissing2` no se ejecutaron.

## Fuera de alcance

- Si nuestro detector de VIIRS 750 calcula μ y σ sobre un dominio que se parezca al de MIROVA (¿círculo de 30 km?):
  no leí `pipeline/`. Si el proyecto adopta el BOX del ejemplo, hereda la diferencia de H2.
- El hallazgo H1 debería entrar como advertencia a `docs/DISENO_D17_REMUESTREO_UTM.md` §3.6 antes de usar la caída de
  MIROVA VIIRS 750 sobre 50° como firma del remuestreo.
- Los 5 TIF VIIRS 750 leídos no repiten valores entre celdas vecinas (entre 0 y 6 pares iguales de unos 4.400,
  M14), lo que es compatible con interpolación y no con vecino más cercano. Dato para D17, no medido con cenit.

## Scripts y salidas (todo en `D:\vrp-trabajo\temporales\s158_d17\experiments\_s158_audit\f6\`)

`m1_identidad_osf.py`, `m2_filas_fuera.py`, `m3_fuera_vs_cenit.py`, `m4_hipotesis_fuera.py`, `m5_fuera_regla.py`,
`m6_max_dist_grilla.py`, `m7_chile_y_dia.py`, `m8_salto_dilatacion.py`, `m9_sunglint.py`, `m10_max_dist_sensores.py`,
`m11_tif_vrp.py`, `m12_scraper_cuantizacion.py`, `m15_etna_caminos.py`, `m16_escalon_50.py`, cada uno con su
`*_salida.txt`; `m13_scraper_vrp_salida.txt` y `m14_tif_duplicados_salida.txt` salieron de comandos en línea (en el
texto de este informe). `osf_logs_p1.json` y `osf_metadatos_codigo.txt` son lecturas de la API pública de OSF. Los
scripts m2 a m8 leen un pickle intermedio de las filas V750 que m1 escribe en el directorio temporal de la sesión
(segundo argumento de m1).
