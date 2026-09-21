# Verificador con contexto limpio: lectura preliminar del A/B de la conectiva (S148)

Afirmación auditada: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\S147_LECTURA_PRELIMINAR_CONECTIVA.md`
Instrumento auditado: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s147_lectura\lectura_por_tramo.py`
Datos: rama `origin/s146-ab/35548121381`, extraída con ruta a un temporal fuera del repo (18 MB).
Scripts y salidas crudas de esta verificación:
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s148_verificador_conectiva\`
Fecha: 2026-09-21. Tramo leído: 2026-09-01 a 2026-09-17, igual que la lectura.

## Veredicto

**LA LECTURA SE SOSTIENE CON SALVEDADES.** Los números se reproducen exactos con el instrumento y
con un recálculo independiente (cargador, etiquetado y predicado escritos de nuevo, sin importar
nada del repo). La caída NO es un endurecimiento parejo: el nulo por barajado lo descarta con
holgura, y un piso de magnitud no la reproduce. En VIIRS el brazo F NO apaga el camino contextual,
a diferencia de MODIS, y el recall no lo sostiene ningún camino ajeno a la conectiva.
Las salvedades: la frase "P2 se invierte" es más fuerte que el dato (8 numeradores, IC de 0,00 a
1,17), la magnitud publicada en las positivas baja (paridad contra MIROVA 0,781 a 0,716), y 30 de
las 124 positivas de F viven sólo del segundo pase. Nada de esto cambia el sentido de la lectura,
y sigue siendo preliminar: 17 días, 129 positivas, ventana completa pendiente.

## Hallazgos, por gravedad

### H1. "P2 se invierte" está sobre-enunciado: la razón 0,25 sale de 2 contra 6 publicaciones
- **Dónde**: `docs/S147_LECTURA_PRELIMINAR_CONECTIVA.md:46-50`; `lectura_por_tramo.py:106-107`.
- **Qué pasa**: la razón borde sobre nadir del brazo F es (2/153)/(6/116). Con numeradores de 2 y
  6, el valor puntual casi no tiene precisión. Que P2 se cumple (razón de 1,3 o menos) sí es
  robusto; que "el borde publica menos que el nadir, que es la forma de la curva de MIROVA" no
  está demostrado con estos datos, y la lectura física que sigue (líneas 49-50) se apoya en eso.
- **Cómo se ve** (`out_v3.txt`):
  ```
  IC 95 % bootstrap: 0.00 a 1.17 | fraccion de remuestras con razon <= 1.3: 0.980
  P(razon <= 0.253) con la zona barajada = 0.0440 (mediana del nulo 1.01)
  ```
  O sea: que la razón sea 1,3 o menos aguanta en el 98 % de las remuestras; que sea menor que 1
  tiene p = 0,044 contra "la zona no importa", marginal. Además las 10 sobrevivientes son de 4
  volcanes (Lastarria 4, Láscar 3, Planchón Peteroa 2, Chaitén 1) y las 2 del borde son ambas de
  Lastarria: una sola fuente puede mover la razón entera.
- **Reproducir**: `python v3_nulos.py <salidas> <congelado> 2026-09-17`.
- **CONFIANZA**: alta. **GRAVEDAD: 3**. No cambia el cumplimiento de P2; sí obliga a rebajar la
  frase y a no usar "0,25" como evidencia de que replicamos la curva de eficiencia de MIROVA.

### H2. La magnitud publicada en las positivas baja con `max`, y aleja la paridad contra MIROVA
- **Dónde**: `docs/S147_LECTURA_PRELIMINAR_CONECTIVA.md:83-84` lo declara "no mirado". Medido acá.
- **Qué pasa**: en las 124 positivas de VIIRS 375 que publican los dos brazos, la magnitud es
  idéntica en 99 y MENOR en 25 (nunca mayor). El cúmulo pierde vecinos: la mediana de píxeles del
  cúmulo pasa de 2 a 1. Es coherente con A99 y A103 (el déficit de magnitud ya era de vecinos
  tibios que MIROVA sí suma): un umbral más alto bota justo a esos vecinos.
- **Cómo se ve** (`out_v2.txt`, secciones 3 y 4):
  ```
  VIIRS375 pos n=124 | desplazamiento km: mediana 0.000, max 0.762, >0.5 km: 1, >1 km: 0
      razon magnitud publicada F/B: mediana 1.000, p10 0.781, ... min 0.249 | identica: 99 | F<B: 25 | F>B: 0
      n_pixels cumulo B mediana 2.0, F mediana 1.0
      suma magnitud publicada: B 20.988 MW, F 19.212 MW
  n=124 | mediana nuestra/MIROVA: B 0.781, F 0.716
  ```
- **Reproducir**: `python v2_pareo_y_caminos.py <salidas> <congelado> 2026-09-17`.
- **CONFIANZA**: alta. **GRAVEDAD: 3**. No es motivo de NO ADOPTAR por sí solo (la suma baja
  8,5 %), pero la conectiva mejora la decisión de publicar y empeora la magnitud, y el veredicto
  final tiene que decir las dos cosas.

### H3. 30 de las 124 positivas de F (y 8 de 11 en VIIRS 750) no tienen ningún píxel del primer pase: las sostiene el segundo pase
- **Dónde**: `pipeline/process_viirs.py:1306-1356` (segundo pase), `pipeline/detection_context.py:943`
  (el segundo pase también usa `combinar = max`), `pipeline/detection_context.py:545` (la compuerta
  de BT existe sólo en el primer pase).
- **Qué pasa**: el segundo pase del paper existe para recapturar vecinos de píxeles YA activos.
  Acá corre también con el conjunto activo vacío y publica por su cuenta. No es un camino ajeno a
  la conectiva (recibe `use_prose_branch`, comprobado en el código), así que NO invalida la
  lectura; pero el recall de F descansa en parte en una diferencia de implementación entre los dos
  pases (el segundo no tiene la compuerta `bt > t_bg + 3 K`, D22), no en el paper. Es la misma
  familia que A73 (recaptura sin soporte de primer pase). Si algún día se iguala el segundo pase
  al primero, el recall de `max` podría caer hasta 94 de 129 en VIIRS 375 y 3 de 16 en VIIRS 750.
- **Cómo se ve** (`out_v2.txt`, sección 6):
  ```
  VIIRS375 pos publicadas en F: 124 ... publicadas en F SIN ningun pixel del primer pase: 30
  VIIRS750 pos publicadas en F: 11  ... publicadas en F SIN ningun pixel del primer pase: 8
  VIIRS375 neg publicadas en F: 10  ... publicadas en F SIN ningun pixel del primer pase: 4
  ```
- **CONFIANZA**: alta en el conteo; media en la causa (no corrí el pipeline; la atribución a la
  compuerta de BT es SOSPECHA leída del código, no medida). **GRAVEDAD: 3**.

### H4. El instrumento clasifica la zona de cada brazo con el cenit de ESE brazo, y el cenit cambia entre brazos
- **Dónde**: `lectura_por_tramo.py:92-101` (usa `x["sensor_zenith_deg"]` del record del brazo).
- **Qué pasa**: `sensor_zenith_deg` no es una propiedad fija de la pasada: difiere entre B y F en
  240 de 814 pasadas de VIIRS 375 (hasta 2,03 grados), 60 de 809 de VIIRS 750 y 385 de 399 de
  MODIS, con el MISMO gránulo. En VIIRS 375 ninguna cambia de zona, así que la tabla principal no
  se afecta. En VIIRS 750 cambia 1 y en MODIS 10, y por eso los denominadores por zona del
  instrumento no coinciden entre columnas (192 contra 191; 165/87/133 contra 164/85/136).
- **Cómo se ve** (`out_v3.txt`, última sección; `out_instrumento.txt`):
  ```
  VIIRS375 n=814 | cenit distinto en 240 | dif max 2.03 grados | cambian de zona 0
  VIIRS750 n=809 | cenit distinto en 60  | dif max 0.86 grados | cambian de zona 1
  MODIS    n=399 | cenit distinto en 385 | dif max 2.62 grados | cambian de zona 10
  ```
- **Arreglo sugerido (no aplicado)**: estratificar los dos brazos con el cenit y el `t_bg_k` del
  control. `t_bg_k` sí es idéntico entre brazos (0 diferencias).
- **CONFIANZA**: alta. **GRAVEDAD: 2** (inocuo hoy en VIIRS 375, latente para la ventana completa).

### H5. El poder de P2 y P3 como umbrales es bajo cuando sobreviven sólo 10 negativas
- **Qué pasa**: si de las 95 negativas publicadas por B se conservaran 10 AL AZAR, la razón caería
  a 1,3 o menos en el 25,7 % de los sorteos, y la celda borde con fondo frío quedaría en 2 o menos
  en el 9,3 %. O sea que "cumple P2" y "cumple P3", como umbrales, no distinguen bien un mecanismo
  selectivo de un apagón casi total. Lo que sí distingue es el valor observado contra el nulo
  (p = 0,002 para la razón) y, sobre todo, el nulo 1 de abajo.
- **Cómo se ve** (`out_v3.txt`, NULO 2):
  ```
  razon bajo el nulo: p2.5 0.61, mediana 2.27 | observado 0.253 | P(nulo <= obs) = 0.00220 | P(nulo <= 1.3) = 0.2566
  borde con fondo frio conservadas bajo el nulo: mediana 4 | observado 2 | P(nulo <= obs) = 0.0928
  ```
- **CONFIANZA**: alta. **GRAVEDAD: 2**. Para el veredicto final: la prueba de selectividad debe
  ser el contraste positivas contra negativas, no P2 ni P3 solos.

### H6. `cobertura.txt` del run dice que el control no tiene ninguna pasada
- **Dónde**: `experiments/_s146_ab_sin_test1/salidas/35548121381/cobertura.txt` en la rama de datos.
- **Cómo se ve**: `::error::el control no tiene ninguna pasada en la ventana: no hay nada que comparar`.
  Es falso respecto de los datos (el control tiene 2.315 records). Coincide con el defecto conocido
  del job `recolectar`. No afecta la lectura, que cuenta la cobertura por su cuenta.
- **CONFIANZA**: alta en el síntoma, SIN VERIFICAR la causa. **GRAVEDAD: 1**.

### H7. El filtro de campos nulos saca una pasada del denominador sin decirlo
- **Dónde**: `lectura_por_tramo.py:92-93`. Hay 325 negativas limpias de VIIRS 375; la tabla usa 324
  porque una no tiene cenit o `t_bg_k`. Ninguna publicación cambia (95 y 10 con y sin el filtro).
- **CONFIANZA**: alta. **GRAVEDAD: 1**.

## VERIFICADO LIMPIO

1. **Reproducción del instrumento**: salida idéntica a `preliminar_conectiva_salida.txt`, los tres
   sensores (`out_instrumento.txt`): 95/324 a 10/324; 125/129 a 124/129; razón 2,10 a 0,25;
   VIIRS 750 30/562 a 3/562 y 11/16; MODIS 34/385 a 0/385.
2. **Recálculo independiente** (`verif_base.py`, `v1_tasas.py`; criterio de noche, pareo a 2 min,
   etiquetas y predicado propios, radios internos de otra fuente): mismos números en VIIRS 375 y
   750. En MODIS da 34/380 en vez de 34/385, por mi criterio de noche distinto; no toca la lectura.
   ```
   B  neg 95/324 nadir 22/116 medio 12/55 borde 61/153 borde_frio 42/68 pos 125/129 razon 2.1
   F  neg 10/324 nadir 6/116  medio 2/55  borde 2/153  borde_frio 2/68  pos 124/129 razon 0.25
   ```
3. **Predicado del tablero**: mi port a Python contra el predicado real ejecutado con node, record
   por record: 0 diferencias en la decisión y 0 en la magnitud, sobre 2.022 pasadas por brazo (`out_v4.txt`).
4. **Control negativo**: control contra sí mismo da columnas idénticas, en el instrumento y en mi script.
5. **Nulo por barajado, endurecimiento parejo** (20.000 sorteos): conservando al azar 134 de las 220
   publicaciones de B, sobreviven entre 69 y 83 positivas (máximo 90 en 20.000). Observado: 124.
   ```
   positivas conservadas bajo el nulo: p2.5 69, mediana 76, p97.5 83, max 90 | observado 124 | P = 0.00000
   ```
   La caída ES selectiva. Y un piso de magnitud no la imita: el piso más alto que conserva 124
   positivas (0,0079 MW) deja 85 negativas publicando, contra 10 de `max`; un piso de 0,06 MW deja
   14 negativas pero sólo 93 positivas.
6. **Identidad de lo que sobrevive**: cero publicaciones nuevas en F (columna 0 a 1 vacía en todos
   los sensores y etiquetas). Las 124 positivas son las mismas pasadas, con desplazamiento mediano
   de 0,000 km y una sola sobre 0,5 km (0,76). De las 10 negativas, 3 se mueven más de 0,5 km, todas
   en Lastarria (hasta 1,54 km, alejándose del cráter pero dentro del radio interno de 3 km).
7. **El brazo F no apaga el contextual en VIIRS** (el riesgo que pasó en MODIS): pasadas con píxeles
   del primer pase, B a F: positivas V375 97 a 94 de 129; negativas 78 a 26 de 325; V750 positivas 4
   a 3 de 16, negativas 29 a 11 de 562. MODIS: 397 a 1 de 399, reproduce lo que dice la lectura.
8. **Ningún camino ajeno sostiene el recall**: en las 124 positivas de F, `n_bt_path` 0, Test 1 0,
   `n_vent_pixels` 0, `diag_n_eti_path` 0, NTI absoluto en 1; fuente del ancla `ctx_cluster` en las
   124. Todo lo publicado pasa por los Tests 2 y 3 (primer o segundo pase), ambos con `max`.
9. **Recall donde el umbral más sube**: en el borde 23 a 22 de 25 positivas, mientras las negativas
   del borde caen de 61 a 2 de 153. Por magnitud de MIROVA: bajo 0,1 MW 39 a 39 de 42; 0,1 a 0,2
   MW 37 a 36 de 38; sobre 0,2 MW 49 de 49 en ambos. La única pérdida es Lastarria 2026-09-04 06:24
   (MIROVA 0,14 MW, control 0,0419 MW), como dice la lectura. Las 4 que ningún brazo publica son las mismas.
10. **Pareo**: 0 claves duplicadas, 0 gránulos distintos, 0 cambios de plataforma, todos `standard`
    en los dos brazos, `t_bg_k` idéntico. La promoción de gránulos no contamina este tramo.
11. **Ventana**: fecha mínima 2026-09-01 01:55 en ambos; 0 records anteriores al 2026-08-28 23:00 UTC.
12. **Cobertura**: B 2.315, F 2.386; los 71 que faltan al control son Chaitén 24, Villarrica 24 y
    Tupungatito 23, del 18 al 20 de septiembre (3, 36 y 32). Tramo hasta el 17: 2.022 contra 2.022.
13. **Definiciones contra el pre-registro**: zonas 36 y 52 grados, fondo frío bajo 260 K y negativo
    limpio (RUTINA del consolidado con VRP 0 a 2 min, sin alerta ni falso positivo esa noche y
    sensor) coinciden con `PREREGISTRO.md`. Las etiquetas salen sólo de la referencia de MIROVA
    congelada y son idénticas entre brazos (0 diferencias): no hay circularidad tipo S33.

## LO QUE NO CUBRÍ

- La **ventana completa** (18 al 20 de septiembre) y el run de reparación 35558196104.
- **No corrí el pipeline** ni miré píxeles: la causa de H3 es lectura de código, no medición.
- La **posición contra MIROVA** con dirección (TIF UTM, A106, A107): sólo medí B contra F.
- La métrica por **noche de volcán**, los brazos G y H, y `evaluar.py` completo.
- Si los negativos limpios del borde en volcanes activos (Cordón Caulle publica 9 de 9 en B y 0 de
  9 en F) son calor real que MIROVA calla: la lectura mide paridad con MIROVA, no verdad física.
  Para la réplica es la vara correcta; para `experimental` no.
- El diff de perfiles (que B y F difieren sólo en el flag): SIN VERIFICAR, lo tomé del pre-registro.
- Representatividad: 17 días de septiembre, sin invierno pleno, Villarrica con 4 positivas.
