# Verificación S172, Chillán (CH172-01 a 04 y 07)

## 1. Encabezado

- Hora del servidor (cabecera Date de GitHub): al empezar Sun, 01 Nov 2026 23:58:17 GMT; al cerrar Mon, 02 Nov 2026 00:13:49 GMT.
- Commit medido: `14fb62030a186fda02ce2ba172866cf01408eeb9` (origin/main; la API de GitHub lo confirma como cabeza a las 23:34:32Z del 1-nov). Es el mismo commit del auditor (`D:/vrp-trabajo/temporales/s172_chillan/COMMIT.txt`).
- Modelo y esfuerzo: Claude Sonnet 5.5 (`claude-sonnet-5-5`), esfuerzo bajo, contexto limpio (no abrí `INFORME.md` ni `hallazgos.csv` del auditor; sí leí sus scripts y salidas crudas, como pedía la tarea).
- CARPETA: `D:/vrp-trabajo/temporales/ver_s172_chillan/`
- caminos.md escrito ANTES de abrir ningún archivo citado: `D:/vrp-trabajo/temporales/ver_s172_chillan/caminos.md`. sha256 del contenido previo a la nota final: `3615e45881123e6c54cd356a60a60e7221e1735c4ce3159f0ff209a3a4618bca`; hora al cerrar: 2026-11-01 23:58:57 UTC; sha256 del archivo con la nota agregada: `89f4babcb90e55c44d6812efe6eb031d1b58aad5fc69e9e1e3c15995bb359e7a`. No lo volví a editar.
- Copia de la referencia (la de origin/main hoy, a 14fb620), sha256 en `salidas/sha256_copia.txt`: consolidado `ab1a208c89b32df2fd5622c102ac2a984fa8a0102cfe0fe9f65cb8ff54b7d88f` (llega al 2026-10-26 12:40), OCR `d4ad8c44d5112ca44751552d4aee6e920c20ac5dc0d73f4fc5d9f6594785026e`, `NevadosDeChillan.json` `8f481c496f930442a2568c1dcd9e4e7801f9b53a790f1c8ace2f5abbfcd4fa8f`, `frontend/index.html` `fda0a628514de93e5afb90eb7115423c739d4aa9596708311d26a6fd4e4f5d2c`. Son idénticos a los del auditor (`INSUMOS_SHA256.txt`).
- Para la prueba fuera de muestra (27-oct a 1-nov) bajé el consolidado remoto de Mirova-v1 con una llamada a la API (1 de 20): `ref_remota/registro_vrp_consolidado_remoto.csv`, sha256 `dac888c94482d97cbf4158263773374d1a5f732a387f7da43cf14d2c50ebf5b6`, llega al 2026-11-01 22:05. Esa prueba usa una referencia distinta de la de origin/main; está rotulada así.
- Qué NO miré: no re-corrí el port MATLAB de V750-C (las grillas no están en disco; usé su `ablacion_por_pasada.csv` de `D:/vrp-trabajo/papelera_s171/`, sha256 `db4e6ef7e485790669048daedc3713ef674b44ab0738d4a474e8793d0f01f77d`, de lectura). No verifiqué qué es el brazo `V` de MOD-D ni sus falsas publicaciones. No miré pasadas diurnas ni otros volcanes más allá del control de generalidad. No abrí `modd_INFORME.md`, `v375e_*` ni los INFORME del auditor.
- Tocado fuera de CARPETA: sólo metadatos de git del árbol compartido por `git fetch origin claude/s170-modd-f4-procedencia` y `git fetch origin main` (escriben `.git/FETCH_HEAD`). Sin checkout, pull, commit, push ni workflow.

## 2. En una pantalla

- CH172-01 CONFIRMADO (mi gravedad 3): los tres Spearman y los rangos barajados reproducen exactos, y por otro camino (sólo tabla CONS, bootstrap por noches, parcial por plataforma y por fecha, sólo código K puro) se mantienen. Replica fuera de muestra del 27-oct al 1-nov: -0,81 (n 8), -0,62 (n 11), -0,90 (n 11). Reserva: en MODIS la prueba dentro de una misma noche es débil (4 noches con 2 pasadas).
- CH172-02 CONFIRMADO en los hechos (3 de 3, cenit 57,58 a 58,19), CONFIRMADO EN PARTE en la lectura (mi gravedad 3): n 3 en 2 ranuras orbitales, dos modos de falla distintos (0 píxeles alertados en dos, 1 píxel con 0,0 MW en la tercera), MIROVA bajo (1,7 a 3,8 MW), y las tres noches sí se publicaron en VIIRS.
- CH172-03 CONFIRMADO como lectura (0,684, n 22; yo lo reproduzco de `ablacion_por_pasada.csv`) pero subestimado: son 22 de 28 alertas; contando las 6 no publicadas como 0 la mediana es 0,548, y el brazo reproduce la dependencia con el cenit (Spearman -0,52) que el port completo no tiene (+0,05). Gravedad 3.
- CH172-04 CONFIRMADO EN PARTE (mi gravedad 1): las seis cifras reproducen, pero es una diferencia de estadístico ya documentada en el código y los tres valores nocturnos ya levantan flag de SUB-estima.
- CH172-07: 01 y 02 NO son nuevos como dirección (S154, S157 §2.2, SINTOMAS §1, flags del auto-audit del 26-oct); lo nuevo es la inferencia estadística, la ventana hasta el 1-nov, la pasada del 25-oct y la lectura dentro de noche. No contradicen lo vigente; no atribuyen D17 ni D25. Veredicto global en la sección 6.

## 3. Hallazgos propios (VCH172)

### VCH172-01
- TÍTULO: la mediana 0,684 del fondo de anillo solo en V750 cubre 22 de 28 alertas, y ese brazo reproduce la caída con el cenit
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `vch_07_fanillo_vs_z.py` : `salidas/v09_fanillo_vs_z.txt`; datos `D:/vrp-trabajo/papelera_s171/s162-viirs750-f63ef4/experiments/_s162_v750c/ablacion_por_pasada.csv` (sha256 `db4e6ef7...`)
- QUÉ PASA: cuando el fondo es la mediana del anillo de 5 a 25 km (como K) en vez del fondo interpolado bajo el halo del código de MIROVA, los píxeles oblicuos, que tienen poco exceso sobre ese fondo, quedan en cero o negativos y la pasada ni se publica. En las 28 alertas de Chillán que deciden el brazo `O_fanillo` publica 22: mediana 0,684 sobre esas 22; con las 6 no publicadas contadas como 0 la mediana es 0,548. Las 6 están a cenit 31,1, 55,8, 64,3, 65,5, 68,0 y 68,0. El port completo `O` da 0,996 sobre las mismas 22 y 0,998 sobre las 28, y su Spearman con el cenit es +0,05; `O_fanillo` con ceros da -0,52 (publicadas solas, -0,35). Por tramo de cenit (ceros incluidos): <30° 0,743 (n 7), 30 a 50° 0,506 (n 9), >=50° 0,138 (n 12).
- CÓMO SE VE EN EL DASHBOARD: invisible (es un ablación sobre el port, no el pipeline); lo que sí se ve es la misma firma en K: magnitud baja y pasadas oblicuas sin publicar.
- CÓMO REPRODUCIRLO: `cd D:/vrp-trabajo/temporales/ver_s172_chillan && python -B vch_07_fanillo_vs_z.py`. Ventana de las 28 alertas: 2026-09-28 04:42 a 2026-10-17 06:18 UTC, VIIRS 750 de las tres plataformas.
- CONFIANZA: CONFIRMADO (lectura del CSV y script propio). Que el efecto del fondo sea LA causa del déficit de K en V750 no lo mide esto (K da 0,418 por pasada en V750, n 39, ventana 2026-09-29 a 2026-10-26, que no es el mismo conjunto de pasadas; el port con fondo de anillo da 0,55 a 0,68).
- GRAVEDAD: 3 (cambia qué palanca se prioriza en V750; no toca una alerta).
- Preguntas del instrumento: (1) si el brazo estuviera roto, el control positivo es el port completo `O`, que da 0,996 y se ve distinto; (2) si `ablacion_por_pasada.csv` estuviera muerto o vacío, `alertas` saldría 0 y se imprime `con z 0`, no 0,684. Denominador: 28 alertas que deciden de Chillán, 28 de 28 con cenit unido por hora.

### VCH172-02
- TÍTULO: las tres protegidas MODIS perdidas comparten el cenit pero no el mecanismo ni la potencia, y son dos ranuras orbitales
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `vch_06_modis_perdidas.py` : `salidas/v06_perdidas_modis.txt`; `salidas/r02_pasadas.csv`
- QUÉ PASA: las cuatro pasadas MODIS con alerta de MIROVA que K no publica (29-sep 07:20, 12-oct 07:20, 15-oct 01:05, 25-oct 07:20) están a cenit 58,42, 58,19, 57,58 y 57,98. La del 29-sep (0,13 MW) no es protegida. De las tres protegidas, dos (12-oct y 15-oct) tienen 0 píxeles alertados y `diag_n_first_pass_pixels` 0 (el detector no vio nada); la del 25-oct tiene 1 píxel alertado a 4,34 km con `vrp_mw` 0,0 (exceso recortado a cero, el modo "cráter en 0,0 MW" de D25). MIROVA da 2,18, 1,72 y 3,79 MW, contra 3,5 a 26,5 MW en las 12 pasadas MODIS que sí publicamos. Tres pasadas son dos ranuras: Aqua 07:20 (dos de ellas, 13 días entre sí) y Terra 01:05. K sí publica a 54,0° (12,97 MW de MIROVA) y a 62,8° (7,09 MW, razón 0,076): no hay umbral de cenit monótono. Entre las 8 pasadas MODIS con cenit 57,5 a 58,5 en la ventana, MIROVA alertó en 4 y K publicó 0 de 8.
- CÓMO SE VE EN EL DASHBOARD: MODIS sin marca esas tres pasadas; la noche sí aparece publicada en VIIRS 375 y 750 (`salidas/v10_noches_cubiertas.txt`: 12-oct 2 de 4 y 1 de 3; 15-oct 4 de 4 y 4 de 4; 25-oct 5 de 6 y 5 de 6).
- CÓMO REPRODUCIRLO: `python -B vch_06_modis_perdidas.py`; ventana 2026-09-29 a 2026-10-25, MODIS_AQUA y MODIS_TERRA.
- CONFIANZA: CONFIRMADO en los hechos; SOSPECHA en que el cenit sea la causa (n 3, rango escogido mirando los resultados, 2 ranuras, potencia de MIROVA baja como confusor). Las fuera de muestra del 27-oct al 31-oct no traen ninguna pasada MODIS con alerta cerca de 58° (`salidas/v08_modis_perdidas_heldout.txt`), así que no hay réplica.
- GRAVEDAD: 3 (pierde alertas protegidas por sensor, no por noche).
- Preguntas del instrumento: (1) si la pérdida fuera falsa, el record nuestro mostraría pixeles alertados; salen 0, 0 y 1 con 0,0 MW; (2) si el JSON no se hubiera leído, no habría filas (se imprimen 4).

### VCH172-03
- TÍTULO: en MODIS la dependencia con el cenit descansa en comparaciones entre noches; dentro de una misma noche no se distingue del azar
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `vch_03_dentro_de_noche.py` : `salidas/v03_salida.txt`
- QUÉ PASA: con efecto fijo por noche (las pasadas de una noche comparten el estado del volcán), la pendiente de la razón por grado es -0,0278 en MODIS (IC95 por bootstrap de noches -0,082 a -0,0038, sólo 4 noches con 2 pasadas, 8 pares) y el nulo de cenit barajado dentro de la noche da -0,0293 a +0,0293, que la contiene. En V375 es -0,0141 (IC -0,0212 a -0,0057; nulo -0,0101 a +0,0095; 17 noches) y en V750 -0,0358 (IC -0,0457 a -0,0271; nulo -0,0171 a +0,0204; 12 noches). Control positivo: inyectar -0,03 por grado mueve la pendiente exactamente -0,03 en los tres. La pendiente de MIROVA en la misma noche es -0,0054 (MODIS), +0,0028 (V375) y -0,0114 (V750): la caída en V375 y V750 es sobre todo nuestra, pero en V750 MIROVA también baja (aprox. 0,71 sobre 30°).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -B vch_03_dentro_de_noche.py` (lee `salidas/r02_pasadas.csv`, que es la salida del s02 del auditor re-corrida por mí y byte a byte igual a la suya).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### VCH172-04
- TÍTULO: CH172-01 y 02 se presentan como hallazgo pero la dirección ya estaba medida y en parte publicada
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `experiments/_s154_chillan/razon_por_cenit_salida_20261018.txt`; `experiments/_s157_magnitud_chillan/README.md` §2.2 (sha256 de mi copia `77b63e98...`); `docs/SINTOMAS.md` §1; `scripts/auto_audit_weekly.py` l. 771 a 777 y 850 a 859; `data/audit_continuous/latest.json` (generado 2026-10-26T16:09:56Z), claves `flags` y `magnitud_publicada_by_vol_sensor_cenit`
- QUÉ PASA: S154 (18-oct, 10 pasadas) ya mostraba la caída con el cenit; S157 §2.2 (K, 87 pasadas de Chillán) la tabuló por sensor: V375 0,73 / 0,58 / 0,45, V750 0,84 / 0,41 / 0,16, MODIS 0,75 / 0,20 / 0,20 en <30 / 30 a 50 / >=50°. Esos números casi coinciden con los de hoy por tramo (V750 0,845 / 0,413 / 0,105 en <30 / 30 a 50 / >=60 (s03)). El docstring de `alertas_protegidas` ya cita por fecha las dos primeras protegidas MODIS ("2026-10-12 07:20, 2,18 MW; 2026-10-15 01:05, 1,72 MW", TEXTO, `scripts/auto_audit_weekly.py` l. 855 a 856) y `latest.json` ya lista las tres con la pasada del 25-oct. El auto-audit ya estratifica por cenit y lleva `n_misma_pasada`. Lo nuevo es la inferencia (Spearman con permutación, bootstrap por noches), la ventana hasta el 1-nov y la lectura dentro de noche.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git -C <repo> show origin/main:docs/SINTOMAS.md | sed -n 28,75p`; `python -c "import json;d=json.load(open('copia/data/audit_continuous/latest.json'));print(d['flags'])"` desde CARPETA.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2 (riesgo de duplicar trabajo o de reabrir lo cerrado, A113).

### VCH172-05
- TÍTULO: la vía V de MOD-D no tiene la dependencia con el cenit en las 12 pasadas MODIS pareadas de Chillán
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `modd/resultado_f4.json` (sha256 `312e2050c680eedad41b6d011a10bf81a5cffed21ee8f5b3f06356868ed4129d`, de la rama `claude/s170-modd-f4-procedencia`), clave `chillan.pares`
- QUÉ PASA: con las mismas 12 pasadas, la razón de K contra el cenit tiene Spearman -0,867 (idéntico al del auditor) y la de V (`razon_b`) tiene +0,497. La mediana de V es 0,926 a 30° o menos y 1,100 sobre 30°. V publica las 5 protegidas del tramo 50 a 60° (K, 2).
- CÓMO SE VE EN EL DASHBOARD: invisible hasta que se encienda la vía.
- CÓMO REPRODUCIRLO: leer `modd/resultado_f4.json`, tomar `chillan.pares` (12 elementos con `z`, `razon_k`, `razon_b`) y calcular el Spearman de `z` contra cada razón; mi cálculo dio -0,867 y +0,497 (se hizo en consola y no quedó en un archivo de `salidas/`; es recalculable en dos líneas). Ventana 2026-10-01 a 2026-10-26, MODIS.
- CONFIANZA: SOSPECHA en cuanto a lo que implica (n 12, no sé qué cambia V en la cadena, no medí sus falsas publicaciones a esos cenit); los dos Spearman son CONFIRMADOS.
- GRAVEDAD: 2.

## 4. Veredicto por afirmación

| ID | Veredicto | Mi gravedad | Base |
|---|---|---|---|
| CH172-01 | CONFIRMADO | 3 | `salidas/r03_salida.txt` (reproducción byte a byte), `salidas/v01_chillan_salida.txt`, `v03`, `v04`, `v05`, `v07` |
| CH172-02 | CONFIRMADO en los hechos, CONFIRMADO EN PARTE en la lectura causal | 3 | `v06`, `v10`, `modd/resultado_f4.json`, VCH172-02 |
| CH172-03 | CONFIRMADO como lectura, con matiz que la hace peor que lo dicho | 3 | `salidas/v09_fanillo_vs_z.txt`, VCH172-01 |
| CH172-04 | CONFIRMADO EN PARTE (cifras sí, "subestima" es diferencia de estadístico ya documentada) | 1 | `salidas/v02_salida.txt` |
| CH172-07 | ver sección 5 | n/a | |

Detalle de CH172-01 (numerador, denominador, ventana):
- Reproducción del auditor: `python -B D:/vrp-trabajo/temporales/s172_chillan/s02_pareo_por_pasada.py <copia> 2026-08-27 2026-10-26 salidas/r02` y `s03_estratos.py`. El CSV de pasadas es idéntico (`cmp`) y el JSON de s03 es igual en todo. MODIS n 12 (8 noches) rho -0,867, barajado [-0,483, 0,503]; V375 n 53 rho -0,500, [-0,250, 0,289]; V750 n 39 rho -0,814, [-0,332, 0,311]. Ventana de los datos: 2026-09-28 a 2026-10-26, noche, pares con alerta CONS más OCR (D-9 SN), publicados por el predicado del tablero con node (control del auditor `control_json_vs_node_difieren` 0).
- Mi camino: sin banco_paridad ni node, sólo tabla CONS, magnitud del JSON (f5_core en V375 con respaldo, pc.vrp_mw en los otros), pareo a ±120 s, mismo rango de fechas. MODIS n 12 rho -0,867 (p MC 0,0005; bootstrap por noches -0,988 a -0,475); V375 n 46 rho -0,463 (p 0,0014; -0,697 a -0,149); V750 n 36 rho -0,835 (p 0,0001; -0,930 a -0,655). Parcial dado fecha: igual (la fecha no es confusor: Spearman fecha contra razón entre -0,06 y +0,01).
- Plataforma (Simpson): dentro de plataforma los Spearman son MODIS Terra -0,90 (n 5) y Aqua -0,82 (n 7); V375 NOAA-21 -0,51, SNPP -0,47, NOAA-20 -0,47; V750 NOAA-20 -0,92, NOAA-21 -0,57, SNPP -0,95 (n 8). Parcial dentro de plataforma -0,854 / -0,486 / -0,788.
- Mezcla de código: los pares traen 11 `codigo_sha` distintos (todos procesados entre 2026-10-18 y 2026-10-26, post K). Sólo con el sha del merge de K (`34cea39e`): MODIS n 8 -0,762, V375 n 41 -0,443, V750 n 29 -0,758.
- Fuera de muestra: 2026-10-27 a 2026-11-01 con consolidado remoto: MODIS n 8 -0,81 (p 0,020), V375 n 11 -0,62 (p 0,047), V750 n 11 -0,90 (p 0,0006). Ventana ampliada 09-28 a 11-01: -0,865 (n 20), -0,532 (n 58), -0,843 (n 47). Pendiente dentro de noche en esa ventana: V750 nuestra -0,0429 y MIROVA -0,0107 por grado.
- Control de generalidad (mismo script, `salidas/v01_todos_mar_oct_salida.txt`, 2026-03-01 a 2026-10-26): la caída es general en volcanes sin kernel local: Isluga V375 -0,52 (n 205), Lascar V375 -0,37 (n 192), V750 -0,36 (n 118), MODIS -0,40 (n 64), Tupungatito V375 -0,50 (n 113), Chaitén V375 -0,43 (n 37); plana en Lastarria (-0,01), Planchón-Peteroa (-0,03) y PCC V375 (-0,11), que tienen kernel local o inner grande. Chillán no es singular en V375; en V750 y MODIS tiene la caída más empinada de la tabla.
- Reservas: Spearman es asociación, no mecanismo. En MODIS el único apoyo dentro de noche es débil (VCH172-03). La razón lleva el VRP de MIROVA en el denominador (Spearman razón contra VRP de MIROVA: MODIS +0,22, V375 -0,25, V750 +0,01 según s03), que no explica el signo.

Detalle de CH172-04: reproduzco 0,56 / 0,662 / 0,683 a partir de las pasadas pareadas con el estadístico de `auto_audit_weekly.py` (máximo publicado de la noche sobre máximo de MIROVA; `salidas/v02_salida.txt`) y coinciden con `data/audit_continuous/latest.json`. Por pasada, mediana 0,362 / 0,571 / 0,418 (n 12 / 53 / 39). La brecha en MODIS no es de pareo distinto: `n_misma_pasada` es 8 de 8 noches; es peso (8 noches contra 12 pasadas, las segundas pasadas oblicuas bajan la mediana). En V375, las noches con una sola pasada pareada (n 4) valen 1,34 y empujan la mediana de noche; las de 2 o más pasadas valen 0,553. El docstring de `estratificar_magnitud` (l. 771 a 777) ya avisa que el tramo "NO es «la razón a ese cenit» pareada por pasada" (TEXTO, l. 774, A116). Los tres valores nocturnos ya levantan flag SUB-estima (< 0,7) en `latest.json`, así que cambiar de estadístico no cambia la decisión del veredicto.

## 5. CH172-07: qué hay de nuevo y qué confirma o contradice lo vigente

| Qué | Estado frente a lo vigente |
|---|---|
| La razón cae con el cenit en los tres sensores (01) | Confirma "La curva es real" de SINTOMAS §1 y la tabla de S157 §2.2. No es nuevo como dirección. Nuevo: Spearman con permutación y bootstrap por noches, replicado fuera de muestra, y la lectura dentro de noche (nuestra pendiente domina en V375 y V750; en V750 MIROVA también baja). Coincide con la rebaja de S158 (MIROVA no es plano), no con el "MIROVA plano" de S130. |
| Tres protegidas MODIS a 57,6 a 58,2° (02) | Dos ya estaban en SINTOMAS (l. 165) y en `auto_audit_weekly.py` l. 855 a 856 y en `latest.json`. Nueva: la del 25-oct 07:20 (posterior a S157) y la lectura de que MOD-D las publica (rama, no está en main). |
| Fondo de anillo solo, 0,684 en V750 (03) | No está en main: vive en la rama de V750-C. Es coherente con S157 (V750 con fondo cero G 0,96 a 1,22) y con 1.14 §3.4 (D25 sube con el ángulo). No contradice "en VIIRS 375 oblicuo ni con fondo cero se cierra": no mide V375. |
| Mecanismo "SIN ATRIBUIR" (1.14 §3.2) | Intacto. Una correlación con el cenit no separa D17, D25, selección ni recorte; ninguna de 01 a 03 lo hace. Lo más cercano a un argumento es VCH172-05: en MODIS la vía V quita la dependencia (n 12), lo que sugiere que en MODIS es de la cadena de K y no de MIROVA, sin decir cuál pieza. |
| D17 | 1.14 §3.2 midió que el Npix de MIROVA no crece hacia el borde; nada de lo nuevo lo contradice ni lo apoya. La distancia que reporta MIROVA sí sube con el cenit (Spearman de s03: MODIS +0,785, V375 +0,669, V750 +0,636, reproducido); es una pista de geometría, SOSPECHA, sin probar. |
| D25 | Consistente: el fondo de anillo reproduce la caída en V750 (VCH172-01). No es prueba de que adoptar D25 la cierre (D25 no se adoptó). |

## 6. Veredicto global: qué se puede afirmar a Nicolás y qué no

Se puede afirmar:
- En Chillán con K, entre el 28-sep y el 1-nov, la razón contra MIROVA cae con el cenit en los tres sensores, de forma robusta (replicada en datos que el auditor no usó) y sin explicación por fecha, plataforma ni versión de código.
- En V375 y V750 la caída dentro de una misma noche es sobre todo nuestra; en V750 MIROVA también baja algo.
- Tres alertas protegidas MODIS se perdieron entre el 12 y el 25-oct, a cenit cercano a 58°, y las tres noches sí se publicaron en VIIRS.
- En V750, el solo cambio de fondo a la mediana del anillo, aplicado al port de MIROVA, deja la razón en 0,55 a 0,68 (según se cuenten las no publicadas) y reproduce la caída con el cenit.

No se puede afirmar:
- Que la causa sea el cenit en el sentido del área del píxel (D17) ni del fondo (D25) en V375 o MODIS: sigue SIN ATRIBUIR.
- Que las pérdidas MODIS sean "por el cenit": n 3, dos ranuras, tres modos de falla distintos entre ellas, MIROVA bajo.
- Que esto sea hallazgo nuevo como dirección: ya estaba medido en S154 y S157 y flaggeado en el auto-audit.
- Nada sobre V375 oblicuo y fondo: no lo medí.

## 7. SEGUIMIENTOS (lo visto fuera de mi eje)

- SOSPECHA: el control negativo de pareo con +1 día y tolerancia de 120 s no cae a cero (28 de 94 pares con CONS sola; en el script del auditor 16 de 104). Los pares reales tienen diferencia horaria de 0 a 2 s (`control_dt_max_s` del auditor, `r02_resumen.json`), así que la tolerancia de `banco_paridad` (120 s) es más ancha de lo que usa un pareo real. No cambia ningún número aquí; la ancha tolerancia puede dejar pasar un pareo erróneo en otra ventana. `scripts/banco_paridad.py` l. 78 (`TOL_S = VENTANA_S`).
- SOSPECHA: la distancia que reporta MIROVA y el cenit se correlacionan (+0,64 a +0,79 en Chillán, s03 reproducido). Además la razón baja con la distancia de nuestro cúmulo al cráter (-0,43 / -0,45 / -0,25). Posible firma de paralaje o remuestreo; no probado.
- Observado: las pasadas perdidas del 29-sep, 12-oct y 15-oct se procesaron con código `34cea39e` y la del 25-oct con `17e356bb`; los records de la ventana traen 11 códigos distintos. El auto-audit ya separa por régimen sólo K contra el anterior.
- Observado: `latest.json` dice para las tres protegidas "la noche sí se publicó en otra pasada"; la regla incluye otras pasadas de cualquier sensor (`scripts/auto_audit_weekly.py` l. 891 y 948 a 950), no de MODIS. Cierto aquí, pero el texto no lo aclara.

## 8. VERIFICADO LIMPIO

- Reproducción del auditor, `python -B D:/vrp-trabajo/temporales/s172_chillan/s02_pareo_por_pasada.py D:/vrp-trabajo/temporales/ver_s172_chillan/copia 2026-08-27 2026-10-26 salidas/r02` y `s03_estratos.py salidas/r02_pasadas.csv salidas/r03.json`. Vara: sus propios números; `cmp` del CSV da igual y `r03.json == s03_salida.json`. Controles propios de s02 (los vi en `r02_salida.txt`): multiplicar por 2 duplica la mediana; `control_json_vs_node_difieren` 0; desplazar la referencia un día deja 0 / 10 / 6 pares.
- Pareo MODIS de K contra el resultado de MOD-D (control `s05` del auditor): 12 de 12 coinciden con `razon_k`; 0 con `razon_b`. Lo leí en `s05_salida.txt` y con mi propio Spearman sobre `resultado_f4.json`.
- Estadístico nocturno: `vch_02_noche_vs_pasada.py` reproduce 0,56 / 0,662 / 0,683 de `latest.json` (control positivo: duplicar nuestra magnitud duplica la mediana).
- Vara de cada verificación: el predicado del tablero con node (auditor) y, en mi camino independiente, la tabla CONS sola con la magnitud del JSON; por eso mi V375 (n 46) no es idéntico al del auditor (n 53 con OCR).

## 9. SIN DATO

- Re-ejecución del port MATLAB de V750-C con sus grillas: no están en disco. Usé el CSV por pasada.
- Qué es el brazo `V` de MOD-D y sus falsas publicaciones a 57 a 59°.
- Réplica fuera de muestra de CH172-02: no hay pasadas MODIS con alerta cerca de 58° después del 26-oct.
- Si el Spearman de V375 oblicuo se debe al área, el fondo o la selección (no es de estas afirmaciones).

## 10. FUERA DE ALCANCE

Cualquier arreglo, el encendido de MOD-D, D25, D17, y la tolerancia de pareo.

## 11. Archivos

Scripts (se quedan): `vch_01_independiente.py`, `vch_02_noche_vs_pasada.py`, `vch_03_dentro_de_noche.py`, `vch_04_plataforma_regimen.py`, `vch_05_solo_sha_K.py`, `vch_06_modis_perdidas.py`, `vch_07_fanillo_vs_z.py`. Salidas en `salidas/`. Antecedentes copiados con sha256 en `ant/`; MOD-D en `modd/`; V750-C en `v750c/`. `hallazgos.csv` en esta carpeta.
