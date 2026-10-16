# Verificador con contexto limpio: tarea 1.19 (dependencia angular VIIRS 375 por agregación)

Estudio verificado: `C:\Users\nmend\AppData\Local\Temp\claude\angular_119\INFORME.md`. Mis scripts y salidas, todos en
`C:\Users\nmend\AppData\Local\Temp\claude\verif_119\`:

| script | salida | qué mide |
|---|---|---|
| `v1_geometria.py` | (consola, abajo) | conversión barrido a cenit; escalón de Npix esperado con remuestreo por vecino más cercano |
| `v2_osf.py` | `v2_salida.txt` | reproducción; sensibilidad al spline y al efecto fijo; selección por clase y Npix |
| `v2b_osf.py` | `v2b_salida.txt` | escalón por tercil de VRP; nulo pre-registrado (barajado); perfil fino; placebo con otros splines y clase 0 |
| `v3_pares.py` | `v3_salida.txt` | pares S139 por volcán y zona; escalones con spline libre |
| `v3b_control_suave.py` | `v3b_salida.txt` | prueba de aplanado con controles suaves de amplitud ajustada |
| `v4_ventana.py` | `v4_salida.txt` | contraste local ±1 y ±1,5° dentro de volcán × mes, sin spline, contra 26 placebos |

**Veredicto global: PARCIAL.** Hay un escalón real en el límite 2:1 a 1:1 (52,66°) y la ley de huella del ATBD
aplana mejor que las alternativas suaves en Láscar. Pero el escalón en 36,32° es frágil, la firma de Npix (que es la
que distingue el mecanismo de remuestreo) depende de la elección del spline, la física del «un tercio» está razonada
al revés, y la palanca recomendada es casi la misma ley que S133 ya probó y que el propio informe ve pasarse con
todos los volcanes.

---

## 1. Límites de zona y conversión a cenit: CONFIRMADO

Miré las tres páginas renderizadas.

- `pag/geo_35.png` (423-ATBD-002, p. impresa 14, §2.2.1.1): «within +/- 31.589 degrees ... groups of three samples
  are aggregated», «between 31.589 degrees and 44.680 degrees ... aggregation factor of two». Dice eso.
- `pag/geo_48.png` (p. 27, §3.3.1.1): transiciones «3:1 to 2:1 at +/- 31.589» y «2:1 to 1:1 at +/- 44.680», borde
  56,063°. Dice eso.
- `pag/img_20.png` (ATBD Imagery, p. 21): 31,59° y 44,68° para las bandas I, altitud nominal 833 km. Dice eso.

Conversión: `sin z = (R+h)/R · sin s` es la geometría correcta para un sensor a altura h sobre una esfera. Recalculé:
36,32° y 52,66° con h = 833 km; 36,27 / 52,57 con 824 km; 36,36 / 52,74 con 840 km; el radio terrestre (6.357 a
6.378 km) mueve menos de 0,02°; un volcán a 5,6 km de altura (Láscar) da 36,28 / 52,60. Incertidumbre ±0,1°, como
dice el pre-registro.

Dos notas, ninguna lo invalida:
- p. 27 dice que a 55° de barrido el cenit es «approximately 65 deg»; la fórmula da 67,9°. Es una aproximación del
  ATBD; el borde de 69,7° coincide con el máximo de SatZen que trae el SDR.
- `pag/geo_34.png` (Tabla 2.2-1, p. 13): **M13 es «Dual Gain Band, not along-scan aggregated on-board»**. El V750 de
  MIROVA usa M13. Si la agregación de M13 se hace en tierra al armar el SDR, el escalón aplica igual; si no, el V750
  no es réplica del mecanismo. El informe lo llama «réplica» sin aclararlo. No lo resolví.

## 2. Escalón en el OSF: PARCIAL

Reproduje exacto: n = 208.293 (206.694 en grupos con 2 o más filas), ln(VRP/Npix) +0,135 / +0,216, ln Npix −0,048 /
−0,213, ln VRP +0,087 / +0,003.

**Lo que sobrevive.**
- Efecto fijo: no fabrica el salto. Con efecto fijo sólo volcán +0,101 / +0,174; volcán × semana +0,146 / +0,227;
  volcán × día +0,195 / +0,304 (`v2_salida.txt` [1]).
- Selección: todas las clases nocturnas dan +0,116 / +0,199; Npix ≥ 2 da +0,135 / +0,242. La selección «clase 1,
  noche» no lo crea (`v2_salida.txt` [2]).
- Placebo: los 89 placebos van de 12° a 66° excluyendo ±2,5° de cada límite; los mayores en ln(VRP/Npix) están en 24,
  15,5 y 49°, no en el borde; en ln Npix sí dominan los de 58 a 63° (borde ruidoso, eso hace al nulo conservador).
  Ojo: los 89 no son independientes (escalones contiguos a 0,5° con los mismos datos casi), así que «más que el máximo
  de 89» vale menos de lo que suena.
- El nulo PRE-REGISTRADO (barajar SatZen dentro de cada volcán) no se corrió; se reemplazó por los placebos. Lo corrí:
  |p95| 0,032, máx 0,051 en ln(VRP/Npix) (`v2b_salida.txt` [4]). Es más permisivo que el placebo (destruye toda la
  estructura de cenit), así que el placebo era la mejor elección, pero el cambio debía declararse como desvío.
- **Contraste local sin spline** (±1° y ±1,5° dentro de volcán × mes, `v4_salida.txt`): en 52,66° da +0,123 y +0,115,
  sobre el máximo de 26 placebos (0,072 y 0,086). **El escalón 2:1 a 1:1 es real.**

**Lo que no sobrevive.**
- **36,32° es frágil.** En el contraste local da +0,060 y +0,082, dentro del rango de los placebos (máx 0,072 y 0,086).
  Y en el modelo global el escalón de ln(VRP/Npix) en 36,32° viene **de VRP total que sube** (+0,087, placebo |p95|
  0,156) y no de Npix que baja (−0,048). El mecanismo propuesto dice lo contrario: VRP total plano, Npix abajo. En el
  primer límite la firma está en la componente equivocada.
- **La firma de Npix depende del spline.** Con nudos cada 2° en vez de 4°: ln Npix −0,015 / −0,064 (placebo |p95|
  0,108), es decir, desaparece en los dos límites; ln(VRP/Npix) baja a +0,129 / +0,119 contra placebo máx 0,112. Con
  nudos cada 1° todo se absorbe (+0,009 / +0,087), cosa esperable porque un spline tan fino imita un escalón. Los
  nudos de 4° caen en 36 y 52, a 0,32° y 0,66° de los límites. El número +0,216 depende de esa elección; el placebo
  medido con el mismo spline lo protege a medias, no del todo.
- El contraste local usa sólo ~1.000 a 1.900 filas por límite (grupos con filas a los dos lados). Las 208.293 filas
  describen el modelo, no la información que identifica el salto.
- Clase 0 nocturna (n = 42.697): +0,016 / +0,071 en ln(VRP/Npix), sin salto. Su placebo es ancho (0,18), así que no
  lo refuta, pero un mecanismo puramente geométrico debería afectar también a esas filas.
- Satélites: SNPP y NOAA-20 comparten órbita y repetición; la réplica es parcial, no dos experimentos independientes.
- MODIS como control descarta artefactos del cenit en sí, pero es un control débil (otra resolución, otras horas).

## 3. «Un tercio del límite físico de fuente extensa»: REFUTADO en el razonamiento

Con el modelo que el propio estudio propone (MIROVA remuestrea conservando energía: cada píxel nativo se reparte en
A_nativo/A_celda celdas de 375 m), lo que depende de la huella es el número de celdas **por píxel nativo caliente**:

- **Fuente subpíxel** (número fijo de píxeles nativos): Npix ∝ A_nativo, salto COMPLETO. Simulé vecino más cercano con
  fase al azar (`v1_geometria.py`): fuente de 1 píxel nativo, E[ln Npix] −0,34 en 36,32° y −0,45 en 52,66°; de 2 o
  más píxeles, −0,40 y −0,68 a −0,72.
- **Fuente extensa** (área en el terreno fija): Npix ≈ S/A_celda, salto CERO (sólo queda el borde).

O sea, ±0,405 / ±0,693 es el límite **subpíxel**, no el de fuente extensa, y «pocas celdas» no diluye el salto: lo
predice entero. El informe y el pre-registro tienen la física invertida.

Los datos además no siguen la predicción subpíxel: por tercil de VRP dentro de cada volcán (`v2b_salida.txt` [3]) el
salto de ln Npix es **más chico en el tercil débil** (−0,017 / −0,100, mediana 2 celdas) que en los fuertes (−0,11 /
−0,26, medianas 4 y 7). Eso calza mejor con un remuestreo que suaviza (bilineal o similar) más un umbral: la fuente
débil sólo alerta su celda pico, sin importar la huella. En ese caso **el VRP de MIROVA de las fuentes débiles también
tendría diente de sierra**, y nuestra razón contra MIROVA no necesitaría la corrección entera justamente donde vive la
mayoría de las alertas (81 a 88 % bajo 0,5 MW). Es hipótesis, no medida; pero la D17 ya cita a Aveni et al. 2023 (Remote
Sens. 15, 2528, p. 15 §4.2.1) diciendo que el remuestreo de MIROVA corrige el cenit sólo «partially». El tercio no está
explicado.

## 4. Aplanado en Láscar, Isluga y Copahue: PARCIAL

- **No es circular en parámetros**: la ley sale del ATBD con exponente 1, no se ajusta a los pares. Punto a favor.
- **Controles suaves justos** (`v3b_salida.txt`): el control del informe (huella sin agregación) tiene la amplitud fija
  y crece ×6 a lo ancho del barrido; es un control de paja. Con amplitud ajustada a los mismos pares: exponencial en
  el cenit 1,22, huella suave ajustada 1,39, ley con agregación ajustada por mínimos cuadrados 1,27. La ley del ATBD
  sin ajustar da 1,09. **Gana igual**, y eso es la mejor evidencia del estudio. Pero en la regresión el R² es casi el
  mismo con y sin agregación (0,164 contra 0,159, `03_salida.txt`), y el exponente que ajustan los datos es 0,69, no 1.
- **Selección de volcanes**: no está en el pre-registro. El criterio (sin kernel local) es mecánico, no por resultado,
  pero Nevados de Chillán tampoco tiene kernel local y quedó fuera sin decirlo (15 pares, R ~0,01, otro régimen).
  Copahue aporta 28 pares, con 2 en dos zonas. En la práctica son **Láscar más Isluga** (723 de 751).
- **Por volcán**: Láscar aplana a 1,13; **Isluga no** (1,33: 0,894 en 20-36° a 0,671 sobre 52,7°); Copahue 3,06 con
  n ínfimo. El 1,09 agrupado esconde a Isluga.
- **Pares por zona** (3 volcanes): 169 / 165 / 100 / 128 / 189. Por volcán y zona en `v3_salida.txt` [a]. Láscar no
  tiene pares en ±3° a la derecha de 36,32°, Isluga no los tiene a la izquierda: la zona de 20-36,3 y la de 36,3-44 no
  tienen la misma mezcla de volcanes. Normalizando por volcán el perfil queda 0,94 a 1,02, así que la mezcla no lo
  explica, pero el escalón de 36,32° no está identificado en los pares (con spline libre, IC de −0,40 a +0,69).

## 5. Sintético: CONFIRMADO lo que dice, pero mide poco

Las energías (1,0 y 3,0 MW) están en `PREREGISTRO.md` antes de correr: sí. Pero el resultado es **tautológico para
la geometría**: se inyecta ΔL·A_nativo constante en un solo píxel sobre fondo uniforme con ruido 0,5 K, y con área
nadir fija la salida tiene que ser 140.625/A_nativo si el detector toma ese píxel y estima bien el fondo. La pendiente
0,995 confirma eso y nada más. La detección es trivial: 1 MW a 800 K a 69,7° de cenit sube la BT I04 del píxel unos 10 K
sobre ruido de 0,5 K; 192 de 192 no informa sobre el régimen débil, la PSF ni el fondo heterogéneo, que es donde
podría haber pérdida. «Nuestro código hace exactamente lo que dice la fórmula» vale sólo para ese caso ideal.

## 6. Recomendación (A/B del área con huella nativa con agregación): PARCIAL, choca con S133 más de lo que dice

- **No es otra ley en esencia.** `pixel_areas_from_geolocation` (`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\pipeline\scan_geometry.py:248`)
  dice en su docstring que la distancia entre centros trae «los saltos de agregacion ya adentro», y S133
  (`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\s133\SUSTRATO_AREA_GEOLOCALIZADA.md`) dice que reproduce el 4,38×
  del ATBD. La diferencia con la huella modelada es el solape de bow tie a lo largo del vuelo. Comparando factores:
  S133 multiplicó el borde 50°+ por ~2,2 relativo al control (0,619 a 1,360, con 1,09 en el nadir); la huella del
  estudio da ~1,7 a 1,8 relativo. Es ~15 % más suave, no una ley distinta.
- **El propio informe predice que se pasa**: con todos los volcanes la razón corregida va de 0,868 (nadir) a 1,096
  (borde), máx/mín 1,26. El criterio C1 de S133 (los dos bins en 0,9 a 1,1) fallaría en el nadir.
- **MISSION y A85**: la adopción es uniforme; per-volcán o per-régimen está excluido. Medir los volcanes con kernel
  local aparte está bien como diagnóstico, pero si la palanca sólo funciona sin kernel, el A/B ya sabe que falla.
- **D17**: el brazo fiel es bow tie más remuestreo, en ese orden. Una ley de área sobre píxel nativo es un sustituto;
  no cierra D17 y no hay que venderla como cierre.
- **A66/A67**: no hay choque de fondo. El OSF confirma que MIROVA aplica área nadir fija sobre **sus celdas de 375 m**
  (fila 2 del CSV: (0,206862 − 0,180726) × 18 × 140.625 = 66.155, igual al VRP publicado); lo que difiere es sobre qué
  píxel se aplica. Pero si (punto 3) MIROVA suaviza y umbraliza, su VRP débil no conserva energía y la corrección
  completa sobre nuestro píxel nativo se pasaría en los débiles.
- **Pares de 2025, antes de #535**: el informe lo dice; S133 midió sobre 2026. Hay que re-medir antes de pre-registrar.

Si se corre, el pre-registro debería exigir: ganarle al brazo «área geolocalizada» de S133 en el borde, el escalón
en 36,32° medido con contraste local y su placebo, y el estrato de fuentes débiles por separado.

---

## Cosas que el informe debería corregir aunque no cambien el veredicto

1. El límite ±0,405 / ±0,693 es el subpíxel, no el de fuente extensa (punto 3).
2. El nulo pre-registrado (barajado) se reemplazó sin declararlo como desvío.
3. En 36,32° el escalón viene del VRP total, no de Npix; «VRP total no salta» es cierto sólo en 52,66°.
4. El control «huella suave» tiene amplitud fija; con amplitud ajustada el contraste es 1,09 contra 1,22 a 1,39, no
   1,09 contra 2,83.
5. Isluga sola no aplana (1,33); Nevados de Chillán excluido sin decirlo.
6. M13 no se agrega a bordo (Tabla 2.2-1); aclarar antes de llamar «réplica» al V750.
