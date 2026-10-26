# Plan de pruebas después de la auditoría S158 (segunda ronda)

> 2026-10-21. Diseño para aprobar antes de ejecutar (gate de `superpowers-brainstorming`). Parte de
> `docs/AUDIT_S158_R2.md` (rama `claude/s158-audit-r2-0eeee2`, commit `854e22e62`, borrador **sin** los veredictos
> de los verificadores en su §5). Nada de esto toca `pipeline/`, `data/` ni `frontend/` salvo el frente A, que va con
> tag y tu sí (A45).

## 1. Por qué hace falta otra vuelta

La segunda ronda dejó la paridad descrita como cinco cambios con nombre. La lista es convincente, pero descansa en
tres cosas que todavía nadie ha comprobado:

1. **Un port, no el código.** Todo lo que «el código de MIROVA da» salió de dos reimplementaciones en Python del `.m`.
   Coinciden entre sí en la detección, pero ninguna se ha corrido contra el `.m` original sobre un gránulo chileno.
   Si el port tiene un error compartido (los dos se escribieron leyendo el mismo texto), las cinco piezas heredan ese
   error sin que nada lo avise.
2. **Diez pasadas.** El hallazgo más grande (el fondo y la suma) se probó en 3 alertas que reproduce, más 1 control
   negativo. El criterio de victoria de `docs/MISSION.md` se mide en las dos direcciones: no basta con que el fondo
   del código «despegue del cero» las alertas, hay que saber cuántas pasadas donde MIROVA no vio nada enciende. Con
   un negativo no se sabe.
3. **Sólo VIIRS 750 tiene código.** Las piezas 1 y 5 se trasladaron a VIIRS 375 y MODIS por analogía. MIROVA no
   publicó el código de esos sensores, así que la única fuente para decidir si el traslado vale son los papers, leídos
   ahora con el código al lado como llave.

Sobre la tercera, tu idea de releer los papers es la correcta y llega en el momento justo. Hasta S158 leíamos los
papers para adivinar qué hacía MIROVA. Ahora sabemos qué hace en VIIRS 750, así que cada frase del paper se puede
clasificar: dice lo mismo que el código, dice otra cosa, o calla. Eso nos dice cuánto creerle al paper donde no hay
código (VIIRS 375 y MODIS).

## 2. Lo que creo que no hemos revisado y puede pesar

En orden de cuánto puede cambiar la respuesta:

- **El escalón de 50° del OSF tiene una sospecha física concreta que nadie probó.** Sobre 50° de cenit, el 24 % de las
  filas VIIRS 750 del OSF no cumplen la fórmula del código. El sensor VIIRS agrega sus muestras de la banda M en tres
  zonas a lo largo del barrido (3 a 1 en el centro, 2 a 1, y 1 a 1 en el borde), y el paso a la zona del borde cae,
  según mi cálculo aproximado, cerca de los 53° de cenit. Si las filas que no cumplen son exactamente las de la zona
  del borde y la razón es constante, el escalón tiene causa y fórmula. **SOSPECHA**: los límites de zona hay que
  leerlos en `documentacion/VIIRS_Geolocation_ATBD_2014.pdf` y en el ATBD radiométrico, no en mi memoria.
- **14 % de las pasadas nocturnas 2025 del OSF no tienen ningún record nuestro** (R2-16, 411 de 2.934; Cordón Caulle 84
  de 436). Sin verificar. Si es cobertura (no bajamos el gránulo), es recall perdido antes de cualquier detector, y
  ninguna de las cinco piezas lo arregla.
- **El tope de cordura de `store.py` puede anular la erupción más grande** (R2-7): en VIIRS 375 anula sin mirar la
  temperatura. Hoy 0 casos. Es el único hallazgo que es un riesgo de seguridad del SDA y no de paridad.
- **El veredicto del A/B de D25 en curso ya no se puede leer tal cual**: su métrica aprueba un placebo con la
  calibración de la adenda, y le faltan el 10-13, el 10-18 y parte del 10-12.
- **Los TIF de MIROVA en UTM nativo (8 adquisiciones, 14 y 15 de septiembre, A106) son la única vara directa de la
  grilla**, y la prueba con gránulos de la segunda ronda usó la grilla como hipótesis. Con ellos se puede ajustar el
  origen y el interpolador en vez de suponerlos.
- **La ROI por volcán de MIROVA** puede estar escrita en los encabezados de sus TIF (extensión y origen por volcán) y en
  el recuadro de sus láminas. Nadie lo ha extraído sistemáticamente.
- **Cuatro definiciones de «alerta de MIROVA»** conviven entre scripts. Sin efecto medido en VIIRS 750, latente en los
  demás. Conviene una sola función y que todos la llamen.

## 3. Los frentes

Cada frente lleva hipótesis, qué la refutaría, insumos y salida. Los criterios se fijan antes de mirar el resultado y
se miden contra MIROVA (A115), no se eligen.

| id | hipótesis | qué la refuta | insumos | salida |
|---|---|---|---|---|
| **P** Relectura de papers | Donde el paper describe un paso que el código fija para VIIRS 750, también dice si ese paso vale para VIIRS 375 y MODIS | La matriz deja pasos clave (fondo, halo, suma, grilla, ROI, día, cenit) sin fuente para VIIRS 375 o MODIS | `documentacion/`: Coppola 2016a (`sp426.5.pdf`), Campus 2022 y 2024, Massimetti (tesis), Coppola 2024 cap. Springer, Coppola 2026 Scientific Data, MIROVA Dashboard UserGuide 2.5, Coppola 2019 y 2023 | Matriz paso del `.m` × sensor × fuente, con página renderizada a imagen (A95) y veredicto IGUAL / DISTINTO / CALLA |
| **O1** Port contra el `.m` | Los dos oráculos reproducen el `.m` original bit a bit en la detección sobre gránulos chilenos | Una máscara distinta en cualquiera de las 10 matrices chilenas o en la de Etna | GNU Octave 11.3 (winget, **requiere tu sí para instalar**); `.m` de `experiments/_s158_d17_diseno/osf_codigo_mirova/`; matrices de la segunda ronda | Tabla máscara a máscara; si Octave no trae `fillmissing2`, se separa detección (comparable) de fondo (no) |
| **O2** Triangulación de MATLAB | La triangulación de MATLAB es una de las 67 y es estable entre pasadas | No aplica (es medición) | Tú corres el `.m` en MATLAB Online con tu cuenta (yo no puedo crear cuentas); 15 minutos | Fondo exacto en las 10 pasadas; cierra la banda de ±1,3 % |
| **N** Escala del fondo y la suma | Con el fondo y la suma del código, las alertas protegidas de VIIRS 750 se publican y las pasadas donde MIROVA no vio nada siguen calladas, en la proporción que exige `docs/MISSION.md` | Encendemos negativos limpios por encima de lo que gana en alertas (criterio de victoria, regla SN de D-9) | Workflow de sólo lectura de la segunda ronda (`EARTHDATA_TOKEN`, A71); todas las alertas VIIRS 750 de abril a octubre más el mismo número de negativos limpios, estratificados por volcán y cenit; incluye el estrato diurno con la rama de día del código | Por pasada: oráculo, producción, MIROVA; recall protegido, publicaciones de más, razón de magnitud. Primer lote tope 400 pasadas (escala a acordar, S120) |
| **G** Grilla e interpolador (D17) | Un origen y un interpolador reproducen los TIF UTM de MIROVA y predicen las dos alertas débiles (Láscar 09-26, Chaitén 10-06) | Ningún candidato reproduce las 8 adquisiciones, o el que las reproduce no predice las dos alertas | `mirova-tif-archive` por la API de GitHub, sin pull (S143); `docs/DISENO_D17_REMUESTREO_UTM.md` | Origen y interpolador ajustados, con su error; o «no identificable con estos TIF» |
| **R** ROI por volcán | La extensión y el origen de cada TIF de MIROVA, y el recuadro de sus láminas, fijan la caja de cumbre por volcán | Los TIF tienen la misma caja en todos los volcanes, o no coincide con las alertas de Cordón Caulle a 7,8 km | Encabezados de TIF (rasterio), láminas de Mirova-v1, KML | Tabla por Tier A: centro, caja de cumbre, caja de escena |
| **S** Escalón de 50° | Las filas del OSF que no cumplen la fórmula son las de la zona de agregación del borde, con razón constante | La fracción que no cumple no salta en el límite de zona, o la razón varía | OSF v2.5 local; ATBD de geolocalización VIIRS (`documentacion/`) | Curva de cumplimiento contra ángulo de barrido, con los límites de zona marcados |
| **M** MODIS con MOD03 | La geolocalización interpolada corre los píxeles 1 a 1,7 km hacia el nadir y cambia clase y fondo | Con MOD03 las posiciones cambian menos de 0,5 km, o no cambia ninguna clase | Workflow de sólo lectura; ~60 records MODIS de cumbre a más de 40° de cenit, más las dos protegidas de Chillán del #864 (10-12 07:20, 10-15 01:05) | Desplazamiento por record, cambios de clase, y si Chillán aparece |
| **C** Cobertura | Las 411 pasadas OSF 2025 sin record se reparten entre «CMR no tiene el gránulo», «fetch falló», «procesado sin record» y «filtro de día» | No aplica (es clasificación) | OSF v2.5, CMR, logs de los runs | Conteo por causa y por volcán |
| **I** Instrumentos | Arreglos de evaluación: cero gránulos no es cobertura completa; la métrica M lleva el placebo como prueba obligatoria; una sola definición de alerta | Las pruebas nuevas pasan sin el arreglo (A116) | `scripts/run_pipeline.py:417`, evaluador D25, `scripts/clase_mirova.py` | PR con pruebas que fallan antes y pasan después |
| **A** Tope de cordura | El tope de `store.py` puede anular una erupción real en VIIRS 375 | La prueba sintética no la anula | `pipeline/store.py:551-557` | Prueba que falla hoy; arreglo **sólo con tag y tu sí** (A45) |
| **D25** Relectura del A/B | El veredicto de D25 cambia con la calibración sellada y con los días faltantes declarados | No aplica | Salida de I; A/B V1, V2a, V2b | Veredicto releído, sin despachar nada nuevo |

## 4. Orden y paralelo

**Puerta 0**: la segunda ronda integra a sus dos verificadores y abre su PR borrador. Ningún frente se apoya en una
afirmación que el verificador marque REFUTADA. **Cumplida el 2026-10-21** (PR #888, §5): ningún hallazgo refutado. Lo
que los verificadores cambiaron y entra al plan:

- **VA-1**: los cúmulos de cumbre en 0 MW salen del segundo pase en los tres sensores. N mide el fondo del código y la
  compuerta de 3 K (D22) **juntos**, con un brazo para cada uno y otro con los dos, no el fondo solo.
- **R2-1** bajó: 64 alertas de MIROVA de la misma pasada en 0 MW, **0 protegidas** (no 96 y 11). La pieza 1 sigue,
  pero su peso en las protegidas es menor de lo que decía el borrador; N lo mide en su escala.
- **R2-2** es asimétrico: 2 a 3,6 km de un lado del barrido sobre 25° y casi nulo del otro. M estratifica por lado del
  barrido, no promedia.
- **VA-2**: VIIRS 375 tiene 271 cúmulos de cumbre en 0 MW sin parear con MIROVA. Entra a N como estrato aparte.
- **VB-1 y VB-4**: un L1B sin geolocalización se descarta en silencio, y hay huecos de producción el 13 y el 20 de
  octubre. Entran a C y a I.
- **VB-2**: el evaluador de D25 deja por defecto la calibración original aunque la simétrica ya está sellada (D-27).
  Entra a I y a la relectura de D25.
- **R2-13**: el 12-oct no se reproduce (CMR sí devuelve esos gránulos); el 18-oct es más amplio que VIIRS 750.

| ola | frentes | por qué juntos |
|---|---|---|
| 1 (al pasar la puerta) | P (tres subagentes por grupo de papers), O1, G + R + S (un frente: geometría de MIROVA), C, I, A | Todos son de sólo lectura o tocan archivos distintos; ninguno necesita el resultado de otro |
| 2 | N, M, D25 | N necesita O1 (para saber si el port es vara) y, si se puede, G y R (grilla y caja correctas); D25 necesita I |
| 3 | Síntesis | Prerregistro de adopción del paquete VIIRS 750 (fondo, suma y detección del código) con la regla de `docs/MISSION.md`, y diseño del A/B respetando A114 (medir cada pieza donde puede actuar); verificador con contexto limpio |

**Dónde corre.** Cada worktree pesa unos 4 GB y C: tiene 36 GB libres (parada bajo 3 GB). En vez de siete worktrees:
un worktree `s159-pruebas` cortado desde la punta de la segunda ronda, donde los frentes de sólo lectura trabajan como
subagentes, cada uno en su carpeta `experiments/_s159/<frente>/`, y sólo el coordinador hace git (así no hay carrera,
A44). I y A van en un segundo worktree porque terminan en PR propio. Total, dos worktrees, unos 8 GB.

**Modelos.** Opus para P, O1, geometría y N, que piden criterio; Sonnet para C. Un verificador final con contexto
limpio que no haya encontrado nada de lo que verifica.

## 5. Lo que este plan no hace

- No cambia el detector. El paquete VIIRS 750 se adopta sólo después de N, con prerregistro y A/B, por A45.
- No envía el correo a Coppola ni comenta el #864 en GitHub sin tu sí.
- No reabre los cierres que la segunda ronda confirmó, salvo que un frente encuentre evidencia nueva.

## 6. Decisiones que te tocan

1. Aprobar el diseño (o recortarlo).
2. Instalar GNU Octave 11.3 con winget para O1.
3. Si quieres hacer O2: correr el `.m` en MATLAB Online (te dejo las matrices y el comando listos).
4. La escala del primer lote de N: propongo tope de 400 pasadas.
