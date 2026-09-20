# Plan para alcanzar la paridad con MIROVA, después de la auditoría S146

> Escrito el 2026-09-20 sobre los hallazgos **verificados** de `docs/AUDIT_S146.md`. Todo lo que
> este plan da por hecho pasó por un verificador con contexto limpio, o está marcado como hallazgo
> del auditor sin verificar. Ningún paso de este plan toca `pipeline/`, el perfil ni el frontend sin
> el ciclo A45 (tag defensivo y confirmación explícita de Nicolás). Los números vienen de los
> informes de `docs/audit_s146/`, que son la fuente (S91).

## 0. Adenda del mismo día: lo que cambió después de escribir este plan

> Las fases 0 y 1, el paso 1 de la Fase 2 y el paso 1 de la Fase 6 **ya se ejecutaron** (PR #712,
> #713, #714), y cuatro auditorías más (frentes F, G, H, I) con sus verificadores cambiaron el
> cuadro. Esta adenda manda sobre lo que sigue cuando se contradigan. Fuentes:
> `docs/audit_s146/FRENTE_F_FIDELIDAD_VIIRS.md`, `FRENTE_G_INVENTARIO_DE_CAMINOS.md` y su
> `FRENTE_G_VERIFICADOR.md`, `FRENTE_H_HIPOTESIS_Y_AB.md`, `FRENTE_I_LA_VARA_DE_MEDIR.md`,
> `FASE1_SUSTRATO_SOBREPUBLICACION.md` y su `FASE1_VERIFICADOR.md`, `MEDICIONES_P1_P2_P6.md`.

**La hipótesis de trabajo dejó de ser hipótesis en VIIRS, y ahora tiene mecanismo.** El Test 1
integrado suma sólo los excesos positivos de los píxeles del disco de 3 km y compara esa suma
contra 3 sigmas por la raíz del número de píxeles. Al recortar los negativos, la suma del ruido
puro deja de tener media cero (vale 0,399 por N por sigma), y la vara es la desviación de la suma
SIN recortar: se compara la media de una variable contra la desviación de otra. Sigma se cancela y
el criterio pasa a depender del tamaño del disco, no del calor: se cumple solo con más de 56,6
píxeles. El disco tiene 208 en VIIRS 375, 50 en VIIRS 750 y 32 en MODIS. Verificado con contexto
limpio, gravedad 5, por tres caminos independientes; los records reales caen sobre la curva del
ruido (razón 1,056 en VIIRS 375). Techo de lo que explica: el Test 1 dispara en 83,3 % de los
negativos limpios de VIIRS 375. El piso sigue SIN DATO y lo decide el A/B. En MODIS no sostiene la
brecha: ahí manda el camino contextual del paper, concentrado en Puyehue Cordón Caulle.

**La vara tiene dos salvedades que cambian cómo se decide** (frente I, sin verificador todavía):
"78 de 78 noches" no discrimina (barajando al azar da lo mismo: publicamos algo en 218 de 219
noches), así que **el recall que decide se mide por pasada del sensor que alertó**, con su nulo
medido antes de fijar umbral; y el 86,3 % cuenta apariciones y no energía (la mitad de lo publicado
en negativos está bajo 0,041 MW), así que la sobre-publicación se reporta también por estrato de
magnitud, sin convertir eso en un piso.

**Qué se cae del plan:** el brazo "sin test de temperatura de brillo" (está apagado, sustrato
cero); la regla de preferencia entre banda I y banda M (P6: no cambia ninguna pasada); y buscar un
umbral k mejor para el Test 1 (P1: la curva no tiene codo, negativos y positivos se traslapan).

**Qué entra, en este orden:**

| # | qué | estado | necesita |
|---|---|---|---|
| 1 | **A/B "sin Test 1 integrado"**: pre-registro, 3 perfiles aislados, workflow por token y evaluador probado en local, en `experiments/_s146_ab_sin_test1/` | **listo para despachar, NO despachado** | que Nicolás lea `PREREGISTRO.md`; 9 a 18 h de reloj en Actions; el token vence el 2026-10-03 |
| 2 | **Verificador con contexto limpio del pre-registro** antes de despachar | pendiente | una sesión corta |
| 3 | **Test 1 integrado con el estadístico corregido** (no recortar, o restar la media nula y dividir por la desviación del estadístico recortado), detrás de un flag apagado | descrito, no implementado | ciclo A45: tag y confirmación explícita. Es el brazo que sigue si "sin Test 1" pierde detección que se quiere conservar |
| 4 | **Re-despachar la batería del Apéndice A** (la primera corrida falló por credenciales: ver abajo) | workflow corregido a sólo token, en `main` | ver una corrida NRT verde después del bloqueo |
| 5 | **Brazo `literal` de S143**: en la re-lectura por volcán pierde 0 noches de 308 y baja la publicación en negativos de 91,7 a 54,7 %, ganando en 7 de 7 volcanes | exploratorio: NO cambia su veredicto | entra como brazo al A/B siguiente, con criterio nuevo escrito antes |
| 6 | **F-05: MIROVA publica la SUMA de todos los píxeles alertados de la pasada**, nosotros el núcleo de un cúmulo (contradice la premisa de A10) | hallazgo de auditor, sin verificador | verificarlo contra la página del paper y medir su efecto en la razón de magnitud: puede ser la mitad de la Fase 4 |
| 7 | **El dashboard no dice lo mismo en sus tres vistas**: `diario.html` no tiene `isValidDetection` y grafica lo que `index.html` oculta; el tope de Villarrica no llega al operador | verificado | entra a la Fase 6, junto con mostrar `pc.classification` |
| 8 | **14 mecanismos nuestros sin declarar en el catálogo** (frente G) y **30 pruebas que valen sólo bajo su configuración** (frente H) | listados | abrir sus divergencias; el libro de pruebas (`docs/LIBRO_DE_PRUEBAS.md`) ya los registra |
| 9 | **Espacio**: la historia de git pesa 9,2 GB en GitHub y se duplicó en seis semanas | decisión del dueño | `docs/audit_s146/ESPACIO_Y_ARCHIVO_S146.md` |

**Incidente que deja regla.** La batería del Apéndice A usó `EARTHDATA_USERNAME` y
`EARTHDATA_PASSWORD`, que están vencidos, y bloqueó la cuenta de Earthdata 10 minutos (A71). El NRT
autentica por `EARTHDATA_TOKEN`. Todo workflow nuevo autentica sólo por token y falla al instante si
viene vacío. La sección "Constraints técnicos" de `CLAUDE.md` todavía nombra los secretos viejos.

## 1. El objetivo, y dónde estamos parados

**Objetivo**: que VRP Chile reproduzca lo que MIROVA publica, de forma que SERNAGEOMIN pueda
depender de él sin mirovaweb.it y que un tercero nos crea. Lo que vemos de más (calor real que
MIROVA no publica) es valor agregado, pero va separado y con nombre propio, nunca mezclado con la
alerta (regla S143: primero igualar, lo demás al experimental).

**Dónde estamos** (S145, régimen actual, 11 Tier A, 2026-09-01 a 2026-09-20):

| | estado |
|---|---|
| Recall por noche | **78 de 78**: detectamos todo lo que MIROVA alerta. Resuelto |
| Sobre-publicación | **la brecha**. En negativos limpios publicamos en 86,3 % de las pasadas VIIRS 375, 21,4 % de VIIRS 750 y 11,4 % de MODIS |
| Magnitud | cerca de 0,7 contra MIROVA, con causa atribuida a conteo de píxeles y fondo (A99), atribución que esta auditoría dejó matizada (V-12) |
| Lenguaje para el operador | no existe: no puede distinguir "MIROVA también lo ve" de "sólo nosotros". `pc.classification` ya está calculado, falta mostrarlo |

**Lo que la auditoría cambia de ese cuadro.** Tres de los mecanismos que más detectan en producción
**no están en el paper de MIROVA**, y dos de ellos pasaron la puerta de la misión con una cita que
no los sostiene:

1. El **Test 1 integrado en el ROI** (V-06, gravedad 5): dispara en 77,89 % de los records VIIRS 375
   (dato del auditor C, línea 127 de su informe, sin pasar por el verificador). En el paper el
   Test 1 es por píxel. La cita con que se justificó corresponde a un artículo de mecánica de rocas.
2. El **test de temperatura de brillo con N·σ = 5 / 10** (V-08): el paper no tiene ningún test de
   temperatura de brillo; los números son los de C2, que en la Tabla 1 multiplican otra variable.
3. La **compuerta `bt > t_bg + 3 K`** y la **banda 21 como primaria** (D22 y D21, ya conocidas),
   que estaban bloqueadas por el criterio de la batería y hoy quedaron desbloqueadas (V-16).

La hipótesis de trabajo que ordena este plan es entonces simple y **todavía no está medida**: *la
sobre-publicación vive en los caminos que MIROVA no tiene*. Si es cierta, acercarse al paper reduce
la brecha. Si es falsa, lo sabremos en la Fase 1, antes de tocar nada. No se da por cierta.

## 2. Reglas del plan (salen de lo que falló)

- **Sustrato antes que A/B** (S130): antes de correr cualquier brazo se mide, sobre los records ya
  persistidos, si el mecanismo llega a decidir algo. Cuesta minutos y ya evitó A/B de horas.
- **Criterio escrito y commiteado antes de correr**, en las unidades del operador: **noche** para
  el recall y **pasada con negativo limpio** para la sobre-publicación. Commiteado, no sólo con
  hash: V-16 mostró que un sello sin historia de git no prueba el orden.
- **Todo control lleva su nulo medido** (A110), y toda tasa su **tasa base** (V-02).
- **Estratificar por volcán y por sensor** antes de creer un agregado (V-03 y V-12 fueron paradoja
  de Simpson).
- **Ninguna ventana cruza el 2026-08-28 23:00 UTC** (#535, A104).
- **"MIROVA publicó" no es "real" y "MIROVA calló" no es "artefacto"** (A54). Las etiquetas del banco
  de paridad dicen qué hizo la referencia y nada más.
- **El que verifica no es el que encontró**, antes y después de cada fase.
- **Una rebaja se propaga a los hijos en el mismo PR** (hallazgo central de S146).
- Escala de agentes pre-acordada por fase. Disco con 9 GB libres: nada de reprocesos locales largos
  ni worktrees sin liberar espacio primero.

## 3. Las fases

Ordenadas por cuánto acercan al objetivo por unidad de riesgo. Las fases 0 y 1 no tocan el
pipeline y se pueden hacer ya.

### Fase 0. Que los documentos digan lo que el proyecto ya sabe (sólo documentos, un PR)

**Por qué primero**: `docs/MISSION.md` es la puerta que se lee antes de tocar el pipeline, y hoy
manda no reabrir cosas que el propio proyecto reabrió. Cada sesión que parte de ahí hereda el
error. Es barato, no tiene riesgo operacional y es condición para que las fases siguientes pasen
la puerta de la misión con la lectura correcta.

| qué | dónde | fuente |
|---|---|---|
| Lista de "Resueltas" y frases "irreducible, agotado, GAP #A no reabrir" | `docs/MISSION.md:99-112` | V-13, E-06 |
| Bajar la rebaja de A82 a sus hijas | A83, A84, D13, NEW-8/S116, A85, D18, una frase de D19, nota de D12, `AUDIT_S122_C2_PASO0.md` | E-01, A-11 |
| Nota "el código ya es fiel" sin marca | `docs/MIROVA_DIVERGENCES.md:455` | A-08, C-08, E |
| Encabezados que contradicen su propio cuerpo | D8 (puntero a D25), D16 (título y "NO REABRIR"), D26 ("efecto nulo"), D-PCC (inner = 7 revertido) | A-07, V-04, E-04, V-13 |
| NEW-8 como gap abierto cuando corre desde S72 | catálogo 435 y 478, `MISSION.md:112` | V-05 |
| D9: "207 de 214 confirmados, sin acciones abiertas" | catálogo 515 y 534, `MISSION.md`, `CLAUDE.md` (A23, puntero de Estado) | V-01 |
| D12: "76 noches de FN recuperadas (reales)" | catálogo y `AUDIT_S121_D12_AB.md` | V-09 |
| A82 y D11: "encuentra el cráter el 90 %" sin tasa base | `CLAUDE.md` A82 | V-02 |
| A83: número, etiqueta y alcance ("agotado" vale sólo contra la etiqueta de MIROVA) | `CLAUDE.md` A83 | V-03 |
| A99: el 0,995 compensa entre factores y entre volcanes | `CLAUDE.md` A99 | V-12 |
| "serie continua desde 2025-02" | `CLAUDE.md`, sección Arquitectura | V-15 |
| Citas de paper corruptas o que no sostienen (Gaua, tope de 5 MW, A76, D3) **en documentos** | catálogo 259, 265, 287 y otros | V-07, C-02, C-05, C-06 |
| Abrir **D30: el Test 1 integrado es un detector propio** y **D31: el test de temperatura de brillo no está en el paper**, con su cita verbatim de la p. 6 y la Tabla 1 | catálogo | V-06, V-08 |
| Control del censo que no puede fallar | `experiments/_s145_censo_cierres/censo.py:113` | V-14 |

Criterio de salida: `grep` de cada frase vieja da 0 fuera de los bloques marcados como históricos;
suite completa verde sobre árbol quieto (hay tests que leen estos documentos); un verificador con
contexto limpio recibe sólo la lista de archivos y busca rebajas que no bajaron.

**Queda fuera de la Fase 0**, porque son archivos protegidos por A45 aunque el cambio sea un
comentario: la cita "Gaua" en `pipeline/profiles/mirova_equivalent.yaml:482` y seis perfiles más, y
la cabecera FICHA de `pipeline/test1_integrated.py`. Van en la Fase 2, con tag.

### Fase 1. Medir dónde vive la sobre-publicación (sólo lectura, sin tocar nada)

**Por qué**: es la pregunta que decide todo lo demás y nadie la ha hecho con esta forma. S139
estableció que la brecha es sobre-publicación; S146 estableció que hay caminos de detección que no
son de MIROVA. Falta cruzarlos.

**Qué se mide**, sobre el banco de paridad de S145 (2.285 pasadas del régimen actual, con sus
negativos limpios) y con los diagnósticos ya persistidos en cada record (`triggered_test1`,
`diag_n_dnti_ctx_path` y los contadores de los otros caminos, `diag_sigma_bg_k`, `t_bg_k`):

1. Para cada pasada que publicamos en un negativo limpio: **qué camino la sostiene**. Atribución
   por simulación de la etapa siguiente, no por conteo (A97, S138): una pasada "depende" de un
   camino si al quitar los píxeles de ese camino deja de publicarse con el predicado literal del
   dashboard, ejecutado con node.
2. Lo mismo para las pasadas que MIROVA sí confirmó: **qué camino sostiene el recall**. Es la otra
   mitad de la cuenta: un camino que explica 60 % de la sobre-publicación y 50 % del recall no se
   puede apagar.
3. Estratificado por volcán y sensor, con el nulo medido (misma atribución sobre etiquetas
   barajadas dentro de cada volcán).

**Salida**: una tabla camino por sensor con dos columnas, "pasadas de sobre-publicación que
dependen sólo de este camino" y "noches de recall que dependen sólo de este camino". Esa tabla
ordena la Fase 2. Si el sustrato dice que los caminos no literales no explican la brecha, la
hipótesis de trabajo cae y el plan se reordena hacia la Fase 4 (geometría y fondo).

**Límite conocido**: los records guardan contadores por camino, no la máscara por píxel. Si la
atribución por simulación no se puede hacer desde lo persistido, se declara SIN DATO y se pide un
probe de sólo lectura en GitHub Actions con el patrón de A75 (monkeypatch por etapa), que ya está
probado.

Escala: 1 agente que mide y 1 verificador. Una sesión.

### Fase 2. El brazo fiel al paper, medido contra la paridad y no sólo contra el Apéndice A

**Por qué**: la batería del Apéndice A dice que el brazo "banda 22, sin compuerta de temperatura,
fondo local, conectiva `max`" da 9 de 9 y producción 5 de 9. Eso es fidelidad en nueve escenas
MODIS. No dice nada de las 2.285 pasadas de hoy. Hay que medirlo donde está la brecha.

**Pasos**, en orden y cada uno con salida propia:

1. **Terminar la batería** (GitHub Actions, MODIS no corre en Windows): los 3 brazos que quedaron
   INDECIDIBLES en A2 por no guardar posición; el brazo "banda 22 con fondo local y con compuerta"
   que nadie corrió; y el nulo por píxel alertado, que es el único con poder (V-16 mostró que N1 y
   N2 están vacíos por construcción). Los comandos exactos están en
   `docs/audit_s146/A2_RESULTADO_VARA_CORREGIDA.md`. Commitear el pre-registro de A2 tal como está,
   con su hash, para que tenga historia.
2. **Escribir y commitear el criterio del A/B de paridad**. Propuesta para discutir, no para
   adoptar sin revisión: ADOPTAR sólo si (a) el recall por noche no pierde ninguna de las noches
   que hoy se detectan, salvo las que la Fase 1 haya mostrado que dependen de un camino no literal
   y que MIROVA publicó con menos de 0,5 MW (FN sub-píxel aceptables según la prioridad de
   `mirova_equivalent`), listadas una por una; (b) la fracción de negativos limpios publicados baja
   en VIIRS 375 por debajo de un umbral fijado antes de correr; (c) la razón de magnitud
   estratificada por volcán no se aleja de 1 en ningún volcán con n suficiente. Todo por tramo, sin
   cruzar #535.
3. **A/B por componentes, no en bloque**: el patrón validado es de perfiles aislados con
   `data_subdir` propio (plantillas en `.github/workflows/_archive/`). Brazos: control; sin Test 1
   integrado (Test 1 por píxel literal); sin test de temperatura de brillo; banda 22 primaria más
   sin compuerta (D21 y D22 juntas, que S137 mostró que interactúan); todo junto. El orden y el
   número de brazos los fija la tabla de la Fase 1: no se corre un brazo cuyo sustrato sea cero.
4. **Verificador antes y después**, y contar las pasadas de cada brazo contra el control antes de
   mirar el veredicto (A108: un run verde no prueba cobertura pareja).
5. Si algún brazo cumple: ciclo A45 completo (tag, TDD, flip, reproc en Actions por volcán y en
   serie, promoción, verificación en el dashboard). En el mismo cambio se corrigen la cabecera FICHA
   de `pipeline/test1_integrated.py`, la cita "Gaua" de los perfiles y
   `docs/FICHA_SDA_VRP_CHILE.md`, que es publicable por la Resolución CPLT N°372 y hoy cita un
   artículo que no es.

**El riesgo que hay que nombrar**: el Test 1 integrado se adoptó en S27 porque subió el recall de
50 a 80 %. Apagarlo puede costar noches reales de señal sub-píxel (el lago de lava de Villarrica es
el caso de manual). Por eso el criterio va en noches, lista las noches perdidas una por una, y por
eso existe la alternativa de la Fase 2b.

⚠️ **El riesgo se RE-DIMENSIONÓ en S147 y es bastante menor de lo que este párrafo dice**
(`docs/audit_s147/VERIFICADOR_H_A01.md`, verificador con contexto limpio): (a) el "50 a 80 %" **no
tiene ningún script** y queda SIN EVIDENCIA; (b) el único A/B limpio del Test 1 encendido contra
apagado dio **6 contra 6**, ganancia cero; (c) la adopción se midió **sin un solo negativo limpio**
habiendo 11.680 en el mismo archivo, así que era una métrica que por construcción sólo podía subir;
(d) el camino contextual contra el que se comparó fue reemplazado 15 días después y **nadie volvió
a medir** el aporte del Test 1 desde entonces. Y una cota propia sobre lo persistido
(`experiments/_s147/cota_por_pasada_con_etiquetas.py`, ventana 2026-08-29 a 2026-09-20) no
encuentra **ninguna pasada positiva** sostenida sólo por el Test 1 en VIIRS 375 (0 de 133) ni en
VIIRS 750 (0 de 9). Sigue siendo una cota, no una re-ejecución: lo decide el A/B. **La unidad de
recall, además, es la PASADA, no la noche** (la noche no discrimina, A94 y frente I).

**Fase 2b, si el brazo fiel pierde recall que no se quiere perder**: los caminos propios no se
borran, **se mudan**. El perfil `mirova_equivalent` queda literal y lo que vemos de más pasa al
perfil `experimental` con `pc.classification` como lenguaje. Es la regla S143 aplicada: primero
igualar, lo demás separado y con nombre. Esta es una decisión de Nicolás, no técnica.

### Fase 3. D9 reabierta: el camino contextual sobre fondo frío

**Por qué**: el argumento que descartó para siempre cualquier co-validación del path D ("mataría
207 detecciones reales") no tiene respaldo: entre 63 y 88 % de esa población no tiene alerta de
MIROVA, y desde #535 la población fría visible crece entre 2 y 3 veces por día (frente A, sin
separar el efecto de la estación).

**Pasos**: (1) re-medir la población en el régimen actual, por volcán y sensor, con su tasa base
(qué fracción de los records **no** fríos tiene alerta: el frente D la midió en 77,9 % para su
variante más generosa, y eso quedó por encima del 73,6 % de los fríos); (2) cruzar con la tabla de
la Fase 1: cuánta sobre-publicación depende sólo del path D en fondo frío; (3) sólo si el sustrato
lo justifica, A/B de la co-validación que A23 proponía, con el mismo criterio de la Fase 2. La
cerca del dashboard sigue ocultando lo `far`, que es el parche de display que A72 pide no confundir
con un arreglo.

### Fase 4. Geometría y magnitud: el brazo que nunca se corrió

**Por qué**: D16 refutó "el regrid F70 arregla la magnitud", no "la grilla de MIROVA explica el
sub-reporte" (V-04). S130 midió que la razón contra MIROVA cae de 0,740 cerca del nadir a 0,253 más
allá de 50° en VIIRS 375, y dejó escrito que el brazo fiel sería bow tie más remuestreo, en ese
orden y centrado en el punto correcto (`get_grid_center`, D17). Y A99 ya no puede apagar la búsqueda
en la fórmula: su 0,995 compensa dos factores opuestos y además compensa entre volcanes.

**Pasos**: (1) sustrato: razón de magnitud por volcán, por ángulo cenital y por conteo de píxeles,
en el régimen actual, con n declarado por celda; (2) implementar el brazo fiel **con el flag
apagado** (patrón de D25 en S145); (3) A/B con criterio en razón de magnitud estratificada. Esta
fase afecta la magnitud, no la alerta: va después de las fases 2 y 3 salvo que la Fase 1 diga otra
cosa.

### Fase 5. MODIS: qué es de verdad el problema

**Por qué**: la premisa de A82, D11 y D12 era "la detección está, el problema es sólo la etiqueta
`far`". Con una tasa base de 89,1 % (hay cúmulo con magnitud dentro del inner casi siempre, haya o
no actividad), destapar la etiqueta destaparía por igual las noches con y sin actividad. El problema
de MODIS es de **especificidad dentro del inner**, y eso apunta otra vez a los caminos no literales
y al fondo (D25: mediana de anillo vigente en 6 de 11 volcanes).

**Pasos**: (1) repetir la tasa base por volcán (144 de 158 positivas son Láscar: fuera de Láscar
casi no hay muestra, y hay que decirlo); (2) usar el OSF v2.5 como segunda referencia donde el CSV
del scraper no llega, sabiendo que es producto filtrado (A105): sirve para corroborar presencia, no
para contar ausencias; (3) MODIS entra a los brazos de la Fase 2 sólo si tiene sustrato. No se
reabre la búsqueda de un discriminante por record contra la etiqueta de MIROVA: eso V-03 lo dejó
reforzado.

### Fase 6. Que el operador lo vea: `pc.classification` al dashboard

**Por qué**: es la mitad del objetivo que no depende de cambiar la detección. Aunque la brecha de
sobre-publicación no se cierre nunca del todo (parte es calor real, A54), el operador tiene que
saber qué está mirando.

**Pasos**: (1) sincronizar `registro_vrp_ocr.csv` en `sync-mirova-csv.yml` (hoy sólo lo trae el
audit semanal, y cerca de un tercio de las alertas del OCR no tiene equivalente en el consolidado:
sin esto 268 de 1.100 "MIROVA calló" son provisorios); (2) corregir el valor de las 33 pasadas
`no_reference` que sí tienen fila RUTINA, y marcar como provisorio todo lo posterior a la última
fila de cada canal de referencia; (3) workflow del post-proceso (propuesta redactada en
`docs/audit_s146/CLASSIFICATION_IMPLEMENTADA.md`, con su propio reintento de push, sin entrar al
grupo `push-main`); (4) display en las tres vistas vivas (`index.html`, `diario.html`,
`mosaico.html`), verificado en navegador real. Decisión de Nicolás: cómo se ve (color, filtro o
leyenda) y si "sólo nuestro" se atenúa o sólo se rotula. **Después de esto se puede revisar D13**
(la cerca del frontend), que S145 dejó esperando este lenguaje.

### Fase 7. Que no vuelva a pasar

| qué | por qué |
|---|---|
| **Regla nueva A113**: una rebaja se propaga a los hijos en el mismo PR, y el grafo del frente E (`experiments/_s146_auditoria/frente_E/grafo.json`) se mantiene como registro de quién cuelga de quién | es el hallazgo central de S146 |
| **Guard de propagación**: un test que lee el grafo y falla si un cierre marcado como caído sigue citado sin marca en `MISSION.md`, en los encabezados del catálogo o en `CLAUDE.md` | una regla que depende de acordarse no se aplica |
| **Censo con control que pueda fallar** y ventana por sección, no de 5 líneas | V-14 y §1 de la auditoría |
| **Segunda tanda de auditoría**: los 89 cierres nuevos del censo ampliado (55 sin respaldo cerca) y los 13 cierres con script que el frente B no tocó | cobertura declarada, no cubierta |
| **Scripts perdidos**: el 0,859 de A83, el probe de A84 y el 207 de D9 vivían en scratchpad | regla de la guía maestra: el instrumento que midió un hallazgo va al repo el mismo día |
| **El libro de cuentas por tramo**: hoy mide 2026 entero y cruza #535 | D-06 |
| **Tests de guardas contra un árbol temporal**, nunca contra `data/mirova_equivalent/` | incidente del verificador en V-17 |
| **El hueco del corpus** (2025-11-16 a 2026-01-28 en 9 volcanes, 111 días en PCC): decidir si se rellena. Un backfill es reproceso largo: va en GitHub Actions por volcán y en serie, o no va. Con 9 GB libres no se hace en local | V-15 |

## 4. Orden y dependencias

```
Fase 0 (docs) ──────────────┐
Fase 1 (sustrato) ──────────┼──> Fase 2 (brazo fiel) ──> Fase 2b (mudar al experimental, si hace falta)
                            ├──> Fase 3 (D9, fondo frío)
                            └──> Fase 5 (MODIS)
Fase 2 paso 1 (batería en Actions) puede correr en paralelo con las fases 0 y 1
Fase 4 (geometría y magnitud) después de 2 y 3, salvo que la Fase 1 diga otra cosa
Fase 6 (dashboard) independiente de todas: puede empezar ya
Fase 7 en paralelo, por partes
```

Próxima sesión, en paralelo y sin tocar el pipeline: **Fase 0, Fase 1, el paso 1 de la Fase 2 y el
paso 1 de la Fase 6.**

## 5. Decisiones que esperan a Nicolás

| # | pregunta | opciones | recomendación |
|---|---|---|---|
| 1 | **¿Se aplica la Fase 0 (correcciones a documentos rectores, incluido `CLAUDE.md` y `MISSION.md`)?** | sí en un PR / revisar una por una | **sí, en un PR**, con verificador antes de mergear. Son textos que el propio proyecto ya desmintió |
| 2 | **¿Se abren D30 (Test 1 integrado es propio) y D31 (test de temperatura de brillo no está en el paper)?** | sí / esperar a la Fase 1 | **sí ahora**: abrir una divergencia es describir, no decidir. El catálogo no puede seguir diciendo que el Test 1 integrado "ES Coppola 2015" |
| 3 | **Si el brazo fiel cuesta recall de señal sub-píxel real, ¿se muda lo propio al perfil experimental (Fase 2b)?** | mudar / conservar en `mirova_equivalent` / decidir con los números | **decidir con los números de la Fase 1**, pero con la regla S143 como punto de partida: `mirova_equivalent` literal, lo demás separado y rotulado |
| 4 | **La FICHA del sistema de decisiones automatizadas cita un artículo que no es**. ¿Se corrige ya (requiere A45 por estar en `pipeline/`) o junto con la Fase 2? | ya, con tag, cambio sólo de comentario / con la Fase 2 | **ya**: es un documento publicable por la Resolución N°372 y el cambio es de comentario. Tag `pre-s146-ficha-test1` y tu confirmación |
| 5 | **Correo a Coppola**: agregar una pregunta nueva | enviar con la pregunta / enviar como estaba | **agregar y enviar**: "¿el NRT usa algún test integrado sobre el ROI o de temperatura de brillo, además de los Tests 1 a 3 de SP426.5?". Es la pregunta que más trabajo puede ahorrar de todo este plan |
| 6 | **`pc.classification` al dashboard (Fase 6)**: ¿cómo se ve? | rótulo / color / filtro | lo propongo con una maqueta en el navegador cuando llegues a esa fase; la sincronización del OCR (paso 1) se puede hacer ya |
| 7 | **El hueco del corpus**: ¿se rellena? | sí en Actions / no | **no por ahora**: no afecta al régimen actual, que es donde se mide la paridad. Anotarlo en `CLAUDE.md` y seguir |
| 8 | **Segunda tanda de auditoría** (89 cierres nuevos) | ahora / después de la Fase 2 | **después**: la Fase 0 ya corrige los que más apagan, y la Fase 7 pone el guard |

Siguen pendientes de antes y no cambian: el token de Earthdata vence el **2026-10-03** (lo renuevas
tú), y la primera corrida NRT posterior al merge de #709 todavía no termina (a las 09:04 UTC del
2026-09-20 había una en cola).
