# El único fallo del mejor brazo de la batería es del criterio, no del algoritmo (S145)

> Medido el 2026-09-20 sobre artefactos que **ya estaban en el repo** desde S137. No se corrió
> ningún run nuevo. Ningún número escrito a mano (S91).

## Por qué importa

La batería del Apéndice A de Coppola 2016a (9 casos: 6 donde el autor detecta, 3 donde no) es la
puerta que bloquea **D21** (banda 22 primaria) y **D22** (quitar la compuerta de 3 K). El criterio
de aprobación es **9 de 9**. Mientras ningún brazo lo cumpla, las dos divergencias siguen abiertas,
y además **condicionan el cierre de D11**.

El catálogo dice de D21: *"ningún brazo cumple aún la batería"*. Eso es cierto de forma literal, y
es lo que ha mantenido el frente parado varias sesiones.

## Lo que muestran los datos guardados

El brazo **B22 + sin compuerta + fondo local, conectiva de la prosa**
(`experiments/_s137/out_apendice_b22_sincompuerta_fondolocal_prosa/`):

| caso | volcán | el paper | nosotros |
|---|---|---|---|
| A1 | Bezymianny | detecta | CONFORME |
| **A2** | **Eyjafjallajökull** | **detecta** | **falso negativo** |
| A3 | Erta Ale | detecta | CONFORME |
| A4 | Dubbi | no detecta | CONFORME |
| A5 | Ubinas | detecta | CONFORME |
| A6 | Villarrica | detecta | CONFORME |
| A7 | Tolbachik | no detecta | CONFORME |
| A8 | Etna | detecta | CONFORME |
| A9 | Stromboli | no detecta | CONFORME |

**8 de 9 conformes, 1 falso negativo, 0 falsos positivos.** Los 3 negativos del paper los cura
entero, que es lo que ningún otro brazo lograba sin romper los positivos.

## Qué le pasa al caso A2

El predicado de la batería exige un cúmulo con magnitud **a 5 km o menos** de la coordenada de
cumbre del GVP (`INNER_KM = 5.0` en `experiments/_s136/conformidad_apendice.py:46`, el ROI1 del
paper). Los cúmulos que ese brazo encuentra en A2:

| distancia | rumbo | magnitud | NTI máx |
|---|---|---|---|
| 8,53 km | 80,9° (E) | 33,6 MW | -0,662 |
| 7,37 km | 104,0° (ESE) | 5,0 MW | -0,815 |
| 10,86 km | 75,8° (ENE) | 1,9 MW | -0,882 |
| 9,11 km | 83,2° (E) | **58,3 MW** | **-0,269** |

El algoritmo **sí encuentra una anomalía fuerte**, de decenas de MW y con el NTI más alto de todo
el caso. Lo que falla es que cae fuera de la caja de 5 km centrada en la cumbre.

## Por qué la anomalía está al este, y por qué eso zanja la duda

La fecha del caso es el **2010-04-07**. En esa fecha la actividad de Eyjafjallajökull era la
erupción de flanco de **Fimmvörðuháls**, que empezó el 20 de marzo y siguió hasta el 12 de abril;
la erupción de la cumbre recién empezó el 14 de abril. Fimmvörðuháls está en el paso **al este** de
la cumbre, hacia Mýrdalsjökull.

La propia batería nombra el confusor de este caso en su nota: *"La línea de costa produce un
aumento MODERADO de dNTI y dETI"*. La costa sur de Islandia está al **sur** del volcán.

**Los cuatro cúmulos apuntan al E, ESE y ENE. Ninguno al sur.** El rumbo descarta la costa, que era
la explicación alternativa, y coincide con la fisura activa de esa fecha.

Esto es exactamente lo que la regla **A107** dice: una cota de distancia escalar no identifica el
objeto, hace falta dirección. Con la distancia sola este caso era indecidible; con el rumbo se
decide.

## La corrección al documento de S137

`experiments/_s137/RESULTADO_BATERIA_B22.md` (l. 46-53) dejó esto como *"Hipótesis, no
verificada"*, con esta razón: *"la batería guarda distancias pero no posiciones, así que hoy no se
puede confirmar desde el repo"*.

**Esa razón es falsa.** Cada pasada guarda `pc_lat` y `pc_lon`, junto con `dist_crater_km`. La
hipótesis era verificable desde el día en que se escribió; el cálculo de rumbo son cuatro líneas.
Es el patrón de **A89**: se dio por ausente algo que estaba guardado, y el frente quedó parado sobre
esa suposición.

## Qué significa para D21 y D22

Bajo un criterio corregido para A2, ese brazo da **9 de 9**, que es la barra de aprobación.

Eso **no autoriza a adoptar nada**. Lo que hace es mover el frente de "ningún brazo cumple" a "hay
un brazo que cumple y falta decidir si el criterio estaba mal". Las preguntas abiertas antes de
cualquier adopción:

1. **¿Se corrige el criterio de A2, y cómo?** Ampliar la caja para ese caso es tocar la vara con la
   que se mide, y eso necesita quedar escrito **antes** de volver a correr, no después de ver el
   resultado. La opción honesta es declarar A2 como caso de **erupción de flanco** y evaluarlo
   contra la posición de la fisura, no contra la cumbre del catálogo.
2. **Este brazo mezcla tres cambios** (banda 22, sin compuerta, fondo local) y una conectiva. El
   A/B que decida la adopción tiene que poder atribuir a cuál se debe la mejora, o se adopta un
   paquete sin saber qué parte lo hace.
3. **El fondo local de este brazo es D25**, el mismo frente que hoy quedó implementado y apagado en
   VIIRS 750. Acá aparece como parte de lo que cura la batería en MODIS. No es contradicción: son
   sensores distintos y criterios distintos (fidelidad al paper contra sobre-publicación medida),
   pero la decisión de uno informa la del otro y conviene tomarlas juntas.
4. **Lo medido acá es fidelidad al paper, no paridad con MIROVA.** Que un brazo reproduzca el
   Apéndice A no dice nada sobre qué le haría a las 2285 pasadas nocturnas del régimen actual. Eso
   es otra medición y va antes de cualquier adopción.

## Reproducir

```bash
python -c "
import json, math
CUMBRE = (63.633, -19.633)
d = json.load(open('experiments/_s137/out_apendice_b22_sincompuerta_fondolocal_prosa/resultado_apendice.json', encoding='utf-8'))
a2 = [c for c in d if c['caso'] == 'A2'][0]
for p in a2['pasadas']:
    if p.get('vrp_pc_mw') is not None:
        dl = math.radians(p['pc_lon'] - CUMBRE[1])
        p1, p2 = math.radians(CUMBRE[0]), math.radians(p['pc_lat'])
        y = math.sin(dl) * math.cos(p2)
        x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
        print(round(p['dist_crater_km'], 2), round((math.degrees(math.atan2(y, x)) + 360) % 360, 1), p['vrp_pc_mw'])
"
```
