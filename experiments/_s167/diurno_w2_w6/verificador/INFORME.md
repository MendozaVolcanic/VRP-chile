# Verificación limpia de la lectura del A/B diurno sobre K (W2 a W6), S167, verificador 2

Veredicto: **CONFIRMADO CON RESERVAS.** La lectura aplica la letra del pre-registro (v3.1 más adenda 1, opción e-ii) y mi
re-ejecución independiente da salida idéntica. Las reservas son de alcance, no de cuenta (abajo).

Carpeta de trabajo: `D:\vrp-trabajo\temporales\s167_diurno_verif2\`. Caminos previos escritos antes de comparar:
`D:\vrp-trabajo\temporales\s167_diurno_verif2\CAMINOS_PREVIOS.md` (22 caminos).

## 1. Lo comprobado

1. **Árbol de código limpio.** Lo armé con `git -c core.autocrlf=false archive 4b86059706d9fd52c8bf166f485446a0e40652b5`
   más `objetivos_adenda1_sha256.txt` de `af5af6a17`. Los 29 blobs del sello (`objetivos_sha256.txt` de `68687d2d4`) calzan
   29 de 29; el árbol extraído calza 28 de 28 (el 29.o, `PREREGISTRO.md`, es el de la adenda: sha `44c3b011...` igual a
   `origin/main` y a lo que sella `objetivos_adenda1_sha256.txt`). Los 7 de la adenda calzan 7 de 7. `evaluar_diurno_k.py` =
   `d6eb25b5...` igual en el árbol del lector.
2. **Hallazgo de contaminación (no de la lectura):** `D:\vrp-trabajo\temporales\s167_diurno_verif\codigo` estaba siendo
   mutado en vuelo por la corrida PID 4492 (su `evaluar_diurno_k.py` tenía 42129 bytes contra 42161 sellados y sha
   distinto). Una copia mía de ahí era un evaluador mutado; la descarté y rehice el árbol desde git. Quien reutilice ese
   directorio sin esta advertencia mide un evaluador roto.
3. **Batería:** 109 pruebas en verde (82 de `test_evaluar_diurno_k`, más las de exclusión, días excluidos y perfiles), en
   mi árbol limpio, 14 s, con TMP en D:.
4. **Re-ejecución completa:** `dias_excluidos_nasa.py` (consulta CMR propia, 2026-10-29T05:01:55Z): **cero días sin
   gránulos**, `excluir_dias = []`; regla (b) original informativa tampoco excluye nada (el control pierde 7 noches de
   VIIRS 750 pero sin día vacío en CMR). `evaluar_con_exclusion.py` con `--sha-codigo 68687d2d4b73bb0527da18a2c886a6dcc241a0ac`,
   `--opcion-e e-ii`, lista vacía: **salida idéntica línea a línea** a `s167_diurno_lectura\evaluar_con_exclusion_salida.txt`
   (excluida sólo la hora de consulta). Salida mía: `evaluar_salida.txt`.
5. **Letra del §6.3.** Barrí las 16 combinaciones de veredicto por sensor (ADOPTAR, NO ADOPTAR, SIN CAMBIO, DECIDE M4)
   contra mi propia lectura del §6.3 en el orden escrito: 0 diferencias (`s7\matriz63.py`). INVÁLIDO, INDECIDIBLE y R1 con
   compuertas verdes también se comportan como dice el texto. Con V375 ADOPTAR y V750 ADOPTAR, la regla "VIIRS 750 en
   ADOPTAR" da DECIDE NICOLÁS (la lectura es correcta); no dispara "DECIDE CON M4" porque ningún sensor está en el caso e.
6. **§6.4.** `veredicto_final` sólo reescribe si el principal es ADOPTAR o NO ADOPTAR; aquí el principal ya es DECIDE
   NICOLÁS, así que las cuatro variantes no agregan motivo. Las cifras de cada variante (tabla sola, sin W2, sin reflejo,
   "otra" como negativo) están en `detalle_variantes_salida.txt` del lector y reproducen el principal. Las de mínimas (SE,
   original, SN 0,04) y el filtro de 12° no cambian nada.
7. **Binomiales** (recomputé): D V375 `P(Bin(36; 0,00223) >= 14) = 2,7e-28`; D V750 con Q_d = 0 cumple por regla. I4 V375:
   `P(Bin(2547; 0,0011) >= 7) = 0,0247`, así que 0 sin record pasa con holgura; I4 V750: `P(>=22) = 0,0466`, `P(>=21) = 0,074`,
   `P(>=17) = 0,32`: 17 de 2.499 pasa (umbral 22) como dice la lectura. Con 5 pasadas más habría sido INVÁLIDO.
8. **Mutaciones.** Ver sección 3: mi corrida propia **no se completó**; reporto la del verificador anterior.

## 2. Reflejo solar (§7, A76)

Cálculo desde los records del brazo (`s7\reflejo.py`, `s7\clase_nuestra.py`, evaluador sellado y su `angulo_reflejo`):

| publicación | MW | elevación solar | ángulo de reflejo | instrumento 1.13 a) | lo marca la regla del §7? |
|---|---|---|---|---|---|
| V375 Chillán 2026-10-09 19:12 (negativo, 0,54 km del cráter, 1 píxel) | 4,07 | 42,3° | 76,8° | consistente (noche máx. 11,8 MW, n = 14) | **No.** Sin reflejo especular (>12°) y proporcional a la actividad nocturna; el volcán está en erupción (alertas protegidas 10-08, 10-10, 10-11) |
| V375 PCC 2026-06-13 18:00 (negativo, 17,3 km, 2 píxeles) | 1,14 | 24,2° | 65,4° | consistente (razón 2,15 < 3,16 contra 0,53 MW nocturno) | **No.** Sol bajo, sin reflejo especular. Cuenta como error igual, por letra |
| V750 Chillán 2026-10-10 18:54 (pasada "otra") | 4,15 | 45,7° | 51,2° | consistente (noche máx. 10,5 MW, n = 12) | **No.** Misma pasada de Suomi NPP en que MIROVA alertó V375 (4,09 MW propios); en la variante "otra como negativo" cuenta +1 |

Ninguna de las 36 publicaciones diurnas del brazo tiene ángulo de reflejo bajo 12° (mínimo 29,8°), así que el filtro de MIROVA
no apaga nada (coincide con la salida). Ninguna de las 3 cambia un veredicto: las dos de V375 ya están en el neto (cuentan
+1 cada una y son parte de las 5 que compensan las 5 alertas bajo 1 MW recuperadas); la de V750 sólo mueve la variante d de
"DECIDE NICOLÁS" a "DECIDE NICOLÁS CON M4", ambas hacia Nicolás. Las 13 de 17 pasadas de "reflejo probable" del estudio 1.13
que la variante c saca son protegidas **no** recuperadas; las 9 protegidas recuperadas no están en esa lista.

## 3. Mutaciones (§5.2 y adenda 1)

- **Mi corrida propia: NO VALE.** Se lanzó doble sobre el mismo árbol (dos bucles `mutar.py` concurrentes, hallados al
  matar el proceso por disco; el mensaje cortado de mi turno repitió la orden): dos mutadores alterando el mismo archivo no
  miden nada. La descarté y maté mis procesos. Luego **C: bajó a 2,0 GB libres** (otras sesiones: `mutar_evaluar_v750a.py`
  escribe a `C:\Users\...\Temp\claude\...` y `mutar_evaluar_f4.py --paralelo 6`; los míos escribían sólo a D:, y no había
  ningún proceso mío vivo al momento de la caída final). Por la regla de parar bajo 3 GB no relancé.
- **Reporto la del verificador anterior** (completa, terminó 02:08), `s167_diurno_verif\mutaciones_salida.txt`, sobre
  `mutaciones.json`: línea base 82 pruebas verdes; **67 mutaciones, las 67 ATRAPADAS por aserción (sin caídas)**; el control
  `C-CAIDA` sale CAIDA (38 caídas, no cuenta), como corresponde (68 entradas, "67 de 68"). Cuadra con el §5.2 (60 + M57 a M61 +
  X1 a X7; no existe M33). **No la reproduje yo**; tampoco corrí `mutaciones_dias_excluidos.json` (10) ni
  `mutaciones_exclusion.json` (9) más allá de la línea base verde de sus pruebas.

## 4. Hallazgos

| id | gravedad | hallazgo | evidencia |
|---|---|---|---|
| VD167-01 | 2 | **Estrato sin etiqueta (A118):** 13 publicaciones diurnas del brazo (12 de V375, 1 de V750) caen en pasadas que la tabla de MIROVA no lista, así que no entran a negativos, a "otra" ni a ninguna cuenta. 7 son de 1 MW o más (Tupungatito 08-30 2,25 MW y sin ninguna publicación nocturna a ±72 h; Villarrica 08-19 2,41 y 08-23 2,34; Lastarria 10-12 1,63; Chillán 10-01 1,70 y 4,21, y V750 10-01 2,99). El pre-registro lo declara ("una pasada que no se lista no entra a ninguna cuenta") pero el INFORME del lector no cuantifica el estrato y su "pub en otra 0" para V375 puede leerse como "nada fuera". Si se contaran como negativos, V375 pasaría de neto 0 a +12 (caso e, DECIDE M4); Villarrica y Chillán probablemente son reales. Decide Nicolás | `s7\estratos_pub.py` |
| VD167-02 | 2 | **El ADOPTAR de V375 es de filo:** neto exactamente 0 (5 negativos publicados contra 5 alertas bajo 1 MW recuperadas, 9 bloques, p = 0,61, EMPATE). Con "tabla sola" el neto es +1 y el sensor cae en e-ii (4 de las 5 recuperadas bajo 1 MW viven en el canal combinado); con "otra" como negativo V750 cae en e-ii. La lectura lo dice en su tabla, y por la letra del §6.4 no cambia el global (el principal ya es DECIDE NICOLÁS), pero "ADOPTAR" por sensor no debe presentarse sin esa fragilidad | `evaluacion_W2_W6.json`, `detalle_variantes_salida.txt` |
| VD167-03 | 1 | El beneficio está concentrado en la erupción de Chillán de W6 (5 de 9 protegidas V375; 2 de 2 en V750, las mismas pasadas Suomi y NOAA-21 que V375), y en V750 el "cumple D" es por Q_d = 0 con 2 eventos que son 1 episodio. La regla sellada lo permite; no sostiene "el brazo funciona en VIIRS 750" fuera de Chillán | listas de protegidas recuperadas |
| VD167-04 | 1 | I4 de V750: 17 pasadas sin record en 2.499 (0,68 %) son el doble de la tasa nocturna del sustrato (9 de 2.650, 0,34 %), y pasa sólo porque la vara es la cota de Clopper-Pearson (umbral 22). Las 17 son RUTINA de 0 MW (no sesgan a favor del brazo) | `detalle_variantes_salida.txt` |
| VD167-05 | 3 (proceso, no de la lectura) | `s167_diurno_verif\codigo` se mutó en vuelo durante mi sesión; cualquier medición hecha ahí mientras corre `mutar.py` usa un evaluador mutado (y mi propio mensaje duplicado lanzó dos mutadores sobre un árbol) | tamaño 42129 contra 42161 bytes, sha `df1dc52f...` contra `d6eb25b5...` |

Ningún hallazgo cambia los veredictos por sensor ni el global: V375 ADOPTAR (caso b), V750 ADOPTAR (caso b), global y final
DECIDE NICOLÁS.

## 5. Lo no comprobado

- Mis propias mutaciones (disco y doble lanzamiento); se apoya en la corrida del verificador anterior.
- Tablas de MIROVA y OCR (canal unión, regla de mínimas SN) y la referencia fuente: sólo comprobé que los 4 CSV congelados
  calzan con `sustrato_k.json` (lo hace el propio evaluador, `ref distinta: []`), no su origen.
- Si Villarrica/Chillán/Tupungatito de VD167-01 son MIROVA-ciegos o reales: sin SWIR ni imagen.
- Los 5 commits de salidas por ventana y el reparto de intentos (me basé en `cobertura.txt` y los runs que cita el lector).
