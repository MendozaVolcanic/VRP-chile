# Caso A2 con la vara corregida: resultado, controles y lo que queda sin dato (S146)

> 2026-09-20. Aplica el criterio de `docs/audit_s146/A2_CRITERIO_PRE_REGISTRADO.md`, escrito y
> hasheado antes de escribir el evaluador y antes de abrir ninguna salida de la batería.
> Hash sha256 anotado del pre-registro: `758b3ea1c54e2bc9c7d8384ce2f279f723098b4a3f095fa431d573421cdc6b27`
> Hash recalculado al armar este informe: `758b3ea1c54e2bc9c7d8384ce2f279f723098b4a3f095fa431d573421cdc6b27` (COINCIDE).
> No se corrió ningún gránulo: todo sale de los `resultado_apendice.json` commiteados en S136 y S137.
> Los números de este informe están en la salida cruda del script, pegada entera en §6 por
> `experiments/_s146_a2/armar_informe.py`; las tablas de la prosa la copian y, si difieren, manda §6.

## 1. El fenómeno, en corto

El 7 de abril de 2010 la cumbre de Eyjafjallajökull estaba fría y bajo hielo. La lava estaba en el
paso de Fimmvörðuháls, en el flanco oriental, saliendo de una fisura corta que el Boletín del GVP
ubica en 63° 38,1' N, 19° 26,4' O. Ese punto queda a 9,53 km de la coordenada de cumbre del
catálogo, casi al este exacto. La figura A2 del paper muestra la máscara de alerta del autor de ese
mismo lado, a unos 10 km del centro de su grilla, y nada en el centro. La batería de S136 preguntaba
"¿publicamos algo a 5 km o menos de la cumbre?", y en este caso esa pregunta tiene la respuesta
cambiada: acertar en la cumbre es publicar otro objeto, y publicar la lava cuenta como fallo.

## 2. El mecanismo de la vara corregida

Se traslada la caja, no se agranda: mismo radio de 5 km, centrado en la coordenada del GVP en vez de
la cumbre, sólo para A2 (la regla general del pre-registro, aplicada a ciegas, deja los otros ocho
casos en la cumbre). Para A2 la caja de cumbre deja de contar. Donde un brazo no guardó la posición
del cúmulo, el acierto no se puede probar con la distancia sola y el caso queda INDECIDIBLE, que no
es acierto ni fallo.

## 3. Resultado, brazo por caso

OK = conforme, FN = falso negativo, FP = falso positivo, INDEC = indecidible por falta de posición.
Cada celda es "vara vieja -> vara nueva". Sólo la columna A2 puede cambiar.

| brazo | A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | vieja | nueva |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B21 min (producción) | OK | **OK -> FN** | OK | FP | OK | OK | FP | OK | FP | 6/9 | 5/9 |
| B21 max (prosa) | FN | FN -> INDEC | OK | OK | FN | FN | OK | OK | OK | 5/9 | 5/9 |
| B22 min | OK | FN -> INDEC | OK | FP | OK | FN | OK | OK | OK | 6/9 | 6/9 |
| B22 max | OK | FN -> INDEC | OK | OK | OK | FN | OK | OK | OK | 7/9 | 7/9 |
| B22 sinBT min | OK | **FN -> OK** | OK | FP | OK | FN | OK | OK | OK | 6/9 | 7/9 |
| B22 sinBT max | OK | **FN -> OK** | OK | OK | OK | FN | OK | OK | OK | 7/9 | 8/9 |
| B22 sinBT loc min | OK | OK -> OK | OK | FP | OK | OK | OK | OK | OK | 8/9 | 8/9 |
| **B22 sinBT loc max** | OK | **FN -> OK** | OK | OK | OK | OK | OK | OK | OK | 8/9 | **9/9** |

Lectura:

- **El mejor brazo (banda 22, sin compuerta, fondo local, conectiva de la prosa) pasa de 8 a 9 de
  9**, que es la barra de aprobación fijada en S136. Sus cuatro pasadas de A2 tienen el cúmulo
  primario a menos de 5 km de la fisura; la pasada de la figura del autor (04:40) lo tiene a menos
  de 1 km, con la magnitud más alta del caso. El acierto se mantiene con radio de 3 km y usando sólo
  la pasada de la figura, así que no es frágil.
- **Producción pierde un acierto que tenía regalado.** Con la vara vieja daba "conforme" en A2
  por cúmulos de décimas de MW a 1,4 a 3,1 km de la cumbre, donde ese día no había erupción. Con la
  vara nueva es FALLO, probado aun sin posición guardada: la cota A93 pone esos cúmulos a más de
  6 km de la fisura. Esto confirma con otra vara lo que S138 ya había dicho (EJE 5, §1.2): ese conforme era
  otro objeto.
- **"B22 sinBT loc min" sigue conforme en A2, pero por otra pasada.** Su conforme viejo era el
  cúmulo de las 03:00 a 1,21 km de la cumbre, que ya no cuenta; el nuevo son las otras tres pasadas,
  que sí caen junto a la fisura. No llega a 9 de 9 porque sigue publicando en Dubbi (A4).
- **Tres brazos quedan INDECIDIBLES en A2** (B21 max, B22 min, B22 max): no guardaron `pc_lat` ni
  `pc_lon`. Sus distancias a la cumbre son compatibles con la fisura, pero una distancia sin rumbo no
  ubica nada (A93, A107). Ninguno de los tres podía aprobar de todos modos: fallan otros casos.

## 4. Los controles y sus nulos

| control | qué pregunta | resultado | qué vale |
|---|---|---|---|
| C0a identidad | ¿mi predicado con la vara vieja reproduce lo commiteado? | 72 de 72 | el instrumento lee lo mismo que S136 y S137 |
| C0b control positivo | con radio 0,01 km, ¿caen todos los positivos? | 48 de 48 | el predicado sí mira la distancia |
| C1 negativos | ¿algún negativo cambia de veredicto con la vara nueva? | 0 de 24 | es una identidad por construcción; sólo descarta un error del script |
| N1 caja rotada en A2 | misma caja a 9,53 km, rumbos girados 90, 180 y 270 grados | VACÍA en las 3 cajas para los 4 brazos con posición y para producción; INDET en los 3 brazos sin posición | ver la advertencia de abajo |
| N2 caja desplazada en los otros 8 casos | mismo desplazamiento, 4 rumbos, 8 volcanes, 8 brazos | 0 cajas con cúmulo, 244 vacías y 12 indeterminadas de 256 | ver la advertencia de abajo |

**La advertencia, que es lo más importante de esta sección: los nulos salieron vacíos, pero son casi
ciegos.** El pre-registro ya declaraba el límite (la batería guarda un solo cúmulo por pasada, el
primario), y al medir su alcance el límite resultó peor de lo que esperaba:

- En N2, para que una caja desplazada pudiera llenarse, el cúmulo primario de alguna pasada tendría
  que estar en el anillo de 4,53 a 14,53 km de su cumbre. El diagnóstico de poder (agregado después
  del pre-registro y rotulado así en la salida) cuenta cuántas pasadas cumplen eso en los ocho casos
  sin A2: entre 0 y 2 por brazo, y **0 de 7 en el mejor brazo**. Un nulo que no puede llenarse no
  prueba que la vara no regale aciertos. En ese brazo N2 no mide nada.
- En N1 pasa lo mismo por otro camino: en el mejor brazo las cuatro pasadas de A2 tienen su único
  cúmulo guardado junto a la fisura, así que las cajas rotadas están vacías por construcción. N1
  habría podido fallar (si el primario hubiera caído al sur, hacia la costa, el acierto pasaba a
  INDECIDIBLE), y no falló. Pero no puede decir si en esas escenas hay además píxeles alertados
  hacia la costa que el cúmulo primario tapa.

Lo que sí sostiene el acierto, y no depende de los nulos: el punto de referencia es una coordenada
publicada por el GVP años antes de este proyecto; el radio es el mismo de toda la batería; el
cúmulo de la pasada de la figura cae a menos de 1 km de ese punto, con decenas de MW y el NTI más
alto del caso, y una anomalía así en un paso de montaña islandés en abril no tiene explicación
alternativa razonable. La costa, que era el confusor nombrado por el autor, queda al sur, y los
cúmulos están al E.

Veredicto de los controles, dicho sin adorno: **C0a, C0b y C1 pasan. N1 y N2 no detectan regalo,
pero tienen poder cercano a cero, así que cuentan como SIN DATO y no como OK.** El nulo con poder
real es por píxel alertado, y eso exige re-procesar (§5).

## 5. Lo que quedó SIN DATO, y qué habría que correr

No descargué ni procesé nada (pyhdf no corre en Windows, no se usan credenciales Earthdata en local,
disco con 9 GB). Quedan sin dato:

1. **A2 en los tres brazos sin posición** (B21 max, B22 min, B22 max) y la posición de los cúmulos de
   producción. Se resuelve re-corriendo la batería con el probe actual, que desde S137 ya guarda
   `pc_lat` y `pc_lon`. En GitHub Actions, workflow `probe-s136-conformidad-apendice.yml` (si está
   en `_archive/`, copiarlo de vuelta a `.github/workflows/` y mergear antes de despachar):
   - producción: `gh workflow run probe-s136-conformidad-apendice.yml --ref main`
   - B21 max: `... -f prosa=1`
   - B22 min: `... -f b22=1`
   - B22 max: `... -f b22=1 -f prosa=1`
   Después, agregar las carpetas de salida nuevas a la lista `BRAZOS` de
   `experiments/_s146_a2/evaluar_vara_corregida.py` y re-correrlo. Basta `-f caso=A2` si sólo se
   quiere cerrar A2; para que C0a siga valiendo conviene correr los nueve.
2. **Un nulo con poder.** Hace falta que el probe guarde, por pasada, TODOS los cúmulos (hoy
   `process_modis.py` los calcula en `cluster_hotspots` y sólo persiste el primero) o la lista de
   píxeles alertados con su lat y lon. Eso pide una copia del probe en `experiments/_s146_a2/` que
   capture esa lista por monkeypatch de lectura (método A75), sin tocar `pipeline/`, y un run del
   mejor brazo: `-f b22=1 -f sin_compuerta=1 -f fondo_local=1 -f prosa=1`. Con eso N1 y N2 pasan a
   contar alertas en la caja, no primarios, y dejan de ser ciegos. No lo escribí porque no se puede
   probar en local y un probe sin probar es una promesa, no un instrumento.
3. **El brazo que nadie corrió** (B22 + fondo local, CON compuerta), señalado en
   `docs/audit_s145/D21_D22_ESTADO_DEL_BLOQUEO.md` §5: `-f b22=1 -f fondo_local=1`. Sin él no se
   puede atribuir el 9 de 9 a la compuerta o al fondo.
4. **El tamaño del píxel MODIS en el borde del barrido** (2 por 4,8 km), citado de memoria en el
   pre-registro: SOSPECHA hasta cotejarlo con la guía del L1B. No afecta el resultado, porque el
   radio se fijó por uniformidad con la batería y no por ese número.

## 6. Salida cruda del script

`python experiments/_s146_a2/evaluar_vara_corregida.py`

```
====================================================================================================
PUNTO DE REFERENCIA A2 (GVP BGVN 35:3): lat 63.6350 lon -19.4400 ; a 9.53 km rumbo 88.6 de la cumbre
radio decisorio 5.0 km ; radio de sensibilidad 3.0 km

====================================================================================================
C0a IDENTIDAD: vara vieja reimplementada vs veredicto commiteado
  reproduce 72 de 72
C0b CONTROL POSITIVO (vara nueva, radio 0,01 km): 48 de 48 positivos caen a fallo o indeterminado

====================================================================================================
TABLA BRAZO x CASO   (vieja -> nueva ; solo A2 puede cambiar)
brazo                   A1           A2           A3           A4           A5           A6           A7           A8           A9           vieja    nueva
B21 min (produccion)    OK->OK       OK->FN       OK->OK       FP->FP       OK->OK       OK->OK       FP->FP       OK->OK       FP->FP       6/9      5/9
B21 max (prosa)         FN->FN       FN->INDEC    OK->OK       OK->OK       FN->FN       FN->FN       OK->OK       OK->OK       OK->OK       5/9      5/9
B22 min                 OK->OK       FN->INDEC    OK->OK       FP->FP       OK->OK       FN->FN       OK->OK       OK->OK       OK->OK       6/9      6/9
B22 max                 OK->OK       FN->INDEC    OK->OK       OK->OK       OK->OK       FN->FN       OK->OK       OK->OK       OK->OK       7/9      7/9
B22 sinBT min           OK->OK       FN->OK       OK->OK       FP->FP       OK->OK       FN->FN       OK->OK       OK->OK       OK->OK       6/9      7/9
B22 sinBT max           OK->OK       FN->OK       OK->OK       OK->OK       OK->OK       FN->FN       OK->OK       OK->OK       OK->OK       7/9      8/9
B22 sinBT loc min       OK->OK       OK->OK       OK->OK       FP->FP       OK->OK       OK->OK       OK->OK       OK->OK       OK->OK       8/9      8/9
B22 sinBT loc max       OK->OK       FN->OK       OK->OK       OK->OK       OK->OK       OK->OK       OK->OK       OK->OK       OK->OK       8/9      9/9

====================================================================================================
C1 NEGATIVOS: veredicto vara vieja vs vara nueva (identidad por construccion de la regla)
  negativos que cambian de veredicto: 0 de 24

====================================================================================================
DETALLE A2: cumulos primarios con magnitud, por brazo y pasada
  B21 min (produccion)
    22:05  vrp=   0.119 MW  n_px=1  d_cumbre=  1.40  rumbo=  s/d  sep_fisura=  s/d  cota_A93= 8.13  nti=-0.6938
    23:40  vrp=   0.119 MW  n_px=1  d_cumbre=  2.34  rumbo=  s/d  sep_fisura=  s/d  cota_A93= 7.19  nti=-0.8273
    03:00  vrp=   0.131 MW  n_px=2  d_cumbre=  1.77  rumbo=  s/d  sep_fisura=  s/d  cota_A93= 7.76  nti=-0.869
    04:40  vrp=   0.524 MW  n_px=7  d_cumbre=  3.12  rumbo=  s/d  sep_fisura=  s/d  cota_A93= 6.42  nti=-0.2685
  B21 max (prosa)
    22:05  vrp=  29.346 MW  n_px=3  d_cumbre=  8.97  rumbo=  s/d  sep_fisura=  s/d  cota_A93= 0.57  nti=-0.6938
    23:40  vrp=   5.000 MW  n_px=1  d_cumbre=  6.37  rumbo=  s/d  sep_fisura=  s/d  cota_A93= 3.16  nti=-0.8273
    04:40  vrp=  52.944 MW  n_px=2  d_cumbre=  9.70  rumbo=  s/d  sep_fisura=  s/d  cota_A93= 0.17  nti=-0.2685
  B22 min
    22:05  vrp=   5.162 MW  n_px=4  d_cumbre=  7.79  rumbo=  s/d  sep_fisura=  s/d  cota_A93= 1.74  nti=-0.6623
    23:40  vrp=   5.000 MW  n_px=8  d_cumbre=  7.03  rumbo=  s/d  sep_fisura=  s/d  cota_A93= 2.50  nti=-0.8145
    03:00  vrp=   5.000 MW  n_px=8  d_cumbre= 11.12  rumbo=  s/d  sep_fisura=  s/d  cota_A93= 1.59  nti=-0.882
    04:40  vrp=   0.321 MW  n_px=1  d_cumbre=  9.13  rumbo=  s/d  sep_fisura=  s/d  cota_A93= 0.40  nti=-0.2685
  B22 max
    22:05  vrp=  43.245 MW  n_px=7  d_cumbre=  8.53  rumbo=  s/d  sep_fisura=  s/d  cota_A93= 1.00  nti=-0.6623
    23:40  vrp=   5.000 MW  n_px=5  d_cumbre=  7.37  rumbo=  s/d  sep_fisura=  s/d  cota_A93= 2.17  nti=-0.8145
    03:00  vrp=   2.082 MW  n_px=2  d_cumbre= 10.86  rumbo=  s/d  sep_fisura=  s/d  cota_A93= 1.33  nti=-0.882
    04:40  vrp=  59.358 MW  n_px=3  d_cumbre=  9.11  rumbo=  s/d  sep_fisura=  s/d  cota_A93= 0.42  nti=-0.2685
  B22 sinBT min
    22:05  vrp=   5.162 MW  n_px=4  d_cumbre=  7.79  rumbo= 59.8  sep_fisura= 4.62  cota_A93=  -  nti=-0.6623
    23:40  vrp=   5.000 MW  n_px=8  d_cumbre=  7.03  rumbo=104.6  sep_fisura= 3.39  cota_A93=  -  nti=-0.8145
    03:00  vrp=   5.000 MW  n_px=8  d_cumbre= 11.12  rumbo= 91.5  sep_fisura= 1.67  cota_A93=  -  nti=-0.882
    04:40  vrp=   0.321 MW  n_px=1  d_cumbre=  9.13  rumbo= 99.9  sep_fisura= 1.88  cota_A93=  -  nti=-0.2685
  B22 sinBT max
    22:05  vrp=  43.245 MW  n_px=7  d_cumbre=  8.53  rumbo= 80.9  sep_fisura= 1.57  cota_A93=  -  nti=-0.6623
    23:40  vrp=   5.000 MW  n_px=5  d_cumbre=  7.37  rumbo=104.0  sep_fisura= 3.12  cota_A93=  -  nti=-0.8145
    03:00  vrp=   2.082 MW  n_px=2  d_cumbre= 10.86  rumbo= 75.8  sep_fisura= 2.63  cota_A93=  -  nti=-0.882
    04:40  vrp=  59.358 MW  n_px=3  d_cumbre=  9.11  rumbo= 83.2  sep_fisura= 0.97  cota_A93=  -  nti=-0.2685
  B22 sinBT loc min
    22:05  vrp=   2.819 MW  n_px=4  d_cumbre=  7.79  rumbo= 59.8  sep_fisura= 4.62  cota_A93=  -  nti=-0.6623
    23:40  vrp=   5.000 MW  n_px=8  d_cumbre=  7.03  rumbo=104.6  sep_fisura= 3.39  cota_A93=  -  nti=-0.8145
    03:00  vrp=   0.311 MW  n_px=3  d_cumbre=  1.21  rumbo=  1.0  sep_fisura= 9.56  cota_A93=  -  nti=-0.882
    04:40  vrp=   0.504 MW  n_px=1  d_cumbre=  9.13  rumbo= 99.9  sep_fisura= 1.88  cota_A93=  -  nti=-0.2685
  B22 sinBT loc max
    22:05  vrp=  33.639 MW  n_px=7  d_cumbre=  8.53  rumbo= 80.9  sep_fisura= 1.57  cota_A93=  -  nti=-0.6623
    23:40  vrp=   5.000 MW  n_px=5  d_cumbre=  7.37  rumbo=104.0  sep_fisura= 3.12  cota_A93=  -  nti=-0.8145
    03:00  vrp=   1.912 MW  n_px=2  d_cumbre= 10.86  rumbo= 75.8  sep_fisura= 2.63  cota_A93=  -  nti=-0.882
    04:40  vrp=  58.289 MW  n_px=3  d_cumbre=  9.11  rumbo= 83.2  sep_fisura= 0.97  cota_A93=  -  nti=-0.2685

====================================================================================================
SECUNDARIOS A2 (informativos, no decisorios)
  B21 min (produccion)     radio 3 km: NO CONFORME (falso negativo)     solo pasada 04:40 (n=1): NO CONFORME (falso negativo)
  B21 max (prosa)          radio 3 km: INDECIDIBLE (sin posicion)       solo pasada 04:40 (n=1): INDECIDIBLE (sin posicion)
  B22 min                  radio 3 km: INDECIDIBLE (sin posicion)       solo pasada 04:40 (n=1): INDECIDIBLE (sin posicion)
  B22 max                  radio 3 km: INDECIDIBLE (sin posicion)       solo pasada 04:40 (n=1): INDECIDIBLE (sin posicion)
  B22 sinBT min            radio 3 km: CONFORME                         solo pasada 04:40 (n=1): CONFORME
  B22 sinBT max            radio 3 km: CONFORME                         solo pasada 04:40 (n=1): CONFORME
  B22 sinBT loc min        radio 3 km: CONFORME                         solo pasada 04:40 (n=1): CONFORME
  B22 sinBT loc max        radio 3 km: CONFORME                         solo pasada 04:40 (n=1): CONFORME

====================================================================================================
N1 NULO EN A2: misma caja (5 km) a 9.53 km de la cumbre, rumbo girado +90/+180/+270
  B21 min (produccion)     rumbo 178.6: VACIA       rumbo 268.6: VACIA       rumbo 358.6: VACIA      
  B21 max (prosa)          rumbo 178.6: INDET       rumbo 268.6: INDET       rumbo 358.6: INDET      
  B22 min                  rumbo 178.6: INDET       rumbo 268.6: INDET       rumbo 358.6: INDET      
  B22 max                  rumbo 178.6: INDET       rumbo 268.6: INDET       rumbo 358.6: INDET      
  B22 sinBT min            rumbo 178.6: VACIA       rumbo 268.6: VACIA       rumbo 358.6: VACIA      
  B22 sinBT max            rumbo 178.6: VACIA       rumbo 268.6: VACIA       rumbo 358.6: VACIA      
  B22 sinBT loc min        rumbo 178.6: VACIA       rumbo 268.6: VACIA       rumbo 358.6: VACIA      
  B22 sinBT loc max        rumbo 178.6: VACIA       rumbo 268.6: VACIA       rumbo 358.6: VACIA      

====================================================================================================
N2 NULO EN LOS OTROS 8 CASOS: caja de 5 km a 9.53 km, rumbos 88.6 +0/+90/+180/+270
  B21 min (produccion)     vacias 24  con cumulo  0  indet  8  de 32   A1@89:INDET A1@179:INDET A1@269:INDET A1@359:INDET A7@89:INDET A7@179:INDET A7@269:INDET A7@359:INDET
  B21 max (prosa)          vacias 32  con cumulo  0  indet  0  de 32   
  B22 min                  vacias 28  con cumulo  0  indet  4  de 32   A3@89:INDET A3@179:INDET A3@269:INDET A3@359:INDET
  B22 max                  vacias 32  con cumulo  0  indet  0  de 32   
  B22 sinBT min            vacias 32  con cumulo  0  indet  0  de 32   
  B22 sinBT max            vacias 32  con cumulo  0  indet  0  de 32   
  B22 sinBT loc min        vacias 32  con cumulo  0  indet  0  de 32   
  B22 sinBT loc max        vacias 32  con cumulo  0  indet  0  de 32   
  TOTAL: {'VACIA': 244, 'CON CUMULO': 0, 'INDET': 12} de 256

====================================================================================================
PODER DE LOS NULOS (diagnostico agregado despues del pre-registro, no decide nada):
pasadas cuyo cumulo primario con magnitud queda en el anillo 4.53 a 14.53 km de la cumbre,
o sea las unicas que PODRIAN caer en alguna caja desplazada. Si son cero, el nulo esta ciego.
  B21 min (produccion)     2 de 20 pasadas con magnitud (8 casos sin A2)   A1 16:55 d=7.84; A7 14:45 d=5.41
  B21 max (prosa)          0 de 2 pasadas con magnitud (8 casos sin A2)   
  B22 min                  1 de 9 pasadas con magnitud (8 casos sin A2)   A3 22:25 d=4.76
  B22 max                  0 de 5 pasadas con magnitud (8 casos sin A2)   
  B22 sinBT min            1 de 9 pasadas con magnitud (8 casos sin A2)   A3 22:25 d=4.76
  B22 sinBT max            0 de 5 pasadas con magnitud (8 casos sin A2)   
  B22 sinBT loc min        1 de 11 pasadas con magnitud (8 casos sin A2)   A3 22:25 d=4.76
  B22 sinBT loc max        0 de 7 pasadas con magnitud (8 casos sin A2)   

====================================================================================================
VEREDICTO FINAL A2 POR BRAZO (pre-registro seccion 4) y total del brazo
  B21 min (produccion)     A2: FALLO                                        otros 8: 5/8   total 5/9   no aprueba
  B21 max (prosa)          A2: INDECIDIBLE (SIN DATO de posicion)           otros 8: 5/8   total 5/9   no aprueba
  B22 min                  A2: INDECIDIBLE (SIN DATO de posicion)           otros 8: 6/8   total 6/9   no aprueba
  B22 max                  A2: INDECIDIBLE (SIN DATO de posicion)           otros 8: 7/8   total 7/9   no aprueba
  B22 sinBT min            A2: ACIERTO                                      otros 8: 6/8   total 7/9   no aprueba
  B22 sinBT max            A2: ACIERTO                                      otros 8: 7/8   total 8/9   no aprueba
  B22 sinBT loc min        A2: ACIERTO                                      otros 8: 7/8   total 8/9   no aprueba
  B22 sinBT loc max        A2: ACIERTO                                      otros 8: 8/8   total 9/9   APRUEBA 9/9

escrito: C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s146_a2\out\resultado_vara_corregida.json
```

## 7. Qué desbloquea y qué no

**Lo que cambia.** La frase del catálogo "ningún brazo cumple la batería" deja de ser cierta bajo un
criterio escrito antes de medir y anclado en una fuente externa: un brazo da 9 de 9. El bloqueo
formal de D21 y D22 por "criterio inalcanzable" (punto (a) de la auditoría de S145) queda levantado,
y con él el condicionamiento derivado de D11.

**Lo que NO cambia, y pesa más:**

- **Esto mide fidelidad al Apéndice A, no paridad con MIROVA.** Son nueve escenas MODIS de 2008 a
  2013, una fecha por caso. No dice nada de qué le haría ese brazo a las pasadas nocturnas del
  régimen actual, ni en MODIS ni mucho menos en VIIRS. Donde D22 y D25 sí se midieron sobre
  producción (S143, VIIRS 375), empujaron la sobre-publicación hacia arriba. Un 9 de 9 acá no
  compensa eso ni lo contradice: son preguntas distintas.
- **El pre-registro no era ciego.** Yo sabía dónde habían caído los cúmulos. El ancla externa y el
  radio heredado quitan los grados de libertad que podía usar a mi favor, pero el acierto de A2 era
  previsible y por sí solo informa poco. Lo que era genuinamente incierto, los nulos, resultó no
  tener poder.
- **El brazo es un paquete de cuatro cambios** (banda 22, sin compuerta, fondo local, conectiva
  `max`) y la batería no permite atribuir. La conectiva `max` además es la lectura de la prosa del
  paper contra su fórmula, una ambigüedad que sólo el autor puede zanjar (pregunta del correo a
  Coppola, redactado y sin enviar).
- **Dos de los cuatro cambios no existen como flag en MODIS** (compuerta y fondo por vecinos).
  Escribirlos es tocar `pipeline/`, con A45: tag defensivo y confirmación explícita de Nicolás.
- **Los otros defectos del instrumento siguen ahí** (S138, EJE 5): mezcla de pasadas de dos noches,
  cúmulos del camino D con el tope de 5,000 MW contados como aciertos (aparecen en A2 a las 23:40 en
  todos los brazos B22), sensibilidad al radio en los casos de cumbre. La vara corregida arregla un
  defecto, el del caso de flanco, y no los demás.
- **No autoriza adoptar nada.** Mueve el frente de "bloqueado por la vara" a "hay un candidato que
  cumple la fidelidad al paper y falta medirlo contra MIROVA con un A/B de cobertura pareja", que es
  exactamente el A/B que hoy no se puede correr en MODIS por falta de flags.
