# Verificador con contexto limpio: sonda S150 de los tres campos

**Objeto.** Rama `origin/s150-sonda-tres-campos`, commit `4ded935a7`: `experiments/_s150_sonda_tres_campos/`
(DISENO.md, sonda.py, campos.py, evaluar.py, seleccionar_pasadas.py, pasadas.json, negativos_camino_d22.json,
plantillas_tif.*, textura_utm_vs_geo.*, prueba_local.*, sellar.py) y `.github/workflows/probe-s150-tres-campos.yml`.
Contexto leído: `docs/S150_ALERTAS_DEBILES_MAX.md`, `docs/audit_s150/VERIFICADOR_PREREGISTRO_D22.md`, D17/D22/D26 y
A106 en `CLAUDE.md`.

**Límites que respeté.** No modifiqué nada del repo salvo este informe; sin commit, push, checkout, stash ni pull; no
despaché workflows; no bajé gránulos ni usé credenciales; no corrí pytest. Todo lo que corrí fue en el directorio
temporal de la sesión (`...\scratchpad\verif\`).

**Nota de proceso (A44).** A mitad de la verificación alguien cambió la rama del árbol compartido (pasó por
`main`, `s150-experimental-diario` y de vuelta a `main`) y la carpeta de la sonda desapareció del disco. Desde ese
momento leí todo con `git show 4ded935a7:<ruta>`, que no depende del árbol. `prueba_local.py` lo corrí antes del
cambio, sobre la rama correcta. Este informe queda como archivo sin seguimiento en el árbol, en la rama que esté
activa.

## Veredicto

**No se puede sellar ni despachar tal cual.** El instrumento de medición (sonda.py y campos.py) está bien armado y
reproduce el pipeline en lo que pude comprobar sin NASA, la lista de pasadas se reproduce exacta y el workflow cumple
casi todo lo pedido. El problema está en el **evaluador**: puede imprimir CONFIRMA cuando el campo nativo no
reproduce las pérdidas, y la propia prueba local lo demuestra (P6 da "CONFIRMA (con salvedad...)" con un acuerdo del
30 % en `nativo|max`). Con los cambios del hallazgo 1 y 2 (acotados a `evaluar.py` y una prueba más en
`prueba_local.py`) y el del sello (hallazgo 3), se puede sellar. Los hallazgos 4 en adelante son mejoras o
salvedades que conviene escribir, no bloqueantes.

## Lo que comprobé y está bien

| comprobación | cómo | resultado |
|---|---|---|
| `prueba_local.py` | corrido por mí (VRP_PROFILE F), salida cruda comparada con `prueba_local_salida.txt` | 61 comprobaciones OK, salida idéntica línea a línea |
| La lista congelada | re-corrí `seleccionar_pasadas.py` del commit fuera del repo, con el índice de TIF bajado del blob `19c9273e` del commit `3660cdfa` (el mismo archivo que usó el autor, `cmp` idéntico) | `pasadas.json` y `negativos_camino_d22.json` **idénticos byte a byte** con finales LF; todos los controles de reproducción (988/946, 42/32, 15/14, 271/576) cumplidos |
| Llamada a `calculate_vrp` y a `store.append_record` | comparé `sonda.procesar_pasada` y `sonda.persistir` contra `scripts/run_pipeline.py:278-300` | mismos argumentos (centro del catálogo, `radius_km`, ancla `get_detection_anchor`, inner, zonas, kernel, etc.) |
| B contra F | todas las constantes de `pipeline.profile` con cada perfil | difieren sólo en `ENABLE_TESTS_23_PROSE_BRANCH` (y nombre y carpeta): voltear ese flag en el perfil F reproduce B |
| Flags reasignables | `grep` en `pipeline/` | `ENABLE_TESTS_23_PROSE_BRANCH`, `ENABLE_TESTS_23_NO_BT_GATE_VIIRS375` y `ENABLE_UTM_REGRID` se leen como globales de `process_viirs` en el momento de la llamada (l. 737, 1194, 1209, 1216, 1298, 1301, 1349); reasignarlos en el módulo funciona (A89) |
| Código del pipeline desde el A/B | `git diff` entre el padre de cada rama `s146-ab/<run>` usada y HEAD, sobre `pipeline/` y `frontend/index.html` | sólo cambió `store.py` (`first_processed_utc`, descriptivo), perfiles nuevos y estilo de puntos del tablero; nada que toque detección ni predicado |
| Recorte del ROI en `evaluar_campo` | `compute_eti_scene_quadratic` deja ETI en NaN fuera de la máscara válida | el pozo del segundo pase queda dentro del ROI aun sin restringirlo, así que el recorte con margen 3 no cambia μ₂ ni σ₂ (ver hallazgo 6 para el control que falta) |
| Todos los gránulos del A/B | `pasadas.json` | 365 de 365 son `standard`, y en las 365 el gránulo de B y de F es el mismo |
| GeoTIFF de MIROVA | cabecera de un TIF real (Chaitén 2026-05-19 05:06) con rasterio | EPSG:4326, float64 sin cuantizar, `AREA_OR_POINT = Area` (centros de celda en +0,5, como la plantilla), valores 0,078 a 0,224 (I04 de 263 a 285 K, plausible) |
| Plantilla contra `get_grid_center` | centro de cada plantilla contra `mirova_center` de `volcanoes.yaml` | a 0,41 km o menos en los 11; semiancho 25,0 a 25,8 km, así que el radio de 26 km cubre la grilla salvo las esquinas |
| Existencia de los TIF en el sha fijado | API de árboles de git de `mirova-tif-archive` en `3660cdfa` (sin bajar blobs) | los 135 `tif_path` usables existen; el repo es público |
| Credencial | `REGISTRO_CREDENCIALES.md` fila 1 | `EARTHDATA_TOKEN` rotado el 2026-10-08, vence 2026-12-07 |
| Workflow | lectura | `"on":` entre comillas, `ubuntu-24.04` en los tres jobs, candado `preregistro_aprobado = si`, sello verificado, falla si el token viene vacío, `sonda.py` además se niega si hay `EARTHDATA_USERNAME` o `EARTHDATA_PASSWORD` en el entorno, `fetch.auth` sólo cae a netrc si el archivo existe (no en el runner), checkout disperso con `filter: blob:none`, `fetch-depth: 1`, fijado por sha, y `README.md` siempre en la lista, artefactos por lote a 90 días, `pipefail` antes del `tee`, rama propia que no toca `main` |
| Elección del campo M | `evaluar.py:177-190` | sale sólo de las métricas contra el TIF (mediana de r_dL y s_ratio); no mira ninguna publicación |
| Cotas de H1 y del azar | razonamiento sobre las tasas de la ventana | ver hallazgo 9: con pérdidas y residual indistinguibles, CONFIRMA exige recuperar al menos el doble de lo que se reabre; un desplazamiento al azar del umbral no lo cumple |

## Hallazgos

### 1. No hay control que exija reproducir F en el nativo antes de leer H1; el evaluador confirma sin él. Gravedad 5

**El fenómeno.** Las 32 pérdidas son, por construcción, pasadas donde el píxel quedó **justo debajo** de μ + 5σ en el
brazo F. Son casos de borde: cualquier perturbación del entorno (otra versión de numpy, otro gránulo si NASA
reprocesó) puede subir algunos sobre el umbral sin que el campo tenga nada que ver. Si eso pasa en el nativo, ya no
son pérdidas en esta corrida, y si se cuentan como recuperadas en M se le atribuye al campo lo que hizo el entorno.

**Lo que hace el código.**
- La reproducción del A/B (`evaluar.py:157-174`) es un acuerdo **agregado sobre las 365 pasadas** contra lo que B y F
  publicaron, con umbral 95 %. Tolera unos 18 desacuerdos, que pueden caer **todos** en las 42 pérdidas. Y no frena
  nada: si falla, el veredicto se imprime igual con "(con salvedad...)" (`evaluar.py:281-283`). El verificador D22
  (H3) ya había pedido determinismo **exacto** en las claves de la lista y medido sobre lo publicado, no un 98 %; acá
  se bajó a 95 % y agregado.
- R_L(M, max) es una tasa **absoluta** (`evaluar.py:265`): no exige que `nativo|max` de esta misma corrida no
  publique. La regla H3 c del verificador D22 ("cuenta sólo si la variante publica y el `max` de este run no") se
  aplicó en D22 (`evaluar.py:297-300`) pero no en H1.
- No hay guarda para `brecha <= 0`: si `nativo|min` y `nativo|max` publican lo mismo en negativos, `ΔFP <= 0,25 ·
  brecha` se cumple con ΔFP = 0.

**Evidencia.** La prueba local P6 (clones que publican en todo): acuerdo de `nativo|max` 0,30, brecha 0, y el
veredicto impreso es `"CONFIRMA (con salvedad: el nativo no reproduce el A/B en ['nativo|max', 'nativo|min']; ver
instrumento)"`. P6 lo marca como OK porque sólo pide que el veredicto esté "en la lista". Es un control que pasa en
verde sobre un instrumento roto (A110 d).

**Corrección.**
1. Gate de reproducción **antes** de H1 y D22, por grupo: en las pérdidas confiables usables, `nativo|max` no publica
   y `nativo|min` publica; en las conservadas, `nativo|max` publica. Si falla en más de 2 de las 32 pérdidas (o el
   número que se fije ahora), H1 y D22 son INDETERMINADO POR INSTRUMENTO, sin "salvedad".
2. R_L como contraste **dentro de la corrida**: pérdida recuperada = `M|max` publica **y** `nativo|max` no, sobre las
   pérdidas que el nativo reprodujo. ΔFP y brecha ya son dentro de la corrida y están bien.
3. Guarda `brecha >= 0,10` (o la que se fije): si no, INDETERMINADO.
4. En P6, exigir que los clones den INDETERMINADO POR INSTRUMENTO, y agregar un caso que sí deba dar CONFIRMA (nativo
   reproduce, M recupera y no reabre) y otro REFUTA. Hoy no hay ninguna prueba que muestre que CONFIRMA puede salir
   sólo cuando corresponde.
5. Exponer como gate, no sólo informar, `sd_dnti_nativo_vs_record_ab`: es la prueba directa de que el nativo es el
   mismo cálculo que el A/B, pasada por pasada.

### 2. El evaluador emite veredictos con cobertura parcial, también en el piloto. Gravedad 3

El job `evaluar` corre con `if: always()` aunque fallen lotes (`probe-s150-tres-campos.yml:166`), y `evaluar.py` no
condiciona el veredicto a la cobertura: sólo a la identidad. Los denominadores (`_tasa`) se encogen en silencio y no
hay mínimo de n. El DISENO §10.7 recomienda un **piloto con el lote 1**, y el lote 1 (verificado: Chaitén, 12
pasadas, 2 pérdidas confiables, 10 con TIF, los tres grupos negativos presentes) bastaría para que el evaluador
imprima CONFIRMA o REFUTA con R_L de 0, 0,5 o 1 sobre 2 pérdidas. Eso es mirar el resultado antes del despacho
completo, contra la lógica del pre-registro, y además el run se guarda en una rama.

**Corrección.** (a) En `evaluar.py`, veredicto INDETERMINADO POR COBERTURA si faltan más de N pérdidas confiables
usables (por ejemplo, menos de 30 de 32) o si algún grupo queda bajo el 90 % de lo esperado; informar n en cada
tasa. (b) Un input `piloto` en el workflow que se salte el job `evaluar` (o lo corra con una bandera que sólo
imprima cobertura, tiempos, memoria y la validación contra el TIF), y escribir en el DISENO que el piloto no se lee
en detección y que su lote se vuelve a correr en el despacho completo.

### 3. El sello no cubre el código que se mide ni el predicado. Gravedad 3

`sellar.py` fija 8 archivos de la carpeta de la sonda. Quedan fuera los que deciden el resultado tanto como el
criterio: `pipeline/` (en particular `process_viirs.py`, `detection_context.py`, `store.py`, `regrid.py`,
`geo_utils.py`, `pipeline/profiles/_s147_ab_sin_test1_max.yaml`), `frontend/index.html` (el predicado que corre
node), `scripts/banco_paridad.py` (el arnés del predicado y `inner_desde_html`), `scripts/run_pipeline.py`
(`load_volcanoes`, `VOLCANIC_FEATURES`), `volcanoes.yaml` y el propio workflow. El despacho por `workflow_dispatch`
corre lo que haya en la rama al momento de despachar (y el yml tiene que estar en `main`, así que se despacha
desde `main`); `main` recibe cambios casi a diario. El verificador D22 (H9) ya lo había señalado.

**Corrección.** Escribir en el sello el sha del commit de sellado y, en el paso de verificación, comprobar que esos
caminos no cambiaron entre ese sha y `HEAD` (`git diff --quiet <sha> HEAD -- pipeline/ frontend/index.html
scripts/banco_paridad.py scripts/run_pipeline.py volcanoes.yaml .github/workflows/probe-s150-tres-campos.yml`,
con `fetch-depth: 0` en ese job). Alternativa más simple: agregar esos archivos a la lista de hashes. Un detalle: el
sello lo escribe quien aprueba y nada impide re-sellar; conviene que la línea del sello incluya quién lo aprobó y
contra qué informe, para que la procedencia quede en la historia de git.

### 4. La validación contra el TIF puede elegir la textura del producto exportado, no la de la grilla donde MIROVA detecta, y es frágil por registro. Gravedad 3

**El fenómeno.** La pregunta de H1 es la σ del campo donde MIROVA **detecta**. Los papers (Aveni 2024, Campus 2024)
dicen grilla UTM; los TIF de abril a agosto son EPSG:4326. Si el TIF geográfico sale del gránulo por otro camino que
la grilla de detección, el interpolador que mejor reproduce el TIF no es necesariamente el de la detección.

**Evidencia.** `textura_utm_vs_geo_salida.txt`: el DISENO §1 lee bien que el geográfico **no** es más suave que el
UTM en sd(dL)/L. Pero no dice que la autocorrelación a una celda de dL es **menor en el geográfico en los 11 de 11
volcanes** (0,18 a 0,30 contra 0,24 a 0,47). Once de once en la misma dirección no es ruido, aunque está confundido
con las noches: los UTM son sólo del 14 y 15 de septiembre y los geográficos de los días vecinos, y una nubosidad
extendida esas dos noches subiría la autocorrelación en todo Chile. SOSPECHA: los dos productos no tienen la misma
textura, y no sabemos cuál corresponde a la detección. Si la detección es la del UTM (más suave), validar contra el
geográfico elige un campo menos suave que el real y sesga hacia REFUTA.

**Fragilidad.** P4 muestra que correr el TIF una celda baja r_dL de 1 a 0,25 con r_L = 0,95: r_dL es casi una prueba
de registro a nivel de subcelda. Cualquier diferencia de geolocalización entre nuestro gránulo estándar y el NRT que
procesó MIROVA, o un TIF pareado a otra pasada (17 de los 135 son archivos `_lm` cuya hora de adquisición la puso el
índice en una captura posterior, no el nombre), baja r_dL para los **tres** candidatos y empuja a INDETERMINADO. Es
una falla segura (no confirma de más), pero puede gastar el run entero. Además, en el sintético `tif_nn` contra un
TIF lineal dio r_dL = 0,800, justo el umbral: el r_dL ≥ 0,80 no separa vecino de lineal; lo separa sólo s_ratio.

**Corrección.** (a) Escribir en el DISENO §9 la salvedad UTM contra geográfico con el 11 de 11. (b) Gate por pasada,
pre-registrado, para entrar a la mediana de validación: r_L ≥ 0,90 con `tif_nn` (si no, el TIF no es esa escena o no
está registrado y se descarta de la validación, contándolo). (c) Informar r_dL con el mejor desplazamiento de
subcelda (±0,5 celda) como diagnóstico, sin que decida. (d) Informar la validez por volcán, al menos en los cinco que
concentran las pérdidas (Tupungatito, Chaitén, Puyehue Cordón Caulle, Planchón Peteroa, Lastarria). (e) Usar el
piloto (hallazgo 2) para mirar **sólo** la validación y ajustar, antes del despacho y por escrito, la geometría de
la validación, no los umbrales de H1.

### 5. El TIF trae sólo I04: alcanza para la textura de dNTI, pero hay que decirlo con números. Gravedad 2

De noche L(I05) ≈ 3 a 5 W m⁻² sr⁻¹ µm⁻¹ y L(I04) ≈ 0,05 a 0,2, así que dNTI ≈ (2 / L5) · (dL4 − (L4 / L5) · dL5) con
L4 / L5 ≈ 0,01 a 0,05. Con el ruido de I04 a 260 K (del orden de 1 K, unos 0,003 en radiancia) y un contraste de
terreno de 2 K en I05, el término de I04 domina la varianza de dNTI por un factor de 3 a 10. Validar I04 valida la
mayor parte de lo que fija σ; I05 entra con el mismo interpolador, así que si el interpolador es el correcto lo es
para las dos. Esto es una estimación de orden, SIN VERIFICAR con datos. **Corrección.** Guardar `L_i05` en la tabla
de píxeles (hoy sólo va `L_i04`) e informar, por campo, la fracción de la varianza de dNTI del pozo que explica el
término de I04.

### 6. Faltan dos comparaciones gratis contra la corrida real sobre el gránulo entero. Gravedad 2

El control de identidad del primer pase compara μ y σ del recorte contra el diag real (bien), pero la máscara del
primer pase y la réplica del segundo pase se comparan contra las funciones reales **corridas sobre el mismo recorte**,
no contra lo que pasó en la corrida sobre el gránulo entero. La sonda ya captura las dos cosas y no las usa:
`cap["fp_hot"]` (máscara real del primer pase, entera) y `ev["sp_out_n_real"]` (píxeles finales reales del segundo
pase, enteros). **Corrección.** En `max|con_compuerta`: `n_hot_1_escena == fp_hot.sum()` y `n_final_escena ==
sp_out_n_real`, como parte de la identidad. Por la máscara NaN del ETI deberían coincidir; hay que comprobarlo, no
suponerlo.

### 7. El tope de 4.000 píxeles puede esconder reaperturas de D22 en Puyehue Cordón Caulle. Gravedad 2

`evaluar_campo` guarda los 4.000 píxeles de mayor dNTI del **primer** pase más el objetivo
(`campos.py:387-390`). Un píxel nuevo del segundo pase o de la variante sin compuerta puede tener dNTI bajo en el
primer pase y quedar fuera; entonces `_nuevo_en_cumbre` no lo ve y la reapertura de D22 se subestima. Con inner de
20 km (unas 8.900 celdas de cumbre en el nativo) PCC es el candidato. **Corrección.** Conservar siempre todo píxel
que sea final o activo en alguna variante, y aplicar el tope sólo al resto.

### 8. El volumen de la rama de datos no está medido. Gravedad 2

La tabla de píxeles lleva unas 34 columnas por campo y hasta 4.000 filas, en 5 campos por pasada; para PCC
(56 pasadas) eso puede rondar los megabytes por pasada. El job `evaluar` hace `git add -f` de todo y lo empuja a una
rama que no caduca. SIN VERIFICAR el tamaño. **Corrección.** Medirlo en el piloto; guardar las salidas con gzip o
empujar sólo `evaluacion.*` y un resumen, dejando el detalle en los artefactos.

### 9. Las cotas: tienen sentido y el azar no las cumple, salvo por lo del hallazgo 1. Gravedad 1 (informativo)

- **H1.** Con los totales de la ventana, brecha ≈ 0,33 (los 766 residuales pesan 0,33 y B los publica todos) y la
  tolerancia de CONFIRMA, ΔFP ≤ 0,25 · brecha ≈ 0,08, equivale a reabrir como mucho una cuarta parte del residual
  apagado. S150 §4 mide que pérdidas y residual son indistinguibles en el record; si un campo sólo baja el umbral,
  recupera y reabre a la misma tasa y no puede dar R_L ≥ 0,5 con reapertura ≤ 0,25. O sea, CONFIRMA exige un campo
  que **discrimine**, que es exactamente H1. El error estándar de ΔFP con 84 y 42 negativos ronda 0,02 a 0,03,
  bien bajo 0,08. Con 32 pérdidas, el error de R_L ronda 0,09: si la tasa real es 0,5, la cota se cruza la mitad
  de las veces, lo que está bien para una cota pre-registrada pero conviene escribirlo como hizo D22 con su
  potencia.
- **Validez.** 0,80 y [0,80; 1,25] fallan hacia INDETERMINADO, no hacia CONFIRMA (hallazgo 4).
- **Sustrato de TIF.** Que sólo 10 de las 42 pérdidas tengan TIF no afecta a H1: M se elige con las 135 pasadas
  validadas y se aplica a todas con la plantilla, que es fija por volcán (3.541 TIF, una grilla por volcán). Sí se
  puede aprovechar: en las 10 pérdidas con TIF, informar el contraste del objetivo en el TIF y en M (sin decidir).
  Aquí el TIF sale del mismo gránulo y eso es lo que se quiere (validar la construcción, A109 no aplica).
- **D22.** 7 de 14 con techo realista 12 y reapertura < 0,25 de 80: heredadas del verificador D22 y coherentes. El
  control positivo `nativo|min` publica las 14 se informa pero no frena; debería frenar, igual que en el hallazgo 1.

### 10. Los campos tif_* cambian también el centro, el radio y la referencia de distancia. Gravedad 1

En `tif_*` la escena se centra en `get_grid_center` con radio 26 km, y `dist` (que define el ROI y la distancia del
píxel suelto) pasa a medirse desde ese centro. Lo revisé por si contaminaba la clase `summit`: no la contamina en
lo que importa, porque las 32 pérdidas de B tienen fuente `ctx_cluster`, y con el ancla honesta la distancia final es
la del cúmulo medida desde el cráter (`anchor.py:82-84`), no desde el centro. Sólo el respaldo `eruption_loose` usa
la distancia al centro. El cambio del pozo de σ por centro y radio sí es real y se separa leyendo nativo → `utm_nn` →
`tif_nn` → M, como dice el §8. **Corrección.** Una línea en el §9 que lo diga, y como diagnóstico, R_L restringido a
publicaciones cuyo cúmulo cae en la zona objetivo, para que una "recuperación" sea del mismo foco y no de otro píxel
de la cumbre.

### 11. Detalles. Gravedad 1

- `nulo_ok` compara las zonas nulas de M con `max` contra el nativo con `min`, que es muy permisivo: sólo detecta un
  campo peor que `min`. ΔFP cubre lo que este control no cubre; no cambiaría nada, pero el DISENO lo presenta como
  "control negativo" y es débil.
- Versiones: numpy sin fijar en la sonda y en el A/B. Con el contraste dentro de la corrida (hallazgo 1) deja de
  importar para H1.
- El job `evaluar` instala sólo `numpy pyyaml pandas`; `evaluar.py` importa `banco_paridad`, que arrastra
  `auto_audit_weekly`, `pipeline.store` y `referencia_mirova_unificada`. Por las importaciones que leí debería
  bastar; SIN VERIFICAR en un entorno limpio.
- `grupos` del DISENO §2: "residual apagado 29 / muestra D22 31" mezcla grupo primario y pertenencia; la salida del
  script da 29 y 28 por grupo primario y 31 por pertenencia. Es consistente, pero conviene decir cuál es cuál.
- El tiempo y la memoria por lote (15 corridas por pasada, 3 sobre el gránulo entero de unos 41 millones de píxeles)
  no están medidos; 330 minutos por lote es un supuesto. El piloto es necesario, no opcional.

## Cambios mínimos para sellar

1. `evaluar.py`: gate de reproducción por grupo en el nativo, R_L dentro de la corrida, guarda de brecha, gate de
   cobertura con n mínimo, control positivo de D22 que frena (hallazgos 1 y 2, y 9 D22).
2. `prueba_local.py`: P6 debe dar INDETERMINADO POR INSTRUMENTO con los clones, y casos sintéticos que den
   CONFIRMA y REFUTA cuando corresponde.
3. `sellar.py` y el workflow: sello con sha y comprobación de que `pipeline/`, el predicado, el arnés y el yml no
   cambiaron (hallazgo 3); input de piloto que no imprima veredictos (hallazgo 2).
4. `campos.py`/`sonda.py`: identidad contra `fp_hot` y `sp_out_n_real`, tope de píxeles que no corte finales,
   `L_i05` en la tabla, gate de r_L por pasada en la validación (hallazgos 4 a 7).
5. DISENO: salvedades de los hallazgos 4, 5 y 10; piloto obligatorio con lectura sólo de validación, cobertura,
   tiempo y memoria.

Después de eso, correr de nuevo `prueba_local.py`, sellar y despachar primero el piloto.
