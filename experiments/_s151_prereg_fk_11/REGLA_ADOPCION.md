# Regla de adopción de K, escrita antes de evaluar V2

> **Estado: APROBADA por Nicolás el 2026-10-17** («Apruebo la regla de adopción de K del PR #848 tal como está,
> incluida la reversión con git revert pre-autorizada»), antes de cualquier evaluación de V2. El instrumento quedó
> fijado en `2766c198` (merge de #847, §3). Desde aquí la regla no se cambia; si un resultado la pone en duda, la
> duda se escribe y decide Nicolás.
>
> Versión 2, S153, 2026-10-17. La versión 1 la revisó un verificador con
> contexto limpio («aprobable con arreglos», `C:\Users\nmend\AppData\Local\Temp\claude\verif_regla_fk\VERIFICADOR.md`,
> sin versionar); la 2 aplica sus diez arreglos (§8). Se escribe **antes** de correr `evaluar_fk.py` sobre V2: al
> escribirla, V2a está unida y pareja pero sin evaluar, y V2b quedó despareja y se está repitiendo (run 39068999603).
> Nadie ha visto un veredicto de V2. **Lo que prueba la fecha es la hora del PR en GitHub**, que tiene que ser anterior
> a la primera evaluación de V2; la hora del commit local no cuenta.
>
> **Qué es este documento respecto del pre-registro.** No cambia ninguna regla de `PREREGISTRO.md` (sellado): el
> veredicto de cada ventana sale de ahí, tal cual. Este documento **agrega** lo que el pre-registro deja fuera a
> propósito (§1 y §8 del pre-registro: «no adopta»): qué se hace con cada veredicto. Algunas condiciones que agrega son
> más estrictas que el pre-registro (Tupungatito, SN, cruce de 1 MW, P4); ninguna es más laxa salvo el rescate por
> error de referencia, que queda acotado a clases ya escritas (§3).

## 1. Por qué hace falta

El pre-registro dice dos veces que no adopta nada. Sin una regla escrita antes, el resultado de V2 se interpretaría
después de verlo, y la pregunta «¿adoptamos?» quedaría abierta a lo que el número sugiera en el momento (A95, A111).
Desde el 2026-09-01 no ha cambiado ningún flag de `pipeline/profiles/mirova_equivalent.yaml`, y la conectiva `max` se
mide desde #621 (2026-09-09): lo que falta no es otra medición sino la decisión.

**Lo que está en juego, en el volcán.** De noche, con un fondo frío y ruidoso al borde del barrido, producción suma el
exceso de infrarrojo medio de todo un disco alrededor del cráter (el Test 1 integrado, que no está en el paper, D30) y
acepta un píxel por el camino más fácil de los dos que pide Coppola 2016a (`min`). Con eso publica en **734 de 832
pasadas** de VIIRS 375 en que MIROVA miró y no vio nada (V1, `resultado_v1/v1.log`, sección 9). K quita el Test 1,
exige los dos caminos (`max`) y en MODIS lee la banda 22, como pide el paper (D21). En V1, K calla en 811 de esas 832
pasadas y no pierde ninguna alerta protegida que decida con la lectura A. Su costo conocido: 21 alertas de VIIRS 375
(19 bajo 1 MW, 11 de 0,05 MW o menos; 16 de las 194 Muy Bajo, `v1.log:90`) y una magnitud de VIIRS 375 más baja en las
pasadas que cambian (§5).

**Información previa, declarada.** Antes de V2 ya se sabía mucho de `max`: S149 y S150 (contra el brazo B, sin Test 1)
y Chillán en erupción (#796). Esta regla no la usa para decidir; la nombra para que nadie lea V2 como la primera
evidencia.

**Poder del veto, repetido del pre-registro (`PREREGISTRO.md:82-87`).** El veto con poder es de Láscar en V2 (36 de 38
protegidas que deciden en VIIRS 375) y de Chillán en erupción en V1 (10 de 12). Un CUMPLE combinado **no dice nada de
los otros nueve volcanes**: por eso existe la sombra (§4.7).

## 2. Qué se adopta: K entera, nada más chico

Los tres flags de K son globales (`pipeline/profile.py:175`, `:636`, `:726`, leídos en los tres procesadores):
`enable_test1_path: false` y `enable_tests_23_prose_branch: true`, los dos **bajo `paths:`** (los lee `_p`,
`profile.py:131`; A89), y `enable_modis_b22_primary: true`. F sola no es adoptable: sin `max`, la banda 21 dejó al brazo
B en 0 de 73 alertas de Láscar (S150), y K es justamente F más la banda 22 (S147). Tampoco se adopta por volcán ni por
régimen (`docs/MISSION.md:140`; la cita «MISSION l. 77» de A85 quedó corrida). Si K falla sólo por MODIS, separar los
flags por sensor es código nuevo en `pipeline/` (A45) y un pre-registro nuevo, no una variante de esta regla.

## 3. Qué se hace con cada veredicto

**Instrumento fijado.** V2 se evalúa, y V1 se re-une y re-evalúa, con `evaluar_fk.py` y `unir_intentos.py` del commit
de `main` en que se mergee el PR #847 (que endurece la regla `borde` de `comparar()`). Ese commit se anota en la
bitácora antes de la primera evaluación de V2. Si V1 re-evaluada no da lo mismo que antes, se informa antes de mirar V2.

**Qué decide.** El veredicto **combinado** (`evaluar_fk.py --combinar`, el peor de V1 y V2) de **K**, con la **lectura
A** (D-4), calculado **dos veces**: con la regla original de alertas mínimas, que es la que sella el pre-registro, y con
la regla SN de D-9, que es la de MISSION. **Si discrepan, manda la más estricta** (la que dé el peor veredicto). La
lectura B se informa y no decide. Además se lee la lista **por ventana** que imprime `--combinar`, no sólo la línea del
peor, porque el empate de gravedad pierde anotaciones («veto sin sustrato», «auditoría espacial pendiente»).

| veredicto combinado de K | qué se hace |
|---|---|
| **CUMPLE** | se abre el ciclo de adopción (§4) |
| **CUMPLE EN DETECCIÓN, FALLA EN MAGNITUD** | se abre el mismo ciclo (§4); la magnitud se trata como dice §5 |
| **PENDIENTE DE REPETICIÓN** o **INDECIDIBLE** | se resuelve con la repetición de §5 del pre-registro y se vuelve a evaluar. **Tope: dos repeticiones** por ventana. Un INDECIDIBLE de controles (referencia, cableado, determinismo) no se repite: se busca el defecto. Si tras dos repeticiones sigue sin resolverse, K queda **sin decidir** y la decisión pasa a Nicolás con la evidencia; no hay adopción por defecto |
| **NO CUMPLE (veto)** | no se adopta. Cada pérdida neta se diagnostica (cabecera de la imagen de MIROVA por Mirova-v1#20, auditoría espacial A61, distancia). **Rescate acotado:** sólo si la pérdida cae en una clase de error de la referencia **ya escrita** en `scripts/calidad_referencia_mirova.py` en el commit de esta regla; entonces esa clase se corrige en **toda** la ventana, en **todos** los brazos y en **todas** las etiquetas (también negativos), y se re-evalúa una sola vez. Una clase nueva, descubierta después de ver la pérdida, no rescata nada. Si la pérdida es una pasada donde C0 publicaba **otro objeto** que el de MIROVA (patrón S150), se lista y decide Nicolás |
| **NO CUMPLE (suma)** o **no gana en ningún sensor** | no se adopta |

**P4 (el cúmulo se mueve).** Con P4 FALLA en cualquier ventana o sensor, la auditoría espacial A61 de **todas** las
pasadas movidas va antes del §4, como sella el pre-registro (`PREREGISTRO.md:210`). Con «veto sin sustrato» en algún
sensor, el paquete lo dice en la primera línea.

**Las 2 protegidas de Tupungatito que descansan sólo en el OCR de Suomi NPP (V1).** Se juzgan en el marco de la propia
lectura A: ¿con su **distancia propia** (la de su imagen, no la de otra pasada), el scraper la habría clasificado
ALERTA? La revisión de cabeceras ya está hecha (`resultado_v1/CABECERAS_SNPP.md`: 11 de 11 imágenes de otra pasada;
«con la clase propia no serían protegidas A»), pero leída a ojo. La distancia de MIROVA en Tupungatito se mide desde su
punto de referencia, a 4,87 km del cráter activo (`volcanoes.yaml:807-808`), así que **no se compara con el
`inner_radius_km` del cráter**. Antes del §4, un segundo lector confirma esa lectura. Si alguna resulta ALERTA con su
distancia propia, cuenta como **pérdida neta** y K queda vetada. Si alguna queda indeterminada, decide Nicolás con la
evidencia, y el paquete lo dice.

## 4. El ciclo de adopción, en orden (sólo si §3 lo abre)

1. **Verificador con contexto limpio** sobre el resultado combinado (ya lo exige el pre-registro).
2. **V2 informado también con `--solo-tabla no`.** En V2 las alertas que sólo trae el OCR son invisibles para el
   evaluador (`evaluar_fk.py:115-118`), y son 20 a 39 % de las alertas de VIIRS 375 de marzo a agosto (A119 a). Se
   listan las protegidas sólo OCR que K pierde. No deciden, pero se miran.
3. **Recuento independiente (R3 y R6, `docs/PROCESS_RULES_S33.md`).** La mejora es mayor a 30 %, así que se exige un
   segundo instrumento: un script nuevo, escrito por quien no escribió `evaluar_fk.py`, que no importe `evaluar_fk`,
   `banco_paridad` ni `clase_mirova`, y que reproduzca desde los JSON y la referencia congelada **la lista de P1, las
   sumas de P2** y la tabla de la sección 9, de C0 y K, por sensor y ventana. Tiene que dar los **mismos conteos**.
   Cualquier diferencia detiene el ciclo hasta encontrar cuál de los dos está mal.
4. **R2 adaptado: cinco pasadas mirando lo que MIROVA publicó.** Dos negativos limpios de VIIRS 375 en que C0 publica y K
   calla (uno al borde del barrido con fondo frío, uno en nadir), una protegida de VIIRS 375 de Láscar, una alerta MODIS
   que K recupera con la banda 22 y una alerta donde el cúmulo se movió más de 0,5 km (P4). Se eligen entre mayo y el
   2026-09-22, porque desde esa fecha los GeoTIFF de MIROVA están congelados (A106: GeoTIFF UTM sólo el 14 y 15 de
   septiembre; si no, GeoTIFF geográfico con la hora de adquisición leída del archivo). **Criterio de salida:** en cada
   pasada, la decisión de K (publica o calla) coincide con la de MIROVA y, si publica, su píxel cae en el área caliente
   de la imagen de MIROVA. **Una discrepancia** se explica por escrito antes de seguir; **dos detienen** el ciclo y
   decide Nicolás. Si no hay imagen para alguno de los cinco casos, se dice y Nicolás decide si sigue sin él.
5. **K sobre el `main` de hoy.** V1 y V2 corrieron sobre `402447f3` y `7b74435e`; después entraron #785, #821, #822 y
   #844 (desempate del top-100 MODIS, que toca la misma selección que la banda 22 cambia). Una corrida corta de K sobre
   `main` contra K del tag, mismos gránulos (tres días de Láscar y tres de Chillán, los tres sensores), tiene que dar
   la misma decisión de publicar en cada pasada, salvo las que el desempate de #844 explique una por una.
6. **Diseño y pre-mortem (R4, R5).** Este documento es el documento de diseño que pide R5 (brainstorming antes de un
   cambio metodológico). El pre-mortem va en el PR. Borrador: si la adopción está mal, lo veríamos como (a) una alerta
   que MIROVA publica, la sombra publica y producción calla; (b) la publicación de VIIRS 375 en negativos limpios
   subiendo muy por sobre lo medido. El peor caso es un **evento incipiente de baja energía** en un nevado (fase efusiva
   que empieza) que sólo el Test 1 veía: vive bajo 1 MW, y por eso la sombra vigila también las Muy Bajo (paso 9).
7. **Tag defensivo** `pre-s153-adopcion-k` en el commit de `main` previo, empujado (A38, A45).
8. **PR de adopción, con esta lista completa:**
   - los tres flags en `mirova_equivalent.yaml` (dos bajo `paths:`) y un guard que los fije;
   - los dos tests que hoy fijan el valor viejo: `tests/test_gr2_profile_invariants.py:96` (`ENABLE_TEST1_PATH: True`)
     y `tests/test_experimental_congelado_s150.py::test_el_laboratorio_hoy_es_igual_a_produccion_salvo_nombre`, que
     según su docstring cae a propósito el día que la réplica cambie: se actualizan diciendo por qué;
   - **el laboratorio no se toca**: `pipeline/profiles/experimental.yaml` quedó congelado en C0 por decisión de Nicolás
     (S150, #771), con los tres flags escritos (`experimental.yaml:71-76`) y su guard. Sigue siendo el centinela de la
     señal débil que la réplica deja de publicar, y es la sombra del paso 9;
   - el auto-audit: `RECALL_MIN` (`scripts/auto_audit_weekly.py:117`) y la banda de magnitud [0,7; 1,4] (`:132`) están
     calibrados sobre C0. **Se decide en el PR, con los números de V1 y V2, si se recalibran o se acepta que salten**,
     para que nadie los «arregle» después de ver el issue;
   - la publicación en negativos limpios por sensor entra a `data/audit_continuous/history.jsonl` (hoy sólo se calcula,
     `:200` y `:543`), sin alarma salvo que Nicolás diga otra cosa (decisión S140);
   - la ficha `docs/FICHA_SDA_VRP_CHILE.md` (obligación de transparencia algorítmica: cambia el detector de un SDA en
     producción) y las marcas A113 en `docs/MIROVA_DIVERGENCES.md` (D21, D30, conectiva), `docs/MISSION.md` y el
     `CLAUDE.md` del proyecto, donde el Test 1 aparece como parte del detector;
   - **una marca visible de la fecha del cambio en las tres vistas** (`index.html`, `diario.html`, `mosaico.html`): con
     K la publicación de VIIRS 375 cae y su magnitud baja; con Chillán en erupción, ese escalón en la tendencia de 90
     días de `diario.html` se leería como «la erupción declina»;
   - el aviso a los consumidores: OVDAS y Integracion_Plataformas (`MAPA_WORKSPACE.md`);
   - **el sí explícito de Nicolás** antes del merge (A45), que incluye la pre-autorización de la reversión del paso 9.
9. ⚠️ **Lectura decidida el 2026-10-19 (S156), viendo un caso concreto.** La primera corrida de la vigilancia
   (`scripts/vigilancia_sombra.py`) encontró una protegida A que la sombra publica y producción calla, confirmada en la
   cabecera: Puyehue-Cordón Caulle, VIIRS 750 (NOAA-21), 2026-10-10 05:54 UTC, 1,19 MW; mismo objeto que MIROVA
   (auditoría espacial A61) y misma pasada publicada por K en VIIRS 375. Es dato reprocesado con K, anterior a la
   adopción y fuera de las ventanas del A/B. La regla no decía desde cuándo cuenta la vigilancia. Nicolás eligió («lo
   que recomiendes», ante la recomendación B de la sesión): (a) **la unidad es la pasada**, como en el veto P1 del A/B;
   no se reinterpreta a noche; (b) **la vigilancia del paso 9 cuenta desde la adopción** (`CAMBIO_DETECTOR_UTC`,
   2026-10-18 09:57:30 UTC): sólo lo posterior dispara reversión o investigación y suma a la duración. Lo anterior
   (datos K reprocesados) se informa como **retrospectivo**, no dispara, y una pérdida retrospectiva va a investigación
   con un issue que se abre a mano (el retrospectivo es fijo: la sombra existe desde el 2026-10-02 y no crece hacia
   atrás, así que no hace falta automatizarlo). El caso de PCC es el primero de esa clase. El corte es al segundo. Esta lectura se tomó **después** de ver el caso, y quien la
   revise debe leerla así. Nota de implementación (no es decisión): la cota de (i) que la regla cita (V1, 16 de 194) es
   de VIIRS 375, donde C0 no perdió ninguna Muy Bajo, así que es la pérdida diferencial; en MODIS y VIIRS 750 el A/B no
   guardó el diferencial por pasada y (i) se informa sin disparar. Evidencia: `experiments/_s156_autoaudit/sombra/`.
   **Dos decisiones más de Nicolás el mismo día**, ante los verificadores 2 y 3 (elegidas entre opciones, con la
   recomendación de la sesión): (c) **(i) coherente con D-9**: las mínimas (0,05 MW o menos, NONE en el banner) no
   cuentan, y la cota es la del A/B medida con la regla SE: 7 de 161 en V1 y 12 de 343 en V2, derivadas de
   `experiments/_s153_fk_v2/v1.json` y `v2.json` (`reglas_d9.SE`; el denominador exacto no quedó guardado y se tomó el
   menor posible, que da la cota más alta). La cita «(V1: 16 de 194)» de abajo es la de la etiqueta original, que
   contaba 9 mínimas; (d) **las pasadas ya juzgadas** se anotan en `sombra_pasadas_juzgadas.json` (junto a esta regla)
   y no vuelven a disparar; (e) **cumplido el plazo** (29 protegidas o 120 días), una candidata se sigue informando pero
   ya no está pre-autorizada: decide Nicolás. Notas de implementación (verificador 4, no son decisiones nuevas): el
   plazo se mide pasada por pasada (dentro si es una de las primeras 29 protegidas vistas, la 29.ª incluida, y anterior
   al vencimiento), que es la letra «hasta ver 29»; y una pasada juzgada sale sólo de la reversión, porque lo juzgado
   fue si revertir, no lo que vio la sombra. Texto original conservado:

   **Sombra: el laboratorio congelado en C0.** `experimental-diario.yml` ya corre a diario los 11 Tier A con C0
   (`experimental_v2`). Cada semana se cuentan contra MIROVA producción (K) y sombra (C0) con el mismo evaluador.
   - **Duración por protegidas, no por días:** hasta ver **29 protegidas A nocturnas** en la sombra, o 120 días, lo que
     ocurra primero. Con 29, una pérdida de una de cada diez protegidas se vería con 95 % de probabilidad
     (1 − 0,9^29 = 0,95). Si se cumplen los 120 días sin llegar a 29, se dice cuántas hubo y qué pérdida puede haberse
     escapado.
   - **Reversión inmediata, pre-autorizada:** una protegida A (con SN), que MIROVA publica, la sombra publica y
     producción calla, confirmada en la cabecera de la imagen. Se ejecuta con `git revert` del PR de adopción (no con un
     reset), la hace la sesión que la detecte, abre un issue y avisa a Nicolás el mismo día.
   - **Investigación (sin reversión automática):** (i) alertas **Muy Bajo** que MIROVA publica, la sombra publica y
     producción calla: si la cota inferior de Wilson de su tasa, por volcán, supera la cota superior medida en el A/B
     (V1: 16 de 194); (ii) **persistencia**: tres noches seguidas en un mismo volcán con una alerta de MIROVA que la
     sombra publica y producción no; (iii) publicación de VIIRS 375 en negativos limpios: si su cota inferior de Wilson
     en la ventana supera la cota superior del A/B (V1: 21 de 832, [0,0166; 0,0383]; se usa la mayor de V1 y V2).
10. **Tablero y datos.** La marca de régimen (#785) separa los records nuevos de los viejos. Se reprocesa con K la
    ventana que el tablero muestra por defecto (`index.html:877`, 30 días), partida para que cada job quepa en el tope
    con el margen de A15; el resto de la historia queda con su marca. Toda comparación con MIROVA que cruce la fecha de
    adopción se estratifica por régimen (como con #535, A104). Al terminar, R8 sobre la URL pública.

## 5. La magnitud: lo que P3 no ve y cómo entra en la decisión

P3 está anulado por construcción en VIIRS 375: más de la mitad de los pares no cambia, la mediana de d es 0 y su
intervalo no puede quedar sobre 0 (verificador de V1, §4). En V1, sobre los 239 pares, la media de d es +0,048
[+0,026; +0,074]; en los 115 pares que sí cambian, F queda bajo C0 en 98 (mediana de log10(F/C0) = −0,142, unos 28 %
menos) y la prueba de signos da p = 0,00035: **sin el Test 1 la magnitud de VIIRS 375 se aleja de la de MIROVA, de forma
significativa.** La razón mediana pasa de 0,748 (dentro de la banda [0,7; 1,4] del auto-audit) a 0,620 (fuera).

El paquete informa sobre V1 y V2, por sensor: la media de d con su intervalo y la prueba de signos sobre los pares que
cambian, y **el número de alertas publicadas que cruzan 1 MW** entre C0 y K (en las dos direcciones). Eso es lo que el
operador vive: una alerta de 1,2 MW que pasa a leerse 0,86 MW cambia de Bajo a Muy Bajo. En MODIS importa en especial,
porque la banda 22 cambia la radiancia de la que sale el VRP.

**Regla por defecto:** si P1 y P2 de K cumplen y **ninguna protegida que C0 muestra sobre 1 MW queda bajo 1 MW con K**,
la magnitud **no bloquea** la adopción: el criterio de victoria (`docs/MISSION.md`) se define sobre alertas, y la palanca
medida que más sube la magnitud es D25 (×1,28, tarea 1.14), cuyo cierre quedó condicionado a la detección que se adopte
(tarea 1.5), así que se re-pre-registra sobre K como siguiente A/B. **Si alguna protegida cruza hacia abajo, decide
Nicolás** con la lista. Nicolás puede cambiar esta regla por defecto antes de que se evalúe V2; después, no.

## 6. Lo que esta regla no decide

- El diurno (D-10), MxD03 (1.23), la caja, `vrp_max`: siguen su propio pre-registro.
- La lectura B: se informa; decidió D-4 (A).
- El perfil experimental: queda congelado en C0 (S150) y hace de sombra; su diferenciación futura es otro diseño
  (`docs/DISENO_SENSIBILIDAD_POR_ZONA_S147.md`).

## 7. Calendario esperado (sin garantía)

V2b se repite y se une; con #847 mergeado se fija el instrumento, se re-evalúa V1 y se evalúa V2, con su verificador.
Si sale CUMPLE, los pasos 2 a 8 del §4 toman uno a dos días de trabajo; el paso 4 depende de encontrar imágenes de
MIROVA. El merge espera el sí de Nicolás.

## 8. Qué cambió de la versión 1 a la 2 (verificador con contexto limpio)

| arreglo | cambio |
|---|---|
| 1. el laboratorio no hereda K | §4.8 y §4.9: queda congelado en C0 y es la sombra |
| 2. la sombra no veía lo débil | §4.9: disparadores sobre Muy Bajo y persistencia; duración por protegidas |
| 3. magnitud «fuera de banda» y sin tope | §5: 0,748 está dentro de la banda; tope = ninguna protegida cruza 1 MW hacia abajo |
| 4. rescate sin acotar | §3: sólo clases ya escritas, simétrico en brazos y etiquetas |
| 5. P4 y «veto sin sustrato» | §3: A61 antes del §4; leer la lista por ventana de `--combinar` |
| 6. Tupungatito en dos marcos | §3: marco de la lectura A, distancia desde la referencia de MIROVA, segundo lector, indeterminada a Nicolás |
| 7. SN, tope de repeticiones, instrumento | §3: manda la más estricta; dos repeticiones; commit de #847 |
| 8. R2 sin salida, R5, reversión | §4.4, §4.6, §4.9 |
| 9. lista del PR | §4.2, §4.5 y §4.8 |
| 10. menores | pasadas y no noches; media de d sobre 239; el 0 de 73 es de B; encabezado «agrega» |
