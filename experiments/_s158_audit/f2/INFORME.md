# F2 (S158): el grafo de cierres contra el código de MIROVA para VIIRS 750

> Auditor F2, historiador de decisiones. Fecha del servidor: 2026-10-21 15:41 UTC (`date -u`). Rama
> `s158-d17-diseno`, HEAD `b2ce96c08`. Carpeta: `experiments/_s158_audit/f2/`. No se tocó nada fuera de ella.
>
> **Vara.** `experiments/_s158_d17_diseno/osf_codigo_mirova/MIROVA_VIIRS750_hotspot_detection.m` (H) y
> `MIROVA_VIIRS750_VRP.m` (V), leídos enteros (444 y 92 líneas). Para MODIS y VIIRS 375 no hay código: lo que se
> traslada desde VIIRS 750 se marca TRASLADADA. Las citas de paper que uso las leí renderizando la página a imagen
> (`render/sp426_5_p5.png`, `p7.png`, `p8.png`, 130 dpi con PyMuPDF): la p. 5 dice «the average (arithmetic mean) of
> the eight neighbouring pixels» y «all the pixels with dNTI or dETI < -0.1»; la p. 7 trae la Tabla 1 (noche ROI1
> K1 -0,8, C1 0,003, C2 5; ROI2 -0,8, 0,01, 10; día -0,6, 0,02, 15) y «The last step is applied only if one or more
> pixels have been detected by the previous tests, and focuses on refining the hotspot detection for the pixels
> adjacent to those already flagged»; la p. 8 dice que L4bk «is estimated from the arithmetic mean of all the pixels
> surrounding the active one (or around the active cluster)».
>
> **Las dos preguntas del instrumento, para este frente.** (1) Si una afirmación sobre MIROVA estuviera refutada por el
> código, ¿la vería? Sólo si la encontré: el censo es por palabras clave (`censo_afirmaciones.py`, 13 patrones, 803
> archivos barridos, salida en `censo_salida.txt`) más lectura dirigida de `docs/MIROVA_DIVERGENCES.md` (encabezados
> de las 34 D y el cuerpo de D1, D8, D9, D18, D19, D22 a D27, D29, D30, D32, D34), `docs/MISSION.md` entero,
> `docs/SINTOMAS.md` entero, las reglas A del `CLAUDE.md` del proyecto, `docs/META_RULES_S80.md` (grep), los
> pre-registros `_s157_prereg_d25`, `_s151_prereg_fk_11`, `_s151_ab_diurno`, `docs/PREREGISTRO_AB_D1_D2_S135.md` y
> los docstrings de 14 archivos de `tests/`. **Es un piso**: una afirmación escrita con otras palabras no aparece.
> (2) ¿Está vivo el instrumento? Control positivo del censo: el patrón P1 tenía que encontrar `CLAUDE.md:142`
> («kernel 8-vec aritmético»), que yo sabía que existe; lo encontró (líneas 142, 165, 415). Control positivo del
> oráculo: `python -B -m pytest tests/test_oraculo_mirova_v750_s158.py -q` dio **6 passed** en mi sesión (2,23 s),
> o sea el port reproduce la pasada de Etna del OSF (mismos 5 píxeles, VRP a 0,09 %) sobre este árbol.
>
> **Salvedad sobre la vara.** El código publicado se declara compacto, no completo (`README.txt`, «Scope»), y al
> cerrar este informe el frente F6 agregó en `docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md` (marca ⚠️ F6, leída con
> `git diff`) que sobre 50° de cenit el VRP publicado por MIROVA en VIIRS 750 no es el de este código en el 24 % de las
> filas del OSF v2.5. Mis veredictos son contra el código publicado tal cual está; donde la cadena completa haga otra
> cosa, el veredicto hereda ese límite.
>
> **Lo que NO rehíce** (ya medido, lo cito como contexto): `docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md` §3 (13
> puntos). Lo comprobé línea por línea contra H y V y lo encontré correcto en los 13; las dos cosas que ese documento
> no dice están en los hallazgos 1 y 3.
>
> Valores efectivos de producción leídos de `pipeline.profile` con `VRP_PROFILE=mirova_equivalent` (no del YAML,
> A89): `NTI_K1_NIGHT=-0.8`, `DNTI_CONTEXTUAL_C1_SUMMIT=0.003`, `DNTI_CONTEXTUAL_C1_SCENE=0.01`,
> `C2_DNTI_SUMMIT_NIGHT=5.0`, `C2_DNTI_SCENE_NIGHT=10.0`, `VIIRS_C2_OVERRIDE_NIGHT=None`,
> `ENABLE_TESTS_23_PROSE_BRANCH=True`, `ENABLE_TEST1_PATH=False`, `ENABLE_SECOND_PASS_ADJACENT=True`,
> `ENABLE_SECOND_PASS_CONDITIONED=False`, `ENABLE_EXCLUDE_ZONES=False`, `ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK=False`,
> `ENABLE_LOCAL_KERNEL_BG=True`, `PATH_D_ONLY_CAP_MW=5.0`, `PATH_D_ONLY_CAP_TBG_MAX_K=270.0`, `NTI_BT_SANITY_K=3.0`,
> `ENABLE_DAYTIME_VIIRS=False`, `NTI_K1_DAY=-0.6`, `ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750=False`,
> `ENABLE_UNSUITABLE_FILTERS_267_273=True`, `ENABLE_ROI1_BOX_PAPER=False`.

## 0. Lo que dice el código y que ningún documento del proyecto decía (resumen de una pantalla)

Del código salen cinco cosas que no están en los 13 puntos de `docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md` ni en D34, y
cada una sostiene o tumba un cierre del proyecto:

1. **MIROVA no agrupa en cúmulos.** `npix = numel(alert)` (V:61) y el VRP suma todos los alertados (V:83 a 85). No
   hay ninguna etapa de conectividad. El «MIROVA reporta `n_hotspots` = regiones contiguas» del glosario es falso
   para VIIRS 750 (hallazgo 1).
2. **El segundo pase de MIROVA corre siempre y sobre toda la escena** (H:228 a 235, H:389 a 399), con los mismos tests
   que el primero. El «condicionado como manda Coppola» de D19, del pre-registro de S135 y de 17 tests describe el
   texto del paper, no el programa (hallazgo 2).
3. **El código admite píxeles excluidos del análisis** (`BOX` NaN, H:29, H:127 a 131) y dice que las ROI se adaptan
   por volcán «to exclude neighbouring active volcanoes or other persistent thermal sources» (H:120 a 125). El
   «MIROVA no usa máscaras geográficas» con que S27 retiró `exclude_zones` no se sostiene en absoluto (hallazgo 3).
4. **De día K1 es -0,5** (H:189), no el -0,6 de la Tabla 1 que fija la rama diurna de VIIRS, y **rechaza la escena
   entera con ángulo de reflejo solar menor a 12°** (H:83 a 89), filtro que no existe en `pipeline/` (hallazgo 6).
5. **El piso de -0,1 sólo existe en el contraste de NTI** (H:298); el de dETI que fija `tests/test_unsuitable_filters.py`
   es del paper, no del programa (hallazgo 9; D34 lo registra, el test no lo sabe).

Lo que el código **confirma** del proyecto, y conviene dejar de dudar (detalle en VERIFICADO LIMPIO): la conectiva
`max` de K, los 5σ y 0,003 de la cumbre, μ y σ de toda la escena con el borde excluido, la regresión cuadrática única
sin las alertas, que los píxeles del Test 1 son alerta directa y salen del fondo (D23 y GAP #A), que no hay compuerta
de temperatura (D22), que el segundo pase recalcula estadísticos y regresión (D26), que MIROVA publica la suma de
todos los alertados sin cúmulo ni tope (D32, D9), el coeficiente 1,97e7 con área nominal fija (A66), la geometría de
ROI como única variación por volcán (MISSION «hecho canónico») y la ausencia de máscara de nube.

## 1. Comandos del censo (para auditar la cobertura)

```
python -B experiments/_s158_audit/f2/censo_afirmaciones.py > experiments/_s158_audit/f2/censo_salida.txt
grep -n -E "^#{1,4} " docs/MIROVA_DIVERGENCES.md
grep -n -i -E "8 vecinos|8-vec|ocho vecinos|8 neighbo|eight neighbo" docs/MIROVA_DIVERGENCES.md docs/MISSION.md docs/SINTOMAS.md docs/META_RULES_S80.md CLAUDE.md docs/FICHA_SDA_VRP_CHILE.md
grep -n -E "n_hotspots|MIROVA no usa máscaras|exclude_zones|Cluster vs pixel|N·σ = 5 summit|C1 = 0\.003 summit|min\(C1|Kernel 8-vecinos|second-run|8-vec" CLAUDE.md
grep -n -i -E "K1|-0\.8|0\.003|0\.010|bt_sanity|t_bg \+ 3|clip|median|refit|conditioned|n_hotspots|unique|duplic|200|glint" tests/test_guard_*.py
grep -l -E "ENABLE_TEST1_K1_RETIRE|local_kernel_bg|L1129|kernel_bg" tests/*.py
grep -l "conditioned=True\|SECOND_PASS_CONDITIONED" tests/*.py
grep -n -i "glint" pipeline/*.py          # 0 resultados
grep -n -E "<= ?200|200\.0|mitad" pipeline/process_viirs_mod.py   # 0 resultados
```

Límites declarados: (a) el censo no entra a `~memory/` (fuera del repo) ni a `documentacion/` salvo
`BIBLIOGRAPHY_SYNTHESIS.md`, que leí por su ruta en `C:` porque no está en git (`git ls-files documentacion` da un solo
PDF); (b) la marca «S158 en archivo» de `censo_salida.txt` es por ARCHIVO, no por pasaje: que el archivo tenga una
marca no prueba que el pasaje la tenga, y eso lo decidí leyendo cada pasaje de la tabla del §3.

## 2. Hallazgos, de peor a mejor

### H1. «MIROVA reporta `n_hotspots` como regiones contiguas» es falso: MIROVA cuenta píxeles alertados, y el cierre «factor 42 = no es bug» tapó una sobre-detección real

- **ARCHIVO:LÍNEA.** Afirmación en `CLAUDE.md:1676-1682` (glosario «Cluster vs pixel»), `docs/MIROVA_DIVERGENCES.md:37-41`
  (D1, «MIROVA junta pixels contiguos (~1 km) en clusters antes de reportar `n_hotspots`»), `docs/MISSION.md:345-347`
  («Cluster aggregation (S27): alineación con `n_hotspots` MIROVA ... explícitamente Coppola 2016a "neighbor pixels"
  connectivity»), `tests/test_cluster_hotspots.py:1-6`, `experiments/50_FACTOR_42_HALLAZGO.md:42-50`,
  `docs/HYPOTHESIS_LOG.md:814`. Código: V:61 (`npix = numel(alert)`), V:83-85 (suma sobre `alert`), H:241-248 (la
  alerta es la concatenación de todas las regiones y pases, sin `unique` ni agrupación). Ninguno de los seis pasajes
  lleva marca S158.
- **QUÉ PASA.** El fenómeno: un foco caliente ocupa un puñado de píxeles, y la pregunta «¿cuántos píxeles alerta
  MIROVA?» tiene respuesta directa en su código: todos los que pasan los tests, contados uno a uno. El proyecto
  decidió en S23 (`50_FACTOR_42_HALLAZGO.md`) que «77 píxeles nuestros contra 4 de MIROVA» era una diferencia de
  unidad de conteo («MIROVA reporta el número de clusters»), sin ningún dato de MIROVA que lo dijera: la prueba fue
  agrupar **nuestros** píxeles con union-find. El CSV del scraper no tiene columna de cúmulos (`head -1
  data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv`: `VRP_MW, Distancia_km, ...`, sin
  `n_hotspots`). El OSF v2.5 trae `Npix` y para la pasada de Etna del ejemplo vale 5 con 5 píxeles alertados por el
  código (`experiments/_s158_oraculo_mirova/README.md`, tabla; 6 tests verdes en mi sesión). Para VIIRS 375 el
  archivo S1 de Vulcano (OSF jepv6) da L_MIRhot/Npix igual con Npix = 1 y con Npix > 1 (0,329 contra 0,329,
  `experiments/_s158_d17_diseno/jepv6_cenit_salida.txt` l. 3; 354 alertas 2021 a 2023): ahí `Npix` también cuenta
  píxeles. O sea: 77 contra 4 era sobre-detección nuestra de 19× en esa pasada, lo que A98 encontró en S139 como «la
  brecha es sobre-publicación» y K corrigió en S153.
- **CÓMO SE VE EN EL DASHBOARD.** Hoy, invisible: con K la sobre-publicación bajó (S153) y el tablero publica el
  cúmulo, no el conteo. Lo que sigue vivo es el razonamiento: cualquier auditoría que compare `n_anomalous_pixels`
  nuestro contra `Npix` de MIROVA y lea un factor 5 a 50 como «unidad distinta, no es bug» (glosario) va a tapar
  sobre-detección otra vez. Y el `n_hotspots_clustered` que persiste `pipeline/process_viirs_mod.py:1023` se presenta
  como «paridad con MIROVA» (`tests/test_cluster_hotspots.py:5`) y no lo es.
- **CÓMO REPRODUCIRLO.** `python -B -m pytest tests/test_oraculo_mirova_v750_s158.py -q` (5 píxeles = Npix 5 del
  OSF); `grep -n "numel(alert)" experiments/_s158_d17_diseno/osf_codigo_mirova/MIROVA_VIIRS750_VRP.m`;
  `sed -n 3p experiments/_s158_d17_diseno/jepv6_cenit_salida.txt`.
- **CONFIANZA.** CONFIRMADO para VIIRS 750 (código) y para la magnitud de VIIRS 375 (datos de jepv6, leídos de la
  salida guardada, no re-corrida: los datos no están en el repo). TRASLADADA para MODIS.
- **GRAVEDAD 3.** No tuerce una alerta de hoy; tuerce la lectura de cualquier comparación de conteos y mantiene en el
  glosario vinculante una regla que convierte sobre-detección en «no es bug».

### H2. El «segundo pase condicionado como manda Coppola 2016a» (D2 de D19) describe el paper, no el programa: MIROVA corre el segundo pase siempre y sobre toda la escena

- **ARCHIVO:LÍNEA.** Afirmación en `docs/MIROVA_DIVERGENCES.md:2577` («Con D2 condicionado como manda Coppola 2016a»),
  `:2492` (encabezado D19: «el second pass corre sin conjunto activo» como defecto), `docs/PREREGISTRO_AB_D1_D2_S135.md:11-12`
  y `:82-83`, `pipeline/profiles/mirova_equivalent.yaml:434-440` (comentario del flag),
  `pipeline/detection_context.py:883-898` (docstring de `conditioned`: «aplica las DOS condiciones que el paper pone a
  este paso»), `tests/test_second_pass_conditioned_s135.py:1-14` (17 tests). Código de MIROVA: H:223-235 (el segundo
  pase se llama sin condición, con `contextualAlertsPass1` que puede estar vacío) y H:389-399 (los `find` recorren
  toda la máscara, sin restricción a la vecindad de lo ya detectado). Paper p. 7 (renderizada): sí dice «applied only if
  one or more pixels have been detected ... adjacent to those already flagged».
- **QUÉ PASA.** El fenómeno que el proyecto describe es real: nuestro segundo pase, corriendo suelto, es «una segunda
  detección más permisiva que la primera» (`detection_context.py:888-891`). Pero la razón de que sea más permisiva no
  es que corra sin condición: es que **nuestro primer pase no es igual al segundo** (el primero lleva la compuerta
  `bt > t_bg + 3 K`, D22, y el segundo no, `detection_context.py:541-544` contra `:822-990`; y el segundo reusa el ETI
  del primero, D26). En MIROVA los dos pases son la misma función con la misma población menos las alertas (H:211-218
  y H:228-235): un segundo pase con conjunto activo vacío recalcula sobre la misma población y da lo mismo que el
  primero, así que correrlo siempre es inofensivo. El «arreglo» pre-registrado (condicionar) se aleja del código en las
  dos condiciones; el arreglo que acerca al código es D22 más D26 (hacer iguales los dos pases). El A/B de S135 corrió
  cinco brazos con un «brazo fiel» así rotulado y concluyó «ninguno de los cinco brazos resuelve el problema»
  (`experiments/_s135_ab_d1d2/RESULTADO_FINAL.md:9`); el rótulo «fiel» del brazo condicionado era del paper, no del
  programa, y además corrió bajo C0 (Test 1 integrado encendido, A114).
- **CÓMO SE VE EN EL DASHBOARD.** Hoy el segundo pase suelto rescata píxeles que la compuerta rechazó (marca S138 de
  D22) y pone el cúmulo en el cráter de Tupungatito 2026-08-21 05:30 UTC VIIRS 750 (D19 l. 2581-2583). Si se adoptara
  el condicionado creyendo que es MIROVA, esos rescates desaparecen y `keep_peak` OFF pierde Lastarria 08-27 y 08-28
  (`experiments/_s135_ab_d1d2/INVESTIGACION_ISLUGA_2NOCHES.md:58-60`). Es decir: la decisión D1/D2 «pendiente de
  Nicolás» (encabezado de D19) está planteada sobre una premisa que el código refuta.
- **CÓMO REPRODUCIRLO.** `sed -n 223,235p experiments/_s158_d17_diseno/osf_codigo_mirova/MIROVA_VIIRS750_hotspot_detection.m`
  y `sed -n 389,399p` del mismo; `sed -n 883,898p pipeline/detection_context.py`. Efecto del segundo pase en el
  oráculo: apagarlo cambia el VRP de Etna en -10,8 % (`experiments/_s158_oraculo_mirova/mutar_oraculo_salida.txt`,
  leído del README; no lo re-corrí).
- **CONFIANZA.** CONFIRMADO (VIIRS 750). TRASLADADA a VIIRS 375, que es donde D19 y el A/B de S135 miden.
- **GRAVEDAD 3.** Tuerce una decisión pendiente de Nicolás (D1/D2) y 17 tests fijan la premisa.

### H3. «MIROVA no usa máscaras geográficas» (retiro de `exclude_zones`, S27) no se sostiene: el código admite píxeles excluidos y dice que las ROI se adaptan por volcán para excluir fuentes térmicas vecinas

- **ARCHIVO:LÍNEA.** Afirmación en `docs/MISSION.md:297` (tabla de anti-patrones: «`exclude_zones` (Salar, lagos) | No en
  papers; MIROVA no usa máscaras geográficas | Removido S27»), `pipeline/profiles/mirova_equivalent.yaml:291-294`
  («MIROVA NO usa máscaras geográficas; depende de N·σ scene=10 para suprimir lagos/salares como FP»),
  `CLAUDE.md:208-211` (A4: «no hay máscaras geométricas ni radios adaptativos»), `tests/test_enable_exclude_zones_flag.py:1-5`.
  Código: H:25-29 («NaN values identify pixels excluded from the analysis»), H:120-125 («For specific volcanoes, ROI1
  and ROI2 can be shifted, reshaped or resized ... The ROIs can also be adapted to exclude neighbouring active
  volcanoes or other persistent thermal sources that fall within the 67-by-67 analysis window»), H:127-131 y H:140
  (`excludedPixels = isnan(BOX)` se aplica a NTI, a los contrastes y a la regresión: el píxel excluido no entra ni a
  la detección ni a μ y σ).
- **QUÉ PASA.** El fenómeno: un salar o un volcán vecino dentro de la ventana de 50 km puede ser el objeto más caliente
  de la escena. El proyecto decidió en S27 que MIROVA resuelve eso sólo con el 10σ de la escena, y retiró el filtro
  geográfico como «parche no MIROVA». El código muestra una capacidad de exclusión por píxel y declara que la usa por
  volcán. Dos salvedades que mantengo: (a) el comentario no dice si «excluir» es poner NaN o mover el vecino a
  `BOX == 0` (umbral conservador); (b) la matriz de ejemplo no tiene ningún NaN fuera del borde (mi `loadmat`:
  clases 0/1/2 suman 4090 + 350 + 49 = 4489 = 67²), así que no hay evidencia de que lo usen en Chile. Lo refutado es la
  forma absoluta de la frase; qué hace MIROVA en Láscar es SIN DATO. Además el mecanismo nuestro
  (`filter_hot_mask` sobre la máscara ya detectada, `process_viirs_mod.py:996-1000`) no es el de MIROVA (exclusión
  previa a la detección y a las estadísticas): reactivar `exclude_zones` tal cual tampoco sería «lo de MIROVA».
- **CÓMO SE VE EN EL DASHBOARD.** Invisible hoy (el tablero oculta `far`). Lo que apaga es una puerta: con MISSION
  pregunta 1 un filtro geográfico está vetado «porque MIROVA no lo usa», y esa razón cayó.
- **CÓMO REPRODUCIRLO.** `sed -n 120,131p experiments/_s158_d17_diseno/osf_codigo_mirova/MIROVA_VIIRS750_hotspot_detection.m`;
  `python -B -c "import scipy.io as s,numpy as n;B=s.loadmat('experiments/_s158_d17_diseno/osf_codigo_mirova/Example/VIIRS750_example.mat')['BOX'];print(n.isnan(B).sum())"` (da 0).
- **CONFIANZA.** CONFIRMADO que la capacidad existe y que el autor la declara usada por volcán; SOSPECHA sobre la forma
  (NaN o clase 0) y SIN DATO sobre Chile.
- **GRAVEDAD 2.** No toca una alerta de hoy; invalida la razón de un retiro y de un veto de MISSION.

### H4. La «tabla canónica de umbrales por sensor» del source of truth bibliográfico da para VIIRS 750 los números de Di Bella (12σ noche, 8σ día), que el código refuta, y el archivo no está en git

- **ARCHIVO:LÍNEA.** `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\documentacion\BIBLIOGRAPHY_SYNTHESIS.md:243-248`
  («## 6. Tabla resumen umbrales canónicos»; fila VIIRS 750m: «n=12 nocturno, n=8 diurno (Di Bella 2024)»). El
  `CLAUDE.md` del proyecto manda leer ese documento primero y lo presenta como «SOURCE OF TRUTH bibliográfico» con
  «Tabla canónica umbrales por sensor (MODIS / VIIRS750 / VIIRS375)». Código: H:177-187 (noche: K1 -0,7; 10σ fuera y
  5σ cumbre; mínimos 0,02 y 0,003 en NTI, 0,01 y 0,003 en ETI) y H:188-199 (día: K1 -0,5; 15σ; mínimos 0,02).
- **QUÉ PASA.** La fila no tiene ningún número de MIROVA: K1, C1 y C2 de VIIRS 750 figuran como de Di Bella, que A9
  excluye como autoridad desde S26. El perfil tiene cableado un `viirs_c2_override_night` para ese 12σ
  (`pipeline/profile.py:789-791`; `process_viirs_mod.py:866-873`), hoy `None` en producción (verificado por
  `pipeline.profile`). El riesgo es documental: una sesión que siga el `CLAUDE.md` al pie lee 12σ como canónico de
  VIIRS 750 y tiene un override listo para aplicarlo. No se puede marcar en un PR porque el archivo vive fuera del
  repo (`git ls-files documentacion` lista un solo PDF).
- **CÓMO SE VE EN EL DASHBOARD.** Invisible (override apagado).
- **CÓMO REPRODUCIRLO.** `sed -n 243,250p "<ruta C: de arriba>"`; `VRP_PROFILE=mirova_equivalent python -B -c "import pipeline.profile as p;print(p.VIIRS_C2_OVERRIDE_NIGHT)"`.
- **CONFIANZA.** CONFIRMADO.
- **GRAVEDAD 2.**

### H5. D8 «RESUELTO» con el kernel local «Coppola 2024 L1129 literal» (media de los 8 vecinos del píxel caliente) no es el fondo de MIROVA: su código aparta justo esos vecinos e interpola desde más afuera

- **ARCHIVO:LÍNEA.** `docs/MIROVA_DIVERGENCES.md:1285` (encabezado D8, «RESUELTO») y `:1312-1313` («Fix adoptado: kernel
  local 3×3 (Coppola 2024 L1129 literal). Reemplaza `median(ring 5-25km)` con `mean(8 vecinos directos del hot
  pixel)`»), `pipeline/profiles/mirova_equivalent.yaml:450-461`, `pipeline/vrp_regimes.py:39-55` (docstring),
  `tests/test_local_kernel_background.py:1-6`, `volcanoes.yaml` (`local_kernel_bg: true` en PCC, Villarrica, Chaitén,
  Planchón Peteroa y Lastarria). Código: V:63-81 (los alertados a NaN, dilatación con cuadrado de 3, 5 o 7 celdas según
  npix ≤ 4, ≤ 30 o más, `fillmissing2` lineal), V:83-85 (sin recorte).
- **QUÉ PASA.** El fenómeno ya lo dice el informe S158 §4.3: el halo de un foco sub-píxel todavía lleva calor, y restarlo
  como fondo se come parte del exceso; MIROVA lo aparta. El kernel de D8 resta exactamente ese halo (media de los 8
  vecinos no calientes, en temperatura). La marca S146 de D8 dice que «RESUELTO vale para el parche adoptado, no para la
  divergencia de fondo contra el paper»; con el código ya no vale ni contra el paper ni contra el programa: es un
  tercer fondo. Alcance real medido en el código nuestro: el kernel actúa en MODIS (`process_modis.py:1103`) y VIIRS
  375 (`process_viirs.py:1473`); **en VIIRS 750 no existe** (`process_viirs_mod.py:461-468`, docstring: «la
  implementación kernel-local para M-band aún no existe»; ningún `compute_local_background` importado). El informe
  S158 §3 punto 12 es correcto para VIIRS 750. El pre-registro D25 de S157 lo sabe (`experiments/_s157_prereg_d25/PREREGISTRO.md:28-32`).
  D8 y el comentario del YAML no llevan marca S158 y el YAML sugiere que el kernel rige en M-band.
- **CÓMO SE VE EN EL DASHBOARD.** En VIIRS 750, nada (no hay kernel). En VIIRS 375 y MODIS de esos 5 volcanes la
  magnitud publicada resta un fondo que no es el de MIROVA; cuánto cambia no está medido en este frente. Dato
  colateral del oráculo (README, no re-corrido): en Etna, usar como fondo la media de los 8 vecinos no alertados da
  +2,65 % contra MIROVA.
- **CÓMO REPRODUCIRLO.** `sed -n 63,85p experiments/_s158_d17_diseno/osf_codigo_mirova/MIROVA_VIIRS750_VRP.m`;
  `grep -n compute_local_background pipeline/process_viirs_mod.py` (0 resultados).
- **CONFIANZA.** CONFIRMADO para VIIRS 750 (donde además no corre); TRASLADADA para MODIS y VIIRS 375, que es donde sí
  corre.
- **GRAVEDAD 2.**

### H6. La rama diurna de VIIRS fija K1 = -0,6 (Tabla 1 de MODIS) donde el código de VIIRS 750 usa -0,5, y no tiene el rechazo de escena por reflejo solar (< 12°) que el código aplica primero

- **ARCHIVO:LÍNEA.** `docs/MIROVA_DIVERGENCES.md:2837` (D27) y `:2845` («De día los Tests 2 y 3 usan K1 = -0,6, C1 =
  0,02 y C2 = 15 (Tabla 1, p. 7, página renderizada)»), `pipeline/diurno.py:128`, `tests/test_rama_diurna_viirs_s151.py:7`
  y `:114-118` (`assert dia["nti_k1"] == -0.6`), `experiments/_s151_ab_diurno/PREREGISTRO.md:18`. Código: H:188-199
  (día: `absoluteNTIthreshold = -0.5`, 15σ, mínimos 0,02) y H:83-89 (`if ~isfinite(sunglint) || sunglint < 12, return`,
  rechazo de la detección completa). `grep -n -i glint pipeline/*.py` da 0 resultados.
- **QUÉ PASA.** De día el canal MIR suma la reflexión solar; MIROVA sube el umbral absoluto y descarta la escena cuando
  el satélite mira cerca de la dirección especular del Sol. La rama nuestra (apagada, `ENABLE_DAYTIME_VIIRS=False`)
  toma la columna diurna de la Tabla 1 de MODIS; para VIIRS 750 el K1 diurno del código es otro y el filtro de
  reflejo falta. C1 = 0,02 y C2 = 15 sí coinciden con el código. De noche nada de esto actúa (con el Sol bajo el
  horizonte el ángulo de reflejo supera 90°, por la fórmula de `README.txt`).
- **CÓMO SE VE EN EL DASHBOARD.** Invisible hoy (flag apagado). El A/B diurno sobre K (`experiments/_s151_ab_diurno/DESPACHO_K.md`)
  mide una rama que en VIIRS 750 no es el detector diurno de MIROVA.
- **CÓMO REPRODUCIRLO.** `sed -n 83,89p` y `sed -n 188,199p` de H; `grep -n -i glint pipeline/*.py`.
- **CONFIANZA.** CONFIRMADO (VIIRS 750). Para VIIRS 375 el K1 diurno es SIN DATO.
- **GRAVEDAD 2** (flag apagado; afecta la lectura de un A/B pre-registrado).

### H7. «Kernel 8-vecinos ... Drift D1 RESUELTO S17» y «C1 = 0,003 summit / 0,010 scene» en CLAUDE.md y en el YAML siguen sin marca, aunque el código usa 9 celdas y 0,02 fuera de la cumbre

- **ARCHIVO:LÍNEA.** `CLAUDE.md:165-166` («Kernel 8-vecinos dNTI contextual: `np.mean` aritmética (Coppola 2016a +
  Campus 2024). Drift D1 RESUELTO S17»), `CLAUDE.md:140-142` (bajo marca S153, sin marca S158), `pipeline/profiles/mirova_equivalent.yaml:114-124`
  («dNTI contextual 8-vecinos», «0.010 scene ROI», «Coppola 2016a Table 2»), `docs/MIROVA_DIVERGENCES.md:1086`
  («scene=0.010 (Coppola 2016a Table 2)»). Código: H:281-287 (`colfilt` 3×3 sobre la población, media con el píxel
  central) y H:183 (`minimumNTIcontrastROI1 = 0.02`, que es la región de fuera: en la matriz de ejemplo `BOX == 2` es
  la caja de 7 × 7 de la cumbre, filas y columnas 30 a 36 de 67, verificado con `loadmat`, y `BOX == 1` es el anillo de
  21 × 19). La tabla del paper es la Tabla 1, no una «Table 2» (p. 7 renderizada).
- **QUÉ PASA.** Ya registrado en D34 y en el informe S158; lo que falta es la propagación (A113) a los lugares que se
  leen primero. Efecto del 3 × 3 con central, por álgebra: para un píxel aislado `x` con vecinos de media `m`, el
  contraste con 9 celdas es `x - (x + 8m)/9 = (8/9)(x - m)`, o sea 8/9 del nuestro; μ y σ escalan igual, así que
  sólo pesa en los mínimos fijos (0,003 de MIROVA equivale a 0,0034 en nuestras unidades y 0,02 a 0,0225). El 0,02
  contra 0,010 fuera de la cumbre es el doble y toca de lleno la sobre-publicación fuera del cráter (A98).
- **CÓMO SE VE EN EL DASHBOARD.** No medido en este frente (el informe S158 §4.2 también lo deja sin medir).
- **CÓMO REPRODUCIRLO.** `sed -n 177,199p` y `sed -n 281,287p` de H.
- **CONFIANZA.** CONFIRMADO (VIIRS 750); TRASLADADA al resto.
- **GRAVEDAD 1** (documental; la divergencia en sí la lleva D34).

### H8. Un comentario en el punto de uso y un test siguen diciendo que el Test 1 K1 es «máscara de saturación, NO un path de detección reportable»; el código lo publica como alerta directa

- **ARCHIVO:LÍNEA.** `pipeline/detection_context.py:974-984` (comentario sobre `combine_hot_paths`: «Test 1 K1 ... es una
  MÁSCARA DE SATURACIÓN que retira pixels del cómputo de mean/std del background, NO un path de detección reportable.
  Nuestro código actual mete `nti_path_hot` al OR del hot_mask, lo cual es un drift respecto al paper»),
  `tests/test_drift1_test1_k1_saturation.py:1` («Test 1 K1 retire from hot_mask (Coppola 2016a literal)»). Código:
  H:201-206 y H:245 (los píxeles sobre K1 son alerta directa) más H:276 y H:328 (salen del fondo). La lectura correcta
  ya está escrita en `docs/MIROVA_DIVERGENCES.md:516-528` (S100) y D23 lleva marca S158; el comentario y el test no.
- **QUÉ PASA.** Quien toque `combine_hot_paths` lee ahí que reportar los K1 «sería un drift» y que encender
  `enable_test1_k1_retire_from_hot_mask` acerca al paper. Hoy el flag está apagado y, con K, `hot_mask_2d = fp_hot` deja
  los K1 fuera del reporte de todos modos (D23 abierta), así que el comentario no decide nada en producción. Decide
  lo que haría el próximo PR.
- **CÓMO SE VE EN EL DASHBOARD.** Invisible.
- **CÓMO REPRODUCIRLO.** `sed -n 974,984p pipeline/detection_context.py`; `sed -n 241,248p` de H.
- **CONFIANZA.** CONFIRMADO.
- **GRAVEDAD 1.**

### H9. Tests que fijan una premisa sobre MIROVA que el código contradice (para que un PR de fidelidad sepa qué va a romper)

| test | premisa que fija | qué dice el código (VIIRS 750) | veredicto |
|---|---|---|---|
| `tests/test_cluster_hotspots.py:1-6` | «MIROVA reporta `n_hotspots` = regiones contiguas ... cada cluster equivale a 1 punto en el mapa MIROVA» | `npix = numel(alert)`, sin agrupación (V:61) | REFUTADA (H1) |
| `tests/test_second_pass_conditioned_s135.py:1-14` (17 tests) | el segundo pase «sólo si hubo detección previa» y «sólo adyacentes» como regla de MIROVA | corre siempre y sobre toda la escena (H:228-235, 389-399) | REFUTADA en el programa, CONFIRMADA en el paper (H2) |
| `tests/test_vrp_negative_clip.py:1-9` | «Fix universal: clip delta_L = max(L_hot - L_bg, 0)» (S26, «Wooster physics») | ΔL sin recorte (V:83-85) | REFUTADA; D25 ya lo marca, el test no |
| `tests/test_unsuitable_filters.py:1-9` | dETI < -0,1 es «unsuitable» (paper §267-273) | sólo el contraste de NTI < -0,1 (H:298); nada sobre ETI | REFUTADA en el programa, CONFIRMADA en el paper (p. 5 renderizada) |
| `tests/test_local_kernel_background.py:1-6` | «Coppola 2024 L1129 literal: T_bk de los píxeles adyacentes al caliente» | dilatación más interpolación; los adyacentes se apartan (V:67-81) | REFUTADA (H5) |
| `tests/test_drift1_test1_k1_saturation.py:1` | «Test 1 K1 retire from hot_mask (Coppola 2016a literal)» | K1 es alerta directa (H:245) | REFUTADA (H8) |
| `tests/test_rama_diurna_viirs_s151.py:114-118` | de día K1 = -0,6 en VIIRS | -0,5 (H:189) | REFUTADA en K1; C1 y C2 CONFIRMADAS (H6) |
| `tests/test_enable_exclude_zones_flag.py:1-5` | `exclude_zones` «NO está en papers MIROVA» | exclusión por píxel en `BOX` y ROI adaptada por volcán (H:25-29, 120-131) | parcialmente REFUTADA (H3) |
| `tests/test_detection_context.py:1-5, 252-254` | kernel de 8 vecinos, media aritmética | 3 × 3 con el central (H:281-287) | REFUTADA en el conteo, CONFIRMADA en la media (H7) |
| `tests/test_daytime_modis.py:20-40` | Tabla 1 día y noche para MODIS | sin código de MODIS | NO APLICA (vale el paper) |

Tests cuya premisa el código **confirma** (no tocar): `tests/test_guard_gap_a_pool_musigma_s128.py` (los K1 salen del
pool de μ y σ: H:276, 328), `tests/test_conectiva_tests23_s136.py` (`max`: H:306-312, 376-382),
`tests/test_d22_compuerta_bt_s142.py` (no hay compuerta de temperatura en H), `tests/test_drift4_second_pass_enabled.py`
(el segundo pase existe y excluye los activos del promedio: H:275-277), `tests/test_guard_caja_llega_al_segundo_pase_s149.py`
(la ROI de cumbre es una caja en celdas y llega a los dos pases: `BOX == 2`, 7 × 7, usada en H:397-399 en ambos pases).

## 3. Tabla: afirmación · dónde · vara · veredicto · quién la cita · qué apagó

Veredicto contra el código de VIIRS 750. «Vara con que se afirmó» es lo que el pasaje cita como respaldo.

| # | afirmación sobre MIROVA | dónde (archivo:línea) | vara con que se afirmó | veredicto | quién la cita | qué frente o decisión apagó | marca S158 en el pasaje |
|---|---|---|---|---|---|---|---|
| 1 | reporta `n_hotspots` = regiones contiguas; «factor 42 no es bug» | `CLAUDE.md:1676-1682`; `MIROVA_DIVERGENCES.md:37-41`; `MISSION.md:345-347`; `experiments/50_FACTOR_42_HALLAZGO.md:42-50` | union-find sobre nuestros píxeles (S23) | **REFUTADA** (V:61, 83-85; OSF Npix 5 = 5 px; jepv6) | `tests/test_cluster_hotspots.py`; `HYPOTHESIS_LOG.md:814` | cerró en S23 la sobre-detección 77 px contra 4 como «unidad distinta»; sostiene `n_hotspots_clustered` como «paridad» | no |
| 2 | el segundo pase corre «sólo si hubo detección y sólo adyacentes» (D2) | `MIROVA_DIVERGENCES.md:2492, 2577`; `PREREGISTRO_AB_D1_D2_S135.md:11-12, 82-83`; `mirova_equivalent.yaml:434-440`; `detection_context.py:883-898` | paper p. 7 (`sp426_5.txt:329-341`) | **REFUTADA** (H:228-235, 389-399); el paper sí lo dice | 17 tests S135; A/B `_s135_ab_d1d2` | decisión D1/D2 de Nicolás (pendiente); el «brazo fiel» del A/B de S135 | no |
| 3 | «MIROVA no usa máscaras geográficas» | `MISSION.md:297`; `mirova_equivalent.yaml:291-294`; `CLAUDE.md:208-211` (A4) | ausencia en papers | **REFUTADA** en la forma absoluta (H:25-29, 120-131); SIN DATO para Chile | `tests/test_enable_exclude_zones_flag.py` | retiro de `exclude_zones` (S27) y su veto por MISSION pregunta 1 | no |
| 4 | VIIRS 750: 12σ noche, 8σ día (Di Bella) como «canónico» | `documentacion/BIBLIOGRAPHY_SYNTHESIS.md:248` (fuera de git) | Di Bella 2024 | **REFUTADA** (H:177-199) | `CLAUDE.md` «SOURCE OF TRUTH bibliográfico»; `viirs_c2_override_night` cableado | ninguno hoy (override `None`); riesgo de reactivación | no (archivo fuera del repo) |
| 5 | fondo del VRP = media de los 8 vecinos del píxel caliente «Coppola 2024 L1129 literal» (D8 RESUELTO) | `MIROVA_DIVERGENCES.md:1285, 1312-1313`; `mirova_equivalent.yaml:450-461`; `vrp_regimes.py:39-55` | Coppola 2024 cap. L1129 | **REFUTADA** (V:63-85); y en M-band ni siquiera corre (`process_viirs_mod.py:461-468`) | `tests/test_local_kernel_background.py`; D25 (`:2767`) | cierre de D8 (S61/S62) | no (D25 sí) |
| 6 | de día K1 = -0,6, C1 = 0,02, C2 = 15 para VIIRS; sin filtro de reflejo | `MIROVA_DIVERGENCES.md:2837-2850` (D27); `pipeline/diurno.py:128`; `_s151_ab_diurno/PREREGISTRO.md:18` | Tabla 1 p. 7 (MODIS) | K1 **REFUTADA** (-0,5, H:189); C1, C2 **CONFIRMADAS**; reflejo solar NO CUBIERTO por nosotros (H:83-89) | `tests/test_rama_diurna_viirs_s151.py:114-118` | A/B diurno sobre K (DESPACHO_K) | no |
| 7 | contraste contra «los 8 vecinos» (media aritmética) | `CLAUDE.md:142, 165`; `MISSION.md:131`; `mirova_equivalent.yaml:114`; `detection_context.py:146-155` | paper p. 5 (renderizada: «eight neighbouring pixels») | **REFUTADA** en el conteo (H:281-287, 9 celdas); CONFIRMADA en la media | `tests/test_detection_context.py` | nada apagado; la escala de los mínimos (8/9) | `MISSION.md:124-130` sí; `CLAUDE.md:165` no |
| 8 | fuera de la cumbre C1 = 0,010 «Table 2» | `CLAUDE.md:140`; `mirova_equivalent.yaml:116-124`; `MIROVA_DIVERGENCES.md:1086` | Tabla 1 de MODIS | **REFUTADA** (0,02 en NTI, 0,01 en ETI; H:183, 186) | `tests/test_detection_context.py:117-194` | sobre-publicación fuera del cráter sin medir (A98) | D34 sí; estos pasajes no |
| 9 | K1 = -0,8 de noche para VIIRS 750 | `mirova_equivalent.yaml:47`; `process_viirs_mod.py:481` | Tabla 1 de MODIS | **REFUTADA** (-0,7, H:178) | `tests/test_unsuitable_filters.py:8` | ídem | D34 sí; YAML no |
| 10 | el Test 1 K1 es «máscara de saturación, no reportable» | `detection_context.py:974-984`; `tests/test_drift1_test1_k1_saturation.py:1` | lectura de §298-300 corregida en S100 | **REFUTADA** (H:245) | nadie más (S100 ya lo corrigió en `:516-528`) | el flag `enable_test1_k1_retire_from_hot_mask` como «fidelidad» | no |
| 11 | ΔL se recorta a cero («Wooster physics») | `process_viirs_mod.py:1055-1056`; `tests/test_vrp_negative_clip.py:1-9` | S26, sin cita | **REFUTADA** (V:83-85) | D25 | magnitud del cráter en 0,0 MW (D25) | D25 sí; test y código no |
| 12 | dETI < -0,1 es no apto | `tests/test_unsuitable_filters.py:1-9`; `process_viirs_mod.py:881` | paper p. 5 | **REFUTADA** en el programa (H:298 sólo NTI); CONFIRMADA en el paper | `ENABLE_UNSUITABLE_FILTERS_267_273` | nada | D34 sí; test no |
| 13 | MIROVA es inmune al cirrus sólo si se topa el camino D en 5 MW (Opción C) | `MIROVA_DIVERGENCES.md:301-324`; `mirova_equivalent.yaml:506-507` | Coppola 2016a «false detections < 5 MW» | **NO APLICA** como mecanismo de MIROVA: el código no tiene tope ni compuerta por `t_bg` (V:91) | A23, MISSION «D9 cap C» | D9 (marcas S146/S151 ya lo rebajan) | informe S158 punto 11 sí; D9 no |
| 14 | el segundo pase reusa el ETI del primero y calcula μ y σ sin los filtros de no aptos (D26) | `MIROVA_DIVERGENCES.md:2808`; `process_viirs_mod.py:916` | paper | **CONFIRMADA como divergencia** (H:228-235 recalcula regresión; H:298 reaplica el piso) | D34 | nada | sí |
| 15 | compuerta `bt > t_bg + 3 K` no está en MIROVA (D22) | `MIROVA_DIVERGENCES.md:2696`; `detection_context.py:541-544` | paper p. 7 | **CONFIRMADA** (no existe en H) | D19, D11 | nada | sí |
| 16 | los K1 son alerta directa y salen del fondo (D23, GAP #A) | `MIROVA_DIVERGENCES.md:2729`; `:516-528`; `tests/test_guard_gap_a_pool_musigma_s128.py` | paper p. 6 | **CONFIRMADA** (H:206, 245, 276, 328) | CLAUDE.md:161 | nada | sí |
| 17 | conectiva `max` (K), 5σ y 0,003 en la cumbre, μ y σ de toda la escena | `MISSION.md:7-17`; `CLAUDE.md:141`; `_s151_prereg_fk_11/REGLA_ADOPCION.md:29-32` | prosa de Coppola 2016a p. 7 | **CONFIRMADA** (H:303-312, 373-382; `std(...,0,...)` con N-1, despreciable) | `tests/test_conectiva_tests23_s136.py` | nada | informe S158 §4.4 |
| 18 | MIROVA publica la suma de todos los alertados, sin cúmulo ni tope (D32) | `MIROVA_DIVERGENCES.md:3150`; `SINTOMAS.md:52` | 3 papers renderizados (S147) | **CONFIRMADA** (H:241-248, V:83-91) | A10 rebajada | nada | sí |
| 19 | «UN algoritmo por sensor, uniforme entre volcanes; la única variación por objetivo es la geometría de la ROI» | `MISSION.md:169-174` | Coppola 2016a y 2024 | **CONFIRMADA** (H:120-125) | A4 | nada | no hace falta |
| 20 | MIROVA no filtra nubes | `mirova_equivalent.yaml:10`; D14 (`:1862`) | Laiolo 2026 p. 4 | **CONFIRMADA** con matiz: sí descarta BT de M15 ≤ 200 K y escenas con la mitad o más de NaN (H:150-167), que no son máscara de nube | D14 | nada | D34 sí |
| 21 | coeficiente 1,97e7 y área nominal fija 0,5625 km² (A66, S14) | `CLAUDE.md` reglas científicas | OSF v2.5 empírico | **CONFIRMADA** (V:88-91) | A36, A66 | nada | informe S158 |
| 22 | la ROI de cumbre es una caja de celdas (D18) | `MIROVA_DIVERGENCES.md:2355` | paper p. 7 | **CONFIRMADA** (matriz de ejemplo: 7 × 7 en `BOX == 2`; umbrales de cumbre en H:397-399) | `tests/test_guard_caja_llega_al_segundo_pase_s149.py` | A/B de S151 (KC veto en D1) sigue válido en su medición | informe S158 sí; D18 no |

## 4. Fuera de alcance (anotado, no perseguido)

- **El comentario de `BOX` está al revés** respecto de los umbrales (el código llama ROI 1 a la región que recibe 10σ y
  ROI 2 a la que recibe 5σ, pero en el ejemplo `BOX == 2` es la cumbre). Ya lo dice el informe S158 §2; lo verifiqué:
  `BOX == 2` ocupa filas y columnas 30 a 36 (7 × 7), `BOX == 1` filas 22 a 42 y columnas 24 a 42. Para F1/F3: cualquier
  port que lea los comentarios y no el ejemplo invierte los umbrales.
- **La dilatación del fondo de MIROVA dilata todos los NaN de `ZI_M13`, no sólo los alertados** (V:76-77:
  `imdilate(isnan(ZI_M13masked), ...)`): un hueco de datos junto al foco agranda la exclusión. El oráculo lo replica
  o no, no lo revisé (F1).
- **En `experiments/_s135_ab_d1d2/`** el veredicto «ninguno de los cinco brazos resuelve» se midió bajo C0 (Test 1
  integrado encendido, A114) y con el brazo «fiel» mal rotulado (H2). Si D1/D2 se reabre, va sobre K y con un brazo
  «pases iguales» (sin compuerta, con regresión recalculada), no «condicionado».

## 5. VERIFICADO LIMPIO (contra qué vara y con qué comando)

- Los 13 puntos de `docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md` §3, leídos uno a uno contra H y V: las líneas citadas de
  MIROVA existen y dicen lo que el documento dice (`cat -n` de los dos `.m`). Los valores «nosotros» coinciden con
  `pipeline.profile` leído en mi sesión (lista en el encabezado) y con `process_viirs_mod.py:481-490, 880-922, 1055-1056`.
- Las marcas S158 ya puestas en D22, D23, D25, D26, D29, D32 y D34 de `docs/MIROVA_DIVERGENCES.md`, en `docs/MISSION.md:124-130`
  y en `docs/SINTOMAS.md:64-73` dicen lo que el código dice (`sed -n` de cada bloque). No encontré en esos pasajes un
  cuerpo que contradiga la marca más abajo sin marcar.
- El oráculo está vivo sobre este árbol: `python -B -m pytest tests/test_oraculo_mirova_v750_s158.py -q -p no:cacheprovider`
  → `6 passed in 2.23s`.
- `BOX` del ejemplo: 67 × 67, clases 0/1/2 = 4090/350/49, sin NaN fuera del borde; `dayflag = 0`; cenit 7,75°
  (`scipy.io.loadmat`). Coincide con el informe S158 §2 y con que el ejemplo no sirve para D17.
- Producción no usa el override de Di Bella: `VIIRS_C2_OVERRIDE_NIGHT = None`, `C2_SUMMIT_OVERRIDE = None`
  (`pipeline.profile`, perfil `mirova_equivalent`).
- El pre-registro D25 de S157 distingue bien quién resta el anillo: VIIRS 375 con kernel en 5 volcanes, VIIRS 750 sin
  kernel (`experiments/_s157_prereg_d25/PREREGISTRO.md:28-32`), y coincide con `process_viirs_mod.py:461-468` y
  `process_viirs.py:1473`.
- La geometría: el `radius_km = 25` de los Tier A (`CLAUDE.md:174`) cubre lo mismo que la ventana de 67 celdas de 750 m
  de MIROVA (50,25 km; H:125, H:162 «fewer than 2244 NaNs» = la mitad de 67²). No es hallazgo.
- Los guards que fijan premisas que el código confirma: `test_guard_gap_a_pool_musigma_s128.py`,
  `test_conectiva_tests23_s136.py`, `test_d22_compuerta_bt_s142.py`, `test_drift4_second_pass_enabled.py`,
  `test_guard_caja_llega_al_segundo_pase_s149.py` (docstrings leídos; vara: H:276/328, H:306-312, ausencia de
  compuerta en H, H:275-277, H:397-399).
- `docs/FICHA_SDA_VRP_CHILE.md:20-35`: no afirma nada sobre MIROVA que el código contradiga; la nota v1.8 («el método
  publicado por el grupo MIROVA sí procesa VIIRS de día, con umbrales más altos») la confirma H:188-199.

## 6. Lo que no pude medir

- **Cuánto cambia la publicación nuestra** con cada afirmación refutada (H1, H3, H5, H6, H7): este frente es de
  cierres y citas; medir efecto pide reprocesar o correr el oráculo sobre pasadas chilenas, que es F1/F3.
- **Qué hace MIROVA en Láscar con el Salar** (H3): el código muestra la capacidad y el comentario la declara por
  volcán; la configuración por volcán no está publicada.
- **Los números diurnos y nocturnos de VIIRS 375 y MODIS** (H6, filas 8 y 9): no hay código; sólo el paper (MODIS) y
  SIN DATO (VIIRS 375), como dice el informe S158 §5.
- **El VRP que imprime `run_example.m`**: sin MATLAB; el oráculo lo reemplaza (0,09 % contra el OSF).
- **`~memory/` y los documentos fuera del repo** salvo `BIBLIOGRAPHY_SYNTHESIS.md`: no entraron al censo.
