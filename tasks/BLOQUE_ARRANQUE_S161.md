# Bloque de arranque S161 (cierre de S160, sesión dueña del loop: noche del 21 al 22 y día del 22-oct, hasta ~18:45 UTC)

Escrito el 2026-10-22 ~18:45 UTC sobre `loop/activo`. **Sin trabajo en curso**: ningún agente vivo, la rama
`s159-evaluador-d25` igual al remoto en `bcfdc7c76`. Más abajo queda, como historia, el bloque que escribió esta misma
sesión a las ~07:30 UTC (secciones `-prev`); varias filas suyas ya cambiaron. El detalle de cada vuelta está en
`tasks/LOOP_OBJETIVOS.md` §6 (entradas del 2026-10-22) y las decisiones en su §5 (D-35 a D-45).

## a. Todo en una pantalla

| qué | estado | evidencia |
|---|---|---|
| D25: veredicto | **SIN LEER, sin tag de lectura.** Falta ejecutar D-45 | rama `s159-evaluador-d25` |
| D25: evaluador | D-28, D-30, D-32, D-34, D-29, D-42 (adenda `ca65069f6`) y el estrato 203 (`5f986a209`) implementados y **verificados** en tres vueltas; D-44 registrada (`172313c2d`) | `experiments/_s159/instrumentos/verificador_d34/`, `verificador_d29/`, `verificador_d42/` (vueltas 1 a 3) |
| D25: placebos de D-44 | **corridos y verificados**: (a) GANA con sustrato, (b) PIERDE, (c) 2 % de falsos por cola | `experiments/_s159/instrumentos/placebos_d44/` (`20ac098a3`), `verificador_d42/vuelta3/` (`bcfdc7c76`) |
| D25: P2 con pocas noches | **defecto confirmado (V42-20)**: con 7 noches P2 nunca decide; con 10 u 11 decide la semilla. **D-45 cerrada: opción (ii)**, por hacer | `verificador_d42/vuelta3/INFORME.md` |
| D25: brazo de sensibilidad del 17 al 19-oct (D-35) | **terminado verde** (run 39756261926, 13 jobs); sin abrir hasta después del tag | rama `s146-ab/39756261926` |
| #892 (cese de Suomi NPP), #891 (preámbulo), #893 (auditoría S160), #895 (R13 del sync) | **MERGEADOS** | GitHub |
| Mirova-v1#26 (arreglos del scraper) | abierto, de Nicolás | sesión `audit-mirova-v1` |
| Auditoría espacial (Tupungatito, Cordón Caulle, Isluga) | **terminada y verificada**: el calor que alerta MIROVA está en el cráter, lejos del centro de su imagen, y lo vemos ahí; Cordón Caulle con radio de 20 km publica lejos en noches limpias; VE-01 SOSPECHA de protegida perdida por radio en Tupungatito | `experiments/_s160_espacial/` (README y `verificador/INFORME.md`), mapa en `experiments/_s160_espacial_mapa/` |
| Umbrales de VRP por sensor de MIROVA | reales en su archivo OSF (VIIRS 750 de noche: 5 MW), **no** aplicados en el NRT; la protegida sigue en 1 MW | bitácora del 2026-10-22, entrada «umbrales de VRP por sensor» |

## b. Decisiones que espera Nicolás

| # | pregunta | recomendación |
|---|---|---|
| D-36 | Ampliar el port con 300 a 400 negativos del estrato `neg_resto` | sí, con pre-registro |
| D-38 | Alarma de plataforma callada: diaria o patrón S123 (#892 ya está en `main`) | patrón S123 |
| D-39 a D-41 | Mirova-v1: bucle de push (en parte cubierto por #26 y #895), operación y OCR, alertas sólo OCR en el criterio | ver la cola |
| D-43 | Lo que sigue abierto de `docs/AUDIT_S160.md` §5 (mensaje «Cobertura: completa» del NRT, guardas de token y de referencia, llevar S157 y S158 a `main`) | ver ese documento |
| nueva | VE-01 y el radio de 20 km de Cordón Caulle: ¿pre-registro de un cambio de radio? | primero el mapa interactivo y la persistencia (§f); después decidir |

## c. Lo aprendido

Reglas generales del workspace:
- **Un control que no puede fallar no es un control** (V42-10): apagar al azar le costaba a K seis alertas por cada
  negativo, así que su «0 GANA» no medía nada. Antes de correr un placebo, contar la composición del sustrato y
  preguntar si el resultado temido es siquiera posible.
- **Ampliar semillas en un solo punto después de mirar es parada opcional** (V42-22): el estimador no se sesga, pero
  el intervalo pierde su cobertura nominal. El número de semillas se fija antes.
- **Un intervalo bootstrap con pocos bloques no es una prueba**: con 7 bloques, el percentil 2,5 no cruza 0 aunque un
  bloque vaya en contra. Con pocos bloques se usa la prueba exacta de signos (enumerar los 2^B repartos).
- Siguen en pie las del bloque de las 07:30: un defecto de la regla sellada se devuelve sin leer; el tipo de falla se
  lee del XML de JUnit; la salida roja se guarda con la prueba final; los enlaces de carpeta se quitan con `rmdir`.

Del proyecto: el calor que MIROVA alerta está en el cráter aunque el cráter quede lejos del centro de su imagen
(Tupungatito 4,79 km, Cordón Caulle 7,61 km); su archivo OSF y su NRT usan umbrales distintos (A105).

## d. Problemas abiertos e hipótesis

| problema | estado |
|---|---|
| P2 de D-34 con pocas noches | **CONFIRMADO** (V42-20); se corrige con D-45 |
| VE-01: protegida de Tupungatito del 2026-09-29 04:54 perdida por radio | **SOSPECHA** |
| VE-02: alerta de Cordón Caulle del 2026-10-21 lejos del cráter | **SOSPECHA** |
| La «fuente persistente» del E de Cordón Caulle | **REFUTADA como persistente** (13 de 15 TIF diurnos, del 9 al 18-may) |
| El corte de Suomi NPP también en LANCE NRT | **SOSPECHA**; confirmar el 3-nov |

## e. Lo que ya está cerrado y no hay que rehacer

- El código del evaluador cumple todas las adendas hasta D-42 y el estrato 203 (tres verificadores).
- Los placebos (a), (b) y (c) están corridos y verificados; sólo el (c) se rehace sorteando por noche (V42-21).
- La geometría de los tres volcanes de la auditoría espacial: el centro no hay que moverlo.
- El umbral de 5 MW de VIIRS 750 no es errata (lo confirma el OSF).

## f. Prompt para la próxima sesión

```
Retoma VRP Chile (cierre de S160, 2026-10-22 ~18:45 UTC). Antes de creerle a nada:

1. cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"; git fetch origin --prune; git status -sb
   (loop/activo, en el commit de este cierre o más nuevo); hora del servidor con
   gh api -i repos/MendozaVolcanic/VRP-chile | grep -i date (A86).
2. Lee CLAUDE.md del proyecto, después tasks/BLOQUE_ARRANQUE_S161.md (el bloque de arriba; las secciones -prev son
   historia), después tasks/LOOP_OBJETIVOS.md §5 (D-35 a D-45) y las entradas del 2026-10-22 de su §6.
3. Comprueba contra GitHub: la rama s159-evaluador-d25 (debe estar en bcfdc7c76), #890 (borrador), Mirova-v1#26.

Trabajo, en orden:
- D-45 (Nicolás dijo sí a la opción ii; su respuesta textual está en la fila D-45): quinta adenda sellada en
  experiments/_s157_prereg_d25/. P2 se decide con la prueba de signos por bloque noche-volcán: valor-p exacto
  enumerado hasta 20 noches (si no, 10.000 sorteos con semilla fija), GANA o PIERDE con p de 5 % o menos, BLOQUEA si
  el neto va en contra sin llegar, SIN SUSTRATO con 4 noches o menos (D-44); decir que la calibración de D-42 deja de
  hacer falta para P2. Después: implementador (agente, worktree C:\vrp-trabajo\s159-evaluador) con pruebas rojas,
  candados por mutación leídos de JUnit y el placebo (c) sorteando por noche (V42-21); verificador con contexto
  limpio en el otro modelo; recién entonces tag de lectura y relectura de D25 con la referencia congelada por hash,
  la tabla de latest.php sola al lado y el estrato 203; y después el brazo del 17 al 19 (run 39756261926, aparte).
  Nunca leas el veredicto antes del tag. Base del diseño: experiments/_s159/instrumentos/verificador_d42/vuelta3/.
- PEDIDO DE NICOLÁS: mapa interactivo (Artifact, Leaflet sobre imagen satelital, con zoom) de Tupungatito, Cordón
  Caulle e Isluga con la geometría de MIROVA y la nuestra, nuestros cúmulos y los focos recurrentes, y la persistencia
  de cada foco mes a mes durante el año SEPARANDO noche y día (el MIR diurno se contamina con sol, A76). Revisar
  VE-01 y VE-02 en las imágenes de MIROVA. Base: experiments/_s160_espacial/ (leer primero verificador/INFORME.md y
  el README). Cargar el skill artifact-design antes de escribir el artefacto; dar también la ruta local.

Reglas duras: nada en pipeline/, data/ ni frontend/ sin tag y sí de Nicolás (A45); sólo EARTHDATA_TOKEN (A71);
nada de gh run watch ni bucles de gh; disco justo (C: 14 GB, D: 8,6 GB al cierre; parada bajo 3 GB); git add por
archivo; esperar el CI con conclusión antes de dar un PR por listo; español de Chile sin voseo ni guiones largos;
rutas absolutas. Si la sesión no alcanza: commitea, anota en la bitácora qué quedó corriendo y cierra con /cierre.
```

---

# (historia) Bloque de arranque S161 escrito a las ~07:30 UTC (cierre de la sesión nocturna S160, dueña única del loop, 2026-10-22 03:27 a 07:30 UTC)

Escrito el 2026-10-22 ~07:30 UTC sobre `loop/activo`. Nicolás durmió toda la sesión: **no se tomó ninguna decisión
suya**; todo lo que la necesita quedó en la cola `tasks/LOOP_OBJETIVOS.md` §5 (D-35 a D-43) con recomendación. El
estado se fijó **sin trabajo en curso**: ningún agente vivo (los de S159 entregaron todos; los míos también). Lo único
que corre es el CI de #890 sobre `29831d7bc` (`pytest` pendiente al cerrar, run 39740189157). El bloque anterior
(`tasks/BLOQUE_ARRANQUE_S160.md`) queda como historia; varias filas suyas ya cambiaron (ver tabla a).

## a-prev. Todo en una pantalla

| qué | estado | evidencia |
|---|---|---|
| D25: D-28, D-30, D-32, D-34 en el evaluador | **implementados y VERIFICADOS** (código fiel a las adendas; las 8 afirmaciones confirmadas, incluido el signo de P2) | `experiments/_s159/instrumentos/verificador_d34/INFORME.md` (`786bfb288`, rama `s159-evaluador-d25`) |
| D25: la regla sellada de P2 | **DESCALIBRADA con pocas noches** (24,8 % de decisiones falsas con 3 noches de signo común; 13,0 % con 4; 6,5 % con 5); la auditoría S160 llega a lo mismo (V1a-01) | V34-01 del informe de arriba; `docs/AUDIT_S160.md` §5.2 (rama `s160-auditoria`) → **D-42** |
| D25: D-29 (sin el 13, 17, 18, 19 y 20-oct) | **implementado y VERIFICADO** en el código; el candado es débil (las pruebas atrapan 4 de 9 mutaciones del verificador) | `6f43ec624` y `experiments/_s159/instrumentos/verificador_d29/INFORME.md` (`29831d7bc`) |
| D25: veredicto | **SIN LEER, sin tag de lectura** a propósito: leer con una P2 que se sabe descalibrada amarraría la decisión | comentario en #890 (`issuecomment-6334430043`) |
| Censo del oráculo V750 (5.476 negativos) | **TERMINADO Y VERIFICADO**: K publica 54, O-def 5, O-sens 15 de 5.353; O-def pierde 6 protegidas de Cordón Caulle; O-sens 0 perdidas, ΔE −90 (GANA EN EL CENSO, descriptivo, no adopta) | `experiments/_s159/oraculo_censo/INFORME.md` y `verificador/INFORME.md` (`ebf8cf861`; integrado a `s159-pruebas` en `812624cc6`) |
| Port del código de MIROVA a V375 y MODIS | **VERIFICADO EN PARTE**: MODIS detecta como MIROVA, pero su «gana a K» queda NO RESUELTO (0 de 37 negativos sorteados); V375 con la tabla sola pierde 0 de 29 protegidas | `experiments/_s159/portes/verificador/INFORME.md` (`ca034d66e`) → **D-36** |
| #892 (cese de Suomi NPP el 2026-11-02 13:00 UTC) | **listo para merge** (CI verde, verificado en el navegador: tres vistas, comparacion sin aviso, reloj simulado, 375 px) | `issuecomment-6332148549` en #892 → **D-37, D-38** |
| Auditoría de Mirova-v1 | **TERMINADA** (13 arreglos, ninguno aplicado) | `experiments/_s159/mirova_v1_auditoria/INFORME.md` (copia); scripts en `D:\vrp-trabajo\mirova-v1-auditoria\` → **D-39 a D-41** |
| Auditoría S160 | **TERMINADA** (27 marcas A113 en su rama, cola de campo de 10 casos) | `docs/AUDIT_S160.md` y `docs/COLA_CAMPO.md` en `s160-auditoria` (`b941c8052`); PR #891 → **D-43** |
| PRs | #889 borrador; #890 borrador (CI pendiente); #891 listo; #892 listo | `gh pr view` al cierre |
| Issue de alerta #864 (auto-audit fuera de banda, 2026-10-19) | **ABIERTO**; su causa (Chillán MODIS, Test 2 y fondo) la midió S159 | `experiments/_s159/chillan_modis/` en `s159-pruebas` |

## b-prev. Decisiones que espera Nicolás

Todas en `tasks/LOOP_OBJETIVOS.md` §5 con su evidencia. En orden de urgencia:

| # | pregunta | recomendación |
|---|---|---|
| D-37 | Merge de #892 (vigilancia por plataforma y aviso del cese) antes del **2026-11-02 13:00 UTC**; y si el issue informativo sale una sola vez aunque se cierre | **mergear ya**; una sola vez |
| D-35 | ~~Brazo de sensibilidad de D25 sobre el 17 al 19-oct por NRT~~ **APROBADO y DESPACHADO** (Nicolás, 2026-10-22 ~09:30 UTC): run 39756261926 desde `s157-d25-k-codigo` | no abrir sus resultados antes del tag de lectura de D25; al terminar, sólo contar cobertura por brazo |
| D-42 | Calibrar P2 de D25 antes del tag (bloquea la lectura) | **calibrar P2 como M** (nulo con el signo de cada noche al azar, 1.000 repeticiones, INDECIDIBLE si los falsos pasan de 5 %) en una cuarta adenda sellada, más los candados que faltan (V34-03 y V29-01); después verificador limpio y recién el tag |
| D-43 | Las nueve decisiones de `docs/AUDIT_S160.md` §5 (#891, mensaje «Cobertura: completa» del NRT, llevar S157 y S158 a `main`, guardas de referencia y token, etc.) | las de ese documento; la más urgente es la 3 (con el cese) |
| D-39 | Bucle de push del scraper Mirova-v1 (pierde filas de la tabla) | **R1+R2+R3** y reponer filas (R4); R13 en el sync de VRP Chile |
| D-40 | Arreglos de operación y OCR de Mirova-v1 | R5 a R7 primero; R9 + R10 (marcar el método de grupo, no apagarlo) |
| D-41 | Alertas sólo OCR en el criterio de victoria | sólo las del método de la estrella, nocturnas y desde V29.2; el resto aparte |
| D-36 | Ampliar el port con 300 a 400 negativos del estrato `neg_resto` por sensor | **sí**, con pre-registro |
| D-38 | Alarma de plataforma callada: comentario diario o patrón S123 | **patrón S123** |
| heredadas | las del bloque S160 §b que no se tocaron: `fetch.py` sin SNPP tras el 2-nov (con tag), sello de MxD03 v2, OCR y `latest.php`, tope de cordura de `store.py`, D-10 diurno, #813, λ de B22, PAT, aviso a OVDAS | ver `tasks/BLOQUE_ARRANQUE_S160.md` §b |

## c-prev. Lo aprendido

Reglas generales del workspace (para el `CLAUDE.md` global o la guía de auditorías):
- **Un verificador puede encontrar un defecto de la regla sellada y no del código.** Ahí no se lee el resultado ni se
  "arregla" sin el dueño: se devuelve como decisión, porque corregir una regla después de mirar es sospechoso.
- **El resumen de `pytest -q` no trae el tipo de la excepción.** Mi lector de mutaciones dio 0 de 4 por eso; leer el
  XML de JUnit. Antes de creerle a un instrumento que da cero, correrlo sobre un caso que tiene que fallar (A116).
- **La salida roja se guarda con la versión final de la prueba.** Guardé la roja y después endurecí una prueba; el
  verificador lo detectó (V29-02).
- **En Windows, un `rm -rf` sobre un enlace de carpeta (junction) puede borrar el destino.** Quitar el enlace con
  `cmd /c rmdir <enlace>` (sin `/S`) y comprobar que el destino sigue entero.
- **La hora de la sesión no es un reloj (A86, otra vez):** escribí encabezados de bitácora 15 a 30 min adelantados;
  pedir la hora del servidor antes de cada encabezado.

Del proyecto (candidatas a reglas A120 en adelante, en un PR que toque `CLAUDE.md`, A113):
- Con el filtro de distancia del tablero, la ventaja del oráculo con recuadro sensible depende del predicado: detecta
  43 negativos y publica 15 (28 quedan `far`).
- Un record sintético que promedia la posición de los píxeles puede convertir un acierto en `far` (Láscar
  2026-08-26 05:48): al comparar contra el código de MIROVA, el sintético es parte del instrumento.

## d-prev. Problemas abiertos e hipótesis

| problema | estado |
|---|---|
| P2 de D25 decide al azar con pocas noches | **CONFIRMADO** (medido con la función real sobre sintéticos, n = 2.000) |
| Bajo el nulo, BLOQUEA de P2 apaga CUMPLE en 37 a 48 % | **CONFIRMADO** (lo pide la adenda; leerlo como moneda) |
| El candado de D-29 no atrapa 5 de 9 mutaciones | **CONFIRMADO** (V29-01) |
| El «gana a K» del port en MODIS | **SIN RESOLVER** (cota de Wilson hasta 9,4 % de silencio roto) |
| 2 de las 6 protegidas que pierde el port en V375 son un píxel débil real del cráter | **SOSPECHA** (no se distingue de «distancia de otra pasada») |
| NRT de LANCE de Suomi NPP también se corta el 2-nov | **SOSPECHA** fuerte; confirmar el 3-nov |
| «Cobertura: completa» del NRT sin gránulos de una plataforma | **CONFIRMADO** por la auditoría S160 (241); #892 no lo cambia |

## e-prev. Lo que ya está cerrado y no hay que rehacer

- **El código del evaluador de D25 cumple D-28, D-30, D-32, D-34 y D-29** (dos verificadores limpios). Lo que falta es
  la regla de P2 (D-42) y los candados, no la implementación.
- **El censo del oráculo V750 está contado y verificado** (tablas byte a byte, recuento propio desde los crudos).
- **#892 está verificado en el navegador**; el desborde de diario y mosaico a 375 px es previo al PR.
- **El plazo de LANCE para el 17-19 está medido** (retención ~7,7 días al 2026-10-22).
- Las ~60 corridas en rojo de `vigilar-osf-mirova.yml` en ramas de prueba son la versión vieja del yml (comillas
  dobles en `if:`); #888 ya la corrige. No es un fallo de producción.

## f-prev. Prompt para la próxima sesión

```
Retoma VRP Chile (cierre de la sesión nocturna S160, 2026-10-22 ~07:30 UTC). Antes de creerle a nada:

1. cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"; git fetch origin --prune; git status -sb
   (debe ser loop/activo en 1810e6bbc o más nuevo, más el commit de este cierre); hora del servidor con
   gh api -i repos/MendozaVolcanic/VRP-chile | grep -i date (A86).
2. Lee CLAUDE.md del proyecto, después tasks/BLOQUE_ARRANQUE_S161.md entero, después tasks/LOOP_OBJETIVOS.md §5
   (D-35 a D-43) y las entradas del 2026-10-22 de su §6.
3. Comprueba contra GitHub: estado y CI de #889, #890 (CI de 29831d7bc), #891 y #892; si Nicolás contestó D-35, D-37
   o D-42; issue #864. Pide al computador que no se suspenda si vas a esperar trabajo largo.

Trabajo, en orden (lo que necesite el sí de Nicolás, sólo si ya lo dio):
- D-35 ya está despachado (run 39756261926, 2026-10-22). Revisar que terminó y contar sus pasadas por brazo contra
  producción (A108) SIN mirar publicaciones; sus resultados se abren recién después del tag de lectura de D25.
- D-37: si dijo sí, merge de #892 antes del 2-nov 13:00 UTC; el 3-nov confirmar el corte con
  experiments/_s159/cese_snpp/cmr_colecciones_y_granulos.py (rama s159-pruebas).
- D-42: si eligió calibrar P2, cuarta adenda sellada + código con prueba roja + candados de V34-03 y V29-01 (un caso
  de punta a punta como experiments/_s159/instrumentos/verificador_d29/cobertura_sintetica.py) + verificador limpio
  del cambio; recién entonces tag de lectura y relectura de D25 con la referencia congelada por hash, informando
  también la tabla de latest.php sola. Nunca leas el veredicto antes del tag.
- D-43 (auditoría S160) y D-39 a D-41 (Mirova-v1): aplicar sólo lo que Nicolás apruebe, cada uno con tag y prueba.
- PEDIDO EXPLÍCITO DE NICOLÁS (2026-10-22, para esta sesión): «vuelve a mostrarme los mapas pero con la imagen
  satelital por detrás en algún artefacto donde podamos hacer zoom, veamos qué tan persistentes son; puedes revisar
  también datos durante el año, lo diurno parece ser no tan fiable, y revisamos si realmente son persistentes.»
  Base: experiments/_s160_espacial/ (leer primero verificador/INFORME.md y el README) y
  experiments/_s160_espacial_mapa/. Hacer: un Artifact con mapa interactivo (Leaflet sobre imagen satelital, con
  zoom) por volcán (Tupungatito, Cordón Caulle, Isluga): cráter, centro de la imagen de MIROVA, caja de cumbre y
  anillo de MIROVA (21 × 19, asimétrico, como lo midió el verificador), nuestro radio interno, nuestros cúmulos
  publicados en noches limpias y con alerta, y los focos recurrentes. Persistencia: contar cada foco por mes durante
  todo el año, SEPARANDO noche y día (el MIR diurno se contamina con reflejo solar, A76; la «fuente» del E de Cordón
  Caulle resultó ser 13 de 15 TIF diurnos del 9 al 18-may), con los TIF de MIROVA (hasta el 2026-09-21) y nuestros
  records nocturnos de todo el año. Revisar también VE-01 (protegida de Tupungatito 2026-09-29 04:54 con nuestro píxel
  a 9,42 km ENE) y VE-02 (Cordón Caulle 2026-10-21 lejos del cráter) en las imágenes de MIROVA. Leer el skill
  artifact-design antes de escribir el artefacto; publicar el artefacto y dar además su ruta local.

Reglas duras: nada en pipeline/, data/ ni frontend/ sin tag y sí de Nicolás (A45); sólo EARTHDATA_TOKEN (A71);
nada de gh run watch ni bucles de gh; disco justo (C: 13 GB, D: 8,3 GB al cierre; parada bajo 3 GB); git add por
archivo; no git en C:\vrp-trabajo\s159-pruebas (worktree de la auditoría S160, en la rama s160-auditoria); esperar el
CI con conclusión antes de dar un PR por listo; español de Chile sin voseo ni guiones largos; rutas absolutas.

Si la sesión no alcanza: commitea lo que haya, anota en la bitácora qué quedó corriendo (run id) y cierra con /cierre.
```
