# Caminos por los que cada afirmación de F3 podría estar mal (escrito antes de abrir los archivos citados)

## 241 (plataforma que calla en CMR = cobertura completa, código 0)
- El simulador monkeypatchea search_granules en un punto que el pipeline real no usa (otro import, otro alias): mide un camino muerto.
- Existe un segundo camino que sí detecta el vacío: un vigilante aguas abajo (nrt-healthcheck, auto-audit, vigilar_plataformas en main) que abre issue cuando una plataforma lleva N horas sin records. Entonces el NRT sale verde pero la vigilancia sí lo vería (gravedad baja).
- search_granules ya distingue "CMR respondió vacío" de "CMR falló" (excepción, timeout) y sólo el primero es silencioso; el auditor pudo confundir los dos.
- La línea "Cobertura: completa" puede no existir en main d516b9d8c (estar sólo en una rama) o depender de otras incidencias.
- El escenario "Villarrica 2026-11-05" puede no reflejar la realidad (por ejemplo, el NRT procesa días recientes por ventana y otra lógica detecta ausencia).
- Que NOAA-21 pida sólo versión 2.1 puede ser correcto hoy; el riesgo depende de un cambio de versión hipotético.
- El dashboard puede mostrar "sin datos" por volcán/sensor (frescura), lo que haría visible el silencio.

## 242 (arreglo SNPP sólo en rama local sin push)
- La rama sí está en el remoto con otro nombre (s159-instrumentos, PR #889) y contiene el arreglo; "sin push" sería falso.
- La ventana 72 h, los archivos y líneas citados cambiaron desde que el auditor miró (otra sesión edita la rama).
- El arreglo sí cubre el mensaje "completa".

## 243 (MODIS 6.1 decomiso)
- La fecha de decomiso es inventada o mal leída; CMR no dice nada de decomiso.
- fetch.py ya pide colección 7 o tiene fallback a 6.1/7.
- store.py sí mide o marca la proporción NRT (product_version) y algún vigilante lo usa.
- "Colección 7 existe sólo en Standard" puede ser falso (existe NRT C7 o no existe C7 L1B).

## 245 (sync consolidado acepta encogimientos)
- Los "encogimientos" son commits legítimos (MIROVA borró filas, dedupe) y no pérdida.
- El conteo cuenta líneas de git log del archivo con otro criterio (merges, renombres) o archivos de otra ruta.
- El workflow sí valida tamaño en un paso que el auditor no vio, o el frontend no lee ese archivo.
- La ventana de 64 días no coincide con lo que dice.

## 244 (PR #889 NO COMPLETA saturado)
- El árbol 889 armado por el auditor no corresponde al commit d0968e389 o está desactualizado (la rama siguió avanzando).
- "dia_parcial" sólo ocurre en el simulador (día actual), no en todas las corridas reales.
- El modo estricto sí cuenta sin_granulos.

## 246 (sync corre 5,2/24 por día)
- Las corridas "desplazadas" son canceladas por otra razón; el conteo mezcla eventos (push, dispatch).
- El insumo (50 corridas) no cubre una ventana representativa; 5,2 por día sale de una ventana sesgada.
- Hueco máximo 22,7 h calculado sobre corridas "success" que no sincronizaron nada nuevo, o al revés.

## 247 (EARTHDATA_TOKEN)
- nrt.yml sí tiene guarda de token vacío en otro paso o fetch.py aborta sin login con par.
- Las fechas (vence 2026-12-07) mal leídas del insumo.
- El "8 logins, 1.300 s" es del simulador, no del código real (fetch.py sin par configurado no intenta login).
- "desconocido sin issue" puede abrir issue en otra rama del workflow.

## 248 (cron-job.org)
- Las 4,7 schedule/día cuentan sólo eventos schedule en una ventana donde el externo también disparaba (que cancela/desplaza los schedule por concurrency).
- medir_cadencia_cron sí sale != 0 o alerta por umbral.
- El PAT sí tiene vencimiento declarado.

## 252 (earthaccess sin pin)
- requirements.txt o nrt.yml sí fijan versión (lock, constraints).
- Hay un test que fija el envoltorio del 401.
- _is_credential_dead tiene camino alternativo que no depende de __cause__.

## Generales
- Copia local atrasada: los scripts del auditor corren contra D:\...\main, que debe ser d516b9d8c; si no lo es, todo cambia.
- La vara: "cobertura completa" se lee del stdout del run_pipeline; el operador ve el tablero, no el log.

---
sha256 del texto anterior: 96c298f73979831a9ef38e3aa2ce1bd27b0a19c80e5824197385240d7eb97dbf
hora del servidor: Date: Thu, 22 Oct 2026 03:42:30 GMT
