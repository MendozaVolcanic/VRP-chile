# Qué se guarda, dónde, y qué se bota (S146)

> Decisión pedida por Nicolás el 2026-09-20: no perder lo que sirve, no gastar espacio en lo que
> no, y recordar que GitHub tampoco es infinito. Los números salen de
> `experiments/_s146_espacio/` (`inventario_ignorados.json`, `manifiesto_zip.json`, `resumen.json`).

## 1. Lo primero: el problema de espacio no son los 3 GB de artefactos

Lo medí antes de decidir. El gasto grande está en otra parte:

| qué | tamaño | tendencia |
|---|---|---|
| Historia de git en este disco (`.git`, `size-pack`) | **6,81 GiB** | en S121 (agosto) eran 3,0 GB: se duplicó en seis semanas |
| Repositorio en GitHub | **9,2 GB** | público, sin tope duro, pero GitHub recomienda quedarse bajo 5 GB y puede pedir reducirlo |
| Artefactos que git ignora, sólo en este disco | 3,9 GB | estable |

El motor es el mismo que S121 ya diagnosticó (`docs/S121_GIT_FILTER_REPO_DESIGN.md`): el cron NRT
commitea los JSON de cada volcán (13 a 17 MB) cada 2 horas, unos 1.800 commits por mes, y cada
versión queda entera en la historia. Eso es lo que hay que resolver, y **no lo toqué**, porque la
única cura real reescribe la historia y hace force-push: es destructivo y la decisión es tuya
(§4, decisión 1).

## 2. La regla que apliqué

Tres preguntas por carpeta, en este orden:

1. **¿Se puede volver a obtener desde una fuente que seguirá existiendo?** (otro repo, el remoto,
   `pip`, un script). Si sí: se bota.
2. **Si no, ¿permite contestar una pregunta que todavía importa sin volver a bajar gránulos de la
   NASA?** Las salidas crudas de los A/B sí: hoy mismo la auditoría mostró que varios veredictos se
   midieron en records y no en noches, o sin negativos limpios. Con el crudo guardado eso se
   re-mide en minutos; sin él hay que re-procesar semanas de satélite. Se guarda, **comprimido**.
3. **¿Dónde?** En GitHub sólo lo chico y decisivo (el resumen que sostiene un veredicto). Lo pesado
   queda comprimido en este disco, que vive dentro de OneDrive (verifica que esta carpeta esté
   sincronizando: es la única copia fuera del computador).

## 3. Lo que decidí, por clase

| clase | MB | decisión | por qué |
|---|---|---|---|
| Artefactos de A/B y reprocesos (`_art`, `_ab`, `_promo_art`, `data/_*`, y `data/mirova_equivalent_pre_s27/`) | 1.344 | **comprimidos a 137 MB** en `experiments/_archivo_ab_local/` (205 zips, los 205 verificados con `testzip` y conteo de archivos). Los originales se pueden botar | los artefactos de GitHub Actions caducan a los 90 días: estos son la única copia. `pre_s27` iba a botarse por "está en la historia", pero su md5 **no coincide** con el tag `pre-s27-baseline`, así que se archiva en vez de confiar |
| Descargas (`_dl_*`, TIF de MIROVA, PNG) | 985 | **botar** | salen de `mirova-tif-archive` o de `git show`; los scripts que las bajan están en el repo |
| `_staging` de reprocesos | 408 | **botar** | paso intermedio de algo ya promovido a `data/` |
| Caches de hoy (`v_cache.json`, `d_cache.json`) | 142 | **botar** | se regeneran en un minuto |
| Papers (`documentacion/*.pdf`) | 558 | **conservar en el disco, nunca a GitHub** | son la fuente de verdad bibliográfica y tienen copyright: el repo es público. Respaldo: OneDrive y Zotero |
| Referencia OSF (`VRP_GLOBAL_ARCHIVE_2025.csv`) | 99 | conservar en el disco | es pública y se puede volver a bajar, pero se usó hoy y pesa poco |
| `.venv` | 298 | conservar | botarlo obliga a reinstalar; no vale el ahorro |
| Archivos chicos y decisivos que git ignoraba (resúmenes `*_ab_audit.json`, `*_result.json`, salidas de S98, S104, S110, S111, S112, S131, S138, S139) | 3,6 | **suben a GitHub** en este PR | son el respaldo numérico de veredictos del catálogo; hoy aparecieron cuatro cifras sin instrumento. Quedan fuera los `.txt` de papers extraídos (copyright) |

Total que libera la limpieza: **2.877 MB**, contra 137 MB de archivo comprimido.

**La limpieza no la ejecuto yo**: borrar archivos de forma permanente es una acción que dejo en tus
manos. El script ya está escrito, lista cada ruta, se salta cualquier cosa que git tenga
trackeada, y sólo toca lo de la tabla:

```
powershell -ExecutionPolicy Bypass -File "C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s146_espacio\limpieza_s146.ps1"
```

## 4. Decisiones que quedan para ti

| # | pregunta | recomendación |
|---|---|---|
| 1 | **Reescribir la historia de git** (plan de S121, niveles A y B) para bajar de 9,2 GB | **sí, y pronto**: a este ritmo el repo pasa los 15 GB antes de fin de año. Nivel A primero (purga los A/B ya removidos, riesgo bajo). Necesita una ventana con el cron NRT detenido, tag de respaldo y un clon espejo guardado antes. Lo preparo cuando digas; no lo hago sin tu orden |
| 2 | **Que el NRT deje de engordar la historia**: hoy cada corrida reescribe el JSON completo de cada volcán | cambiar el formato para que cada corrida **agregue** (un archivo por mes, o JSON por líneas) en vez de reescribir 15 MB. Es cambio en `pipeline/store.py` y en el frontend: ciclo A45, con plan propio. Sin esto, la decisión 1 hay que repetirla cada pocos meses |
| 3 | Mientras tanto, compactar la copia local | `git gc` en este disco es seguro y no toca la historia, pero necesita unos 7 GB libres mientras corre y hoy hay 11. Hazlo después de la limpieza |
| 4 | ¿Está esta carpeta sincronizando con OneDrive? | compruébalo tú: es el único respaldo de los papers y del archivo comprimido |

## 5. Para que no vuelva a pasar

Van a la Fase 7 del plan de paridad, como reglas con guard y no como buenas intenciones:

- **Todo run de Actions que mide algo deja sus salidas en una rama propia**, no sólo como artefacto
  con caducidad. La batería de hoy ya lo hace.
- **El resumen decisivo de un A/B se commitea**; el crudo se comprime al archivo local el mismo día.
- **Ningún probe se queda en el scratchpad al cierre.**
- **Un documento de resultados no puede citar una ruta que no existe**: hoy son 29 de 323. Guard
  pendiente.
- **Un registro único de lo probado** (pregunta, script, ventana, configuración, veredicto, si el
  instrumento existe). Se arma fundiendo `hipotesis.json` (frente H), `inventario.json` (frente G) y
  `grafo.json` (frente E).
