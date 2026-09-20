# Bloque de arranque S146

> Cierre de S145 (2026-09-20, hora del servidor). `main` en **`91ae0a594`**, verificado igual al
> remoto con `git ls-remote`. **Sin PR abiertos**; las tres ramas de la sesión
> (`s145-sustrato-y-plan-d25`, `s145-d25-v750`, `s145-paridad-y-objetivos`) están integradas,
> comprobado **por contenido** y no con `git cherry`, que miente con squash (A96). Suite al cerrar:
> **1568 passed, 4 skipped, 2 xfailed** (la base de S144 era 1551; los 17 nuevos son 12 del flag de
> M-band y 5 del sustrato). Sin cambios sin commitear salvo `experiments/_s140/`, que ya venía sin
> trackear desde S140. Disco: **9,8 GB libres de 476**.
>
> **Sin trabajo en vuelo.** El vigía que esperaba la primera corrida NRT posterior al merge de #709
> terminó: dio verde y con datos, así que ese pendiente quedó **resuelto dentro de esta misma
> sesión**. Ver la fila del NRT en §a.
>
> Sesión de tres tramos: ejecutar el plan de D25 en VIIRS 750, medir dónde está la paridad, y auditar
> cuatro frentes en paralelo. El tercero terminó dando vuelta la prioridad de los otros dos.

## a. Todo en una pantalla

| qué | estado | evidencia |
|---|---|---|
| **D25 (fondo por vecinos) en VIIRS 750** | **implementado y APAGADO** en producción | PR #709 (`d70199136`), tag `pre-s145-d25-v750`, A45 confirmado. `ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750 = False` |
| Su efecto, medido de punta a punta | fondo 0,204 → 0,105 W/m²/sr/µm, magnitud 0,705 → **2,291 MW** (factor 3,2) | `tests/test_d25_fondo_vecinos_v750_s145.py`, escena `nevado` del arnés de S142 |
| **Primera corrida NRT con ese cambio** | ✅ **VERDE Y PRODUCIENDO** (resuelto al cerrar) | run `35501310002`, 09:04 UTC, `success`; y commiteó datos de 6+ volcanes entre 09:24 y 09:43 UTC. No es un verde vacío (A64): produjo. **D25 en M-band queda verificado en producción** |
| **Paridad del régimen actual** | recall **78 de 78 noches**; brecha en sobre-publicación | `experiments/_s145_paridad/banco_s145.json`, `docs/audit_s145/PARIDAD_Y_OBJETIVOS_S145.md` |
| D13: la cerca del frontend | **subestimaba por más del doble**: apaga el **70,7 %** de la magnitud, no el 31 % | `docs/audit_s145/D13_CERCA_FRONTEND_REMEDIDA.md` |
| D26: "efecto nulo" | **deja de ser menor**: el sigma gobierna en 58,7 % de V375 y 75,0 % de V750 | `docs/audit_s145/DIVERGENCIAS_MENORES_VERIFICADAS.md` |
| D23, D24, D29 | siguen menores, ahora **medidas** y no estimadas | ídem. D24 con matiz: el píxel más caliente está a **0,6 K** de saturar la banda 22 |
| **El caso A2 de la batería** | el fallo es **del criterio, no del algoritmo** | `docs/audit_s145/A2_EL_FALLO_ES_DEL_CRITERIO.md` |
| `pc.classification` | la capacidad **existe** como `geo_class` y **no hace el trabajo** | `docs/audit_s145/CLASSIFICATION_SUSTRATO_Y_DISENO.md` |
| **Censo de cierres + plan de auditoría S146** | listo para ejecutar con Fable | `docs/PLAN_AUDITORIA_S146.md`, `experiments/_s145_censo_cierres/` |
| NRT | **sano**, 4 corridas verdes seguidas; último dato 04:11 UTC | los datos entran ~03, ~08 y ~14 UTC |
| Poller de TIF | produciendo | último commit 02:52 UTC, "27 new MIROVA snapshot(s)" |

### Los números de la paridad (ventana 2026-09-01 a 2026-09-20, 11 Tier A)

| sensor | recall por noche | publica en negativos limpios (pasada) |
|---|---|---|
| VIIRS 375 | 1,000 (75) | **0,863** (373) |
| VIIRS 750 | 0,929 (14) | 0,214 (622) |
| MODIS | 1,000 (n = 1, no legible) | 0,114 (438) |
| **cualquiera** | **1,000 (78)** | 0,352 (1433) |

**En una línea**: detectamos todo lo que MIROVA alerta, publicamos bastante más, y no tenemos cómo
decirle al operador cuál de las dos cosas mira.

## b. Decisiones que espera Nicolás

| # | pregunta | opciones | recomendación |
|---|---|---|---|
| 1 | **¿Correr el A/B de D25 en VIIRS 750?** El flag ya está | correr / dejarlo apagado | **no ahora**. El sustrato dice que no puede ganar recall (0 noches), el factor 3,2 medido dice que dispararía la sobre-publicación, y en VIIRS 375 el mismo fondo **ya se midió con criterio pre-registrado y no cerró la brecha** (H_S141_VECINO_FOCO_V2). Si se corre, con el criterio de §4 del plan y esperando NO ADOPTAR con hallazgo |
| 2 | **¿Ejecutar la auditoría S146 con Fable?** | sí / posponer | **sí**. A51 se disparó por su segunda vía: 4 contradicciones cross-source en una sesión. Alcance medido: 89 cierres, 50 sin respaldo. Escala pre-acordada: 5 auditores + 1 verificador |
| 3 | **El caso A2: ¿se corrige la vara de la batería?** | corregirla y re-correr / dejarla | **corregirla, pero escribiendo el criterio ANTES de correr**. Declarar A2 como caso de erupción de flanco y evaluarlo contra la fisura, no contra la cumbre. Desbloquea D21 y D22 juntas |
| 4 | **`pc.classification`: ¿se implementa?** | sí, como post-proceso / no | **sí, y no en el pipeline**. La recomendación medida es derivarlo del eje de referencia con 5 valores que `banco_paridad.etiquetar` ya calcula, por un job de post-proceso sobre ventana móvil, **sin ningún valor que diga "artefacto"** (toda regla candidata destruye lo confirmado por MIROVA) |
| 5 | **D13: ¿se toca la cerca del frontend?** | no por ahora | **no**: apaga el 70,7 % de la magnitud pero **0 de 411 pasadas que MIROVA confirmó** en el régimen actual. Antes de tocarla hay que decidir la #4, porque es la que da el lenguaje para mostrar lo que hoy se apaga |
| 6 | **Token de Earthdata: vence el 2026-10-03** | | renovarlo esta semana. Es credencial, lo haces tú. Quedan 13 días |
| 7 | **Correo a Coppola** | enviar / seguir esperando | **enviar**. Lleva desde S142 con tu "ajustar y enviar", y su pregunta 4 (fondo por vecinos y recorte a cero) es hoy la palanca de un frente vivo. `docs/audit_s139/BORRADOR_CORREO_COPPOLA.md` |

## c. Lo aprendido

| lección | tipo | dónde vive |
|---|---|---|
| **Un cierre hereda las premisas de la lectura con que se derivó, y eso es sistemático, no anecdótico.** Cuatro veces en una sesión: D26 midió un test y habló de dos; D13 midió records y tituló magnitud; S137 dijo que no había posiciones guardadas cuando sí las había; y el orquestador dijo que `pc.classification` no existe cuando existe como `geo_class` | **refuerzo de A95**, con censo | `docs/PLAN_AUDITORIA_S146.md` §1 |
| **Una cota escalar no identifica el objeto; el rumbo sí.** El caso A2 era indecidible con la distancia y se decidió con el acimut: los 4 cúmulos apuntan al E, lo que descarta la costa | refuerzo de **A107** | `docs/audit_s145/A2_EL_FALLO_ES_DEL_CRITERIO.md` |
| **El cero de un grep se lee como ausencia, y le pasa a quien audita.** Busqué `classification`, dio cero, concluí "no existe". La capacidad estaba en `geo_class` desde S88 | refuerzo de **A89**, con caso propio | este traspaso y el commit `d28b2d2f4` |
| **Una suite corriendo en segundo plano mientras editas no mide lo que dice medir.** La línea base de la Tarea 0 salió con 3 fallas fantasma; al re-correrla sin tocar nada, las 3 eran otras, justo las que el plan predecía | **regla general del workspace** | proponer como regla nueva junto a A50 |
| **El verificador con contexto limpio encontró 3 fallas graves que el autor no vio, y una se confirmó en la práctica el mismo día**: un import de una línea rompió dos citas de `CLAUDE.md`, un archivo que el cambio no edita | refuerzo de A93 | `docs/audit_s145/VERIFICADOR_PLAN_D25_V750.md` |
| **Un plan autorrevisado igual llega con errores al código que otro copiará.** Encontré 4 míos revisando el mío, y el verificador encontró 3 más | proyecto | mismo informe |

## d. Problemas abiertos e hipótesis

| qué | etiqueta |
|---|---|
| El recall por noche está resuelto: 78 de 78 en el régimen actual | **CONFIRMADO** (banco de paridad, controles en verde) |
| La brecha es sobre-publicación y está concentrada en VIIRS 375 (86,3 %) | **CONFIRMADO** |
| D25 en V750 no agrega ninguna noche de recall y expone 1035 pasadas | **CONFIRMADO** (sustrato, estable ante dos instantáneas de la referencia) |
| D13 apaga el 70,7 % de la magnitud, no el 31 % | **CONFIRMADO** |
| El sigma gobierna algún umbral en 58,7 % de V375 y 75,0 % de V750 (D26) | **CONFIRMADO** |
| El mejor brazo de la batería falla A2 por la caja de 5 km, no por el algoritmo | **CONFIRMADO** (8/9, 0 FP; 4 cúmulos a 7,4-10,9 km, rumbo E/ESE/ENE) |
| Que esa anomalía al este **sea** Fimmvörðuháls | **SOSPECHA fuerte**: el rumbo descarta la costa y la fecha coincide con la fisura activa, pero no se identificó el objeto |
| Bajo un criterio corregido ese brazo daría 9 de 9 | **SOSPECHA**: no se ha re-corrido con la vara corregida |
| Que adoptar ese brazo mejore la paridad con MIROVA | **SIN MEDIR**: lo medido es fidelidad al Apéndice A, que no dice nada de las 2285 pasadas del régimen actual |
| `geo_class` existe y no separa nada (5 `extension` en 62.880 records) | **CONFIRMADO** |
| Que las categorías b, c y d se puedan separar con lo persistido | **REFUTADO**: 621 de 1050 quedan mezcladas, y toda regla candidata destruye lo confirmado por MIROVA |
| El cambio de D25 no rompe el NRT en producción | **CONFIRMADO** al cerrar: run 35501310002 verde y con datos de 6+ volcanes |

## e. Lo que ya está cerrado y no hay que rehacer

- **El plan de D25 en V750 está ejecutado entero.** No re-implementar: el flag, los 3 sitios, los
  diagnósticos, los guards y el remapeo de citas están en `main`.
- **No re-medir el sustrato de D25 en V750**: se corrió dos veces con instantáneas distintas de la
  referencia de MIROVA y dio idéntico.
- **No re-medir la paridad del régimen actual** sin motivo: está en `banco_s145.json` con sus
  controles en verde.
- **No buscar un discriminante físico per-record** para separar cat-b de artefacto: A83 lo declaró
  agotado y el sustrato de `pc.classification` lo volvió a confirmar (toda regla candidata destruye
  lo confirmado por MIROVA; la de A80 marca 397 de 414).
- **No reabrir el frente `keep_peak` con dirección**: cerrado en S144 con siete rondas de
  verificación. `docs/CIERRE_FRENTE_KEEP_PEAK_S144.md` §4 lista los cuatro controles refutados.
- **No tocar MODIS en D25**: su sustrato son 11 pasadas de rescate con 0 alertas de MIROVA.
- **No usar `git cherry`** para decidir si una rama está integrada: miente con squash (A96).

## f. Prompt para la próxima sesión

```
Retoma VRP Chile en S146. Trabaja en español de Chile (formas de tú, nunca voseo), sin guiones
largos ni medios, explicando como geólogo: fenómeno, mecanismo, números al final.

1. VERIFICA ANTES DE CREER:
   cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
   git fetch origin --prune && git pull --ff-only && git status -sb
   git rev-parse HEAD ; git ls-remote origin -h refs/heads/main    (deben coincidir; base 91ae0a594)
   gh pr list --state open
   gh api -i repos/MendozaVolcanic/VRP-chile | grep -i date         (hora del servidor, A86)
   python -m pytest tests/ -q -p no:cacheprovider | tail -1          (base: 1568 passed)
   NRT: gh run list --workflow nrt.yml -L 5
   (S145 dejó esto RESUELTO al cerrar: el run 35501310002 de las 09:04 UTC quedó verde y
   commiteó datos de 6+ volcanes, así que D25 en M-band ya corrió en produccion sin romper nada.
   Si aun asi ves algo raro en M-band, el tag para revertir es pre-s145-d25-v750.)

2. LEE EN ORDEN: CLAUDE.md del proyecto · tasks/BLOQUE_ARRANQUE_S146.md ·
   docs/PLAN_AUDITORIA_S146.md · docs/audit_s145/PARIDAD_Y_OBJETIVOS_S145.md ·
   docs/audit_s145/A2_EL_FALLO_ES_DEL_CRITERIO.md · docs/MIROVA_DIVERGENCES.md (catálogo vivo).

3. TRABAJO EN ORDEN (lo que Nicolás decida en §b manda):
   a) AUDITORÍA S146 con Fable, si la aprueba (decisión 2). El plan está escrito y su alcance
      medido: 89 cierres, 50 sin respaldo. ANTES de lanzar auditores, leer entera
      ../../GUIA_MAESTRA_AUDITORIAS.md y ../../GUIA_PROMPTING_prompting-claude-fable-5-1.md.
      Escala pre-acordada: 5 auditores + 1 verificador. No agrandarla.
   b) Si la auditoría no se hace: el caso A2 (decisión 3) es el de mayor palanca, porque
      desbloquea D21 y D22 juntas. El criterio corregido se escribe ANTES de correr nada.
   c) pc.classification (decisión 4): post-proceso, no pipeline, sin valor "artefacto".

4. REGLAS DURAS: nada a pipeline/ ni a mirova_equivalent.yaml sin tag defensivo y confirmación
   explícita (A45); criterio escrito antes de correr y verificador con contexto limpio antes y
   después; todo control lleva su nulo medido (A110); ningún número transcrito a mano (S91);
   esperar el CI con conclusión antes de mergear ("0 checks" es SIN DATO, no verde); correr la
   suite tras editar docs que un test lee; NO correr la suite en segundo plano mientras editas
   (S145: da fallas fantasma); no hacer pull de mirova-tif-archive (17 GB); para ediciones con
   secuencias de escape usar el editor, no heredocs.

5. SI LA SESIÓN NO ALCANZA: deja la auditoría con su cobertura declarada aunque esté incompleta
   (un informe que cubre poco y lo dice vale; uno que no lo dice, no), y cierra con /cierre.
```
