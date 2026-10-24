# Verificador con contexto limpio: pre-registros V375-B, V375-C y V375-E (S162)

- Hora del servidor: Sat, 24 Oct 2026 15:49 GMT al empezar y 16:07 GMT al cerrar (header Date de `gh api -i repos/MendozaVolcanic/VRP-chile`).
- Commit medido: `041e7fc43`. HEAD avanzó a `75bb1aefc` mientras verificaba (otra sesión): `git diff 041e7fc43 -- PREREGISTRO_B/C/E.md` da 0 líneas; el único archivo que cambió es `probar_brazos_salida.txt` (+18 líneas, idéntico a mi corrida).
- Modelo: Sonnet 5.5. Sólo lectura de lo ajeno; todo lo mío está en esta carpeta. Sin commits, stash, push, workflows ni Earthdata (sólo `gh secret list`: metadatos, EARTHDATA_TOKEN rotado el 2026-10-08, vigente).
- NO miré: el lote S162 (no existe resultado), `probar_brazos.py` contra datos que no sean los de S159, el evaluador común del instrumento (d', placebo de E: SIN DATO), la referencia de MIROVA fuera de lo congelado en `poblacion_completa.json`, el comportamiento real del runner en GitHub Actions (no despaché nada), PD3/`pipeline/`.
- Carpeta: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs375-c1b864\experiments\_s162_v375\verificador\`

## En una pantalla

1. Los números de arranque y el instrumento se sostienen: población (949/80/133/3.323), pesos 6,8 a 8,5, Wilson 0,86 % con 0 de 445, las 20 cifras de E de la línea base, hash de la selección, humo idéntico línea a línea con la caché, prueba de signos igual a la sellada (2.000/2.000), y bajo nulo intercambiable no da falsos GANA/PIERDE (0 de 400). No encontré un defecto que invalide B.
2. Hay tres reglas que no pueden fallar o son más laxas que su texto: el nulo de cenit parecido de E (orden al azar: d y 1/d equiprobables; con sesgo de plataforma x0,3 dispara 6 %, el nivel del azar), «VALIDA EN O» del compuesto por volcán (valida con hasta 4 alertas perdidas por B <= 4 = SIN SUSTRATO), y el disparador V375-D (b) que en el código compara contra el punto de K y no contra su intervalo (con valores realistas dispara, con el texto no).
3. La elección por volcán en T empata a menudo y desempata por el orden de la tabla, no por caja chica: en el humo elige M21 (441 celdas, al borde del cráter) para Tupungatito cuando C13/C14/C21/SENS/CIRC empatan en T y tienen 9,0 contra 21,7 de error en O. El docstring dice «los más chicos primero» y es falso.
4. Inconsistencia de canal entre C y E: C §5.3 usa la tabla sola para el disparo de V375-D; E §5.4 (a) exige 0 protegidas perdidas que K publica en cualquier canal, y las 3 que el port pierde hoy (Tupungatito 08-01 y 09-14, Isluga 09-09) son sólo OCR y las pierden los diez brazos.
5. «Decide el lote S162 solo» deja sin representar 15 de 80 protegidas, 29 de 949 bajo 1 MW y 17 de 3.323 negativos sin que ningún veredicto lo use como condición; el veredicto B/C no lleva escrito «cobertura de la referencia pendiente» en la línea donde se lee.

## Caminos escritos ANTES de abrir cualquier salida

Archivo: `CAMINOS_ANTES_DE_LEER_SALIDAS.md` (17 caminos; escrito 15:5x GMT tras leer los tres pre-registros y todo el código, sin abrir ningún `*_salida.txt`). Resumen del destino de cada uno:

| # | camino | resultado |
|---|---|---|
| 1 | pesos de la unión no son los del texto | NO CONFIRMADO: S159 sorteó al azar en volcán x cenit (`_s159/portes/02_seleccion.py:57-86`), y el nuevo sorteo condicional da muestra al azar del estrato |
| 2 | intervalo que no puede fallar | CONFIRMADO en (c) nulo de cenit de E; (a) y (b) no aplican |
| 3 | signos con pesos reales distinto de la sellada | NO CONFIRMADO (2.000/2.000 y simulación) |
| 4 | regla que no da un veredicto | CONFIRMADO para VALIDA EN O (H-2) y NULO SESGADO (H-1); B ENCIENDE DE MAS sí es alcanzable |
| 5 | veto relativo esconde pérdidas | CONFIRMADO en parte (H-5) |
| 6 | lote nuevo deja estratos fuera | CONFIRMADO (H-6) |
| 7 | runner vs recálculo (float32) | NO CONFIRMADO en la práctica (H-13, gravedad 1) |
| 8 | ventana cruza cambio de régimen | SIN DATO para S162; el marco ya está congelado y tratado por tramo |
| 9 | un brazo no es lo que dice | CONFIRMADO en parte (H-7): C = M en 5 volcanes, ~M en 4 más |
| 10 | summit medido desde el punto de MIROVA | CONFIRMADO como diferencia declarada (H-10, gravedad 1) |
| 11 | etiqueta de negativo contamina | REFUTADO: 3.551 neg_limpio sólo con filas RUTINA (8 OCR RUTINA), las OCR-sólo de T están fuera de `decide` |
| 12 | NUNCA/PLACEBO no pueden fallar | NO CONFIRMADO: ambos producen veredicto que sólo sale bien si el evaluador funciona (humo: NUNCA PIERDE B 37) |
| 13 | desempate favorece sin decir | CONFIRMADO en el desempate por volcán (H-3) |
| 14 | comparaciones múltiples | CONFIRMADO, gravedad 2 (H-8) |
| 15 | cobertura pendiente sin marca en el veredicto | CONFIRMADO, gravedad 1 (H-9) |
| 16 | regla E (c)(d) ambigua | CONFIRMADO (H-11) |
| 17 | cifras de E | CONFIRMADO |

## Veredictos por afirmación

| afirmación | pre-registro | veredicto | gravedad |
|---|---|---|---|
| Población: 949 bajo, 80 prot, 133 neg_pub, 3.323 neg_resto, 274 de 949 en PCC+Tupungatito | B §3, C §1/§3 | CONFIRMADO (cuenta propia sobre `poblacion_completa.json`; 949 = 274 PCC+Tup) | |
| Unión = muestra al azar dentro de volcán x cenit, peso N_h/(n159+n162) entre 6,8 y 8,5 | B §3 | CONFIRMADO (diseño S159 y `seleccion.py`; `x2_pesos.py`: Kish 444,8 de 445) | |
| Con 0 de 445 la cota baja a ~0,85 % | B §1 | CONFIRMADO (0,0086; `probar_evaluar` 2c) | |
| «El humo reproduce a S159» (0,616/0,618; 0,0091/0,0090; ΔE +150/+148) | C §6 | CONFIRMADO: mi corrida con la caché es IDÉNTICA al `humo_s159_salida.txt` | |
| Prueba de signos con pesos reales = sellada con pesos 1 | C §5 | CONFIRMADO (2.000/2.000, `git show s161-d25-lectura`); y bajo nulo intercambiable 0 falsos GANA/PIERDE en 400 (`x6`) | |
| Los brazos son los que dicen ser (tamaños, M14/PIX7/SENS = cajas de S159, 149/149 iguales al runner) | C §4 | CONFIRMADO; la tesis BOX 0 = BOX 1 se verificó en el oráculo (`mirova_v750_r2.py:115-117`) | |
| «ROI1 y escena usan los mismos umbrales; sólo la caja de cumbre es distinta» | C §1 | CONFIRMADO (`_pasada_contextual`: a0 y a1 usan s1, u_nti1, u_eti1; a2 usa s2) | |
| B: el veredicto SILENCIO ACOTADO / ENCIENDE DE MAS / NO RESUELTO es alcanzable en sus tres salidas | B §5 | CONFIRMADO EN PARTE: SILENCIO y NO RESUELTO sí; ENCIENDE exige IC inferior > 3,85 %, con neg_pub 35 % publicado por el port necesita unas 3 % de neg_resto encendidas con Wilson inferior alto (el punto 4,2 % da NO RESUELTO). Cola conservadora, no error | 1 |
| C 5.1 brazo global | C §5.1 | CONFIRMADO EN PARTE: la regla funciona, pero 9 de 11 volcanes casi no distinguen C de M (H-7) y hay multiplicidad sin control (H-8) | 2 |
| C 5.2 compuesto por volcán «VALIDA EN O» | C §5.2 | REFUTADO como validación: valida con SIN SUSTRATO o EMPATE (H-2) | 3 |
| C 5.3 disparador V375-D | C §5.3 | CONFIRMADO EN PARTE: (a) y (c) coinciden con el código; (b) no (H-4) | 3 |
| C 5.5 / B decide el lote S162 solo | C §5.5 | CONFIRMADO EN PARTE: cubre 81 % de las protegidas, 97 % bajo, 99,5 % neg_resto (H-6) | 2 |
| E: cifras de línea base (0,778; 0,573; 0,766 [0,722; 0,861] n 215; 0,733 n 153; nulo 1,035 [0,784; 1,182] n 37; 0,818 n 365; controles 0,766 y 0,988) | E §1/§4 | CONFIRMADO (re-corrí `linea_base_curva.py`, salida idéntica; 0,818/365 con `x4_hora.py`) | |
| E: cifras de S159 (0,651 [0,436; 0,848]; 1,000 [0,966; 1,019] n 61; recall 96,8 %; «dos de cada tres puntos») | E §1 | CONFIRMADO contra `portes/INFORME.md:21,108-110,165`; el 96,8 % es del programa, no de S159 (población: K publica 908 de 949 = 95,7 % de bajo y 77 de 80 = 96,3 % de protegidas) | 1 |
| E: «nulo de cenit parecido ... tiene que contener 1» detecta un sesgo pasada a pasada | E §4 | REFUTADO como detector (H-1) | 3 |
| E §3 paso 1: equivalencia del 99 % + 80 protegidas idénticas | E §3 | CONFIRMADO EN PARTE: 1 % de tolerancia es del tamaño del efecto medido en negativos (H-12) | 2 |
| E §5.4 regla de adopción | E §5.4 | CONFIRMADO EN PARTE: (a) de otro canal que C, (c) y (d) ambiguas (H-11, H-5b) | 3 |

## Hallazgos

### H-1. El nulo de cenit parecido de E no puede detectar un sesgo de plataforma; sólo falla por azar
- Dónde: `curva_cenit.py:94` (`a, b = ... if rng.random() < 0.5 else ...`) y `veredicto` (l. 140). PREREGISTRO_E §4.
- Qué pasa: con orden al azar d y 1/d son equiprobables, así que la mediana de d vale 1 por construcción y «el IC contiene 1» sólo se rompe por azar (5 %). El texto de `curva_cenit.py` (l. 20-25) dice que el nulo declara «un sesgo de pasada a pasada que no es el cenit (por ejemplo, de plataforma)». No lo declara: el sesgo sólo ensancha el IC. El único caso donde el nulo falló en la línea base (sin condicionar, d 1,145 [1,040; 1,281]) fue por el filtro asimétrico `va <= 0`, no por un sesgo físico. Además con 37 noches el IC es [0,78; 1,18], más ancho que el efecto que se busca (0,77).
- Reproducir: `python -I x3b_nulo.py` (K sintético = MIROVA x sesgo por plataforma x ruido log-normal 0,3 sobre las 1.029 pasadas): NULO SESGADO en 2,7 % (sesgo x1,0), 7,3 % (x0,6), 6,0 % (x0,3). Datos reales: K/MIROVA por satélite 0,608 (SNPP), 0,660 (NOAA-20), 0,641 (NOAA-21).
- Confianza: alta (analítico y simulado). Gravedad 3: E dice que su curva «no se lee» si el nulo falla, y el nulo no puede fallar; la guarda es decorativa. Alternativa barata: comparar |log d| del nulo contra |log d| de la lectura, o usar un orden fijo (SNPP/NOAA) en vez de al azar.

### H-2. «VALIDA EN O» del compuesto por volcán valida por vacío y con un listón menor que el del brazo global
- Dónde: `evaluar.py:461` (`nuevas_o == 0 and veredicto not in ("PIERDE","BLOQUEA")`), `regla_signos` l. 132-133. PREREGISTRO_C §5.2.
- Qué pasa: SIN SUSTRATO (B <= 4) y EMPATE cuentan como «valida». Un compuesto igual a M14 en todo valida (B = 0). Uno que pierde 4 alertas bajo 1 MW frente a M14 también (neto +18,8, SIN SUSTRATO). El global exige GANA; el compuesto sólo «no empeora». Con la elección en T sobre pocas pasadas (Tupungatito 13 bajo y 4 negativos en T, Llaima 1 bajo, Chillán 0) el compuesto puede dar un sí sin evidencia, y PD1 lo recibe con la etiqueta «valida».
- Reproducir: `python -I x7_reglas.py`: pierde 0, 2, 4 alertas -> VALIDA; 5 -> no.
- Confianza: alta. Gravedad 3. Arreglo mínimo: VALIDA sólo si GANA, o EMPATE con B > 4; SIN SUSTRATO no valida.

### H-3. El desempate por volcán sigue el orden de la tabla y elige cajas grandes; el docstring es falso
- Dónde: `evaluar.py:389-405` (docstring «en el orden de BRAZOS (los más chicos primero)»); `brazos.py:37` (orden M14, M13, M21, C13...). C §5.2 dice «orden de la tabla»; C §5.1 usa otro orden (`ORDEN_DESEMPATE`, caja más chica).
- Qué pasa: en el humo, Tupungatito en T tiene 7 brazos con error 0 (M21, C13, C14, C21, SENS, CIRC, SENS_PT) y gana M21 (441 celdas) por ir primero. En O ese mismo volcán da error 21,67 con M21 contra 9,00 con C13/C14/C21/SENS/CIRC/SENS_PT (`x5_pervol.py`; T de Tupungatito en el humo: 3 pasadas). M21 alcanza el cráter al borde: semicaja 10,5 x 375 = 3,94 km contra 3,97 km de dy.
- Confianza: alta (corrida). Gravedad 3 para la elección por volcán; no afecta al global.

### H-4. V375-D (b): el código compara contra el punto de K, el texto contra su intervalo
- Dónde: `evaluar.py:475` (`lg["recall_bajo"]["ic_kish"][1] < lk["recall_bajo"]`, `lk` es el punto). PREREGISTRO_C §5.3 (b) «el intervalo ... queda entero bajo el de K».
- Con valores de la población real (K 0,957, port 0,905, n efectivo ~198): K [0,919; 0,978], port [0,856; 0,938]: el código dispara V375-D, el texto no (`x7_reglas.py`). Nota: el 0,882 de K en S159 era una subestimación de muestra pequeña; la población da 0,957.
- Confianza: alta. Gravedad 3: abre o no un frente (V375-D) con una regla distinta de la sellada.

### H-5. El veto relativo a M14 y los canales
a) (gravedad 2) Los diez brazos pierden las mismas 6 protegidas, y 3 las publica K (Tupungatito 2026-08-01 y 09-14, Isluga 09-09, las tres sólo OCR; `mi_evaluar.json`, `P1.lista`). Ningún brazo puede ganar a M14 en eso; el texto lo dice (veto de adopción). La elección por volcán en T usa el veto absoluto (`evaluar.py:399`), distinto al relativo del global: dos criterios en la misma tabla.
b) (gravedad 3) E §5.4 (a) exige «0 protegidas perdidas que K publica» (lectura A, todos los canales; en O decide también el OCR), mientras C §5.3 usa la tabla sola porque el verificador de S159 (V-2, V-3) mostró que la distancia de esas filas OCR puede ser de otra pasada. Con los datos de hoy, E (a) falla antes de medir nada por motivos que C declara no causados por la caja. El pre-registro de E debe decir qué canal veta.

### H-6. «Decide el lote S162 solo» deja estratos fuera y ningún veredicto lo toma como condición
- Dónde: `evaluar.py:415-425` (`repesar`), `decidir` imprime «N representado» pero no condiciona.
- `x2_pesos.py` (S162 solo): pos_prot 65 de 80 representadas (6 estratos, 15 protegidas sólo en S159; Kish 37,5), pos_bajo 920 de 949, neg_pub 130 de 133, neg_resto 3.306 de 3.323. Además las 41 protegidas nuevas son casi todas publicadas por K (S159 tomó todas las que K no publica, `02_seleccion.py:108-113`): el veto «nuevo» no vuelve a ver ese estrato.
- Confianza: alta. Gravedad 2.

### H-7. En 9 de 11 volcanes las cajas C y M casi coinciden
- Dónde: salida de `probar_brazos.py` (mía, `mi_probar_brazos.txt`): C a M = 0,00 km en Copahue, Isluga, Lastarria, Llaima y Chillán; 0,59 a 0,85 km en Chaitén, Láscar, Villarrica; 2,06 km en Planchón. Sólo Cordón Caulle (7,58 km) y Tupungatito (4,83 km) separan los brazos de forma sustantiva. En el humo los cuatro candidatos (C13, C14, C21, SENS_PT) tienen el mismo neto -254 con B 13 porque las diferencias vienen de esos dos volcanes.
- Consecuencia: el «brazo global» es en la práctica una decisión sobre dos volcanes; «global» no es evidencia de que sirva en los otros nueve. C §5.1 debería informar el P2 sin PCC ni Tupungatito. Confianza alta. Gravedad 2.

### H-8. Comparaciones múltiples sin control
- 9 brazos contra M14 con 5 % cada uno y selección del mínimo de ΔE entre los que ganan (`evaluar.py:440-451`). Los brazos están muy correlacionados (H-7), por eso el daño es menor que 1 - 0,95^9, y el lote S162 decide solo; pero no está escrito. SOSPECHA (sin simulación del daño). Gravedad 2.

### H-9. Falta la marca «no final» en la línea del veredicto
- `evaluar.py:537-539` sólo la deja en la sección 1 y en la línea ESTADO. Las secciones 3 y 4 (`B ... -> SILENCIO ACOTADO`) no la repiten. Quien copie la línea de veredicto pierde la advertencia. Gravedad 1.

### H-10. «summit» se mide desde el punto de MIROVA, no desde el ancla del tablero
- `evaluar.py:160-179` (`dist_regla` usa X0, Y0 y `centroid_dist_km` queda en esa distancia). Declarado en B §2, pero para Tupungatito (inner 7, cráter a 4,83 km de M) y Cordón Caulle (inner 20, a 7,58 km) el borde de «summit» cae en otro lugar que en el tablero. Efecto no medido: SOSPECHA. Gravedad 1.

### H-11. Reglas de E ambiguas
- (c) «M da MEJORA con d' dando MEJORA o, si d no mejora, no EMPEORA» admite un paquete sin mejora de magnitud. (d) «al menos el IC de D del paquete queda entero sobre el de K» no dice si es sobre el IC o sobre su mediana. (b) EMPATE incluye casos con 0 bloques discordantes (SIN SUSTRATO no está listado). Gravedad 2.

### H-12. Equivalencia PD3 al 99 %
- E §3 paso 1 acepta 1 % de pasadas distintas en (npix, VRP a 1e-3). Sobre 859 pasadas son ~8; el silencio de B mide un fenómeno de 0,9 % de negativos y la diferencia de K contra port en neg_pub es de ~87. Una vía de `pipeline/` con 8 pasadas distintas ya cambia el veredicto de B. Pedir 100 % en publicación (no sólo en npix/VRP) o listar las excepciones. Gravedad 2. Además «859 pasadas» incluye el 12-oct de S159, que el evaluador excluye (858).

### H-13. Control «recálculo = runner» y float32
- `probe_v375.py:81` guarda float32; el control exige 1e-6 MW en el 100 %. `x1_float32.py`: el redondeo mueve el VRP 1e-7 a 3e-7 MW en pasadas de 6 a 14 MW; la población llega a 19 MW de MIROVA y 11 MW de K. El 1e-6 se rompería sólo sobre ~50 MW. No hay riesgo con los datos de hoy. Gravedad 1.

### H-14. Menores
- Si una grilla aparece dos veces (re-despacho de un trozo), `grilla_npz` devuelve None (`evaluar.py:213-221`) y la pasada desaparece de `arms` sin figurar en SIN DATO (se cuenta como ok en la sección 1). Gravedad 1.
- PLACEBO exige igual publicación; el predicado del tablero oculta cirrus con VRP > 10 MW y t_max < 273,15 K (`frontend/index.html:1336-1340`), y x1,2 puede cruzar esos cortes en una pasada; con VRP máximo de 14 MW y sin BT bajo en alertas de noche, improbable. Gravedad 1.
- Las neg_resto de Isluga son 3 nuevas + 2 de S159 y las de Láscar 11 + 6: ningún veredicto por volcán de silencio es legible donde más se enciende (los volcanes con alertas frecuentes). El agregado ponderado es correcto; el texto no lo afirma por volcán. Informativo.

## VERIFICADO LIMPIO (contra qué vara)

- Hash de la selección: `python -I seleccion.py` reproduce `objetivos_v375_bc.json` sha256 `9ef02ad02139aa1c...6cc0b4` antes y después de correr (vara: el archivo commiteado).
- Salida de `seleccion.py` igual a `seleccion_salida.txt` (709 nuevas: 155/400/41/113; 531 gránulos; pesos 6,80-8,50; tramos 116/174/110; 16 partidas).
- Población y clases: 949 bajo, 80 protegidas, 3.456 neg_limpio con 133 publicados y 3.323 neg_resto; Tupungatito + PCC = 274 (vara: `poblacion_completa.json`, sin 12, 13, 17 a 20 oct).
- Negativos sin alerta oculta: los 3.551 neg_limpio tienen sólo filas RUTINA (CONS 3.551, OCR 8); las 179 pos no-decide son filas OCR-sólo de T, fuera de ambos lados.
- Diseño de S159: SRS dentro de volcán x cenit (vara: `02_seleccion.py`).
- Evaluador: salida con la caché idéntica al humo; `probar_evaluar.py` OK (prueba de signos = sellada 2.000/2.000; casos a-f y mutación); H0 intercambiable 0 falsos de 400.
- `probar_brazos.py` (3,5 min, sin caché): tamaños, equivalencia con S159 149/149, sintética (M14 0, C14 1, CIRC 1, M21 1). Sin errores.
- `linea_base_curva.py` salida idéntica al archivo commiteado; 0,818/365 y 215 noches.
- m0 = m1 en los umbrales: `mirova_v750_r2.py:115-117`.
- Token de Earthdata rotado el 2026-10-08 (`gh secret list`).

## SIN DATO

- Qué hará el port en neg_resto de verdad (tasa): es el objeto del lote.
- Evaluador común del instrumento (d', placebo de E, protegida de cráter V375-A, cobertura de la referencia): no existen todavía.
- Efecto de H-10 y de la multiplicidad (H-8): sin simulación.
- Si la rama de disparo contiene el código K de #850 (el control 2.2 K re-corrido = publicado lo dirá).
- Comportamiento del runner en Actions con ~28 trozos (no despaché).
