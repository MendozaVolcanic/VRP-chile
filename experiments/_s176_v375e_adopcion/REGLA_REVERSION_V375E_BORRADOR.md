# Regla de adopción y reversión de la vía «código MIROVA» en VIIRS 375 y VIIRS 750

**BORRADOR, SIN SELLO.** Escrito el 2026-11-08 en el PR A del encendido (S176, diseño
`docs/superpowers/specs/2026-11-08-encendido-v375e-design.md`, decisiones 3 y 7), para la frase de sello de Nicolás. Modelo: la regla sellada de
MODIS, `experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md`, y la adopción de K, `experiments/_s151_prereg_fk_11/REGLA_ADOPCION.md` paso 9.
Se cambia lo que VIIRS pide y nada más; donde VIIRS se aparta de MODIS, se dice.

- **Cómo se sella**: Nicolás contesta las decisiones D1 a D7 de abajo, un verificador limpio de otro modelo lee esta versión y Nicolás da la frase de sello. El encendido de cada sensor (B1, B2) pide además su tag defensivo y su sí de A45 (frases distintas).
- **Una regla, dos encendidos.** VIIRS 375 (PR B1) y VIIRS 750 (PR B2) se encienden, se vigilan y se revierten por separado. Lo que aquí se dice vale para cada sensor con sus propios números; una alerta callada en un sensor nunca pide revertir el otro.
- **Mientras no se selle**, las cotas de `COTAS` en `scripts/vigilancia_guardia_viirs.py` valen `None`: se cuentan y se informan sin disparar.

## Decisiones de Nicolás antes del sello

Cada una se contesta con una palabra. La recomendación y el número que la sostiene salen de archivos citados.

| # | Pregunta | Recomendación | Número que la sostiene | Dónde rige |
|---|---|---|---|---|
| D1 | ¿Aceptas las cotas de investigación de VIIRS 375: Muy Bajo perdidas **más de 14** y sobre-publicación diferencial **más de 17** en los 120 días? | **Contestada: «C-rad (14/17)»** (Nicolás, 2026-11-10, S178) | S178 (P10): ventana O más F26-V de la prueba retrospectiva, sumada **por pasada** y con F26-V en el brazo **radiante** (el que cuenta `scripts/vigilancia_guardia_viirs.py`): se esperarían 9,48 y 11,82 en 120 días; falsa alarma 5,9 % y 5,6 %. `experiments/_s178_cotas_v375/cotas_v375_con_retro_salida.txt` (opción C-rad), verificador limpio de las opciones en la bitácora S178 de loop/activo. Texto anterior (A113): «más de 14» y «más de 15», de la ventana O sola, fila conservada abajo. | §4.4 |
| D1 (anterior a S178) | ¿Aceptas las cotas de investigación de VIIRS 375: Muy Bajo perdidas **más de 14** y sobre-publicación diferencial **más de 15** en los 120 días? | Sí | Retrospectiva V375-B y V375-C, brazo C13, NOAA-20 y NOAA-21 en la ventana O: se esperarían 9,4 y 10,1 en 120 días; falsa alarma 5,8 % y 5,0 %. `cotas_retrospectiva_v375_salida.txt` | §4.4 |
| D2 | ¿Aceptas las cotas de investigación de VIIRS 750: Muy Bajo perdidas **más de 12** y sobre-publicación diferencial **más de 2** en los 120 días? | Sí | Lectura de V750-B, brazo B4 (la ROI que la vía usa), sin Suomi NPP: se esperarían 7,6 y 0,8 en 120 días; falsa alarma 4,5 % y 5,3 %. `cotas_retrospectiva_v750_salida.txt` | §4.4 |
| D3 | ¿Aceptas 29 protegidas o 120 días por sensor como plazo? | Sí | La misma potencia de K y MODIS: con 29, una pérdida de una de cada diez se ve con 95 % (1 menos 0,9 elevado a 29 = 0,953) | §4.6 |
| D4 | ¿Aceptas 24 h de espera antes de leer como silencio una protegida sin record de producción? | Sí | La misma de MODIS (D3 de esa regla). El NRT corre cada 2 h y LANCE tarda unas 3 h; es lo que ya usa `ESPERA_SIN_RECORD_H` | §4.4 (a) |
| D5 | ¿Aceptas que la lectura sellada de V375-E (tag `s172-v375e-lector-resellado`) y la de V750-A (#964) dejen de decidir el encendido y queden informativas? | Sí | Es la decisión 6 y 7 del diseño. Pasó igual con la sombra de 28 noches de MODIS. Los lectores se conservan y se corren | §2 |
| D6 | ¿Aceptas revertir sin la imagen de MIROVA cuando la protegida viene de la tabla y la imagen no está disponible el mismo día? | Sí | La misma de MODIS (D6 de esa regla). Si la protegida es sólo del OCR y no hay imagen, decide Nicolás | §4.3 |
| D7 | ¿Aceptas el paso del día después (§4.7): apartar los records de la vía y reponerlos con K en un PR aparte, con tag defensivo? | Sí | La misma de MODIS (D7 de esa regla) | §4.7 |

## 1. Por qué, como geólogo

MIROVA suma la energía de todos los píxeles que alerta. VIIRS 375 de producción publica el núcleo de un cúmulo que K ya recortó, con un fondo de anillo propio: el volcán se ve con cerca de la mitad de la potencia que MIROVA le asigna, y el tablero sub-informa una anomalía real. En VIIRS 750, K publica 0,510 de MIROVA en la retrospectiva y el código de MIROVA 0,999 sobre la misma grilla (`experiments/_s162_v750c/INFORME.md`, punto 3). La vía corre el código publicado por MIROVA sobre su misma grilla y casi calza.

El costo que se acepta es que la vía puede callar señales débiles que K publica. Un foco incipiente, sub-píxel, al empezar una fase efusiva, puede ser justamente lo que se calle. Por eso K sigue corriendo aparte como guardia, y por eso esta regla se escribe antes del encendido.

## 2. Qué se enciende

- **B1**: `enable_v375_codigo_mirova: true` en `pipeline/profiles/mirova_equivalent.yaml` (`pipeline/process_viirs.py`).
- **B2**: `enable_v750_codigo_mirova: true` en el mismo perfil (`pipeline/process_viirs_mod.py`). Condición propia de B2 (decisión 7): vara MATLAB del §4.1 en verde (`experiments/_s162_v750a/vara_matlab_v750a.py`); hoy con Octave da roja por una decisión ya tomada (S163). Es lo que prueba que el código portado es el de MIROVA.
- Los dos flags tocan `mirova_equivalent.yaml`, dentro del congelamiento del §12.6 del programa: cada uno pide su excepción, como MODIS.
- La lectura sellada de V375-E y la de V750-A dejan de decidir (D5).

## 3. La guardia

- **Perfil**: `pipeline/profiles/guardia_k_viirs.yaml`: `extends: mirova_equivalent`, las vías de los dos VIIRS apagadas, sólo los dos VIIRS, carpeta `data/guardia_k_viirs/` (A47).
- **Workflow**: `.github/workflows/guardia-k-viirs.yml`, una vez al día a las 19:35 UTC, sobre las mismas 8 fechas que el NRT, con el mismo techo de 75 min por paso que la guardia de MODIS. Antes de correr, afirma por `pipeline.profile` que es K pura y sólo VIIRS; sólo `EARTHDATA_TOKEN` (A71). Revisión propia, `scripts/revisar_guardia_viirs.py`, que exige cada VIIRS por separado: una guardia que deja de escribir un sensor deja ese sensor sin vigilar.
- **Vigilancia**: `scripts/vigilancia_guardia_viirs.py --sensor v375|v750`, corrida por `.github/workflows/vigilancia-guardia-viirs.yml` al terminar la guardia, con respaldo a las 22:55 UTC. Escribe `data/audit_continuous/guardia_v375_latest.json` (o `v750`) y abre issues; **no revierte**.
- **El nulo.** Mientras B1 y B2 no entren, guardia y producción son el mismo detector y tienen que publicar lo mismo en los dos VIIRS. Ese es el nulo medido de la guardia (A110): **al menos tres noches** antes de pedir cada B.

## 4. Reversión e investigación

### 4.1 Desde cuándo cuenta

- **Encendido** de cada sensor = el menor `processed_utc` de un record de producción de ese sensor con `via_codigo_mirova: true`, como lo publica `encendido_utc` en la salida de la vigilancia. Sale de los datos.
- La primera **observación** con record de la vía puede ser anterior al encendido (producto estándar re-escrito, marca A113 de la regla de MODIS): esa franja es retrospectiva y no dispara la reversión; una protegida de esa franja que la guardia publica y producción, ya con record de la vía, calla, se investiga (`borde_del_encendido`).
- El plazo de §4.6 cuenta desde el encendido así definido.

### 4.2 Unidad: la pasada nocturna

La unidad es la pasada nocturna. **Protegida** = alerta de MIROVA del sensor de 1 MW o más (lectura A, D-4). D-9 sí aplica a VIIRS 375: una alerta de 0,05 MW o menos es «MIROVA no vio nada» y no cuenta como alerta. N-3 (las protegidas sólo OCR de Suomi NPP anteriores al 2026-10-09) no aplica: la ventana empieza después del cese de Suomi NPP. Las alertas diurnas de MIROVA no entran a esta regla (S177, VPR967-05 (d)): ni la vía ni K procesan esas pasadas; el verificador de la medición contó, entre el 2026-11-03 y el 11-07, 10 alertas diurnas de Chillán de 1 MW o más: 4 de VIIRS 375, 4 de VIIRS 750 y 2 de MODIS.

### 4.3 Reversión inmediata, pre-autorizada

- **Disparador**: una pasada nocturna posterior al encendido de ese sensor, dentro del plazo de §4.6, con una protegida que MIROVA publica, la guardia K publica y producción (la vía) **tiene record y no publica**. La vigilancia la informa como `REVERSION_CANDIDATA` y abre el issue «Guardia K de VIIRS 375: candidata a reversion» (o «VIIRS 750»).
- **Quién y cuándo**: la sesión que lee el issue, el mismo día UTC.
- **Confirmación**: la cabecera de la imagen de MIROVA de esa pasada. Si la muestra, revierte. Si no está disponible ese día, según D6 revierte igual cuando la protegida viene de la tabla, y deja la decisión a Nicolás cuando es sólo del OCR. Si la imagen la contradice, no revierte, la anota como juzgada y avisa.
- **De dónde sale la procedencia para D6 (S177, VPR967-05 (b)).** La vigilancia no publica si la protegida viene de la tabla o del OCR. La sesión la mira a mano: busca la pasada (volcán, sensor, minuto de `Fecha_Satelite_UTC`) en `monitoreo_satelital/registro_vrp_consolidado.csv` del repo `MendozaVolcanic/Mirova-v1` (la tabla, `latest.php`). Si está ahí con 1 MW o más, viene de la tabla; si sólo está en `registro_vrp_ocr.csv`, es sólo del OCR. Ojo con las variantes de nombre del scraper (A14).
- **Cómo**: `git revert -m 1` del commit de merge del PR de **ese sensor**, nunca un reset. Cada B entra por merge commit, después de A y por separado. Comprobación: `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; print(p.ENABLE_V375_CODIGO_MIROVA, p.ENABLE_V750_CODIGO_MIROVA)"` debe dar `False` en el sensor revertido (A89). Si el revert choca, se resuelve a mano dejando ese flag en `false`, sin esperar a nadie.
- **Después**: issue de la reversión, aviso a Nicolás el mismo día, la pasada en `experiments/_s176_v375e_adopcion/sombra_pasadas_juzgadas_viirs.json` y el paso del día después (§4.7).

### 4.4 Investigación, sin reversión automática

Cada una abre el issue «Guardia K de VIIRS 375: investigar» (o «VIIRS 750»). Investigar es mirar y decidir, no revertir.

- **(a) Protegida sin record de producción**, pasadas 24 h (D4). No es «calla»: es la vía que no escribió.
- **(b) Borde del encendido**: §4.1.
- **(c) Nulo de la guardia**: antes del encendido, cualquier pasada que guardia y producción publiquen distinto (A110).
- **Caída a K**: si el record de producción de una protegida que la guardia publica no es de la vía (la vía cayó a K, `sin_grilla`), se investiga; **nunca es candidata a reversión**, porque compara K con K.
- **(i) Muy Bajo.** Alertas de MIROVA sobre 0,05 MW y bajo 1 MW que la guardia publica y la vía calla, contadas en el plazo, sólo en pasadas con record de la vía en los dos lados. Investiga con **más de** la cota del sensor (tabla de abajo). Se informa siempre con su denominador (`muy_bajo.n`).
- **(ii) Sobre-publicación diferencial.** Pasadas de negativo limpio en que la vía publica y la guardia, que procesó la misma pasada, no. Investiga con **más de** la cota del sensor (tabla de abajo), con su denominador (`sobrepublicacion.n`).
- **(iii) Pasadas que la guardia registra y la vía no**, por semana ISO. Se informa y no dispara: no hay vara citable para ese número y A115 prohíbe inventarla.
- **Región sensible de VIIRS 750 (informa).** En Cordón Caulle y Tupungatito la región sensible corre desde #939 con pocas pasadas, y en Cordón Caulle la sombra publicó 1 vez contra 4 de producción sin saberse si esas 3 son sobre-publicación de K. La vigilancia cuenta las pasadas que publica cada lado (`region_sensible`). No dispara: no hay cota citable y la diferencia puede ser un acierto.
- **Vigilancia ciega.** Un VERDE con avisos no es VERDE: guardia o producción sin datos frescos de ese sensor en algún volcán (más de 3 días), referencia de MIROVA detenida o sin filas del sensor, nulo sin pares, guardia con records de la vía, perfiles cruzados, flag encendido sin records de la vía, vía detenida en un volcán, o una cota de §4.4 aún PENDIENTE con la vía encendida.

**Cotas de la investigación.** Método, el mismo con que Nicolás fijó las de MODIS (D1 y D2 de esa regla): la tasa de discordancias de la retrospectiva se lleva a los 120 días del plazo y la cota es el primer entero con falsa alarma de 8 % o menos si la vía rinde como en la retrospectiva (Poisson). **Las cotas se miden sobre datos anteriores a la ventana de noviembre**, nunca sobre los 5 días ya mirados (A115).

| Sensor | (i) Muy Bajo perdidas | (ii) Sobre-publicación diferencial | Fuente (anterior a noviembre) |
|---|---|---|---|
| VIIRS 375 (S178, D1 contestada) | **más de 14** (O ponderado más F26-V radiante 3 de 139, por pasada; se esperan 9,48 en 120 días) | **más de 17** (O ponderado más F26-V 5 de 528, por pasada; se esperan 11,82) | `experiments/_s178_cotas_v375/cotas_v375_con_retro.py`, opción C-rad: reusa `cotas_retrospectiva_v375.py` sin cambiarlo y suma por pasada porque en F26-V la tabla de MIROVA no trae NOAA-21 (antes del 2026-04-09) y sumar por día mezcla exposiciones |
| VIIRS 375 (anterior a S178, A113) | **más de 14** (crudo 2 de 97; ponderado 9,8; se esperan 9,44 en 120 días) | **más de 15** (crudo 5 de 993; ponderado 10,5; se esperan 10,05) | `cotas_retrospectiva_v375.py` sobre el evaluador sellado `experiments/_s162_v375/evaluar.py`, artefactos de los runs 40116289866 y 40131572769, ventana O (2026-06-13 a 2026-10-21 sin 6 días, 125 días), sólo NOAA-20 y NOAA-21, regla «cercano» |
| VIIRS 750 | **más de 12** (9 de 90; se esperan 7,55) | **más de 2** (1 de 3.218; se esperan 0,84) | `cotas_retrospectiva_v750.py` sobre `analizar_v750b.py`, runs 41615021658 y 41693265163, brazo B4, ventana O (143 días, hasta el 2026-11-02), sin Suomi NPP |

**Lo que estas cotas no son.** Salen del port de V375-B y C (`brazos.py`), que PD3 declaró equivalente a la vía (`PREREGISTRO_E.md` §3), y del oráculo de V750-B; no de la vía de `pipeline/` corriendo en producción. Las cifras crudas son chicas (2 y 5 pasadas en VIIRS 375, 9 y 1 en VIIRS 750), y en VIIRS 375 el peso de la muestra multiplica por cerca de 5: la tasa de 120 días es una estimación y su Poisson no incluye la incertidumbre de esa tasa. En MODIS y en estas dos cotas el criterio de falsa alarma de 8 % o menos es propuesta del implementador; las fija Nicolás. Con Suomi NPP incluido las cotas serían 25 y 20 en VIIRS 375, y 12 y 4 en VIIRS 750: no se usan porque esa plataforma terminó el 2026-11-02 (A104).

### 4.5 Pasadas juzgadas

Como en K y MODIS: una pasada ya decidida por una persona se anota en `experiments/_s176_v375e_adopcion/sombra_pasadas_juzgadas_viirs.json` (un commit por entrada, con quién, cuándo y la evidencia) y no vuelve a disparar. No hay rachas, por la misma razón que en MODIS (D4 de esa regla): el instrumento no las computa y la cota acumulada ya las cubre.

### 4.6 Duración

Por sensor, hasta que la guardia **tenga record** de 29 protegidas nocturnas de ese sensor posteriores al encendido, o 120 días desde el encendido, lo que ocurra primero (D3). Cumplido el plazo, una candidata se sigue informando (`CANDIDATA_FUERA_DE_PLAZO`) pero ya no está pre-autorizada: decide Nicolás.

### 4.7 El día después de una reversión

El revert apaga el flag pero no deshace los datos: los records de la vía se quedan como están hasta que llegue su producto estándar o se reprocesen. Dentro de los 7 días siguientes, en un PR aparte y con tag defensivo (A38), esos records se apartan a `data/_via_viirs_residuales/` y se reponen con K, o con los records de la guardia si el nulo de §4.4 (c) dio 0 diferencias (D7). Hasta entonces la serie del sensor mezcla dos detectores y así se dice en el issue. La guardia y su vigilancia siguen corriendo hasta que Nicolás decida apagarlas. La ficha SDA y las marcas A113 del PR revertido se reponen con una marca que diga que ese sensor volvió a K y desde cuándo.

## 5. Lista de los PR

**PR A (este, inerte con los flags apagados):** guardia, vigilancia, audit por detector, marca del tablero y esta regla en borrador. Comprobado sin cambio de records ni de régimen: `control_lectores.py` y `control_produccion.py` en esta carpeta, con su salida.

**PR B1 y B2, cada uno aparte, antes del merge:**
- Sello de esta regla; las cotas de `COTAS` en `scripts/vigilancia_guardia_viirs.py`, con los valores sellados.
- Guardia corriendo como identidad al menos tres noches (nulo en cero).
- `#965` en main (ya entró). Probar en navegador con records de la vía lo que el diseño dejó en la decisión 5: el tablero con la vía de V375, `diario.html` y `mosaico.html`.
- La línea del flag, la prueba que fija su valor (`test_las_vias_de_viirs_siguen_apagadas_en_produccion_en_este_pr` se cambia ahí), `tests/test_guard_declarado_vs_efectivo_s131.py`.
- Ficha SDA, `docs/MISSION.md`, `CLAUDE.md` y `docs/MIROVA_DIVERGENCES.md` (A113).
- Un paso en `nrt.yml` que deje el job en rojo si el log trae `ERROR processing` en un gránulo de ese sensor (VPR967-05 (a)). `scripts/revisar_errores_modis_nrt.py` hoy sólo mira MODIS y su prueba exige que no falle con VIIRS: hay que generalizarlo con el modelo de `tests/test_revisar_errores_modis_nrt_s173.py`. Lo seguro es el job rojo; `nrt-monitor.yml` abre issue sólo con 3 corridas seguidas fallidas.
- Prueba de que el revert del flag de ese sensor no choca con un PR que cambie una clave cercana del perfil, con el modelo de `tests/test_revert_flag_modis_no_choca_s173.py` (VPR967-05 (c)). B entra con el botón de merge commit, nunca squash: el `-m 1` lo supone.
- Tag defensivo, sí de A45 y frase de merge. Medir el tiempo del NRT: el peor job hoy dura 16 min y el techo es 50 por paso.
- Excepción al congelamiento (§12.6) en la bitácora.
- Aviso a los consumidores.

## 6. Lo que esta regla no cubre

Los 34 volcanes fuera del tablero. El reemplazo de la historia publicada (decisión 8 del diseño): va después de cada encendido, con tag y frase.

## 7. Pre-mortem

Si el encendido está mal, se vería como: (a) una protegida que la guardia publica y la vía calla (§4.3); (b) una sin record de la vía (§4.4 (a)); (c) alertas débiles perdidas sobre la cota (§4.4 (i)), que es el costo aceptado; (d) sobre-publicación subiendo sobre lo medido (§4.4 (ii)); (e) el NRT pasando su techo por el remuestreo a la grilla, que no está medido en los volcanes lentos; (f) en VIIRS 750, la región sensible de Cordón Caulle y Tupungatito callando lo que K publicaba, sin que se sepa si K sobre-publicaba.
