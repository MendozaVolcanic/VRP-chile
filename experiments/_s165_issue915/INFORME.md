# S165, issue #915: clasificación de los ítems que la vuelta 1 dejó abiertos

Escrito el 2026-10-27 (S165, agente de sólo lectura). No toca `pipeline/`, `data/`, `frontend/` ni `.github/`; no
comenta el issue ni despacha nada. Las tres protegidas MODIS de Chillán (12, 15 y 25 de octubre) ya están
clasificadas en `tasks/LOOP_OBJETIVOS.md` §6, vuelta 1 de S165, y no se rehacen acá.

## Datos usados (A8)

- Árbol de `origin/main` en `97ef53aa5` extraído con `git archive` a `D:\vrp-trabajo\temporales\s165_issue915\main`
  (records, loaders, el código del auto-audit y la referencia). Todos los records de la ventana llevan
  `codigo_sha` `34cea39e4` (detector K).
- Referencia: `latest_consolidado.csv` de main (último sync 2026-10-27 21:17 UTC, posterior al D-39 de las 12:41) y
  el OCR del snapshot. Para control, lo mismo con el consolidado del snapshot que usó el audit del 2026-10-26.
  **Los dos dan resultados idénticos** en todo lo que sigue (la única diferencia es una fila RUTINA de Tupungatito
  que pasó de «histórica» a «principal»): `detalle_issue915_snapshot_salida.txt` contra
  `detalle_issue915_latest_salida.txt`.
- Ventana del audit (2026-08-27 a 2026-10-26) y su misma regla por noche (`evaluar_detector`): con eso se
  reproducen exactos los 6 «sin publicar» y las 5 razones del issue (0,56 / 0,662 / 0,683 / 0,375 / 0,409).

Scripts y salidas, todos en esta carpeta:
`detalle_issue915.py` (parte A: cada protegida con todas las filas de MIROVA y todos nuestros records a ±3 h;
parte B: noche por noche de cada celda de magnitud), `magnitud_objeto_y_contraste.py` (objeto, contraste y
correlaciones por celda), `tope_d9_en_celdas.py`.

## Tabla de clasificación

| ítem | qué pasó físicamente | categoría A54 | evidencia | qué falta para cerrarlo |
|---|---|---|---|---|
| **Tupungatito V375 2026-09-28 05:18** (MIROVA 2,51 MW) | Esa pasada de Suomi NPP vio una fuente caliente lejos del volcán, no el cráter. Nuestro record de la misma pasada tiene un cúmulo `far` de 1 píxel a 21,57 km del cráter (0,15 MW); la serie «Last Month» de MIROVA dibuja su alerta a 22,6 km de su centro (S158). La fila del scraper es sólo OCR, y su 5,27 km es la estrella de la pasada de 05:36, que la tabla sí trae como cráter (0,09 MW a 5,21 km) y que nosotros publicamos (`summit`, 0,26 km). | **Problema de referencia** (A119: clase y distancia de otra pasada; el VRP sí es de la suya). No es FN: no publicar un objeto a 21 km es lo correcto. CONFIRMADO. | `detalle_issue915_latest_salida.txt` parte A; `experiments/_s158_tupungatito/README.md` §2 y su verificador (`verificador/v6_miniaturas_direccion.py`) | Nada del pipeline. Que el auto-audit no cuente como protegida una fila sólo OCR de Suomi NPP anterior al 2026-10-09 cuya distancia no es de su pasada (hoy la marca «sospechosa» pero igual levanta flag). Decide Nicolás. |
| **Tupungatito V375 2026-09-29 04:54** (MIROVA 1,86 MW) | Igual: nuestro record de la misma pasada (cenit 62°) ve un cúmulo `far` de 1 píxel a 9,40 km del cráter, rumbo 77°, 1,11 MW, con 47 K sobre el fondo; MIROVA lo dibuja a 9,6 km (S158). La tabla trae el cráter en otra pasada (05:18 NOAA-20, 0,04 MW a 5,41 km) y la publicamos (05:18 y 06:00, `summit`). El 5,68 km de la fila OCR no tiene origen explicado (S158). | **Problema de referencia** (A119). No es FN. CONFIRMADO. | Mismas | Lo mismo que el anterior. |
| **PCC V750 2026-10-10 05:54** (MIROVA 1,19 MW, tabla, 7,83 km) | Señal débil del lacolito de Cordón Caulle (mismo objeto que MIROVA, A61 de #865): dos píxeles contiguos que se bajan el contraste uno al otro en el promedio de 8 vecinos, y con la conectiva `max` de K el Test 2 no llega por 6 y 15 %. Sigue igual con datos de hoy: el record VIIRS 750 tiene 0 píxeles anómalos. En **la misma pasada** publicamos el mismo objeto en VIIRS 375 (NOAA-21, cúmulo a 0,10 km del lacolito, 0,688 MW publicados contra 0,39 de MIROVA), así que el operador lo vio. El código de MIROVA con su caja por defecto tampoco lo detecta (S158 R2: 0 píxeles; 1 si el anillo usa umbrales de cumbre). | **Señal real sub-umbral** (FN real de K en V750, de un objeto que el tablero sí muestra en V375). CONFIRMADO. | `detalle_issue915_latest_salida.txt` parte A; #865 (cerrado por Nicolás el 2026-10-20 sin cambiar K) y PR #881, `experiments/_s157_pcc865/`; `docs/AUDIT_S158_R2.md` §3 | Ya decidido: no cambiar K (la única palanca, `min` en V750, cuesta 314 negativos limpios más, #865). Para que deje de reaparecer en cada audit: registrarla como pérdida aceptada por decisión, o esperar a la ROI de MIROVA (D17, C-03 de `docs/COLA_CAMPO.md`). Decide Nicolás. |
| **Chillán MODIS 0,56× (n = 8)** | Chillán está en erupción: MIROVA da 3,5 a 26,5 MW, contraste nuestro de 16 K de mediana. No es régimen débil. La razón cae con el cenit del sensor: 0,751 bajo 30° (n = 5) y 0,203 sobre 30° (n = 3), Spearman ρ = −0,83, p = 0,010. Las tres noches de cenit alto son también las tres con el cúmulo más lejos del centro de MIROVA (2,1 a 3,7 km contra 0,8 a 1,9). No son noches raras: sacando cualquiera la mediana queda entre 0,485 y 0,635. Todas pareadas en la misma pasada y todas de la tabla. | **Geometría del sensor a cenit alto**, no artefacto ni referencia. Mismo patrón que las tres protegidas de la vuelta 1. CONFIRMADO que es cenit; SOSPECHA en el mecanismo (área sin remuestreo D17, la geolocalización `_interp_geo` que corre el punto hacia el nadir, o el fondo; MOD-D fase 3 y MxD03 los están midiendo). | `magnitud_objeto_y_contraste_salida.txt`; `detalle_issue915_latest_salida.txt` parte B | El resultado de MOD-D fase 3 (#919) y del probe de MxD03 (#920) estratificado por cenit. Con n = 8, una tasa por tramo de cenit vale más que la mediana. |
| **Chillán V375 0,662× (n = 21)** | Erupción, foco fuerte (MIROVA 7,3 MW y contraste 53 K de mediana). La razón cae con el cenit: 1,03 bajo 30° (n = 6) contra 0,598 sobre 30° (n = 15), ρ = −0,51, p = 0,019. Estable: sin cualquier noche, 0,651 a 0,705. Con cúmulos de 3 o más píxeles da 0,873 y con 1 a 2, 0,553. Ninguna noche compara objetos distintos. | **Geometría a cenit alto** (S158 R2: en V375 nuestro conteo de píxeles cae con el ángulo y el de MIROVA no). No es régimen débil ni noches raras. CONFIRMADO el estrato; atribución al conteo, SOSPECHA (S154 la dejó SIN ATRIBUIR). | Mismas | V375-E del programa por sensor; medir la razón por cenit pareada por pasada (la curva de `experiments/_s154_chillan/razon_por_cenit.py`) con el resultado. |
| **Chillán V750 0,683× (n = 16)** | Erupción. Déficit parejo: sin cualquier noche la mediana queda entre 0,678 y 0,687, y el cenit pesa poco (ρ = −0,48, p = 0,062). Una noche (2026-10-24 05:30) publica 5,0 MW topado por D9 contra 7,14 de MIROVA; no mueve la mediana. | **Fondo y conteo** de nuestro VRP (S158 R2 reprodujo con el código de MIROVA en Chillán 2026-10-10 05:54: 12,4 MW el oráculo, 13,1 MIROVA, 10,5 producción). No es régimen débil, ni noches raras, ni referencia. CONFIRMADO que es déficit sistemático; el mecanismo, por el oráculo de S158 R2 en un caso. | Mismas; `tope_d9_en_celdas_salida.txt` | V750-A del programa (fondo del código de MIROVA). La celda está a 0,02 de la banda: cualquier corrimiento chico la cruza. |
| **PCC V750 0,375× (n = 11)** | Régimen débil del lacolito: MIROVA da 0,63 MW de mediana y nuestro píxel queda 3 K sobre el fondo. La razón sigue al contraste (ρ = +0,84, p = 0,001), no al cenit (ρ = −0,36, p = 0,27). En tres noches el píxel queda a menos de 0,6 K del fondo y publicamos 0,02 a 0,06 MW (razón 0,03 a 0,08): el fondo del anillo casi iguala al píxel (D25). Además, una noche compara **otro objeto**: el 2026-10-10 el máximo publicado es de la pasada de 04:54 (cenit 63°), a 18,5 km del centro de MIROVA, contra el lacolito a 7,83; la separación es al menos 10,7 km. Es la cola dispersa de VIIRS 750 que el `inner_radius_km` de 20 km deja como `summit` (S115). Sin esa noche, 0,517. Frágil: sin cualquier noche, 0,333 a 0,517. | **Señal real sub-umbral** con déficit de fondo (régimen débil, como S124), más **una noche de artefacto** (objeto distinto) que entra a la métrica. CONFIRMADO. | Mismas | V750-A (fondo). Y que la métrica de magnitud por noche exija que nuestro máximo y el de MIROVA sean el mismo objeto (re-anclado al centro de MIROVA, como hizo este script); hoy compara el máximo de la noche sin mirar dónde está. |
| **Tupungatito V375 0,41× (n = 20)** | Foco débil en cumbre glaciar: MIROVA 0,14 MW de mediana, contraste nuestro de 7 K sobre el anillo de valle. La razón sube con el contraste (ρ = +0,55, p = 0,012) y no depende del cenit (ρ = 0,01). Cinco noches tienen como máximo de MIROVA una fila sólo OCR (razón 0,016 a 0,272, mediana 0,029): dos son los objetos lejanos de arriba (09-28, 09-29), otra es el de 13 km del 09-14 (S158), y las del 09-16 y 09-17 traen 2,84 km, al menos 1,95 km del radio del cráter, o sea tampoco miden el cráter. Sólo con la tabla: 0,618 (n = 15). | **Problema de referencia** en 5 de 20 noches (alertas OCR que no son del cráter inflan el denominador) más **señal real sub-umbral** con déficit de fondo en el resto (régimen débil, S124 y S158 §1). CONFIRMADO. | Mismas; `experiments/_s158_tupungatito/README.md` §3 | V375-E (fondo). Lo mismo que PCC sobre exigir el mismo objeto, y contar con la tabla sola además del combinado (memoria S159). |

## Lectura de conjunto

- **Ninguna de las tres protegidas es una pérdida de cráter que el operador no haya visto.** Las dos de Tupungatito
  son objetos lejanos que nosotros también vemos y clasificamos `far`; la etiqueta de alerta de cráter es del
  scraper, con la distancia de otra pasada. La de PCC es un FN real de VIIRS 750, ya decidido, de un objeto que
  publicamos en VIIRS 375 en la misma pasada.
- **Las magnitudes bajas no son una sola cosa.** Se separan en dos regímenes:
  - En **Chillán (erupción, varios MW)** el déficit no es de régimen débil. En MODIS y VIIRS 375 sigue al cenit; en
    VIIRS 750 es parejo, y el oráculo de S158 R2 lo atribuye al fondo y al conteo.
  - En **PCC y Tupungatito (focos débiles, menos de 1 MW)** sí es el régimen débil de S124: la razón sigue al
    contraste del píxel sobre el anillo, que es el fondo de D25. A eso se suman noches donde la referencia o
    nuestro máximo son de otro objeto (1 de 11 en PCC, 5 de 20 en Tupungatito).
- **No son pocas noches raras**, salvo en parte PCC: la mediana dejando una noche fuera se mueve 0,05 en Chillán
  V375 y 0,01 en V750; 0,15 en Chillán MODIS; 0,18 en PCC; 0,08 en Tupungatito.
- Que el fondo sea la palanca de las celdas débiles choca con D25 sin adoptar (D-48, S162). El camino abierto es el
  fondo del código de MIROVA por sensor (V750-A, V375-E, MOD-D).

## Lo que este informe NO mide

- No reprocesa nada ni abre gránulos: el mecanismo de Chillán a cenit alto (área, geolocalización o fondo) queda en
  SOSPECHA hasta MOD-D, MxD03 y V375-E.
- La separación entre objetos es una **cota inferior** (diferencia de radios desde el centro de MIROVA, sin acimut;
  A93): prueba objeto distinto cuando es grande y no prueba el mismo cuando es chica. Para las filas sólo OCR de
  Suomi NPP la distancia de MIROVA puede ser de otra pasada, así que una separación chica ahí no dice nada.
- El contraste es la BT máxima de los píxeles anómalos a 1,5 km del centroide menos `t_bg_k`, no el ΔL del VRP.
- n de 8 a 21: las correlaciones de Spearman con p entre 0,01 y 0,1 son indicios, no pruebas.
