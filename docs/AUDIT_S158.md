# AUDIT S158: todo lo hecho, medido contra el código de MIROVA

> S158, 2026-10-21. Plan: `docs/PLAN_AUDITORIA_S158.md`. Seis frentes con una lente cada uno y tres verificadores con
> contexto limpio, todos subagentes de una sesión, sobre la rama `s158-d17-diseno` (PR #885). Informes, scripts y
> salidas crudas en `experiments/_s158_audit/f1` a `f6` y `v1` a `v3`. Nada de `pipeline/` ni `data/` se tocó.
> Lo que este documento llama CONFIRMADO lo confirmó un verificador que no vio el trabajo del auditor.

## 0. En una pantalla: ¿con esto alcanzamos la paridad?

**Todavía no, pero por primera vez sabemos dónde está.** El código de VIIRS 750 que MIROVA publicó, el oráculo que lo
reproduce (la pasada de Etna del OSF v2.5: mismos 5 píxeles, VRP a 0,09 %) y los nueve agentes dejaron la brecha
partida en piezas con nombre, causa y número. Ninguna se cierra sin tocar `pipeline/`, y ninguna se adopta sin A/B
pre-registrado y tu «sí» (A45). Ordenadas por lo que más acercan a MIROVA:

1. **El fondo del VRP es la causa mayor del déficit de magnitud.** Usamos un solo número por escena (la mediana del
   anillo de 5 a 25 km) y recortamos el exceso a cero; MIROVA interpola un fondo local bajo los alertados y no recorta.
   De noche la cumbre es más fría que las laderas del anillo. En Etna, con **los mismos 5 píxeles**, MIROVA da 9,881 MW y
   nosotros 2,748; con nuestro coeficiente y el fondo de MIROVA da 9,8809: **la brecha entera es el fondo** (V1). En
   VIIRS 375, con el fondo de MIROVA sobre nuestros propios píxeles, el déficit a nadir desaparece en Copahue (0,42 a
   1,08) e Isluga (0,73 a 1,01) (V3). En VIIRS 750, donde no hay kernel local, deja en 0,0 MW 235 de 855 cúmulos de
   cumbre nocturnos (Tupungatito 63 de 84, Isluga 76 de 134), que el tablero oculta; no se pierde ninguna noche de
   alerta, pero sí la serie del sensor y su recall (V3).
2. **La caída con el cenit es real, es de conteo, y yo la había subestimado.** En la misma región, nuestra energía
   sobre la de MIROVA va de 0,98 cerca del nadir a 0,72 a 30-40° y 0,48 a 60-75°; nuestro conteo cae (0,90 a 0,42) y el de
   MIROVA no se mueve, dentro de cada volcán (V3). Candidato: el remuestreo D17 o la dilución en píxeles grandes; lo
   decide el A/B.
3. **La detección de VIIRS 750 se aparta del código en piezas acopladas.** La compuerta `bt > t_bg + 3 K` del primer
   pase no existe en MIROVA y vacía ese pase en cumbres frías: 19 de 67 publicados con K salen sólo del segundo pase,
   entre ellos 3 alertas protegidas de Chillán (V1). El segundo pase de MIROVA corre siempre y sobre toda la escena, sin
   la condición de adyacencia del paper (V2). Fuera de la cumbre MIROVA exige un dNTI de 0,02 (0,0225 en nuestras
   unidades de 8 vecinos) y nosotros 0,010: nuestro umbral de escena queda bajo el suyo en ~79 % de las pasadas de VIIRS
   750 (V3). K1 casi no decide en Chile (F4).
4. **Lo que se publica.** MIROVA publica la unión de todos los alertados; nosotros un cúmulo, con modo de un píxel. En
   Cordón Caulle, 8 publicados de VIIRS 750 están a 9,9 a 19 km del cráter, donde MIROVA nunca publicó: salen de
   `inner_radius_km = 20` (V1).
5. **El día.** Rechazamos todo VIIRS 750 diurno; MIROVA no, y en la ventana K perdimos 3 alertas protegidas de Chillán de
   2,5 a 3,7 MW (V1). Es la decisión D-10, con A/B pendiente.

Y dos defectos de instrumento que hay que arreglar **antes** de creerle a cualquier A/B:

6. **Cero gránulos se registra como «Cobertura: completa»** (`scripts/run_pipeline.py:417`, `pipeline/fetch.py:622-643`;
   V2-1). Por eso al A/B de D25 le falta el 2026-10-18 entero, con 9 alertas protegidas de Chillán; puede repetirse en
   cualquier reproceso de días recientes.
7. **La métrica de magnitud del A/B de D25 aprueba un placebo** (D = 1,10·K da MEJORA en dos estratos que deciden,
   con la calibración que rige; V2). Mientras K esté bajo MIROVA, cualquier subida gana.

## 1. Hallazgos verificados

Gravedad final = la del verificador.

| id | hallazgo | veredicto | G |
|---|---|---|---|
| F1-H1 | fondo escalar del anillo + recorte; Etna: toda la brecha es el fondo | CONFIRMADO, con matiz (el recorte sólo suma 6 %) | 4 |
| F5-01 | al A/B de D25 le faltan 152 de 4.762 pasadas (todo el 18-oct; 9 protegidas de Chillán) | CONFIRMADO (sí hay control al 5 %, no salta) | 4 |
| V2-1 | cero gránulos = «Cobertura: completa» | propio de V2 | 3 |
| F3-H1 | fondo + recorte dejan en 0 MW cumbres frías de VIIRS 750 | CONFIRMADO; 0 noches perdidas | 3 |
| F3-H2 | la caída con el cenit es de conteo | CONFIRMADO | 3 |
| F3-H4 | el fondo del anillo sobreestima en Copahue e Isluga (no en Chillán, no explica Láscar) | CON MATIZ | 3 |
| F4-H1 | mínimo de dNTI fuera: con 0,010 decide en ~10 %; con el 0,02 de MIROVA decidiría casi siempre | CON MATIZ (título refutado) | 3 |
| F1-H2 | VIIRS 750 diurno rechazado; 3 protegidas perdidas | CONFIRMADO, con matiz | 3 |
| F1-H5 | compuerta de 3 K acoplada al segundo pase (19 de 67; 3 protegidas) | CONFIRMADO, agravado | 3 |
| F1-H7 | 5 alertas de MIROVA sin detección nuestra (1 protegida, Cordón Caulle 10-10 05:54) | CONFIRMADO; mecanismo SOSPECHA | 3 |
| F2-H2 | el segundo pase de MIROVA corre siempre y en toda la escena | CONFIRMADO, con matiz | 3 |
| F5-02 | la métrica M de D25 aprueba un placebo | CONFIRMADO, con matiz | 3 |
| F6-1 | sobre 50° el VRP de VIIRS 750 del OSF no es el del código (24 %, mediana 0,51) | CONFIRMADO | 3 |
| V1-1 | 30 cúmulos de cumbre de VIIRS 750 publicados en 0 con K (7 alertas de MIROVA) | propio de V1 | 3 |
| V2-2 | 53 records VIIRS 750 con el primer pase vacío y el segundo con píxeles (imposible en MIROVA) | propio de V2 | 3 |
| F2-H1 | «MIROVA cuenta regiones, factor 42» es falso: cuenta píxeles | CONFIRMADO, con matiz | 2 |
| F3-H3 | a nadir pierde la selección | CON MATIZ | 2 |
| F4-H6 | las citas del «traslado estructural» no separan estructura de números | CONFIRMADO, más fuerte | 2 |
| F1-H3 | caja de 7 × 7: el conteo se reproduce, la premisa no (en PCC MIROVA no usa esa caja) | premisa REFUTADA | 2 |
| F6-2 | ningún resultado publicado prueba los umbrales de detección | CONFIRMADO, con matiz | 2 |
| V3-1 | el popup dice «Distancia al cráter» y mide desde el centro del volcán (7,6 km en PCC) | propio de V3 | 2 |
| V3-2 | un fondo local también publicaría en 68 negativos limpios | propio de V3 | 2 |

Hallazgos de gravedad 1 y 2 sin verificar (F2-H3 a H9, F4-H2, H3, H5, H7, H8, F5-03 a 07, F6-3 a 8, F1-H4, H6, H8, H9):
en cada informe. F2 dejó además una tabla de 22 afirmaciones del proyecto contra el código y 10 pruebas de `tests/`
que fijan premisas que el código contradice (`experiments/_s158_audit/f2/INFORME.md` §3).

## 2. Lo que afirmé yo y cayó

| afirmación (S158) | quién la tumbó | estado |
|---|---|---|
| el control de Etna «prueba que el código publicado es el que corrió en producción» | F6, V1 | corregido: prueba cumbre, fondo y fórmula, no los umbrales ni lo que pasa sobre 50° |
| «el déficit grande es de nivel, no de pendiente; D17 cierra como mucho 23 %» | F3, V3 | rebajado: el estadístico S de dos tramos escondía la pendiente |
| «el halo lleva calor y D25 se lo come» | F3, F5 | refutado: los vecinos inmediatos están más fríos que el fondo interpolado |
| el A/B de D25 «en cola» | F5 | corregido: terminó con falla y le falta el 18-oct |

Las cuatro quedaron marcadas en sus documentos. La lección es la de siempre (A95, A111): las cuatro eran inferencias
mías que ningún instrumento había puesto a prueba.

## 3. Lo que quedó marcado en este PR (A113)

`docs/MISSION.md` (código como autoridad para VIIRS 750; cluster aggregation), `CLAUDE.md` (aviso del código; glosario
«cluster vs pixel»; A76), `docs/MIROVA_DIVERGENCES.md` (D16, D17, D22, D23, D25, D26, D29, D32, D1 «cluster
aggregation», D19 segundo pase, D34 nueva), `docs/SINTOMAS.md`, `docs/DATA_SOURCES.md`, `docs/_prompts/PREAMBULO-AUDITOR.md`,
`docs/audit_s139/BORRADOR_CORREO_COPPOLA.md`. **Pendiente**: el resto de la tabla de 22 afirmaciones de F2 y sus 10
pruebas; va a la segunda ronda (§6), que tiene que marcarlas con su propia verificación.

## 4. Decisiones para Nicolás

| # | decisión | recomendación |
|---|---|---|
| 1 | A/B de D25 (run 39530508296) | **no leer su veredicto**: reponer el 18-oct (y el 12 y 13), arreglar antes V2-1 y la métrica M; agregar un brazo con el fondo del código |
| 2 | V2-1 (cero gránulos = cobertura completa) | arreglarlo primero: que cero gránulos en un día con pasadas esperadas sea falla, no «completa». Toca `pipeline/fetch.py` y `scripts/run_pipeline.py` (A45) |
| 3 | el fondo del VRP | A/B pre-registrado con el fondo del código (`MIROVA_VIIRS750_VRP.m` l. 63 a 85) en VIIRS 750 y, trasladado y marcado como tal, en VIIRS 375; contando las dos caras (V3-2) |
| 4 | D1/D2 (segundo pase) | no condicionar con adyacencia; igualar los dos pases al código (sin compuerta de 3 K, sin piso de -0,1 en dETI, recalculando la regresión), en un solo brazo porque están acoplados (V1, V2) |
| 5 | umbrales de VIIRS 750 del código (K1 -0,7, mínimo de dNTI 0,02 fuera, 3 × 3 con central) | en el mismo A/B «detector del código» que la 4 |
| 6 | lo publicado (unión de alertas, modo de un píxel, inner de 20 km en PCC) | después de 3 a 5, con su A/B |
| 7 | D-10 (VIIRS diurno) | ya pendiente; el código trae la rama diurna (K1 -0,5, glint bajo 12°) y hay 3 protegidas perdidas |
| 8 | el popup «Distancia al cráter» (V3-1) | corregir el rótulo o el origen; cambio de tablero, bajo riesgo |
| 9 | la prueba sobre gránulos chilenos (oráculo sobre L1B reales de ~10 pasadas con alerta de MIROVA) | **hacerla**: es la única forma de saber si el fondo y el remuestreo cierran la brecha en Chile; despacha un workflow de sólo lectura |
| 10 | revisión tuya en el tablero y en los TIF | 3 a 5 casos (§5) |

## 5. Cola de pruebas

| prueba | qué decide | qué necesita |
|---|---|---|
| oráculo sobre L1B chilenos (VIIRS 750, ~10 pasadas con alerta de MIROVA, incluidas Tupungatito en 0 MW, Láscar 2026-10-08 05:42 y Cordón Caulle 2026-10-10 05:54) | si el fondo y la detección del código cierran la brecha en Chile; si sus umbrales coinciden con lo que MIROVA publicó | workflow de sólo lectura (tu sí) |
| segundo oráculo, escrito sin ver el primero | si el instrumento base es confiable | segunda ronda |
| revisión visual: Tupungatito VIIRS 750 en 0 MW, Etna (oráculo), Cordón Caulle a 9,9 a 19 km, una pasada sobre 50°, Chillán diurno | si lo que dicen los números se ve en la imagen | tus ojos, en el tablero y en los TIF |
| reproceso del 18-oct con el arreglo de V2-1 | completar el A/B de D25 | V2-1 arreglado |

## 6. Segunda ronda (aprobada por Nicolás, 2026-10-21)

En una sesión nueva, con contexto limpio y su propio worktree (requiere 24,8 GB libres en C:, que Nicolás está
liberando). No repite la primera: cambia el método. (1) Un segundo oráculo escrito sin ver el primero; (2) replicación
de los hallazgos de gravedad 3 o más con scripts nuevos y el otro modelo, recibiendo sólo la afirmación y su fuente; (3)
un meta-auditor de método (instrumentos que no podían fallar, propagación, lo que nadie miró: MODIS entero); (4) las
marcas A113 pendientes del §3, cada una verificada. El correo a Coppola **no** se envía todavía (Nicolás).

## 7. Lo que la auditoría no pudo medir

El efecto de cada umbral por píxel (los records no guardan dNTI); si el fondo interpolado da exceso positivo donde
nosotros damos 0 (falta el gránulo); la caja de MIROVA en cada volcán chileno; qué decide el factor 0,5 sobre 50° y si
corre en el NRT; los números de MODIS y VIIRS 375; el mínimo de dNTI de VIIRS 375.
