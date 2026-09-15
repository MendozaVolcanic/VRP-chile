# ¿Sirve un cron externo para el NRT? Evaluación S141 (2026-09-15)

Pregunta de Nicolás: "si el NRT depende de GitHub Actions, quizás tenemos que usar cron job".

## 1. El fenómeno

Un cron declarado en un workflow de GitHub no es un reloj propio: es un pedido a un despachador
compartido. Desde el 2026-08-27 ese despachador atiende los pedidos de este repositorio con atraso y
funde las franjas que vencen mientras hay una pendiente (S139, `docs/audit_s139/NRT_CADENCIA_Y_MEJORAS.md`
§1). La consecuencia no es pérdida de datos, porque cada corrida reprocesa siete días, sino
**latencia**: una anomalía de las 05:00 UTC puede aparecer en el dashboard muchas horas después.

La pregunta que decide si un cron externo sirve es **dónde** está el atraso: en que GitHub cree el
evento o en que un runner tome el trabajo. Si es lo primero, un disparador externo que llame a
`workflow_dispatch` lo evita, porque ese evento nace en el momento de la llamada.

## 2. La medición

`scripts/medir_atraso_despacho_nrt.py --n 60`, salida en `experiments/_s141_cron/atraso_despacho.json`
(las cifras de esta tabla salen de ese archivo):

| evento | corridas | creación del run a primer job (mediana / máx) | atraso de creación sobre la franja (mediana / máx) | corridas por día |
|---|---|---|---|---|
| `schedule` | 57 | 2 s / 12 s | 56 min / 120 min (cota inferior: las franjas fundidas no se ven) | 4,75 de 12 declaradas |
| `workflow_dispatch` | 3 | 3 s / 4 s | no aplica: se crea al llamarlo | |

**Conclusión: el atraso está entero en la creación del evento programado.** Una vez creado, el run
arranca en segundos. Un disparador externo a horas fijas eliminaría el atraso y la fusión de franjas.

## 3. Opciones

| opción | cómo | a favor | en contra | credencial |
|---|---|---|---|---|
| **A. Servicio externo de cron** (por ejemplo cron-job.org) | cada 2 h hace `POST /repos/MendozaVolcanic/VRP-chile/actions/workflows/nrt.yml/dispatches` con `{"ref":"main"}` | no depende de tu PC; puntual; gratuito | un servicio de terceros guarda un token | **token nuevo**: fine-grained, sólo el repo VRP-chile, permiso *Actions: Read and write*, con vencimiento |
| **B. Tarea programada de Windows en tu PC** | `gh workflow run nrt.yml -R MendozaVolcanic/VRP-chile --ref main` cada 2 h | sin credencial nueva (`gh` ya está autenticado con permiso `workflow`, verificado hoy) | sólo corre con el PC encendido; la ventana que importa (07 a 10 UTC, 03 a 06 hora de Chile) es de madrugada | ninguna nueva |
| **C. Tarea programada de la app de Claude** | una tarea que llama al mismo `gh workflow run` | ya está instalada | corre sólo con la app abierta y abre una sesión de Claude por disparo: caro y frágil para algo que es una llamada HTTP | ninguna nueva |
| **D. Dejar el cron de GitHub** | nada | cero cambios | la latencia sigue | ninguna |

En todas las opciones A a C **el cron de GitHub se deja como respaldo**: si el disparador externo falla,
el programado sigue entrando tarde pero entra. Dos corridas cercanas no se pisan: el grupo de
concurrencia `push-main` las serializa, y el store no duplica records (clave pasada y sensor).

## 4. Recomendación

**Opción A, con el cron de GitHub como respaldo**, cada dos horas en horas impares UTC a los 10 minutos
(expresión `10 1-23/2 * * *`: 01:10, 03:10, ..., 23:10). Por qué impares: las pasadas nocturnas útiles de
VIIRS en Chile se concentran a las 04, 05 y 06 UTC (S139, `analiza_latencia.py`: 171, 458 y 406 records de
1.315) y LANCE las publica unas 3 h después; las corridas de las 07:10 y las 09:10 capturan esa ventana
apenas está disponible, y las pares siguen cubiertas por el cron de GitHub.

Si prefieres no crear un token, **B** es la alternativa honesta, sabiendo que no cubre las noches con el
PC apagado.

## 5. Lo que necesito de ti para hacerlo

- **Opción A**: crear tú el token fine-grained (yo no puedo crear ni pegar credenciales) y configurar
  el trabajo en el servicio, o decirme que te deje el paso a paso exacto. Antes de usarlo se agrega su
  fila a `REGISTRO_CREDENCIALES.md` §2 sin el valor, con qué se apaga si vence (la latencia vuelve a la
  del cron de GitHub; no se pierden datos).
- **Opción B**: tu confirmación para crear la tarea programada de Windows; es configuración persistente
  del sistema y la creo sólo con tu visto bueno.

Verificación después de activarlo: correr `scripts/medir_atraso_despacho_nrt.py` una semana después y
ver `workflow_dispatch` con ~12 corridas diarias y el healthcheck con el dato del Tier A a menos de 3 h.
