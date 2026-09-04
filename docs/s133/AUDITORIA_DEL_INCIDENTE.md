# S133 · Auditoría del incidente: una alerta que no vimos, y las cinco cosas que la escondieron

**Punto de partida.** El 2026-09-04 MIROVA publicó una anomalía térmica MODIS de **4,75 MW
a 1,41 km del cráter de Villarrica**, de la pasada de las 07:50 UTC. Nosotros no la
teníamos. Nicolás preguntó por qué.

**Desenlace.** La tenemos: **3,859 MW a 0,85 km, clasificada *summit***. Razón contra MIROVA
**0,81×**, dentro de la banda de paridad. No hizo falta tocar la detección ni la magnitud:
el dato simplemente nunca había llegado.

Debajo de esa sola pregunta había cinco defectos distintos, cuatro de ellos silenciosos.
Ninguno producía un error; todos producían un cero, una etiqueta equivocada o una métrica
en verde.

---

## 1. El camino casi-en-tiempo-real de MODIS pedía una colección inexistente

**Qué pasaba.** Para el fallback NRT de MODIS pedíamos `MYD021KM_NRT` versión `61`. Esa
colección no existe. LANCE nombra las suyas con el **mismo** short_name del estándar y marca
lo casi-en-tiempo-real en la **versión**: `MYD021KM` v`6.1NRT`.

**Por qué nadie lo vio en años.** Una colección inexistente **no da error**: da cero
granules. Y cero granules es indistinguible de «todavía no hay dato», que es una situación
perfectamente normal a las tres horas de una pasada.

**Por qué se destapó justo ahora.** El fallback sólo importa cuando el estándar se atrasa, y
Aqua estaba a **35,6 h** (Terra 11,6 h; VIIRS 9,8-11,8 h). Aqua sobre Villarrica: 3 o 4
granules diarios hasta el 2 de septiembre, y **cero** el 3 y el 4. Con el estándar a 36 horas
y el NRT roto, no había por dónde entrara.

**De dónde salió el error.** Para VIIRS el sufijo `_NRT` **sí es correcto**. Se extrapoló el
esquema de un sensor al otro — la misma familia que A37, que nació de descubrir que MODIS y
VIIRS marcan la saturación de maneras distintas.

→ PR #587. El test fija las **dos** convenciones: sin el control de VIIRS, alguien podría
«arreglar» VIIRS por simetría y romper lo único que funcionaba.

## 2. Y los granules NRT de MODIS se guardaban como «standard»

Apareció al **verificar el resultado** en vez de darlo por bueno: el record entró, pero con
la procedencia equivocada. Los nombres reales:

    MODIS  MYD021KM.A2026247.0750.061.2026247092322.NRT.hdf   -> token ".NRT."
    VIIRS  VNP02IMG_NRT.A2026247.0606.002.2026247081613.nc    -> prefijo "_NRT"

El detector sólo miraba `_NRT`. **No es cosmético**: `store.py` reemplaza un record por su
calibración definitiva sólo cuando el guardado dice `nrt` y el nuevo dice `standard`. Un
granule de LANCE mal etiquetado nunca dispara esa condición y se queda con la calibración
provisional para siempre. Reprocesar tampoco lo arregla.

Se repararon 10 records, verificando **uno por uno contra el catálogo** si existía el
estándar de esa pasada. De 77 revisados, 67 estaban bien.

→ PR #588.

## 3. La cadencia del cron cayó 51 % y ningún monitor lo miraba

Desde el 2026-08-27 GitHub entrega **la mitad** de los eventos programados de este
ecosistema. Es externo: cero corridas canceladas (así que no es la concurrencia), los `cron`
declarados no cambiaron, y la caída es uniforme sobre los cuatro workflows con cron
(98→40 %, 96→45 %, 96→40 %, 84→22 %).

**No se perdió un solo record**: 116 records/día antes contra 121 después, 11/11 volcanes
todos los días. Cada corrida procesa el día completo, así que una franja saltada la cubre la
siguiente. Se degrada la latencia, de ~3-4 h a ~7 h.

**El agujero era que estuvimos ocho días sin verlo.** Ningún monitor falló: `nrt-monitor`
mira 3 fallas seguidas y no hubo ninguna, `nrt-healthcheck` mira dato de más de 48 h y nunca
pasó de 7. Dos métricas en verde sobre un mecanismo degradado a la mitad. Y hay una razón
mecánica por la que se escapa de cualquier monitor de fallas: **una corrida que no ocurre no
deja rastro**.

→ PR #585. La medición va en el healthcheck que ya corre, no en un cron nuevo que empeoraría
lo que mide.

## 4. El archivo de TIF llevaba una semana sin capturar

Y esto **sí destruye información de forma irreversible**: MIROVA sobrescribe su imagen
«Last» en cada pasada, así que una captura que no se toma no se puede tomar después. El TIF
de la anomalía de 4,75 MW se perdió.

Dos causas encadenadas, y **mi primer diagnóstico fue incompleto**:

- **Lo que dije primero**: el grupo de concurrencia. GitHub mantiene una sola corrida
  pendiente por grupo, así que con cron-job.org disparando cada 5 minutos cada disparo
  desplazaba al anterior. Es real y estaba agravando.
- **Lo que faltaba, y era el asesino principal**: el `timeout-minutes` estaba en **10**, y la
  duración típica del poll es de **12,3 minutos de mediana, 14,6 el p90 y 15,0 el máximo**,
  medido sobre las 100 últimas corridas exitosas. El reloj estaba **por debajo de la
  mediana**: la mayoría de las corridas estaba condenada de antemano.

Lo que me despistó: **GitHub reporta un job matado por timeout como `cancelled`**, la misma
palabra que usa para la cancelación por concurrencia. Leí la palabra y no la duración. La
corrida que lo delató empezó 18:40:12 y murió 18:50:28 — diez minutos y dieciséis segundos.

La otra pista que confirmaba el timeout y no la concurrencia: la última corrida **exitosa**
fue el 27 de agosto, no el 2 de septiembre. Los commits de septiembre son de corridas que
alcanzaron a hacer `push` **antes** del hachazo.

→ `mirova-tif-archive` PR #2 (quitar el grupo) + commit del timeout a 25 min (A15: 15 × 1,3
= 19,5, más margen porque los runners vienen lentos). **El disparo de 5 minutos de
cron-job.org se conserva a propósito**: con la entrega de GitHub al 40 %, depender del cron
nativo sería depender justo de lo que está fallando.

## 5. VegStress-v1 lleva tres semanas caído

Del barrido de salud de los 16 repos del ecosistema: falla desde el 2026-08-13, 7 de 15
corridas. El error es explícito y el propio workflow tiene la guardia que lo dice: faltan los
secrets `SH_CLIENT_ID` y `SH_CLIENT_SECRET` de Sentinel Hub. Se arregla cargándolos.

Los demás: nueve publicando hoy sin problemas; VolcPlume-v1 (152 días) y
openVIS-Colaboracion-1 (131 días) dormidos sin CI; lago-caburga y valles-volcanicos-chile
parecen análisis terminados.

---

## Lo que este incidente enseña sobre cómo fallan estos sistemas

**Ninguno de los cinco defectos produjo un error.** Produjeron un cero (colección
inexistente), una etiqueta plausible (`standard` en vez de `nrt`), una métrica en verde
(monitores que miran fallas donde el problema era ausencia), y una palabra ambigua
(`cancelled` para dos causas distintas). Un sistema que sólo vigila errores es ciego a los
cuatro.

**Y tres veces el instrumento se equivocó antes que el dato**, en esta misma sesión:

| lo que parecía | lo que era | qué lo atrapó |
|---|---|---|
| «sub-reportamos Villarrica 24×» | comparé nuestra mediana sobre TODAS las pasadas contra la de MIROVA sobre sus ALERTAS | mirar las noches concretas |
| «el audit está ciego a 5 volcanes» | truncé el diccionario en mi propio `print` | volver a imprimirlo completo |
| «los TIF se dejaron de guardar en julio» | la API de GitHub corta en 1000 archivos **sin avisar** | el `index.csv` del propio repo |

Las tres las corrigió Nicolás insistiendo o yo verificando el instrumento antes que la
conclusión. La primera y la tercera las había reportado ya como hallazgo. Es exactamente lo
que A62 dice y lo que la regla A92 acaba de nombrar para el caso de los guards: **la
herramienta se equivoca en la misma dirección que el defecto que busca**.
