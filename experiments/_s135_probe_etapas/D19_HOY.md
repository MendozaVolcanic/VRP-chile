# ¿De qué tamaño es D19 hoy? (S135)

> Números de `d19_regimen_vigente.py` → `d19_regimen_vigente.json` (regla S91, ninguno
> transcrito a mano). Definiciones heredadas del verificador con contexto limpio de S134
> (`experiments/_s134_audit/f3/verif_h1.py`, `verif_h1c.py`). Universo: records VIIRS 375 m de
> los 11 Tier A desde 2026-06-01 hasta el último record (2026-09-06 06:36). Corte de régimen:
> 2026-08-28 23:00:56 UTC, el merge del PR #535 que sacó la máscara de nube del código y la pasó
> al perfil (D14), verificado con `gh pr view 535`.
>
> **Esta es la segunda versión.** La primera midió la proporción sobre los records etiquetados
> *summit*, y ese denominador se movió con el mismo cambio de código que se estaba midiendo. Un
> verificador con contexto limpio lo refutó (gravedad 5). Lo que sigue usa el denominador
> robusto —todos los records de VIIRS 375 m— y agrega la serie mensual, que era lo que faltaba
> para no confundir un cambio de código con la variación normal entre meses.

## Por qué había que medirlo antes del A/B

D19 se abrió en S134 con conteos del régimen de fondo anterior, y el probe del paso 0 mostró que
11 de 12 pasadas persistidas como `test1_roi` hoy salen por el path contextual. Si el mecanismo
cambió de tamaño, el A/B se diseñaría sobre el número equivocado.

## Lo que cambió de verdad

**1. El etiquetado, mucho.** La fracción de records de VIIRS 375 m que el pipeline etiqueta
*summit* pasó de **69,3 %** a **88,7 %**. Es el cambio más grande de todos, y es consecuencia
directa del fondo: con la máscara de nube apagada entra al anillo de fondo la nieve fría, el
fondo global baja y más cúmulos quedan dentro del radio interno.

**2. La fracción de píxeles más fríos que su propio fondo, bastante.** De **66,4 %**
(1.056/1.591) a **34,5 %** (57/165). Con la salvedad de que los denominadores no son homogéneos:
en el régimen viejo el 15,8 % de los `test1_roi` no trae `anomaly_pixels` y queda fuera del
cálculo, mientras que en el nuevo están todos. Acotando ese sesgo por los dos extremos, el valor
viejo está entre **55,9 % y 71,7 %**: la caída se sostiene igual.

**3. La proporción del mecanismo, no.** Sobre el denominador robusto:

| ventana | `test1_roi` / todos los V375 |
|---|---|
| junio 2026 | 49,1 % [46,5-51,7] |
| julio 2026 | 40,0 % [37,4-42,6] |
| agosto (hasta el corte) | 49,5 % [46,8-52,2] |
| **desde el PR #535** | **39,0 % [34,5-43,7]** |

El valor del régimen nuevo es **indistinguible del de julio**. La variación mes a mes es del
mismo tamaño que la supuesta caída, así que **la reducción del mecanismo no está demostrada**;
lo que está demostrado es el salto del fondo y del etiquetado. El antes/después agregado
(46,2 % → 39,0 %) existe, pero descansa en que junio y agosto fueron altos, no en un quiebre.

**4. La producción del artefacto, tampoco.** La población que el pre-registro llama «nivel base
falso» —cúmulo de un píxel, más frío que el fondo global, sin alerta de MIROVA esa noche— son
**974 records en los 88 días** del régimen viejo y **91 en los 9 días** del nuevo: 11,1 contra
10,1 por día. **La tasa diaria es prácticamente la misma.** El artefacto se sigue publicando al
mismo ritmo.

## Lo único que sí cambió para el diseño del A/B

De esa población de nivel base falso, la porción que el A/B de `keep_peak` puede mover —la que
viene por la rama `test1_roi`— cayó de **87,0 %** (847 de 974) a **62,6 %** (57 de 91). El resto
llega por el path contextual, que ningún brazo del experimento toca.

> Es decir: el artefacto no se redujo, **se mudó de rama**. Hoy más de un tercio de él está fuera
> del alcance del A/B propuesto. Eso cambia el criterio de éxito, no la justificación del
> experimento.

## Lo que NO se puede leer de esta tabla

La corroboración de MIROVA en el régimen vigente. El CSV de referencia termina el **2026-08-31**
y nuestros records llegan al 09-06: de los nueve días del régimen nuevo sólo tres tienen ground
truth, y el denominador por volcán queda entre **1 y 9 noches**. La primera versión de este
script no recortaba esa ventana y mostraba «0,0 %» en ocho de los once volcanes, que se lee como
«dejó de corroborar» cuando significa «MIROVA no fue observada». Corregido: la columna lleva su
propio `n` y donde no hay ground truth dice `s/gt`.

**Hallazgo lateral, del mismo tipo** (familia A17, canal partido): el archivo que leen el
cargador canónico y todos los análisis —`data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv`,
35.037 filas hasta el 31-ago— está siete días atrás de `latest_consolidado.csv` (36.160 filas,
hasta el 07-sep), que es el que `sync-mirova-csv.yml` refresca cada hora y consume el frontend.
El workflow corre verde: no está roto, escribe en otro archivo. Queda como seguimiento; no se
toca acá porque cambiar la fuente del ground truth en medio de una medición comparativa la
invalidaría.

## Otras correcciones del verificador, incorporadas

- «El 100 % de un solo píxel» era **97,6 %** (161 de 165; hay cuatro cúmulos de dos píxeles).
- El corte se aplica sobre la hora de la pasada, no sobre cuándo se escribió el record. Con las
  ~3 h de latencia del NRT, unos pocos records de las horas previas al corte fueron producidos
  por el código nuevo y quedan contados en «viejo». El efecto es marginal y no se corrigió.
- No se pudo descartar que algún reproceso histórico haya reescrito records viejos con código
  posterior al PR #535: el esquema no guarda la fecha de procesamiento.

## Consecuencia

El A/B sigue justificado: el mecanismo produce el 39 % de los records de VIIRS 375 m y el
artefacto se publica a razón de unos diez por día en los 11 Tier A. Pero el criterio de éxito
tiene que medirse **sobre la población que los brazos pueden mover**, y la ventana del
experimento tiene que ser la histórica reprocesada con el código de hoy, no los nueve días
sueltos del régimen nuevo. Está escrito en `docs/PREREGISTRO_AB_D1_D2_S135.md`.
