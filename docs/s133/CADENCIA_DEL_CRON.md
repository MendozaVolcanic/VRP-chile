# S133 · El cron dejó de correr la mitad de las veces, y estuvimos ocho días sin verlo

**Diagnóstico: GitHub dejó de entregar aproximadamente la mitad de los eventos `schedule`
de este repo el 2026-08-27. Es externo, nuestra configuración no cambió, y no se perdió un
solo dato.** El efecto es de latencia. Lo que sí quedó demostrado es un agujero propio: no
teníamos con qué verlo.

Todos los números salen de la API de GitHub y de los JSON del repo, medidos en la sesión.

## Lo que se observó

El NRT declara `cron: "0 */2 * * *"`, doce corridas al día. Hasta el 26 de agosto hacía
once o doce; desde el 27 hace entre dos y cinco. La data de los once Tier A llegó a tener
siete horas de antigüedad, contra las dos que declara el diseño del cron.

## Las hipótesis, y cómo se cayeron

**No es la concurrencia.** La sospecha natural era el grupo `push-main`: `nrt.yml` ocupa el
lock unos cincuenta minutos y GitHub mantiene una sola corrida pendiente por grupo, así que
una corrida encolada puede ser desplazada por la siguiente. Si fuera eso, veríamos corridas
**canceladas**. De las últimas 200 corridas del NRT, 199 terminaron en `success` y una
estaba en curso. **Cero canceladas.** Las corridas que faltan no se desplazaron: nunca se
crearon.

**No es nuestra configuración.** Se compararon las declaraciones de `cron` de todos los
workflows entre el 26 de agosto y hoy. Son las mismas. La única diferencia es un cron
**agregado** después, el del watchdog: la carga declarada subió, no bajó.

**No es del NRT.** Ésta es la prueba que decide. La caída golpeó por igual a los cuatro
workflows con cron del repo:

| workflow | antes (por día) | después | entrega |
|---|---:|---:|---|
| NRT VRP Pipeline | 11,8 | 4,8 | 98 % → 40 % |
| NRT Retry | 11,5 | 5,4 | 96 % → 45 % |
| Deploy GitHub Pages | 11,5 | 4,8 | 96 % → 40 % |
| sync-mirova-csv | 20,2 | 5,4 | 84 % → 22 % |

Ventanas: 23-26 de agosto contra 30 de agosto - 3 de septiembre. En total, 60,2 corridas
programadas por día antes y 29,4 después, una caída del 51 %. Un fenómeno que afecta por
igual a cuatro workflows independientes no está en ninguno de los cuatro. Y las que sí
ocurren llegan tarde: el healthcheck tiene cron a las 12:00 UTC y últimamente arranca entre
las 15:24 y las 21:34.

## Lo que NO pasó, y es lo que cambia la prioridad

**No se perdió un solo record.** La mediana de records por día es 116 antes (19-26 agosto) y
121 después (28 agosto - 3 septiembre), con los once Tier A cubiertos **todos** los días. La
razón es de diseño: cada corrida del NRT procesa el día completo, así que una franja saltada
la cubre la siguiente. Lo que se degrada es la latencia, de unas tres o cuatro horas a unas
siete, no la completitud.

Eso reordena la urgencia. El dashboard muestra todo; lo muestra más tarde.

## El agujero real: nadie miraba la ausencia

Ningún monitor falló. Es peor que eso: **ninguno mide esto**.

- `nrt-monitor` abre issue si fallan tres corridas seguidas. No falló ninguna.
- `nrt-healthcheck` abre issue si el dato pasa de 48 horas. Nunca pasó de siete.

Las dos métricas en verde sobre un mecanismo degradado a la mitad. Es exactamente la forma
de A87: un indicador que deja de señalar no prueba que el fenómeno se haya ido. Y hay una
razón mecánica por la que este caso se escapa de cualquier monitor de fallas: **una corrida
que no ocurre no deja rastro**. No hay un run en rojo que mirar. Sólo se ve contando lo que
debería haber pasado y no pasó.

## Lo que se hizo

`scripts/medir_cadencia_cron.py` cuenta las corridas por `schedule` de cada workflow en una
ventana y las compara con lo que su cron declara. Se enchufó al healthcheck diario, que ya
corre, en vez de crear otro cron: agregar uno más empeoraría justamente lo que se quiere
medir.

**Reporta siempre, alerta casi nunca.** La única condición de alerta es cero corridas del
NRT en 24 horas, que sí es un apagón accionable. Una entrega del 40 % no abre issue, y es
deliberado: no hay pérdida de datos, no está en nuestras manos arreglarlo, y una alerta que
no se puede accionar es ruido. El ruido tapa la alerta que importa, que es la lección que
dejó la issue #567 con sus 22 comentarios sobre un workflow borrado.

El contrato de cuántas corridas declara cada cron vive en el script y hay un test que lo
coteja contra el `cron` real de los yml, para que cambiar uno sin el otro no deje el
porcentaje mintiendo.

## Lo que queda sin responder

**Por qué GitHub empezó a descartar eventos el 27 de agosto.** No se determinó y no se
inventó una causa. Las candidatas razonables son la carga del planificador de GitHub, que
su documentación reconoce explícitamente, o alguna forma de limitación por uso, en un
período en que este repo corrió muchos reprocesos pesados. Ninguna de las dos se puede
verificar desde afuera, y ninguna cambia lo que corresponde hacer: medir, y no alertar por
algo que no se puede accionar.

Si la entrega baja de forma que sí amenace la frescura, el healthcheck de 48 horas sigue
puesto y ahora, además, la cadencia queda registrada todos los días.
