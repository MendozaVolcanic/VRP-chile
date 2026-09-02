# S131 · El remuestreo es una ley de área, y en VIIRS el bow-tie ya está hecho

Trazado del único frente que S130 dejó abierto. **Tres cosas cambian respecto de lo
que el bloque de arranque heredaba**: el mecanismo tiene magnitud suficiente para
explicar el gradiente, el bloqueo del bow-tie no aplica al sensor donde el gradiente
está probado, y hay un número mal leído en nuestro propio código.

## 1. Qué dice el paper, verbatim

El bloque heredaba «MIROVA remuestrea a una malla de área constante (Coppola 2014
§2.2)». Se leyó el PDF local. Dice más que eso, y lo dice con el mecanismo:

> *«high scan angles contribute to the growth of the projected ground spatial element
> (up to approximately 10 km² for scan angles of 55°; Nishihama et al. 1997). This
> leads the radiance of a potential sub-pixel hot-spot to be integrated over a
> variable area, thus introducing a further source of error in estimating its thermal
> output.»*

Y el paso concreto:

> *«one hot-spot pixel, whose area is 2 km² in the original image, becomes two pixels
> with equal areas of 1 km² in the resampled image.»*

Y el cierre del círculo, en la ecuación del VRP (§ VRP):

> *«where APIX is the pixel size (1 km² for the resampled MODIS pixels).»*

**El área nominal fija de MIROVA es válida PORQUE remuestrearon.** Las dos piezas van
juntas. Nosotros adoptamos la mitad —área nadir-fija (A66/A67)— sin la otra. Lo que
S130 midió como gradiente cenital es exactamente «the further source of error» que
Coppola nombra en ese párrafo.

## 2. La equivalencia que abarata el arreglo

Un píxel oblicuo de área real `A` con exceso de radiancia `ΔL`, remuestreado a celdas
de área nominal `A₀`, produce `A/A₀` celdas cada una con `ΔL`. La suma sobre el ROI da

    Σ k·A₀·ΔL  =  (A/A₀)·k·A₀·ΔL  =  k·A·ΔL

que es **idénticamente** lo que se obtiene usando el área verdadera del píxel sin
remuestrear nada. Para la **integral de magnitud**, remuestrear y usar el área real
son la misma operación. El regrid no agrega nada que el área no dé.

⚠️ **La equivalencia es sólo para la magnitud sobre un conjunto de píxeles ya
detectados.** El remuestreo también cambia el fondo (μ/σ sobre la malla remuestreada),
el conteo de píxeles y la contigüidad de los clústeres. Y **A67 ya enseñó que el área
es multiplicador en el Test 1**, así que cambiarla mueve la DETECCIÓN, no sólo la
magnitud. Eso hay que medirlo, no suponerlo.

## 3. El bow-tie no bloquea el camino de VIIRS

S130 dejó escrito «bow-tie + regrid en ese orden, o nada», citando a Coppola 2012
§3.2. La cita es correcta **y es sobre MODIS**: Coppola 2014 §2.1 describe el
de-solape scan-a-scan con Nishihama et al. 1997, dentro de una tubería MODIS.

En VIIRS el de-solape **lo hace el sensor a bordo**. El ATBD de geolocalización
(423-ATBD-002 §2.2) describe la agregación along-scan en tres zonas —3×1 hasta
31,589° de scan, 2×1 hasta 44,680°, 1×1 después— y el L1B entrega los píxeles
sobrantes marcados `Bowtie_Deleted`. **Nuestro código ya los enmascara**:
`pipeline/process_viirs.py:80`, `FLAG_DNS = {65532, 65533, 65534, 65535}`.

La ironía ordena el frente: **el sensor donde el gradiente está probado (VIIRS) es
aquel donde el bow-tie ya está resuelto; el sensor donde el bow-tie es trabajo real
(MODIS) es donde el gradiente NO está probado** (bins no monótonos, 17-21 pares).

## 4. La medición: ¿alcanza el área?

> ⚠️ **CORRECCIÓN S131 (misma sesión, eje magnitud de la auditoría —
> `docs/s131/agentes/MAGNITUD.md` §2.7-§2.9).** La tabla de abajo empareja **cada
> pasada nuestra contra el máximo de la noche de MIROVA**: `cargar_mirova` colapsa por
> `(fecha, bucket)` aunque el docstring del script diga «un par por (volcán, fecha,
> bucket)». Una pasada oblicua débil queda comparada con la mejor pasada de MIROVA de
> esa noche —que suele ser otra, más cerca del nadir— y el gradiente se infla. Es el
> error que la propia cabecera de `experiments/_s126_lib.py` documenta, y **S130 lo
> heredó igual** (su 0,740 → 0,253 tiene la misma definición).
>
> Con emparejamiento **pasada a pasada** (la ground truth trae hora al segundo;
> `experiments/_s131_audit/magnitud/03_pares_por_pasada.py`, n = 1.596 V375): el ratio
> va de **0,771 en nadir a 0,447 a 50°+** → **f requerido 1,72**, no 2,93. Y aplicando la
> ley de área anclada al ATBD, **los cinco bins quedan planos** (0,79 / 0,80 / 0,87 /
> 0,81 / 0,86; IC95 de nadir y 50°+ se solapan) y la mediana global sube de 0,58 a
> **0,82**. Conclusión corregida: **el área explica el gradiente completo**, no es sólo
> «condición necesaria». Lo que sobra es un déficit **uniforme** (~0,82), que es otro
> mecanismo (el fondo de Eq. 6 y la suma/clúster, §2.3 y §2.5 del informe).
>
> Matiz sobre «MIROVA es plano» (S130): vale por noche; por pasada MIROVA baja de 0,230 a
> 0,170 MW en V375 — sigue mucho más plano que lo nuestro (0,159 → 0,076), y la
> conclusión «el sub-reporte es nuestro» se mantiene.
>
> La tabla original se conserva abajo tal como se midió, por historia.


Atribuir no es explicar. `experiments/_s131_remuestreo/factor_requerido.py` despeja de
los datos, sin asumir ninguna ley, cuánto crecimiento de área haría falta para que
cada bin volviera al ratio del bin de nadir: `f_req(bin) = ratio(0-15) / ratio(bin)`.

| sensor | bin | cenital mediano | ratio | **f requerido** |
|---|---|---|---|---|
| VIIRS375 | 0–15° | 7,4° | 0,740 | 1,00 |
| VIIRS375 | 15–25° | 21,4° | 0,584 | 1,27 |
| VIIRS375 | 25–35° | 31,8° | 0,466 | 1,59 |
| VIIRS375 | 35–50° | 43,1° | 0,389 | 1,90 |
| VIIRS375 | 50°+ | 60,3° | 0,253 | **2,93** |
| VIIRS750 | 50°+ | 59,1° | 0,343 | **2,26** |

Y `ley_atbd.py` pone al lado el crecimiento **disponible**, de la Tabla 2.2-1 del
ATBD (HSI en km, along-track × along-scan):

| banda | nadir | fin de swath | eje track | eje scan | **área** |
|---|---|---|---|---|---|
| I4 (VIIRS375) | 0,371 × 0,388 | 0,80 × 0,789 | 2,16× | 2,03× | **4,38×** |
| M13 → fila M6/M8 (VIIRS750) | 0,742 × 0,776 | 1,60 × 1,58 | 2,16× | 2,04× | **4,39×** |

**El requerido (2,93× a 60° de cenital) entra cómodo bajo el disponible (4,38× al
borde, ~70°).** Es condición necesaria, no prueba: la ley por ángulo tiene los saltos
de las zonas de agregación y hay que tomarla del ATBD, no interpolarla.

## 5. El número mal leído en nuestro código

`pipeline/scan_geometry.py`, docstring de `viirs_pixel_areas`, afirma que el área del
píxel I agregado *«varies only between ~0.32 and ~0.6 km² across the full swath (Cao
et al. 2014)»* y por eso topa la corrección en **2,0×**.

Contra el ATBD (tope de la jerarquía A35, por encima de cualquier paper): el área va
de **0,144 a 0,631 km²** — el extremo de nadir no coincide, y el crecimiento es
**4,38×**, no 1,9×.

De dónde salió el 2: el propio ATBD dice *«the pixel growth multiplier is limited to
approximately 2 both along track and along scan»*. Ese 2 es **por eje**. El área es el
producto de los dos. **El docstring leyó el multiplicador por eje como si fuera el del
área** — y ese tope de 2,0× es justamente lo que impediría que una ley de área
correcta funcionara, si algún día se apagara `nadir_fixed`.

Hoy no hace daño operacional: producción corre `nadir_fixed=True` y no pasa por esa
rama. Es una mina enterrada, no un incendio.

## 6. Lo que NO está probado

- **MODIS.** El gradiente no está establecido ahí, y es el sensor donde el bow-tie sí
  es trabajo real. Extender la corrección a MODIS sería extrapolar.
- **El efecto sobre la detección.** ~~A67: el área multiplica la energía integrada del
  Test 1.~~ ⚠️ **SIN RESPALDO en el código de hoy** (auditoría S131, MAGNITUD §2.8):
  `test1_integrated.py` integra `Σ max(0, L − L_bg)` **sin área**, y `detection_context.py`
  no usa área. En el código actual una ley de área cambia **sólo la magnitud**; la vía por
  la que un cambio de área apagó detecciones en S103 tuvo que ser aguas abajo (piso de VRP,
  hoy 0). El A/B igual mide FN a nivel record, por si queda algún gate en MW.
- **La ley por ángulo.** Los dos extremos del ATBD no dan la curva intermedia; las
  zonas de agregación la hacen discontinua.
- **Que el área sea el ÚNICO mecanismo.** Que alcance no implica que sea todo.

## 7. Sustrato (la regla de esta etapa)

Antes de gastar CI: el mecanismo tiene ocasión de actuar en **todas** las pasadas
oblicuas, y el bin de 50°+ es el **más poblado** de VIIRS375 (1.147 de 2.773 pares).
A diferencia del A/B de los fondos de S130, acá el sustrato sobra. Y a diferencia del
A/B de D18, el mecanismo **sí decide**: el factor requerido es de 2 a 3×, no un
empujón marginal sobre un umbral.

---

**Fuentes**: `documentacion/coppola2014_ijrs_strombolian_10.1080-01431161.2014.903354.pdf`
§2.1, §2.2 y ec. del VRP · `documentacion/VIIRS_Geolocation_ATBD_2014.pdf` §2.2 y
Tabla 2.2-1 · `pipeline/process_viirs.py:80` · `pipeline/scan_geometry.py:180-215`.
**Scripts**: `experiments/_s131_remuestreo/{factor_requerido,ley_atbd}.py` con sus JSON.
