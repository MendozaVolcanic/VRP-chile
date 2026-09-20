# Caso A2 con la vara corregida: resultado, controles y lo que queda sin dato (S146)

> 2026-09-20. Aplica el criterio de `docs/audit_s146/A2_CRITERIO_PRE_REGISTRADO.md`, escrito y
> hasheado antes de escribir el evaluador y antes de abrir ninguna salida de la batería.
> Hash sha256 anotado del pre-registro: `{{HASH_ANOTADO}}`
> Hash recalculado al armar este informe: `{{HASH_AHORA}}` ({{HASH_ESTADO}}).
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
{{SALIDA_CRUDA}}
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
