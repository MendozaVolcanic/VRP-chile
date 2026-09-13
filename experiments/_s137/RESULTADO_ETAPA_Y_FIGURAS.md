# S137 · La compuerta de temperatura elimina el cráter de Villarrica, y las figuras del paper miden el sigma de MIROVA

> Probe por etapa: run 34746870643, `out_etapa/etapa_apendice.json`. Medición de figuras:
> `medir_figuras_apendice.py` → `out_figuras/figuras_apendice.json`. Probe de sigma:
> `out_sigma/sigma_dnti_4brazos.json`. Todos los números salen de esos archivos (regla S91).

## El fenómeno, primero

La cumbre de Villarrica está cubierta de hielo a 2.847 m. El lago de lava ocupa una fracción
diminuta de un píxel de 1 km, así que en el infrarrojo medio ese píxel mezcla un poco de lava con
mucho hielo y, de noche, marca unos 268 K. El fondo de la escena de 50 km, en cambio, incluye el
lago Villarrica, bosques y valles a pocos cientos de metros, y su mediana queda en 272 K.

En términos absolutos el cráter está **más frío que el fondo**, aunque tenga lava. Lo que lo delata
es el contraste espectral: el NTI del píxel sobresale respecto de sus ocho vecinos, que es justo lo
que miden el dNTI y el dETI. Y así lo detecta el autor: su figura A6 muestra un único píxel de
alerta en el cráter.

Nuestro primer paso agrega una condición que el paper no tiene: `bt > t_bg + 3 K`, el píxel debe
estar 3 K por encima del fondo. En una cumbre helada esa condición descarta exactamente el objeto
que se quiere ver. Es la imagen especular de A69: allá el MIR absoluto inventaba anomalías en los
valles tibios; acá las borra en las cumbres frías.

## El probe por etapa, Villarrica 24 de junio de 2009, 05:55 (la pasada de la figura A6)

| brazo | sigma dNTI | cráter dNTI | cráter dETI | umbral prosa dNTI / dETI | BT cráter | fondo + 3 K | pasa |
|---|---|---|---|---|---|---|---|
| B21 | 0,0076 | 0,0080 | 0,0090 | 0,0382 / 0,0378 | 267,87 | 276,94 | no |
| B22 | 0,0016 | **0,0121** | **0,0140** | 0,0078 / 0,0036 | 268,32 | 275,25 | **sólo falla la compuerta** |
| B22 remuestreo | 0,0017 | 0,0117 | 0,0138 | 0,0086 / 0,0037 | 268,32 | 275,25 | sólo falla la compuerta |

Con la banda 22 el cráter pasa los Tests 2 y 3 **incluso con la conectiva más estricta**, la de la
prosa, y cae únicamente por la compuerta de temperatura, por 7 K. Con la banda 21 no pasa ni el
umbral de la prosa, porque el ruido infla el contraste exigido.

En la otra pasada del mismo día (04:10, Terra) el cráter no muestra señal con banda 22 (dNTI
-0,0019). La figura del autor es la de las 05:55.

## De dónde salió la compuerta

`NTI_BT_SANITY_K = 3.0`, "pixel must also be at least 3 K above t_bg". Entró el **8 de abril de 2026**,
commit `59846e897` ("E3: add NTI dual-criteria detection to MODIS"), para el camino del NTI absoluto
(`nti > -0,8 AND bt > t_bg + 3`). El comentario de ese mismo commit dice *"We don't implement
dNTI/dETI (would need full spatial-contrast machinery)"*: la compuerta se diseñó para un camino **sin
contraste espacial**, donde un NTI alto sobre un píxel frío sí podía ser artefacto.

Después se heredó a los caminos contextuales y al primer paso de los Tests 2 y 3 (hoy aparece en unos
13 lugares de los tres sensores). La fórmula de los Tests 2 y 3 del paper (`sp426.5.pdf`, p. 7) no
tiene condición de temperatura: sólo dNTI y dETI contra C1 o contra el contraste estadístico.

## El sigma del dNTI de MIROVA, medido en sus figuras

Método: la barra de color se ancla a sus marcas de graduación (la escala no es simétrica), cada píxel
del panel se convierte a valor, y se toma una muestra por celda de la grilla de 51 km. Control
pre-registrado: la mediana del dNTI debe quedar dentro de ±0,0003. **Pasa en los cuatro paneles.**
La primera versión del script falló ese control (leía el marco de la barra) y no se usó.

| panel | sigma por celda (MAD / percentiles / recorte) | sin lago ni costa |
|---|---|---|
| A2 dNTI, Eyjafjallajökull 04:40 | 0,00036 / 0,00051 / 0,00057 | 0,00058 |
| A2 dETI | 0,00026 / 0,00038 / 0,00031 | 0,00043 |
| A6 dNTI, Villarrica 05:55 | 0,00064 / 0,00084 / 0,00082 | 0,00078 |
| A6 dETI | 0,00026 / 0,00029 / 0,00035 | 0,00027 |

**En la misma escena y a la misma hora** (Villarrica 05:55): el autor tiene sigma dNTI de unos
**0,0008**; nosotros **0,0076** con la banda 21 y **0,0016** con la banda 22. La banda 22 queda a un
factor 2 del autor y la 21 a un factor 10.

Límite: el raster de imprenta suaviza y empuja el sigma del autor hacia abajo. El factor 2 que queda
entre banda 22 y autor puede ser en parte ese suavizado; el factor 10 de la banda 21 no.

## Eyjafjallajökull: el autor detecta a 9,6 km de la cumbre

Medido sobre la máscara de alerta de la figura A2 (grilla de 50 km centrada en la cumbre, sur abajo
según la línea de costa): centroide de la alerta a **9,5-9,7 km, rumbo 83°**.

| brazo, pasada 04:40 | cúmulo primario |
|---|---|
| autor (figura A2) | 9,5-9,7 km, rumbo 83° |
| B22 | 9,13 km, rumbo 100°, 0,32 MW |
| B22 remuestreo | 8,37 km, rumbo 73°, 3,27 MW |
| B21 | **3,12 km, rumbo 153°**, 0,52 MW |

La banda 22 encuentra el objeto del autor. La banda 21 publica otra cosa, al sureste y cerca de la
cumbre. Consecuencia para la batería: evaluar A2 dentro de 5 km de la cumbre **está mal especificado
respecto de la propia referencia**, porque el autor detecta fuera de esa caja. Y el "conforme" de hoy
en A2 no era la erupción.

En esa pasada el sigma con banda 22 es excepcionalmente alto (0,0165) y el remuestreo lo baja a
0,0029. En las 84 escenas de 2026 de Láscar y Villarrica eso **nunca** ocurre (el remuestreo nunca baja
el sigma más de la mitad sobre banda 22). Hipótesis no verificada: geometría de esa pasada (ángulo de
escaneo, bow tie). No afecta el veredicto de A2, cuya anomalía está a 9 km.

## Lo que esto NO dice

- No dice que quitar la compuerta sea seguro: puede devolver falsos positivos en los negativos del
  apéndice o en los Tier A. Hay que medirlo.
- No dice que el sigma de MIROVA sea 0,0008 exacto: es un orden de magnitud con sesgo conocido.
- No dice nada de VIIRS, que no tiene banda 22.

## Pre-registro de la corrida siguiente (escrito antes de verla)

**Brazos.** Banda 22 con la compuerta de temperatura quitada **sólo dentro de los Tests 2 y 3**
(`bt_sanity_k` del primer paso anulado; los demás caminos quedan intactos), con la fórmula (`min`) y
con la prosa (`max`).

**Criterio primario, sin cambios desde S136:** conservar los 6 positivos y curar los 3 negativos,
con la evaluación de siempre (cúmulo con VRP > 0 dentro de 5 km de la cumbre del catálogo).

**Evaluación secundaria, declarada post hoc y NO usable para adoptar:** A2 evaluado en la posición
del autor (cúmulo con VRP > 0 a 3 km o menos del punto a 9,6 km, rumbo 83°, desde la cumbre del
catálogo). Existe porque la figura del autor muestra que la evaluación primaria de A2 mide otra cosa,
pero se reporta aparte para no mover el criterio después de ver el dato.

**Predicción escrita:** Villarrica pasa a conforme en los dos brazos. Riesgo que hay que mirar: que
alguno de los tres negativos vuelva a ser falso positivo sin la compuerta.

**Aun si cumple**, adoptarlo exige además A45 (tag y confirmación de Nicolás) y un A/B sobre los Tier
A, porque la compuerta aparece en 13 lugares y la batería tiene nueve escenas.
