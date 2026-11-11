# Auditoría S179, frente B: VIIRS 375 y VIIRS 750, el encendido preparado y su regla de reversión

## 1. Encabezado

- **Fecha y hora del servidor**: 2026-11-11 01:22:20 GMT (cabecera `Date` de GitHub, llamada propia). Los insumos de GitHub que me entregaron son del 2026-11-10 20:37:28 GMT.
- **Sobre qué medí**: código de `main` en `438a60a1e` (instantánea `D:\vrp-trabajo\temporales\s179-audit\main\`, 12 archivos comprobados por sha256 contra `git show`); documentos del loop en `0472cd95e`; datos de `438a60a1e` sacados con `git show`; lectura de la retrospectiva en `ff8a39972` (rama `claude/s178-retro-lectura`); PR #974 en `bbbe2068d`, #975 en `9d3e63015`, #983 en `e68819484`, #980 en `9c880c61c`. Lo que vive en esas ramas está **fuera de main**.
- **Modelo y esfuerzo**: Fable 5.2 (`claude-fable-5-2`). El nivel de esfuerzo no lo puedo leer desde dentro de la sesión: SIN DATO; se lee en el transcripto.
- **CARPETA**: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s179_audit\b\`. Temporal: `D:\vrp-trabajo\temporales\s179-audit\b\` (176 MB de datos; se rearma con `extraer_datos.sh`).
- **Llamadas a GitHub**: 4 a 5 de 10 (corridas de la guardia, salida vigente de la vigilancia de VIIRS 375, log de la falla del CI de #980).
- **Qué NO miré** (mi silencio ahí no es «todo bien»):
  - No corrí la suite de pruebas sobre ningún árbol mergeado (no podía crear worktrees). El CI de #974 y #983 lo leí, no lo repetí.
  - No abrí `docs/PLAN_AUDITORIA_S179.md` ni nada bajo `experiments/_s179_*` salvo mi carpeta.
  - De la bitácora (`tasks/LOOP_OBJETIVOS.md` §6) leí completas las entradas de S178 y el cierre de S177 (líneas 570 a 699). Las de S172 a S176 las recorrí por encabezado y por las frases de Nicolás (comando en el §5), no línea a línea. De los bloques de arranque sólo leí entero el de S179.
  - No leí por dentro `experiments/_s162_v375/evaluar.py`, `brazos.py`, `PREREGISTRO_V750A.md`, `evaluar_v750a.py`, `experiments/_s162_v750c/INFORME.md` ni el bloque de la vía de `pipeline/process_viirs_mod.py` (sí el de `pipeline/process_viirs.py`).
  - No re-corrí los scripts de cotas de S176 y S178: leí sus salidas commiteadas y rehíce por mi cuenta el Poisson y la exposición.
  - No audité el candado, C-K ni C-montaje de la retrospectiva (frente C): tomé `lectura.json` como dato.
  - No probé nada en navegador. No medí el tiempo del NRT con la vía.

## 2. En una pantalla

1. **Los PR encienden sólo lo aprobado, pero hoy no se pueden mergear, y la punta que finalmente entre será un commit nuevo sin CI ni verificador propios.** #974 y #983 cambian un flag cada uno en producción y nada en `pipeline/*.py`, `data/` ni `frontend/`. Los dos chocan con `main` en la ficha; su CI verde es anterior a #982 y #984. Cinco condiciones que la regla sellada pone «antes del merge» (§5) siguen sin hacerse.
2. **El plazo de reversión pre-autorizada dura unos 11 días, no 120.** Con Chillán en erupción se juntan 20 protegidas de VIIRS 375 en 7,8 días (18 de Chillán). Las 29 del plazo se cumplen hacia el día 11 y casi todas son de una erupción de 2 a 37 MW, que no prueba nada sobre una alerta de 1 MW en un volcán tranquilo.
3. **Las cotas de investigación disparan por azar más de lo declarado.** La regla dice 4,5 a 5,9 %; con la incertidumbre de tasas hechas con 1 a 9 casos da 12 a 28 %. En la semana de la sombra la vía ya calló 3 alertas débiles de VIIRS 375 (se esperaban 0,6): a ese ritmo la cota 14 se supera cerca del día 39.
4. **«Ninguna protegida perdida» se sostiene, pero sobre dos volcanes.** Retrospectiva: 26 de 26 protegidas de VIIRS 375 y 29 de 30 de VIIRS 750 son de Láscar. Sombra: 18 de 20 y 16 de 19 son de Chillán. En Cordón Caulle VIIRS 750 la vía dio 0,57 de MIROVA (n 3).
5. **Sano y medido**: el nulo de la guardia (223 y 220 pares, 0 distintos, VRP idéntico), la aritmética y la exposición de las cotas, el tablero mostrando 0,99 y 1,00 de MIROVA con records de la vía, y 0 candidatas a reversión en la semana de la sombra.

## 3. Hallazgos (lo peor primero)

Cada número lleva su commit y su ventana. «Semana de la sombra» = noches del 2026-11-03 al 2026-11-09, 11 volcanes Tier A, datos de `438a60a1e`. «Simulacro» = el vigilante de `main` corrido con la sombra en el papel de producción y K de producción en el papel de guardia (`sim_vigilancia.py`).

### 451

- **TÍTULO**: El plazo de la reversión pre-autorizada (29 protegidas) se agota en unos 11 días y con un solo volcán
- **ARCHIVO:LÍNEA**: `experiments/_s176_v375e_adopcion/REGLA_REVERSION_V375E_BORRADOR.md` l. 27 (D3) y l. 106 (§4.6); `scripts/vigilancia_guardia_modis.py:228-237` y `:327` (438a60a1e). SCRIPT:SALIDA: `sim_vigilancia.py` y `cotas_poder.py`, salidas `sim_vigilancia_salida.txt` y `cotas_poder_salida.txt` (parte 4).
- **QUÉ PASA**: Nevados de Chillán está en erupción y MIROVA lo alerta con 2 a 37 MW dos o tres veces por noche. La regla cierra la reversión pre-autorizada cuando la guardia ve 29 protegidas o a los 120 días, lo que ocurra primero, y el vigilante cuenta las 29 sin mirar de qué volcán son. En el simulacro (7,79 días desde el 2026-11-03 05:00 UTC): 20 protegidas de VIIRS 375, 18 de Chillán; 19 de VIIRS 750, 16 de Chillán. A ese ritmo las 29 se juntan en 11,3 y 11,9 días. En la ventana O (2026-06-13 a 2026-10-21, NOAA-20 y NOAA-21) el ritmo era 0,22 protegidas por día; en los últimos 20 días es 1,95. El número que sostiene D3 («con 29, una pérdida de una de cada diez se ve con 95 %») supone 29 pasadas independientes y parecidas; aquí son casi todas la misma erupción fuerte.
- **CÓMO SE VE EN EL DASHBOARD**: invisible. Desde el día 11 o 12 después de cada encendido, una protegida de 1 a 2 MW en un volcán tranquilo que la vía calle ya no se revierte el mismo día: el vigilante la informa como `CANDIDATA_FUERA_DE_PLAZO` y espera a Nicolás. Mientras tanto el operador no ve esa anomalía.
- **CÓMO REPRODUCIRLO**: `bash "C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s179_audit\b\extraer_datos.sh"`; `python "C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s179_audit\b\sim_vigilancia.py"`; después `python "C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s179_audit\b\cotas_poder.py"`. Volcán: Nevados de Chillán; primera pasada 2026-11-03 06:00 UTC, última 2026-11-10 05:30 UTC.
- **CONFIANZA**: CONFIRMADO (medido; la proyección a 11 días supone que Chillán sigue como en esa semana).
- **GRAVEDAD 1-5**: 4. Es la red que reemplaza a las lecturas selladas (D5). Si se cierra en 11 días, la pérdida de una alerta de 1 MW o más queda sin reversión automática durante casi todo el período en que la vía es nueva.

### 452

- **TÍTULO**: La cota (i) de VIIRS 375 (más de 14 Muy Bajo perdidas) está calibrada 4,9 veces por debajo de lo que la vía calló en la semana de la sombra
- **ARCHIVO:LÍNEA**: `scripts/vigilancia_guardia_viirs.py:73` (COTAS); regla l. 92. SCRIPT:SALIDA: `sim_vigilancia.py` (escenario A, VIIRS375) y `cotas_poder.py` (parte 4), `detalle_sombra.py` (c).
- **QUÉ PASA**: Un foco débil (0,05 a 1 MW) que K publica y la vía no ve es el costo aceptado del encendido; la regla investiga si se juntan más de 14 en 120 días, porque espera 9,48. En el simulacro la vía calló 3 de 36 en 7,79 días: Cordón Caulle 2026-11-04 05:42 (0,09 MW) y 2026-11-07 06:30 (0,36 MW), Planchón-Peteroa 2026-11-05 05:24 (0,06 MW). En las tres el record de la vía tiene 0 píxeles alertados (no es el tablero el que la oculta). Con la tasa de la calibración se esperaban 0,62; la probabilidad de ver 3 o más es 0,025. Llevado a 120 días son 46 (IC 95 %: 9,5 a 135). Si noviembre es representativo, la cota se supera hacia el día 39 con probabilidad cercana a 1. La regla excluye a propósito esos días de la calibración (A115), pero nadie comparó después.
- **CÓMO SE VE EN EL DASHBOARD**: tres pasadas con alerta débil de MIROVA en que el tablero, con la vía, queda vacío y con K mostraba 0,09, 0,26 y 0,14 MW. Hacia mediados de diciembre se abriría el issue «Guardia K de VIIRS 375: investigar».
- **CÓMO REPRODUCIRLO**: `python "C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s179_audit\b\sim_vigilancia.py"` (línea «(i) Muy Bajo ... 3 de 36») y `python "...\b\detalle_sombra.py"` (bloque (c)). Volcán: Puyehue-Cordón Caulle, VIIRS 375, 2026-11-07 06:30 UTC.
- **CONFIANZA**: CONFIRMADO el conteo; SOSPECHA que la tasa de una semana se mantenga.
- **GRAVEDAD 1-5**: 3. No revierte nada, pero convierte el «costo aceptado» en una alarma casi segura, y deja ver que en Cordón Caulle la vía calla más de lo que midió la retrospectiva (en R25, 6 de las 12 pérdidas listadas también son de Cordón Caulle).

### 453

- **TÍTULO**: Las cuatro cotas declaran 4,5 a 5,9 % de falsa alarma tomando la tasa como exacta; con su incertidumbre es 12 a 28 %, y la cota (ii) de VIIRS 750 nace de un solo caso
- **ARCHIVO:LÍNEA**: regla l. 88 a 98 (§4.4, «Cotas de la investigación»); `experiments/_s178_cotas_v375/cotas_v375_con_retro_salida.txt` (opción C-rad) y `experiments/_s176_v375e_adopcion/cotas_retrospectiva_v750_salida.txt` (438a60a1e). SCRIPT:SALIDA: `cotas_poder.py`, `cotas_poder_salida.txt` (parte 1).
- **QUÉ PASA**: La cota es el primer entero con falsa alarma Poisson de 8 % o menos si la tasa verdadera fuera la estimada. Pero las tasas salen de 2 casos crudos que pesan 4,9 cada uno más 3 (VIIRS 375 (i)), 5 más 5 (VIIRS 375 (ii)), 9 (VIIRS 750 (i)) y 1 (VIIRS 750 (ii)). Mi control reproduce las cifras de la regla (0,058; 0,057; 0,045; 0,053). Metiendo la incertidumbre de cada conteo (posterior de Jeffreys, 200.000 sorteos), la probabilidad de que la cota dispare aunque la vía rinda como en la retrospectiva es 0,28; 0,20; 0,12 y 0,17. Las cuatro juntas, aun con la tasa puntual, dan 0,20 de que al menos una dispare en 120 días. Poder: la cota (ii) de VIIRS 750 (más de 2) dispara sólo 24 % de las veces si la sobre-publicación se duplica y 46 % si se triplica. La regla dice que «su Poisson no incluye la incertidumbre de esa tasa» (l. 98, TEXTO), pero no dice cuánto pesa.
- **CÓMO SE VE EN EL DASHBOARD**: invisible; se ve como un issue «investigar» que puede no significar nada, o como un silencio de la cota (ii) de VIIRS 750 que tampoco significa nada.
- **CÓMO REPRODUCIRLO**: `python "C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s179_audit\b\cotas_poder.py"` (parte 1; semilla fija 179). Sin volcán ni pasada: es aritmética sobre los casos crudos.
- **CONFIANZA**: CONFIRMADO (el modelo de incertidumbre es mío y simple; el orden de magnitud no depende de él: el IC 95 % de la tasa de VIIRS 375 (i) va de 3,5 a 26).
- **GRAVEDAD 1-5**: 3. Nicolás firmó D1 y D2 leyendo «falsa alarma 5,9 % y 5,6 %» y «4,5 % y 5,3 %».

### 454

- **TÍTULO**: Cinco condiciones que la regla sellada pone «antes del merge» de B1 y B2 no están hechas, y una se movió a «después del merge» sin decisión
- **ARCHIVO:LÍNEA**: regla l. 116 a 126 (§5); `.github/workflows/nrt.yml:374-384` y `scripts/revisar_errores_modis_nrt.py:13` (438a60a1e); bitácora `tasks/LOOP_OBJETIVOS.md` l. 645 y bloque `tasks/BLOQUE_ARRANQUE_S179.md` l. 11-12 y l. 38 (0472cd95e); cuerpos de #974 y #983 (insumos).
- **QUÉ PASA**: Con la vía, si un gránulo VIIRS falla, no cae a K: esa pasada queda sin record y el job del NRT sale verde. La regla lo prevé y pide, antes de cada merge, un paso de `nrt.yml` que deje el job rojo. En `main` ese paso sólo mira MODIS: cita, `scripts/revisar_errores_modis_nrt.py` l. 13, TEXTO: «se cuentan y se informan, pero NO hacen fallar el job». La bitácora lo reclasifica: cita, l. 645, TEXTO: «Pendiente tras el merge (fuera de los PR)». El bloque S179 dice que el encendido «sólo espera las 3 noches verdes de la guardia K y su frase». También siguen sin hacer, según los cuerpos de #974 y #983, y no encontré en las entradas de S178 de la bitácora que se hayan hecho después: probar `index.html`, `diario.html` y `mosaico.html` en navegador con records de la vía; medir el tiempo del NRT con la vía; la excepción al congelamiento §12.6 en la bitácora; el aviso a los consumidores.
- **CÓMO SE VE EN EL DASHBOARD**: una pasada VIIRS que desaparece sin dejar rastro (ni record «sin detección»). La vigilancia la vería a las 24 h sólo si era protegida y la guardia la publicó.
- **CÓMO REPRODUCIRLO**: `grep -n "revisar_errores" "D:\vrp-trabajo\temporales\s179-audit\main\.github\workflows\nrt.yml"` y leer `scripts/revisar_errores_modis_nrt.py` l. 1 a 15. Sin volcán: es una condición de proceso.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD 1-5**: 3.

### 455

- **TÍTULO**: «Ninguna protegida perdida» en VIIRS descansa en Láscar (retrospectiva) y Chillán (sombra); en seis volcanes no hay ninguna protegida con la vía real
- **ARCHIVO:LÍNEA**: `experiments/_s178_lectura/lectura.json` en `ff8a39972`, claves `sensores.VIIRS375.lectura_b`, `sensores.VIIRS750.lectura_b` y `osf.por_sensor`. SCRIPT:SALIDA: `sim_vigilancia_salida.txt` (protegidas por volcán).
- **QUÉ PASA**: La prueba de que la vía no calla una anomalía de 1 MW o más vale para los volcanes que tuvieron una. En el tramo F26-V (2026-02-01 a 2026-03-31) las 26 protegidas de VIIRS 375 son de Láscar (26 de 26) y las de VIIRS 750 son 29 de Láscar y 1 de Isluga. En el OSF de 2025: VIIRS 375, 273 de 317 de Láscar (28 Cordón Caulle, 14 Planchón-Peteroa, 2 Isluga); VIIRS 750, 17 de 17 de Láscar. En la semana de la sombra: 18 de 20 y 16 de 19 de Chillán, el resto Cordón Caulle. Villarrica, Copahue, Llaima, Lastarria, Tupungatito y Chaitén: 0 protegidas con la vía real en los tres conjuntos. El veredicto de la bitácora nombra «alertas: Isluga, Láscar, Planchón-Peteroa, Cordón Caulle» (l. 634), que son los volcanes con alguna alerta, no los de las protegidas. Para VIIRS 750 el bloque S179 sí dice «14 casos, 12 de Chillán».
- **CÓMO SE VE EN EL DASHBOARD**: invisible. Es el alcance de la evidencia, no un defecto.
- **CÓMO REPRODUCIRLO**: `git show ff8a39972:experiments/_s178_lectura/lectura.json` (con `export MSYS_NO_PATHCONV=1`) y leer `lectura_b` por volcán; `python "...\b\sim_vigilancia.py"`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD 1-5**: 3. No contradice el encendido; cambia cuánto se le puede pedir a «no pierde protegidas».

### 456

- **TÍTULO**: El día del encendido la magnitud de VIIRS sube entre 1,3 y 3,2 veces según el volcán y el tablero sólo lo marca con una línea
- **ARCHIVO:LÍNEA**: `frontend/cambio_detector.js:273-296` (438a60a1e, tras #984); diseño `docs/superpowers/specs/2026-11-08-encendido-v375e-design.md` l. 60 (0472cd95e). SCRIPT:SALIDA: `detalle_sombra.py`, `detalle_sombra_salida.txt` (b).
- **QUÉ PASA**: K publica el núcleo recortado y la vía la suma de todos los píxeles: el mismo foco pasa a mostrarse con el doble de potencia. Medido con el predicado del tablero ejecutado con node, en pasadas con alerta que los dos publican: VIIRS 375, vía 0,991 de MIROVA y K 0,496 (n 50); el salto por volcán va de 1,32 (Planchón-Peteroa) a 3,16 (Isluga); Chillán 1,56. VIIRS 750: vía 1,000 y K 0,446 (n 21); Chillán 2,14. El diseño pedía que el operador leyera que no es el volcán: cita, l. 60, TEXTO: «el operador debe leer que **no es que el volcán crezca**». Nicolás pidió «quita los 3» por los tres avisos que estaban en la página (K, vía de MODIS, cese de Suomi NPP). El cambio quitó el aviso de texto de la vía para todas las familias, también el de VIIRS, que aún no existía en la página: cita, `frontend/cambio_detector.js` l. 288, TEXTO: «la vía ya no pone aviso de texto arriba del tablero».
- **CÓMO SE VE EN EL DASHBOARD**: en Chillán, en plena erupción, la serie de VIIRS 750 sube a algo más del doble de un día para otro (donde MIROVA da 17 MW, K muestra cerca de 8 y la vía cerca de 17), con una línea punteada y un rótulo de 10 px «VIIRS 750: vía MIROVA». Se puede leer como un aumento de la tasa de efusión.
- **CÓMO REPRODUCIRLO**: `python "C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s179_audit\b\detalle_sombra.py"` (bloque (b)); leer `frontend/cambio_detector.js` l. 273 a 296.
- **CONFIANZA**: CONFIRMADO el salto y el código; SOSPECHA sobre si «quita los 3» quería cubrir el aviso futuro de VIIRS (eso lo sabe Nicolás).
- **GRAVEDAD 1-5**: 3 si alguien lee el tablero para decidir; 2 mientras OVDAS siga usando el scraper (memoria del proyecto, S173).

### 457

- **TÍTULO**: Revertir B1 después de que entre B2 choca en 9 archivos y nadie ensayó esa resolución
- **ARCHIVO:LÍNEA**: cuerpo de #974 («Cómo se revierte») y de #983 («Lo que no está verificado»), insumos `pr_974.json` y `pr_983.json`; regla l. 71 (§4.3).
- **QUÉ PASA**: VIIRS 375 es el sensor con más flujo y entra primero (B1), así que es el más probable de revertir. Según el propio PR, `git revert -m 1` del merge de B1 con B2 ya adentro choca en la ficha y en 8 pruebas. La regla dice que se resuelve a mano «sin esperar a nadie». Esa resolución (8 pruebas que deben quedar con la vía de VIIRS 750 encendida y la de VIIRS 375 apagada) no existe escrita ni pasó por CI.
- **CÓMO SE VE EN EL DASHBOARD**: el día de una reversión, la alerta callada sigue callada mientras una sesión resuelve conflictos a mano.
- **CÓMO REPRODUCIRLO**: leer `D:\vrp-trabajo\temporales\s179-audit\insumos\pr_974.json`, sección «Cómo se revierte». No lo re-medí.
- **CONFIANZA**: SOSPECHA (lo afirma el PR con `git merge-tree`; yo no repetí la simulación).
- **GRAVEDAD 1-5**: 3.

### 458

- **TÍTULO**: #974 y #983 chocan hoy con main, su CI verde es anterior a #982 y #984, y la numeración de la ficha está escrita de dos maneras
- **ARCHIVO:LÍNEA**: SCRIPT:SALIDA: `mergetree_comando.txt`, salidas `mergetree_974_bbbe2068d_salida.txt` y `mergetree_983_e68819484_salida.txt`. Bitácora l. 576 y cuerpo de #983.
- **QUÉ PASA**: El merge ES el encendido, así que importa qué commit exacto entra. Simulado contra `438a60a1e`: los dos PR tienen 2 conflictos, ambos en `docs/FICHA_SDA_VRP_CHILE.md`. Para mergear hay que agregar commits nuevos a los dos, y #983 contiene los commits viejos de B1, así que hay que rehacerlo después de tocar #974. El CI de #974 corrió el 2026-11-10 02:47 UTC y el de #983 a las 10:17 UTC sobre `main` en `d7a655a7f`: ninguno vio #982 (cotas selladas en el vigilante, mergeado a las 11:25 UTC) ni #984 (`frontend/cambio_detector.js`, 17:00 UTC). La bitácora dice «#974 pasa a v1.23 y #983 a v1.24» (l. 576) y el cuerpo de #983 dice «v1.23 (B2) > v1.22 (B1)». #975 (B2 solo) sigue abierto al lado de #983.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: los comandos de `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s179_audit\b\mergetree_comando.txt`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD 1-5**: 2 (los conflictos son de documento; el riesgo es que la punta que encienda no tenga verificador ni CI propios).

### 459

- **TÍTULO**: En Cordón Caulle, VIIRS 750, la vía mostró 0,57 de la potencia de MIROVA en la sombra (n 3)
- **ARCHIVO:LÍNEA**: SCRIPT:SALIDA: `pcc_v750.py`, `pcc_v750_salida.txt`; `detalle_sombra_salida.txt` (b, VIIRS750).
- **QUÉ PASA**: En Cordón Caulle la anomalía es un campo difuso y la vía usa la región sensible (`roi sens`) desde #939. En las tres protegidas de la semana: 2026-11-07 05:30, MIROVA 1,54 MW y la vía 1,631 (2 píxeles); 2026-11-08 05:12, MIROVA 1,69 y la vía 0,956 (1 píxel); 2026-11-09 04:54, MIROVA 1,67 y la vía 0,852 (1 píxel). Mediana 0,566. El «1,000» de VIIRS 750 que citan el diseño y #975 es de Chillán (17 de 21 pasadas en mi medición). Con D5 la condición de magnitud del lector de V750-A dejó de decidir; queda el audit semanal con banda 0,7 a 1,4 por volcán.
- **CÓMO SE VE EN EL DASHBOARD**: Cordón Caulle en VIIRS 750 con cerca de la mitad de la potencia de MIROVA en dos de tres noches, igual que con K (0,446).
- **CÓMO REPRODUCIRLO**: `python "C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s179_audit\b\pcc_v750.py"`. Volcán: Puyehue-Cordón Caulle, VIIRS 750, 2026-11-08 05:12 UTC.
- **CONFIANZA**: CONFIRMADO para esas tres pasadas; SOSPECHA como rasgo del volcán (n 3).
- **GRAVEDAD 1-5**: 2.

### 460

- **TÍTULO**: La vía no escribe record en 4,9 % de las pasadas de VIIRS 375 y una alerta débil en esas pasadas no entra a ninguna cota
- **ARCHIVO:LÍNEA**: `pipeline/process_viirs.py:766-786` (los `return None` de las l. 774 y 782); `scripts/vigilancia_guardia_modis.py:252-254` y `:280-294` (438a60a1e). SCRIPT:SALIDA: `detalle_sombra.py`, `detalle_sombra_salida.txt` (a).
- **QUÉ PASA**: Cuando el gránulo no cubre el volcán, K deja un record «sin detección» y la vía no deja nada. En la semana de la sombra, de 223 pasadas que la guardia registra, la vía no tiene record en 11 (VIIRS 750: 0 de 220). Nueve son de borde (cenit 56° a 70°). Dos no: Láscar 2026-11-04 05:42 (cenit 11°) y Cordón Caulle 2026-11-08 06:06 (cenit 32°, donde K publica 0,58 MW). La cota (i) sólo cuenta pasadas con record en los dos lados, y la regla sólo investiga la falta de record si la alerta era protegida. En estas 11 MIROVA no alertó (4 negativos limpios, 7 sin información), así que no se perdió nada esta vez.
- **CÓMO SE VE EN EL DASHBOARD**: menos pasadas VIIRS 375 listadas por noche; en esas pasadas no hay punto ni «sin anomalía».
- **CÓMO REPRODUCIRLO**: `python "C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s179_audit\b\detalle_sombra.py"` (bloque (a)). Volcán: Puyehue-Cordón Caulle, VIIRS_NOAA20, 2026-11-08 06:06 UTC.
- **CONFIANZA**: CONFIRMADO el conteo; SOSPECHA la causa de las dos que no son de borde (puede ser una descarga caída de la sombra, que corre una vez al día: SIN ATRIBUIR).
- **GRAVEDAD 1-5**: 2.

### 461

- **TÍTULO**: La regla pide revertir «el mismo día UTC», pero la guardia corre en la práctica pasada la medianoche UTC
- **ARCHIVO:LÍNEA**: regla l. 68 (§4.3); `.github/workflows/guardia-k-viirs.yml:26` (cron 19:35 UTC); `.github/workflows/vigilancia-guardia-viirs.yml` (respaldo 22:55 UTC). SCRIPT:SALIDA: `api_guardia_runs_salida.txt`.
- **QUÉ PASA**: Una alerta nocturna de Chile ocurre entre las 04:30 y las 07:00 UTC. La guardia la procesa en su corrida diaria. Las dos corridas programadas que existen empezaron el 2026-11-10 02:21 UTC y el 2026-11-11 00:12 UTC: 6,8 y 4,6 horas después de su cron. La vigilancia de respaldo de las 22:55 UTC puede correr antes que la guardia, y entonces mira datos del día anterior. Del silencio al issue pasan del orden de 19 a 22 horas, y el «mismo día UTC» ya terminó.
- **CÓMO SE VE EN EL DASHBOARD**: una protegida callada por la vía quedaría sin publicar al menos un día entero antes de que alguien pueda revertir.
- **CÓMO REPRODUCIRLO**: `gh run list --workflow guardia-k-viirs.yml --limit 6 --json databaseId,event,createdAt,conclusion` (1 llamada).
- **CONFIANZA**: CONFIRMADO con n 2 corridas programadas.
- **GRAVEDAD 1-5**: 2.

### 462

- **TÍTULO**: Con B1 y B2, 55 perfiles derivados pasan a correr la vía en VIIRS sin declararlo, entre ellos el del «reproceso histórico con K»
- **ARCHIVO:LÍNEA**: SCRIPT:SALIDA: `flags_por_perfil.py`, `flags_por_perfil_salida.txt`; `pipeline/profiles/_s154_reproc_k_historico.yaml` l. 1 a 12; `scripts/reemplazar_ventana_reproceso.py:7,28-29` (438a60a1e).
- **QUÉ PASA**: Todo perfil que hereda de producción y no declara el flag lo hereda encendido. Resuelto con `pipeline.profile` sobre los 105 perfiles: de `main` a #983 cambian 56, producción (lo aprobado) y 55 más. Los PR declaran la vía apagada sólo en cuatro (`experimental`, `experimental_ndc_focus`, `_s146_ab_control`, `guardia_k_modis`). De los 55, 20 los nombra algún workflow de reproceso que se puede despachar a mano, y `_s154_reproc_k_historico` (cita, l. 1, TEXTO: «REPROCESO HISTORICO CON K») dejaría de producir K en VIIRS. Los mismos 55 ya heredan la vía de MODIS desde #934: es un patrón aceptado antes, no uno nuevo.
- **CÓMO SE VE EN EL DASHBOARD**: invisible mientras nadie use esos perfiles. Si alguien reprocesa «con K» para reponer historia, escribe la vía; el record lo dice (`via_codigo_mirova: true`).
- **CÓMO REPRODUCIRLO**: `python "C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s179_audit\b\flags_por_perfil.py"`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD 1-5**: 2.

### 463

- **TÍTULO**: D5 dice que los lectores sellados «se conservan y se corren», pero el de V375-E no está en main, nadie lo corre, y al encender B1 pierde su brazo K
- **ARCHIVO:LÍNEA**: regla l. 29 (D5) y l. 44; `docs/AUDIT_S175.md` §6 fila F2-209 y §8 decisión 20 (rama `claude/relaxed-almeida-d17378`, `37670d910`).
- **QUÉ PASA**: La lectura sellada de V375-E (30 noches o 40 alertas, parada hacia el 2026-12-02) dejó de decidir. La regla dice: cita, l. 29, TEXTO: «Los lectores se conservan y se corren». El lector (`experiments/_s168/v375e_sombra/leer_sombra_v375e.py`) vive sólo en el tag `s172-v375e-lector-resellado`; en `438a60a1e` no está, y `experiments/_s162_v375/PREREGISTRO_E.md` de `main` es distinto del que trae el tag (la cabecera del de `main` dice «BORRADOR, sin sellar»; no comparé los dos textos). El pendiente F2-209 de la auditoría S175 sigue abierto. Además ese lector compara la sombra con K de producción: desde B1 producción deja de ser K en VIIRS 375 y K pasa a vivir en `data/guardia_k_viirs/`.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `git ls-tree -r --name-only 438a60a1e | grep leer_sombra_v375e` (vacío) y `git ls-tree -r --name-only s172-v375e-lector-resellado | grep leer_sombra_v375e`.
- **CONFIANZA**: CONFIRMADO que no está en main; SOSPECHA que el lector no pueda leer K desde la guardia (no lo abrí).
- **GRAVEDAD 1-5**: 2.

### 464

- **TÍTULO**: El diseño del encendido que citan la regla sellada, el vigilante y dos workflows no existe en main
- **ARCHIVO:LÍNEA**: regla l. 10; `scripts/vigilancia_guardia_viirs.py:21`; 12 archivos de `main` lo citan (438a60a1e). El archivo `docs/superpowers/specs/2026-11-08-encendido-v375e-design.md` sólo está en `loop/activo` (0472cd95e).
- **QUÉ PASA**: Quien lea la regla pública desde `main` no puede abrir el documento que explica las decisiones 3 a 8.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `git cat-file -e 438a60a1e:docs/superpowers/specs/2026-11-08-encendido-v375e-design.md` (falla) y lo mismo con `0472cd95e` (existe).
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD 1-5**: 1.

### 465

- **TÍTULO**: #980 (vara MATLAB) tiene el CI en rojo y está recomendado para merge sin re-correr
- **ARCHIVO:LÍNEA**: insumo `pr_980.json` (pytest FAILURE, run 42780551986); SCRIPT:SALIDA: `api_run980_falla_salida.txt`; bloque S179 l. 42.
- **QUÉ PASA**: La falla es ajena a la vara: `tests/test_guard_regla_c_s134.py::test_p5_diag_nti_max_persistido_en_modis`, la que arregló #978 después. El PR no se actualizó con `main`, así que su estado sigue rojo.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `gh run view 42780551986 --log-failed | grep FAILED`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD 1-5**: 1.

### 466

- **TÍTULO**: La bitácora registra la frase «Sello la regla» sin hora propia y una entrada posterior dice que falta
- **ARCHIVO:LÍNEA**: bitácora l. 592 a 595 (entrada «10:20 UTC», que dice «Falta la frase de sello de Nicolás») y l. 585 a 586; regla l. 3 («servidor 10:12:44 UTC»); commit del sello `5b887f157`, 10:13:26 UTC.
- **QUÉ PASA**: La hora del sello está en la regla y en el commit, no en una entrada de la bitácora; la entrada de las 10:20 quedó escrita como si el sello aún no existiera. La vara de este plan pide la frase «con su hora».
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `sed -n '585,595p' "D:\vrp-trabajo\temporales\s179-audit\loop\tasks\LOOP_OBJETIVOS.md"` y `git log -1 --format=%cI s178-regla-reversion-viirs-sellada`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD 1-5**: 1.

## 4. Veredicto por decisión

Inventario armado con: `sed -n '570,1660p' "D:\vrp-trabajo\temporales\s179-audit\loop\tasks\LOOP_OBJETIVOS.md" | grep -n -E "Nicolás[^.]{0,60}«[^»]{2,80}»"` filtrado por VIIRS, guardia, regla, D1 a D7, retro, sello, B1, B2; más los encabezados `^### ` de ese tramo y el bloque `tasks/BLOQUE_ARRANQUE_S179.md` entero.

| # | Decisión (sesión, fuente) | Veredicto | Evidencia de esta sesión |
|---|---|---|---|
| 1 | «Sí, prepáralo»: adelantar VIIRS 375 con guardia K, dos PR como MODIS (S176, bitácora 2026-11-08 17:44 UTC) | SOSTENIDA | PR A en main; B1 cambia sólo el flag (`git diff --stat 438a60a1e...bbbe2068d`) |
| 2 | VIIRS 750 entra al mismo plan con su flag (S176, decisión 7 del diseño) | SOSTENIDA CON RESERVAS | Vara MATLAB vigente para el código de `438a60a1e`; magnitud 1,000 con 17 de 21 pasadas de Chillán; Cordón Caulle 0,57 (459) |
| 3 | «Retro primero»: leer la retrospectiva y encender si no pierde protegidas (S177, 2026-11-10 01:17 UTC) | SOSTENIDA CON RESERVAS | `lectura.json`: P1 sin pérdida en VIIRS 375 con los dos brazos de posición y en VIIRS 750; pero 455 |
| 4 | «Sí, escríbelos»: A45 para escribir B1 y B2 (S177, 03:21 UTC) | SOSTENIDA | Nada en `pipeline/*.py`, `data/` ni `frontend/`; reserva 462 |
| 5 | D1 «C-rad (14/17)» (S178) | SOSTENIDA CON RESERVAS | Aritmética y exposición reproducidas; pero 452 y 453 |
| 6 | D2: VIIRS 750, más de 12 y más de 2 (S178, «Sí a D2 a D7») | DEBILITADA en (ii) | 1 caso crudo; poder 24 % con el doble (453). (i): SOSTENIDA CON RESERVAS |
| 7 | D3: 29 protegidas o 120 días (S178) | DEBILITADA | 451 |
| 8 | D4: 24 h antes de leer silencio sin record (S178) | SOSTENIDA | `scripts/vigilancia_guardia_modis.py:110` y `:317-319`; con el atraso del cron (461) la espera real es mayor |
| 9 | D5: las lecturas selladas de V375-E y V750-A dejan de decidir (S178) | SOSTENIDA CON RESERVAS | Es decisión de Nicolás y está registrada; «se conservan y se corren» SIN RESPALDO (463) |
| 10 | D6: revertir sin la imagen si la protegida viene de la tabla (S178) | SOSTENIDA, sin medir | El vigilante no publica la procedencia; la regla lo declara (l. 70). SIN DATO sobre cuánto tarda a mano |
| 11 | D7: el día después, apartar y reponer con K (S178) | SOSTENIDA CON RESERVAS | No existe script; la carpeta `data/_via_viirs_residuales/` iría al sitio público (`pages-deploy.yml:77` copia `data/`) |
| 12 | «Sello la regla» y «Mergea #982» (S178) | SOSTENIDA | Tag `s178-regla-reversion-viirs-sellada` igual a `438a60a1e` en regla y vigilante (diff vacío); `COTAS` igual a la tabla; reserva 466 |
| 13 | B2 sobre B1 (#983) y orden #974 después #983 (S178) | SOSTENIDA CON RESERVAS | 458 y 457 |
| 14 | «quita los 3» avisos del tablero (S178, #976 y #984) | APLICADA DISTINTO (más ancho) | 456 |
| 15 | Verificador de B1 y B2: «Pendiente tras el merge» el paso de `nrt.yml` (S178, bitácora l. 645) | APLICADA DISTINTO respecto de la regla sellada | 454 |
| 16 | Vara MATLAB verde como condición de B2 (S178, #980) | SOSTENIDA | sha256 de la vía en la salida de #980 (`62d6538b...`) igual al de `pipeline/mirova_v750_codigo.py` en `438a60a1e`; `git diff e7cfbaf54 438a60a1e -- pipeline/` vacío; reserva 465 |
| 17 | Tres noches de guardia con el nulo en cero (regla §3) | EN CURSO, SOSTENIDA | 1 de 3 al 2026-11-11 01:22 UTC (corrida 42929475700 verde); nulo 254 pares, 0 distintos (salida de `main` de las 00:50 UTC) |
| 18 | Veredicto de la retrospectiva, VIIRS 375: fila 6 (S178) | SOSTENIDA CON RESERVAS | 455 |
| 19 | Veredicto de la retrospectiva, VIIRS 750: fila 4, decide Nicolás (S178) | SIN RESPALDO todavía | No hay frase de Nicolás; P1 sin pérdida, razón 0,999 con 29 de 30 de Láscar |
| 20 | Cifras de magnitud que citan los PR (0,504 y 0,993; 0,482 y 1,000) (S176 y S177) | SOSTENIDA | Re-medido con node: 0,496 y 0,991 (n 50); 0,446 y 1,000 (n 21) |
| 21 | Caja B4 en VIIRS 750 (S173) y #964, pre-registro de V750-A en borrador (S175) | SIN DATO | No lo medí; `c_montaje_caja_v750` dice OK en `lectura.json` |

## 5. PROPUESTAS PARA LOS PLANES

Ninguna está implementada. Cada una nombra el hallazgo que la sostiene.

1. **Antes de «mergea #974», decidir cómo se cuentan las 29 protegidas (451).** Opciones para Nicolás: un tope por volcán dentro de las 29; exigir protegidas de al menos tres volcanes; o un piso de días (por ejemplo, que el plazo no cierre antes de 60 días). Cambia D3, así que pide re-sello.
2. **Escribir en la regla qué se hará cuando la cota (i) de VIIRS 375 se supere (452, 453).** Hoy es casi seguro si noviembre se repite. Dos caminos: dejar la cota y dejar escrito que superarla es el costo esperado y que la pregunta es dónde (Cordón Caulle); o medir una cota por volcán. No recalibrar con la semana de la sombra sin decirlo (A115).
3. **Decir a Nicolás la falsa alarma real al pedir cualquier lectura de las cotas (453)**: 12 a 28 %, y que la cota (ii) de VIIRS 750 casi no distingue un empeoramiento al doble.
4. **Cerrar o re-decidir cada ítem de §5 antes del merge (454).** Como mínimo: generalizar `scripts/revisar_errores_modis_nrt.py` a VIIRS (no toca `pipeline/`), y dejar en la bitácora la excepción al congelamiento. Si Nicolás acepta mover alguno a «después», que quede como frase suya.
5. **Rehacer las puntas que encienden (458).** Actualizar #974 sobre `main`, CI verde y verificador limpio sobre esa punta; recién entonces rehacer #983 sobre ese #974; cerrar #975; una sola numeración de la ficha.
6. **Preparar la reversión de B1 con B2 adentro antes de mergear B2 (457)**: la rama resuelta y con CI, o el PR previo que generaliza las 8 pruebas, que el propio #974 sugiere.
7. **Preguntar a Nicolás si el encendido de VIIRS lleva un aviso de texto temporal (456)**, dado el salto de 1,3 a 3,2 veces y que Chillán está en erupción.
8. **Al pedir la frase de B2, decir el alcance (455, 459)**: P1 probado en Láscar y Chillán; Cordón Caulle VIIRS 750 en 0,57 con n 3. Proponer leer `region_sensible` del vigilante a los 14 días con un criterio escrito antes.
9. **Acortar el camino del silencio al issue (461)**: adelantar el cron de la guardia o dispararla con el cron externo que ya usa el NRT, y cambiar «el mismo día UTC» por un plazo en horas desde el issue.
10. **Que la vigilancia informe las alertas de MIROVA en pasadas sin record de la vía, también las débiles (460)**, y que el procesador deje en el log por qué no escribió.
11. **Decidir qué pasa con el lector de V375-E (463)**: llevarlo a `main` leyendo K desde `data/guardia_k_viirs/`, o declarar por escrito que la ventana P no se lee.
12. **Declarar las vías apagadas en `_s154_reproc_k_historico` o renombrarlo (462)**, antes de que el plan de reemplazo de la historia lo use.

## 6. SEGUIMIENTOS (fuera de mi eje)

- En la sombra, Tupungatito VIIRS 750 2026-11-07 05:30 (MIROVA 0,11 MW): la vía tiene 0 píxeles y K un cúmulo de 0,0 MW. El «hallazgo 101» de la auditoría S175 no se arregla con la vía en ese caso (n 1). `pcc_v750_salida.txt`. Confianza: CONFIRMADO para esa pasada.
- En Cordón Caulle VIIRS 375 la vía no alerta donde MIROVA publica 0,09 y 0,36 MW: el port y el MIROVA operacional difieren ahí. `detalle_sombra_salida.txt` (c). Confianza: CONFIRMADO el hecho, causa SIN ATRIBUIR.
- `experiments/_s178_cotas_v375/INFORME.md` cita `scripts/vigilancia_guardia_viirs.py:149` para `bp.cargar_nuestros`; en `438a60a1e` esa llamada está en la l. 153. Cita corrida, gravedad 1.
- `scripts/clase_mirova.py` cambió entre `s172-retro-d2` y `438a60a1e` («la tabla decide», #970): toca qué es protegida en MODIS y VIIRS 750. Frente A o C.
- Los issues #968 y #969 («vigilancia ciega» del 2026-11-09) seguían abiertos el 2026-11-10 20:37 UTC aunque la vigilancia ya da VERDE.
- Decisiones de MODIS (regla de MODIS, reemplazo de la historia, #955, #981): frentes A y D.
- Decisiones de instrumento de S178 («Sí, opción A», «Sí, opción 1», caja B4, OSF local): frente C.

## 7. VERIFICADO LIMPIO

| Qué | Contra qué vara | Comando | Resultado |
|---|---|---|---|
| Los PR sólo tocan perfiles, pruebas y documentos | «sólo el flag» (A45 de S177) | `git diff --stat 438a60a1e...bbbe2068d` y `...e68819484` | 22 y 25 archivos; ninguno en `pipeline/*.py`, `data/`, `frontend/`, `scripts/` |
| El flag efectivo cambia sólo donde se aprobó y la guardia sigue en K | `pipeline.profile` resuelto en proceso aparte (A89) | `python flags_por_perfil.py` | `mirova_equivalent` False a True; `guardia_k_viirs`, `guardia_k_modis`, `experimental`, `experimental_ndc_focus`, `_s146_ab_control`, `_s172_retro_k` quedan en False |
| La regla sellada y el vigilante de main son los del tag del sello | tag `s178-regla-reversion-viirs-sellada` | `git diff --stat s178-regla-reversion-viirs-sellada 438a60a1e -- <regla> scripts/vigilancia_guardia_viirs.py scripts/vigilancia_guardia_modis.py` | vacío |
| El Poisson de las cotas | las falsas alarmas que publica la regla | `python cotas_poder.py`, parte 1 | 0,058; 0,057; 0,045; 0,053 |
| La exposición que usó la calibración de VIIRS 375 | censo propio con el predicado del tablero, ventana O, NOAA-20 y NOAA-21 | `python cotas_poder.py`, parte 2 | 454 Muy Bajo y 2.068 negativos que K calla, contra 464,5 y 2.062,7 ponderados |
| El nulo de la guardia tiene sustrato | pares guardia y producción a 120 s, publicación y VRP mostrado | `python cotas_poder.py`, parte 3 | VIIRS 375: 223 pares, 84 publicados en 8 volcanes, 0 distintos, VRP idéntico; VIIRS 750: 220, 28, 0 |
| El vigilante ve lo que tiene que ver | controles propios | `python sim_vigilancia.py`, escenarios N, M y P | K contra K: 0 de 38 y 0 de 98 (0 de 8 y 0 de 164 en VIIRS 750); brazo mudo: 20 y 19 candidatas; siempre publica: 93 de 98 y 161 de 164 |
| Ninguna protegida callada por la vía en la semana de la sombra | el vigilante de main, regla §4.3 | `python sim_vigilancia.py`, escenario A | 0 candidatas; 19 de 19 y 18 de 18 protegidas con record publicadas; sobre-publicación 0 de 86 y 0 de 155 |
| El tablero muestra bien un record de la vía | predicado ejecutado con node | `python detalle_sombra.py`, (b) | 0,991 (n 50) y 1,000 (n 21) de MIROVA |
| La evidencia se midió con el código que se va a encender | `git diff` de `pipeline/` | `git diff --stat a7a6ae360 438a60a1e -- pipeline/ ':!pipeline/profiles'` | sólo `pipeline/fetch.py` |
| P1 no depende del brazo de posición | `lectura.json`, `otros_brazos.radiante` | lectura directa | `P1_veto` vacío en cercano y en radiante |
| Las citas archivo:línea de la regla al vigilante | `scripts/vigilancia_guardia_modis.py` en `438a60a1e` | lectura de las l. 229, 252, 254, 265, 312 y 318 | calzan |

## 8. SIN DATO

- La suite de pruebas sobre `main` más #974 y sobre `main` más #983: no pude armar el árbol. Por eso 458 dice «CI anterior», no «CI roto».
- Si el revert de B1 con B2 adentro choca como dice el PR (457).
- El tiempo del NRT con la vía y el dibujo en navegador.
- Por qué la vía no tiene record en Láscar 2026-11-04 05:42 y Cordón Caulle 2026-11-08 06:06 (460).
- El contenido de `PREREGISTRO_V750A.md` y del lector de V750-A; la caja B4.
- Mi nivel de esfuerzo.
- El texto completo de las entradas S172 a S175 de la bitácora.

## 9. FUERA DE ALCANCE

MODIS (frente A), el instrumento de la retrospectiva (frente C), el plan de reemplazo de la historia y los 34 volcanes (frente D). No arreglé nada ni toqué ningún archivo fuera de mi carpeta.
