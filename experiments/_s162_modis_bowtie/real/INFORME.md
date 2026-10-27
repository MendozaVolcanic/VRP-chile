# S162 MOD-E real: el bow tie de MODIS (D28) en el código de MIROVA, con los recortes nativos del lote 40120713181

> ⚠️ **Verificado con contexto limpio el 2026-10-24** (Fable alto, `verificador/INFORME.md`; las cinco salidas y los
> dos json se reproducen bit a bit). **Se sostiene**: la reproducción del lote (403 de 403, también B21 y geometría de
> 5 km); el método A sin huecos reales (huella sacada de la geolocalización, 1,0 a 1,7 km a lo largo; sus rendijas
> cierran con la huella x1,05 a x1,10, las de B y C ni con x1,5; A deja todavía 8,4 % del suelo bajo dos barridos porque
> quita sólo centros cubiertos); con A las 11 protegidas publican; B mataría la protegida de Chillán 2026-10-01 08:35
> (5,18 MW de MIROVA, VBT-03, gravedad 5 si se adoptara). **No se sostiene**: que el efecto quede confinado al foco
> duplicado (VBT-02: en Láscar 79, con el cráter visto una vez, la magnitud sube 8,7 % porque quitar duplicados a 8 km
> cambia la sigma global con que el oráculo arma el umbral de cumbre); y el 2 a 0 en `neg_resto` no es una propiedad
> robusta del método: los dos cambios de publicación ocurren al filo, con márgenes de NTI de 1e-6 a 8e-4 (VBT-01). «El
> signo depende de la copia» vale en 1 de 3 casos, y el estrato «cráter bajo 2+ huellas» toma 91 de 102 sobre 50° pero
> deja fuera 1 de los 2 cambios de publicación. Seguimiento del verificador (S-1): el umbral de cumbre del oráculo usa la
> sigma de toda la grilla de 51 km, lo que acopla cualquier A/B de remuestreo (D17, D28) a lo que pase en el borde de la
> escena. Texto original conservado:


2026-10-24. Sólo lectura: nada en `pipeline/`, `data/` ni `frontend/`. Insumos: los 403 recortes nativos y los
resultados del lote `C:\vrp-trabajo\temporales\s162_negmodis\run_40120713181\`, los objetivos
`experiments\_s162_modis_negativos\objetivos_neg_resto_modis.json` y el port del árbol base
`experiments\_s162_modis_verif_cde\arbol\`. Todo número de este informe sale de un script de esta carpeta con su salida
al lado. **Pendiente: verificador con contexto limpio.**

## En una pantalla

1. **El recorte alcanza.** Rearmar la grilla desde el recorte nativo y correr el port `fisica` sin quitar nada da el
   mismo npix, el mismo VRP y las mismas celdas que el lote en **403 de 403** pasadas (máximo |ΔVRP| 4,2e-13 MW). Control
   negativo: con B21 primaria el resultado cambia en 13 de 13 pasadas con detección (`01_reproducir_salida.txt`).
2. **El traslape real es grande lejos del nadir.** En la caja de la ROI1 del port (±7,875 km), con todos los píxeles,
   el suelo visto dos o más veces es 0,4 % bajo 15° de cenit, 16,3 % de 25 a 40°, 34,2 % de 40 a 50° y **66,7 % sobre
   50°** (156 de las 403 pasadas están sobre 50°). Sobre 50° el traslape ocupa los detectores 0 a 3 de un barrido y 6 a 9
   del anterior, no sólo el 0 y el 9 (`02_cobertura_salida.txt`).
3. **Método que se sostiene: A, quitar sólo lo que el barrido vecino ya cubre** (el centro del píxel cae dentro del
   tramo de centros del barrido vecino, en el mismo frame). Baja el doble conteo sobre 50° de 66,7 % a 10,8 % y sus
   huecos nuevos (de 1,5 a 3,1 %) son rendijas: con la huella agrandada 20 % quedan en 0,60 %, igual que con todos
   (0,57 %). **La regla de filas de borde (B) abre huecos de verdad**: 6,1 % de 25 a 40° y 6,4 % sobre 50°, que siguen
   en 3,2 % y 2,6 % con la huella agrandada. El control C (quitar siempre el detector 0) abre 10,7 % de huecos en el nadir
   (`02b_rendijas_salida.txt`). Las dos variantes de A (conservar la copia del barrido anterior o la del siguiente)
   tienen la misma cobertura; la de huella entera da lo mismo que la de centro.
4. **Ablación.** Con A, las **11 alertas protegidas siguen publicando**, en las dos variantes. En los 390 `neg_resto`,
   las 2 publicaciones del port (Llaima 2026-07-24 01:05 y Láscar 2026-05-11 07:55) bajan a **0** conservando la copia
   anterior y a **1** conservando la siguiente (queda Láscar con 0,25 MW). No aparece ninguna publicación nueva. El
   npix cambia sólo en 2 negativos y 4 protegidas; en las 98 pasadas bajo 25° no cambia nada (en 91 de ellas A no quita
   ningún píxel). Nulo por construcción: en las 92 pasadas donde A no quita nada la grilla sale idéntica, 0 distintas
   (`03_ablacion_salida.txt`, `02_cobertura.json`).
5. **La regla de filas de borde pierde una alerta protegida**: Chillán 2026-10-01 08:35 (port 5,8 MW, MIROVA 5,18). El
   foco está visto dos veces, en el barrido 18 detector 8 (272,7 K) y en el 19 detector 1 (270,9 K), y B quita **las dos
   copias** (`04_casos_salida.txt`). Es la falla que el verificador predijo para el sintético, ahora en un dato real.
6. **Magnitud en las protegidas**: port sobre MIROVA, mediana 1,074 con todos, 1,049 con A conservando la copia anterior
   y 0,956 conservando la siguiente. Los cambios por pasada van de 0,736 a 1,087 veces y caen en las tres pasadas de
   Chillán sobre 50° (el foco duplicado) y en Láscar 2026-03-15 (cenit 30°, +8,7 %, sin quitar ningún píxel cercano al
   foco: el efecto llega por el fondo de la escena). **El signo depende de qué copia se conserva.** Chillán
   2026-10-15 01:05, la pasada de razón 1,734, queda en 1,835 o 1,645: D28 no la explica.

## Costura del barrido

Con el criterio pedido (el píxel nativo más cercano al punto de referencia de MIROVA cae en el detector 0 o 9), 60 de
403 pasadas están en la costura y en **ninguna** cambia nada. No es que la costura no importe: lejos del nadir la
franja duplicada es de 3 o 4 detectores, así que el detector 0 o 9 no la delimita. El estrato que sí la delimita es
«el cráter cubierto por dos o más huellas con todos los píxeles» (148 pasadas, 108 de ellas sobre 50°): ahí caen los
cambios de npix (4 con A conservando la anterior). Los focos de las tres protegidas de Chillán que cambian se ven en dos copias, en los detectores 8 y 1, 7 y 1, y 6
y 0 (`04_casos_salida.txt`), todos dentro de la franja duplicada.

## Lo que cambia y lo que no

| | todos | A (anterior) | A (siguiente) | B filas de borde |
|---|---|---|---|---|
| publican, protegidas (n 11) | 11 | 11 | 11 | 10 |
| publican, neg_resto (n 390) | 2 | 0 | 1 | 1 |
| port/MIROVA, mediana protegidas | 1,074 | 1,049 | 0,956 | 1,123 (n 10) |
| huecos ROI1 sobre 50° (huella 1,2x) | 0,57 % | 0,60 % | 0,63 % | 2,64 % |
| doble cobertura ROI1 sobre 50° | 66,7 % | 10,8 % | 10,7 % | 7,2 % |

Fuentes: `03_ablacion_salida.txt` (filas 1 a 3) y `02b_rendijas_salida.txt` (filas 4 y 5).

## SIN DATO y SOSPECHA

- **Qué copia conserva MIROVA**: SIN DATO (el método exacto de D28 no está localizado). Como el efecto sobre la
  magnitud cambia de signo según la copia, el efecto de D28 sobre la magnitud del port sigue SIN DATO; lo medido es
  su rango con las dos variantes de A (de 0,736 a 1,087 veces por pasada en las 4 que cambian).
- **Que quitar duplicados haga callar al port en `neg_resto`** (2 a 0 o 1): SOSPECHA. Son 2 eventos, el análisis es
  posterior al lote y no está pre-registrado; no cambia el veredicto INDECIDIBLE de MOD-C. Si se quiere usar, hay que
  pre-registrarlo y elegir la copia antes de mirar.
- **Huella nominal sin PSF**: la cobertura se midió con el paralelogramo nominal (paso entre detectores por paso entre
  frames). El nulo es sano (bajo 15°, 98,6 % visto una vez con todos), pero la PSF triangular de MODIS a lo ancho del
  barrido no está modelada.
- **Sólo 13 pasadas detectan** con todos (11 protegidas y 2 negativos): la magnitud se mide sobre 4 pasadas que
  cambian. La variante con la geolocalización de 5 km de producción no se ablacionó.
- **Margen continuo en los negativos** (cuánto se acerca cada pasada al umbral con y sin duplicados): no medido.
- Cuatro pasadas tienen más de 10 % de huecos ya con todos (borde del gránulo, sin NaN en el recorte); los métodos no
  las empeoran en la medida con huella agrandada.

## Cómo reproducirlo

Desde esta carpeta, en orden (el 3 lee el JSON del 2 y el 4 lee el del 3): `python -I 01_reproducir.py`,
`python -I 02_cobertura.py` (unos 15 min), `python -I 02b_rendijas.py`, `python -I 03_ablacion.py` (unos 8 min, usa
node para el predicado del tablero), `python -I 04_casos.py`. La carpeta del lote se cambia con `VRP_S162_RUN`.
Definiciones de los métodos y de la huella: `comun.py`.
