# S149: el costo oculto de la conectiva `max`, medido contra MIROVA

> Estado: **medido y verificado con contexto limpio: se sostiene con salvedades**
> (`docs/audit_s149/VERIFICADOR_COSTO_OCULTO.md`; las salvedades están incorporadas abajo y en la sección 6). Sólo lectura: no se tocó
> `pipeline/` ni se reprocesó nada. Ventana: 2026-09-01 a 2026-09-20, VIIRS 375, los mismos dos
> brazos del A/B de la conectiva (control B sin Test 1, brazo F sin Test 1 y con `max`).
> Todos los números salen de los scripts de `experiments/_s149_costo_oculto/` y están en sus
> archivos `salida_*.txt`; ninguno está transcrito de memoria.

## 0. En una frase

De las 50 publicaciones que `max` apaga en noches en que MIROVA alertó por otra pasada, en **34
MIROVA miró esa misma pasada y publicó RUTINA con VRP 0**; las otras 16 no tienen fila en la
referencia, y 14 de esas 16 son de Suomi NPP, el satélite que la tabla de MIROVA casi no lista. Para el perfil réplica
esas 34 no son un costo: son sobre-publicación que el evaluador no podía ver.

## 1. El fenómeno

En una noche activa el volcán pasa bajo el satélite dos o tres veces. En la pasada cercana al nadir
el píxel mide 375 m y el foco caliente se destaca; en la pasada del borde del barrido el píxel se
estira a más del doble, el mismo foco se diluye y lo que queda es una señal de pocas centésimas de
MW encima de un fondo frío. MIROVA publica la primera como alerta y la segunda como rutina. El
control B publicaba las dos.

## 2. Por qué el evaluador no lo veía

`scripts/banco_paridad.py::etiquetar` define el negativo limpio como una pasada con fila RUTINA del
consolidado y VRP 0 **y además sin ninguna alerta esa noche en ese sensor**. La segunda condición
se puso para no contar como falso algo que podía ser calor real. El efecto lateral es que una
pasada donde MIROVA miró y dijo rutina, en una noche con alerta, cae en `sin_info` junto con las
pasadas que el scraper no capturó. En noches con alerta no existe ni un negativo limpio: las 114
pasadas etiquetadas de esa clase son todas positivas (`salida_c2_que_haria_mirova.txt`). El
verificador de S148 encontró el estrato; acá se abre por dentro.

## 3. Los números

Pasadas VIIRS 375 `sin_info` en noche con alerta de MIROVA en el volcán (`salida_c4_cruce.txt`):

| conjunto | n | MIROVA miró esa pasada y dijo RUTINA VRP 0 | sin fila |
|---|---|---|---|
| todas | 171 | 109 | 62 |
| publicadas por el control B | 84 | 54 | 30 |
| **apagadas por F** | **50** | **34** | **16** |
| sobreviven a F | 34 | 20 | 14 |

Sobre las 109 pasadas donde MIROVA dijo rutina en noche con alerta, el control publica el **49,5 %**
y el brazo F el **18,3 %**. Por zona del barrido (universo algo mayor, 141 pasadas, porque incluye
las noches con etiqueta de falso positivo del scraper; `salida_c3_rutina_en_noche_con_alerta.txt`):
nadir 55,2 a 44,8 %, medio 39,1 a 17,4 %, borde 50,6 a 6,7 %. Es el mismo patrón que en los
negativos limpios: `max` recorta el borde y casi no toca el nadir.

## 4. ¿Y son calor real?

Probablemente una parte sí, y eso no cambia la conclusión para la réplica. Medido por posición
contra **nuestro** cúmulo en la pasada positiva de la misma noche, que es otro gránulo (A109; no es
la posición de MIROVA, que no trae acimut, A107;
`salida_c1_las_50.txt`):

- las apagadas quedan a **0,91 km** de mediana del cúmulo confirmado, 16 de 49 a un píxel o menos
  (0,4 km) y 14 a más de 2 km;
- las que sobreviven a `max` quedan a **0,24 km**, 27 de 34 a un píxel o menos;
- los negativos limpios que F apaga quedan a **2,99 km** de la posición positiva típica del volcán.

O sea que las apagadas son una mezcla: cerca de un tercio está sobre el foco confirmado (Láscar,
Chaitén, Cordón Caulle), y otro tercio está lejos y se parece a los negativos (Isluga, Tupungatito y
Villarrica tienen la **mediana por volcán** a más de 2 km; pasada a pasada no es parejo: tres de
Tupungatito están a menos de 0,5 km). **Límite del instrumento, medido**: el nulo contra las positivas
de otras noches da 0,81 km, igual que la misma noche (el verificador, con el mismo estadístico en los
dos lados, obtiene 0,71 km; y mostró que esta separación correlaciona 0,996 con la distancia al
cráter, o sea que mide cuán lejos del cráter cae el cúmulo y poco más). La posición no distingue "calor de esta
noche" de "lugar donde siempre cae algo"; sólo separa lo que está sobre el foco de lo que no.
El 90 % de las apagadas está en el borde del barrido (z de 52 grados o más), contra 29 % de las
que sobreviven y 20 % de las positivas.

## 5. Qué significa para cada perfil

- **Réplica (`mirova_equivalent`)**: la vara es la base de MIROVA (A115). Donde MIROVA arbitra,
  34 de 34 apagadas son correctas. El costo oculto de `max` no es un costo de fidelidad.
- **Experimental**: el tercio que cae sobre el foco confirmado es justo lo que ese perfil quiere
  conservar (señal real bajo el umbral de MIROVA). Es un argumento para que el experimental se
  quede con `min`, no para frenar `max` en la réplica.
- **Queda sobre-publicación con `max`**: 20 de las 34 que sobreviven son pasadas donde MIROVA
  dijo rutina. `max` no toca ese residuo, que por zona vive sobre todo en el nadir (sección 3).

## 6. Lo que esto NO dice

- No dice nada de las 16 sin fila: no son arbitrables. **No son un hueco de fechas** (mi sospecha
  inicial, refutada por el verificador): no tiene fila el 60 % de las pasadas de Suomi NPP, contra
  15,5 % de NOAA-20 y 8,7 % de NOAA-21, y 14 de las 16 son de SNPP. Consecuencia: 85 de las 109
  pasadas arbitrables son de NOAA-20 y NOAA-21; sobre SNPP este resultado casi no dice nada. Por qué
  la tabla de MIROVA lista tan poco SNPP queda SIN VERIFICAR.
- Las 50 publicaciones son 49 sobrevuelos: Isluga 2026-09-02 06:36 y 06:42 son dos gránulos
  contiguos del mismo paso.
- La referencia congelada termina el 2026-09-20 02:45 UTC: la ventana efectiva es del 1 al 19.
- No dice nada fuera de septiembre ni fuera de VIIRS 375.
- "RUTINA con VRP 0" significa que **la tabla `latest.php` de MIROVA lista esa pasada, para ese
  volcán y sensor, con VRP 0**. Verificado en el código del scraper (repo Mirova-v1, `scraper.py`,
  bucle sobre las filas de `latest.php`: el tipo RUTINA se asigna sólo cuando la fila de MIROVA trae
  VRP 0; el scraper no fabrica filas). El verificador había dejado esta premisa SIN VERIFICAR porque
  ese código no está en este computador; se leyó por la API de GitHub. Lo que sigue sin verificarse
  es la tabla misma de MIROVA contra sus imágenes.
- El conteo del verificador (50) usa noches con alerta en cualquier sensor; `c1` usa sólo alertas
  VIIRS 375 y da 49. La diferencia es una pasada.

## 7. Los cúmulos que cambian de lugar, con dirección

Otro costo declarado en S148: con `max` el cúmulo publicado se mueve más de 500 m en algunas
pasadas. Medido sobre los 201 pares VIIRS 375 publicados por ambos brazos
(`salida_c5_cumulos_que_se_mueven.txt`): se mueven **12**, de los cuales **10 son de Lastarria**, uno
de Cordón Caulle y uno de Tupungatito. Sólo uno de los 12 es una pasada positiva.

En Lastarria el cúmulo salta entre **dos puntos fijos**: uno sobre la posición típica de las alertas
(a 0,1 a 0,3 km) y otro a cerca de 1,1 km al noroeste. `max` lo lleva hacia la posición típica en 5
casos y lo aleja en 5: no hay sesgo sistemático, y la magnitud publicada queda igual en 8 de los 10.
Físicamente son dos grupos de píxeles débiles del mismo campo fumarólico que compiten por ser el
cúmulo primario, y cambiar el umbral cambia cuál gana. No se afirma acá cuál de los dos puntos es
el campo fumarólico: eso pide una coordenada de terreno que no tengo (SIN VERIFICAR).

## 8. Qué sigue

1. Agregar al evaluador el estrato **negativo de pasada en noche con alerta** como métrica
   informativa, con su nulo medido (A110), sin cambiar la definición de negativo limpio.
2. Repetir esta medición en la ventana de invierno cuando se despache.
