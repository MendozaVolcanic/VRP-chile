# Bloque de arranque S147

> Cierre de S146 (2026-09-20, 14:47 UTC según la hora del servidor). `main` en **`d00e2fdb9`** al
> momento de reunir la evidencia (el commit de este cierre va encima), verificado igual al remoto
> con `git ls-remote`. **Sin PR abiertos.** Cinco PR de la sesión, del #711 al #715, todos mergeados
> con CI en verde y con conclusión. Las ramas `s146-*` están integradas por squash: comprobado por
> contenido, no con `git cherry`, que miente con squash (A96). Suite sobre árbol quieto:
> **1599 passed, 4 skipped, 2 xfailed** (la base de S145 era 1568; los 31 nuevos vienen de los
> tests de `pc.classification`, del libro de pruebas y de los que agregaron los agentes; no los
> desglosé uno por uno).
> Sin cambios sin commitear salvo `experiments/_s140/`, que viene sin trackear desde S140. Disco:
> **19 GB libres de 476**.
>
> **No queda trabajo en vuelo.** Los 20 agentes de la sesión terminaron. No hay workflows propios
> corriendo: la batería del Apéndice A se CANCELÓ (ver el incidente en §a) y el A/B "sin Test 1" no
> se despachó.
>
> Sesión de tres tramos: auditar los cierres del proyecto, corregir los documentos y medir dónde
> vive la sobre-publicación, y cuatro auditorías más que terminaron encontrando la causa raíz.

## a. Todo en una pantalla

| qué | estado | evidencia |
|---|---|---|
| **Causa raíz de la sobre-publicación en VIIRS** | **encontrada y verificada con contexto limpio, gravedad 5** | El Test 1 integrado suma sólo los excesos positivos del disco de 3 km y los compara contra 3 sigma por raíz de N, que es la desviación de la suma SIN recortar. Con ruido puro la suma recortada vale 0,399 por N por sigma: sigma se cancela y el criterio depende del tamaño del disco, no del calor. Se cumple solo con N mayor que 56,6; el disco tiene 208 píxeles en VIIRS 375, 50 en 750 y 32 en MODIS. Tres caminos independientes: `docs/audit_s146/FRENTE_F_FIDELIDAD_VIIRS.md` (F-01), `FRENTE_G_INVENTARIO_DE_CAMINOS.md` (G-27), `FRENTE_G_VERIFICADOR.md`. Records reales sobre la curva del ruido: razón 1,056 |
| Cuánto explica | techo medido, piso SIN DATO | el Test 1 dispara en 83,3 % de los negativos limpios de VIIRS 375 (la sobre-publicación es 86,3 %). Fase 1 verificada: es el único sostén de 186 de 322 en VIIRS 375 y 89 de 133 en VIIRS 750; de 78 noches positivas ninguna se pierde con certeza, 4 SIN DATO. En MODIS no sostiene la brecha (manda el camino contextual, 28 de 38 en Puyehue Cordón Caulle) |
| **A/B "sin Test 1 integrado"** | **listo, NO despachado** | `experiments/_s146_ab_sin_test1/PREREGISTRO.md`, perfiles `pipeline/profiles/_s146_ab_*.yaml` (difieren de producción en un atributo cada uno, comprobado sobre los 143), workflow `reproc-s146-ab-sin-test1.yml` (sólo token), evaluador probado en local. 9 a 18 h de reloj |
| Auditoría de los cierres (5 frentes + verificador) | terminada | `docs/AUDIT_S146.md`. 17 afirmaciones verificadas, 0 refutadas, 13 con matiz. Hallazgo central: las rebajas no bajaban a los hijos |
| Fase 0: documentos rectores corregidos | terminada y verificada | PR #713. 42 marcas, 19 hallazgos del verificador, los 19 aplicados. Regla A113. D9 REABIERTA. D30 y D31 nuevas |
| La vara de medir (frente I) | auditada, **sin verificador** | sirve con salvedades: "78 de 78 noches" no discrimina (el azar da lo mismo); el 86,3 % cuenta apariciones y no energía (la mitad bajo 0,041 MW) |
| Caso A2 de la batería | vara corregida | mejor brazo 9 de 9, producción 5 de 9. Lo sostiene la figura del paper, no los nulos. Desbloquea D21, D22, D11; no autoriza adoptar nada |
| **Batería del Apéndice A en Actions** | ⚠️ **falló y se canceló** | run 35507516244: usó `EARTHDATA_USERNAME` y `EARTHDATA_PASSWORD`, que están VENCIDOS, y **bloqueó la cuenta de Earthdata 10 minutos** (A71). Corregido en #714 a sólo token. No se re-despachó. Quedó una rama `s146-bateria-salidas-35507516244` que NO inspeccioné |
| NRT después del bloqueo | **sano** | corrida de las 13:57 UTC en verde. El pendiente de S145 (primera corrida tras #709) también quedó verde a las 09:04 UTC |
| `pc.classification` | implementado, con provisoriedad; **el operador no lo ve** | `scripts/clasificacion_referencia.py`, `data/clasificacion_referencia/`. `sync-mirova-csv.yml` ahora baja el OCR: comprobado en producción, llega al 2026-09-20 06:00 |
| Libro de pruebas | terminado | `docs/LIBRO_DE_PRUEBAS.md`: 53 pruebas, 46 con instrumento, 3 perdidos. Dos guards |
| Espacio | decidido lo mío, pendiente lo tuyo | `docs/audit_s146/ESPACIO_Y_ARCHIVO_S146.md`. `.git` 6,81 GiB, GitHub 9,2 GB. A/B comprimidos 1.344 a 137 MB. Script de limpieza (2.877 MB) sin correr |
| Plan | escrito, con adenda | `docs/PLAN_PARIDAD_POST_AUDITORIA_S146.md` §0 manda sobre el resto |

## b. Decisiones que espera Nicolás

| # | pregunta | opciones | recomendación |
|---|---|---|---|
| 1 | **¿Despachar el A/B "sin Test 1 integrado"?** | ya / tras verificador / no | **tras un verificador con contexto limpio del pre-registro**, que es una sesión corta. Léelo tú primero: fija umbrales que deciden un cambio al sistema de alerta. Hazlo antes del 2026-10-03, que vence el token |
| 2 | **¿Implementar el Test 1 con el estadístico corregido**, detrás de un flag apagado? | sí con A45 / esperar al A/B | **sí, en paralelo al A/B**: es la salida elegante si "sin Test 1" pierde detección que se quiere conservar. Necesita tag defensivo y tu confirmación explícita |
| 3 | **Corregir la cita de la ficha publicable** (`pipeline/test1_integrated.py`, y "Gaua" en 24 perfiles) | ya con tag / con la decisión 2 | **junto con la 2**, un solo ciclo A45. Es un documento de la Resolución N°372 que cita un artículo de mecánica de rocas |
| 4 | **Re-despachar la batería del Apéndice A** | sí / no | **sí**: el NRT ya corrió verde después del bloqueo y el workflow autentica sólo por token. Mira antes qué dejó la rama `s146-bateria-salidas-35507516244` |
| 5 | **Correr la limpieza de disco** | sí / no | **sí**, la corres tú: `powershell -ExecutionPolicy Bypass -File "C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s146_espacio\limpieza_s146.ps1"`. Libera 2,9 GB; los A/B ya están comprimidos y verificados |
| 6 | **Reescribir la historia de git** (9,2 GB en GitHub, el doble que en agosto) | nivel A / A y B / no | **nivel A pronto**, con el NRT detenido, tag y clon espejo. Y abrir el cambio de formato del NRT, o habrá que repetirlo cada pocos meses |
| 7 | **Correo a Coppola** | enviar / esperar | **enviar**. Lleva la pregunta sobre el test integrado y el frente F dejó siete más. Es lo más barato de todo el plan |
| 8 | **Actualizar los secretos `EARTHDATA_USERNAME` y `EARTHDATA_PASSWORD`** o borrarlos | actualizar / borrar | **borrarlos** si el token basta: un secreto vencido es una trampa para el próximo workflow. Es credencial, lo haces tú. El token vence el **2026-10-03** |
| 9 | ¿Esta carpeta sincroniza con OneDrive? | | compruébalo: es el único respaldo de los papers (558 MB, ignorados por git) y del archivo comprimido |

## c. Lo aprendido

| lección | tipo | dónde vive |
|---|---|---|
| **Una rebaja que no baja a los hijos es un cierre vivo.** El proyecto sabía que varios cierres habían caído, y `MISSION.md` y los encabezados del catálogo seguían diciendo lo viejo | regla del proyecto | **A113** en `CLAUDE.md` |
| **Un estadístico recortado no se compara contra la desviación del estadístico sin recortar.** El defecto estuvo 120 sesiones a la vista y apareció cuando alguien derivó el nulo en vez de mirar umbrales | regla del proyecto | `docs/MIROVA_DIVERGENCES.md` D30; proponer como A114 |
| **Una métrica que el azar también cumple no decide nada.** "78 de 78 noches" se reprodujo cinco veces hoy con el mismo banco, y eso probaba que el banco es determinista, no que mida | **regla general del workspace** | `feedback_s146_metrica_sin_poder.md`; refuerza A110 |
| **Las credenciales de un workflow nuevo se copian del workflow que funciona, no de la documentación.** `CLAUDE.md` nombraba secretos vencidos, los usé, y bloqueé la cuenta de Earthdata | **regla general del workspace** | `feedback_s146_credenciales_del_workflow_vivo.md`; A71 reforzada |
| **Un guard que mira el sistema de archivos mide la máquina.** Dos veces hoy: rutas que existen sólo en este disco (rojo en CI), y `autocrlf` convirtiendo un golden a CRLF tras el checkout (rojo en local). Cura: declarar lo local en el guard y fijar `eol=lf` en `.gitattributes` | **regla general del workspace** | refuerza la lección S142; `.gitattributes` nuevo |
| **El proyecto pierde sus instrumentos, no sus conclusiones.** Artefactos de Actions caducan a 90 días, probes en scratchpad mueren con la sesión, y el A/B de S143 vivía sólo en el temporal de otra sesión | regla del proyecto | `docs/audit_s146/ESPACIO_Y_ARCHIVO_S146.md` §5; libro de pruebas y sus guards |
| **El verificador con contexto limpio encontró algo propio en todas las tandas**, y dos veces cometió el error A89 (filtrar por `test1` donde el código escribe `test1_roi`) y lo declaró | refuerzo de A89 y A93 | informes de verificador en `docs/audit_s146/` |
| **Usé `git reset --hard` dos veces** para alinear con el remoto. No había nada que perder, pero es la costumbre que un día pierde algo | regla general | usar `git pull --ff-only` o `git switch -C`; nunca `reset --hard` con agentes escribiendo |

## d. Problemas abiertos e hipótesis

| qué | etiqueta |
|---|---|
| El criterio del Test 1 integrado se cumple con ruido puro cuando el disco tiene más de 56,6 píxeles | **CONFIRMADO** (derivación, simulación con controles y records reales, tres caminos) |
| El Test 1 es el único sostén de 186 de 322 y 89 de 133 negativos limpios publicados | **CONFIRMADO** como inferencia desde lo persistido; **no es simulación** |
| Apagar el Test 1 baja la publicación de VIIRS 375 a entre 21 y 36 % sin perder noches | **SOSPECHA**: cota, no re-ejecución. Lo decide el A/B |
| El test de temperatura de brillo está apagado y no decide nada | **CONFIRMADO** (`ENABLE_BT_PATH_HOT = False`) |
| "78 de 78 noches" no discrimina; la pasada sí, en los dos VIIRS | **CONFIRMADO** por dos agentes independientes (frente I y el pre-registro); sin verificador formal |
| La mitad de la sobre-publicación está bajo 0,041 MW | **SOSPECHA** (frente I, sin verificador) |
| MIROVA publica la suma de todos los píxeles alertados, no el núcleo de un cúmulo (F-05, contradice A10) | **SOSPECHA** (frente F, sin verificador). Puede explicar parte del 0,7 de magnitud |
| El "+30 puntos de recall" con que se adoptó el Test 1 contaba su propio disparo como acierto (H-A01) | **SOSPECHA** (frente H, sin verificador) |
| El brazo `literal` de S143 pierde 0 noches de 308 y gana en 7 de 7 volcanes | **CONFIRMADO** como re-lectura exploratoria; **no cambia su veredicto** |
| `diario.html` grafica records que `index.html` oculta; el tope de Villarrica no llega al operador | **CONFIRMADO** (verificador de G) |
| El 482 de la regla A87 | **SIN VERIFICAR**: no se reproduce con ningún campo |
| La rama `s146-bateria-salidas-35507516244` contiene salidas útiles | **SIN MIRAR** |
| Las pasadas que MIROVA no lista no faltan al azar (SNPP 41 %, ninguna a las 04 UTC) | **SOSPECHA**, causa desconocida |

## e. Lo que ya está cerrado y no hay que rehacer

- **No re-auditar los 89 cierres originales**: están en `docs/AUDIT_S146.md` con veredicto. Lo pendiente son los 89 del censo ampliado.
- **No re-aplicar la Fase 0**: está en `main`, verificada. Quedan fuera sólo los archivos de `pipeline/` (decisión 3).
- **No correr un brazo "sin test de temperatura de brillo"**: sustrato cero.
- **No buscar un umbral k mejor para el Test 1**: la curva no tiene codo (P1).
- **No probar la regla de preferencia entre banda I y banda M**: cambia 0 pasadas (P6).
- **No re-medir la línea base de paridad**: se reprodujo exacta cinco veces. Lo que falta es medirla con una vara que tenga poder.
- **No volver a autenticar un workflow con usuario y clave de Earthdata.**
- **No re-comprimir los A/B**: 205 zips verificados en `experiments/_archivo_ab_local/`.
- **No usar "noches" como unidad de recall para decidir**: no discrimina.
- Sigue valiendo todo lo de S145 §e (D25 en V750 apagado, keep_peak cerrado, no usar `git cherry` con squash).

## f. Prompt para la próxima sesión

```
Retoma VRP Chile en S147. Trabaja en español de Chile (formas de tú, nunca voseo), sin guiones
largos ni medios, explicando como geólogo: fenómeno, mecanismo, números al final.

1. VERIFICA ANTES DE CREER:
   cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
   git fetch origin --prune && git pull --ff-only && git status -sb
   git rev-parse HEAD ; git ls-remote origin -h refs/heads/main     (deben coincidir)
   gh pr list --state open
   gh api -i repos/MendozaVolcanic/VRP-chile | grep -i date         (hora del servidor, A86)
   python -m pytest tests/ -q -p no:cacheprovider | tail -1          (base: 1599 passed)
   gh run list --workflow nrt.yml -L 5                               (¿sigue sano?)
   El token de Earthdata vence el 2026-10-03: mira cuántos días quedan.

2. LEE EN ORDEN: CLAUDE.md del proyecto · tasks/BLOQUE_ARRANQUE_S147.md ·
   docs/PLAN_PARIDAD_POST_AUDITORIA_S146.md (la sección 0 manda) · docs/AUDIT_S146.md ·
   docs/audit_s146/FRENTE_G_VERIFICADOR.md (la causa raíz) ·
   experiments/_s146_ab_sin_test1/PREREGISTRO.md · docs/LIBRO_DE_PRUEBAS.md ·
   docs/MIROVA_DIVERGENCES.md (D30 y D9 reabierta).

3. TRABAJO EN ORDEN (lo que Nicolás decida en la sección b manda):
   a) Verificador con contexto limpio del pre-registro del A/B "sin Test 1 integrado". Recibe
      sólo la ruta. Que ataque: los umbrales, el poder de cada métrica de recall, la paridad de
      cobertura, y que los perfiles difieran sólo en lo declarado. Antes de lanzar, lee entera
      ../../GUIA_MAESTRA_AUDITORIAS.md y ../../GUIA_PROMPTING_prompting-claude-fable-5-1.md.
   b) Si Nicolás aprueba: despachar el A/B (gh workflow run reproc-s146-ab-sin-test1.yml
      --ref main). Contar pasadas por brazo contra el control ANTES de mirar el veredicto.
   c) Con tag defensivo y confirmación explícita (A45): el Test 1 con el estadístico corregido
      detrás de un flag APAGADO, y en el mismo ciclo la cita de la ficha y de los perfiles.
   d) Re-despachar la batería del Apéndice A (probe-s146-bateria-apendice.yml); mirar antes la
      rama s146-bateria-salidas-35507516244.
   e) Pasar por verificador los frentes F, H e I, sobre todo F-05 (MIROVA suma todos los píxeles
      alertados) y H-A01, que siguen como hallazgo de auditor.
   f) Fase 6: pc.classification al dashboard, y que diario.html y mosaico.html usen el mismo
      predicado que index.html.

4. REGLAS DURAS: nada a pipeline/ ni a mirova_equivalent.yaml sin tag defensivo y confirmación
   explícita (A45); criterio escrito Y COMMITEADO antes de correr; verificador con contexto
   limpio antes y después; todo control lleva su nulo medido y toda tasa su tasa base; el recall
   que decide se mide por PASADA, no por noche; ninguna ventana cruza el 2026-08-28 23:00 UTC;
   ningún número transcrito a mano; una rebaja se propaga a los hijos en el mismo PR (A113);
   todo workflow autentica SÓLO por EARTHDATA_TOKEN; esperar el CI con conclusión antes de
   mergear; no correr la suite mientras hay agentes editando; nunca git reset --hard; agentes en
   paralelo sin git de escritura y con archivos disjuntos (el disco no da para worktrees);
   pre-acordar la escala de cada tanda de agentes; no hacer pull de mirova-tif-archive.

5. SI LA SESIÓN NO ALCANZA: deja cada frente con su cobertura declarada, rescata al repo
   cualquier salida que viva en el scratchpad, y cierra con /cierre.
```
