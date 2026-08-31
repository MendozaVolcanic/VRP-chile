# S129 · V6 — Transparencia algorítmica: ¿el dashboard muestra lo que la ficha declara?

**Alcance**: `docs/FICHA_SDA_VRP_CHILE.md` (v1.4) contra `frontend/index.html`,
`diario.html` y `mosaico.html`. Auditoría de cumplimiento, read-only. Marco:
Resolución Exenta CPLT N°372.

---

## Resumen (la brecha de mayor riesgo primero)

**La ficha no es alcanzable desde el entregable.** Un `grep -rn -i "ficha|SDA|transparencia|CPLT|372"`
sobre todo `frontend/` devuelve **cero coincidencias**, y `pages-deploy.yml:68-70,92`
copia al sitio publicado sólo `frontend/`, `data/` e `imagenes/` — `docs/` no se
despliega. El sistema publica sus resultados en la web y deja su ficha de
transparencia únicamente dentro del repositorio. Quien mira el dashboard no tiene
cómo saber que esto es un SDA declarado, ni llegar a lo que la ficha dice de él. Es
la brecha de más alto riesgo y la más barata de cerrar: un enlace en el modal
"Acerca de" y el archivo copiado al sitio.

Segunda: **en Puyehue–Cordón Caulle, 696 de 1.062 registros MODIS se clasifican
`summit` con mediana de 17,2 km del cráter** y se pintan de rojo, mientras el mismo
fenómeno en Llaima (mediana 21,1 km) sale `far` y queda oculto. La única diferencia
es `inner_radius_km` (20 contra 5, `index.html:677`). La ficha declara la
sobre-detección difusa a 1 km como límite físico caracterizado — pero el dashboard
la muestra como anomalía de cumbre, sin marca, y para PCC no existe ni un solo
registro MODIS de referencia que la respalde.

Tercera, y trivial de arreglar: **la ficha se contradice consigo misma en la
versión** — encabezado `v1.3 — 2026-08-09` (línea 7) contra `v1.4 — 2026-08-30` en el
historial (línea 48). Es el campo por el que un fiscalizador empieza.

Lo demás es de riesgo medio o bajo. Dos hallazgos son **negativos limpios y conviene
decirlo**: la supresión de artefactos hoy **no suprime nada** (0 de 57.696 registros),
y la cadencia declarada sí se cumple.

---

## Tabla: declarado → efectivo → brecha → riesgo

| Lo que la ficha declara | Lo que el dashboard hace | Brecha | Riesgo |
|---|---|---|---|
| Es un SDA en scope Res.372, con ficha publicable | Cero menciones a ficha/SDA/CPLT en las tres vistas; `docs/` no se despliega (`pages-deploy.yml:68-70`) | La ficha no es alcanzable desde el punto de contacto con el servicio | **Alto** |
| *"Sobre-detección difusa a la resolución MODIS: foco débil y gradiente son indistinguibles; el detalle se cubre con VIIRS 375 m"* | PCC: 696/1.062 MODIS como `summit` a 17,2 km, coloreados como anomalía de cumbre y contando para el nivel de alerta. Llaima: 1.050/1.103 como `far`, ocultos. La diferencia es `inner_radius_km` (`index.html:677`) | El límite declarado se muestra como detección normal, y de forma incoherente entre volcanes. Verificado sobre `latest_consolidado.csv`: de 94 alertas MODIS de referencia, **88 son de Láscar**; PCC, Copahue, Llaima, Isluga, Lastarria, PP y Tupungatito tienen **cero**. Histórico PCC hasta 233 MW ("Alto"); hoy 5,0 MW | **Alto** |
| Encabezado: v1.3 (2026-08-09) | Historial: v1.4 (2026-08-30) | Versión publicada inconsistente dentro del propio documento | **Alto** (costo cero) |
| *"Método: reglas físicas determinísticas (Wooster; Coppola 2016a/2024 por régimen)"* | `mirovaEqVrpCore` (`index.html:1082-1090`) aplica el Núcleo F5' **sólo a VIIRS I-band**; MODIS y VIIRS 750 usan `pc.vrp_mw` crudo. El tooltip del control (`index.html:567`) lo describe sin restricción de sensor | La fórmula que produce el número publicado depende del sensor, y eso no se declara ni se muestra. Es el modo de falla de S127 (alcance declarado ≠ efectivo), esta vez en un texto que el usuario sí lee | **Medio** |
| *"Verificación de coherencia espacial… validación cruzada contra valores MIROVA publicados"* | `_mirova_confirmed` **sí se muestra**, pero sólo en el mapa: anillo verde (`index.html:2603-2605`) y línea en el popup (`2626-2628`). No aparece en tarjetas, tabla ni gráficos. En `diario.html` y `mosaico.html` **nunca se puebla** (sus propios comentarios: `diario.html:334`, `mosaico.html:326`) | *(Corrige el supuesto del encargo: no es que "nunca se muestre".)* La consecuencia real es otra: el cinturón "nunca ocultar un registro confirmado por MIROVA" que `index` aplica en los filtros de artefacto **no existe** en diario ni mosaico | **Medio** |
| Ficha única para todo el sistema | Sólo `index.html` tiene modal "Acerca de" con método, papers y límites. `diario.html:136` y `mosaico.html:191` cierran con una línea de crédito y nada más | Dos de las tres vistas live son URLs autónomas, sin ninguna declaración metodológica | **Medio** |
| *(la ficha no declara métricas de desempeño)* | El modal publica "Recall … MODIS-cráter **100 %**" (`index.html:474`), fechado S119 / 2026-07-01 | Métrica de titular cuya muestra es 94 % un solo volcán (Láscar), presentada como cifra de red y con dos meses de antigüedad. El panel *live* por sensor (`index.html:2023-2052`) sí es honesto y muestra "—" cuando no hay referencias | **Medio** |
| *"Mitigación: filtros de contexto, zonas de exclusión y degradación explícita a fondo regional"* | Dos filtros de display suprimen del gráfico (`isCirrusArtifact` 1112-1116, `isDiffuseFieldArtifact` 1131-1139) sin informar cuántos | **Medido: hoy no suprimen nada.** Reimplementé ambos criterios usando `pc.vrp_mw` como cota superior de `mirovaEqVrp` sobre los **57.696** registros de los 11 Tier A: **0 los cruzan**. En PCC, el volcán que motivó ambos, el máximo `pc.vrp_mw` entre los 2.276 registros con `t_max < 278 K` es **5,0 MW**, contra umbrales de 10 y 50 MW. Y cuando disparan, el registro **no desaparece**: queda en la tabla con distintivo y explicación (`3358-3364`) | **Bajo** |
| *"revisar la ficha cuando cambie la lógica…; el CPLT sugiere refresco mensual"* | Cron NRT cada 2 h (`nrt.yml:12`); datos verificados al día (`updated` 2026-08-31T10:56Z); el dashboard muestra "Act: … UTC" (`1911-1913`) y marca los volcanes sin pasadas (`1499-1507`) | **Sin brecha.** La cadencia se cumple y es visible | **Bajo** |
| *"la lógica es íntegramente auditable"* | Ningún registro guarda la versión del pipeline. Verificado sobre el esquema de los 57.696: el único campo con "version" es `product_version`, que es el producto L1B de NASA (`standard`/`nrt`), no el código | Un número publicado puede cambiar entre reprocesos sin dejar rastro en el dato. Mitigado de hecho —`data/` está versionado en git, así que `git log` sobre el JSON reconstruye—, pero eso no es "auditable desde el dato" ni está declarado como límite | **Bajo-medio** |

---

## Reconstrucción por un tercero

*"¿Por qué el sistema mostró 3,2 MW en Villarrica esa noche?"* — el dashboard alcanza
casi por completo. El popup del mapa (`index.html:2620-2640`) entrega sensor,
timestamp UTC, clase `summit`/`far`, el VRP del clúster con su número de píxeles, la
suma de escena **rotulada explícitamente como diagnóstico y no como el VRP**, y la
confirmación MIROVA con su distancia; el botón "Exportar CSV (periodo)"
(`index.html:2057-2059`) baja la serie.

Falta **un** dato, y es justamente el del hallazgo de riesgo medio: **cuál de las dos
fórmulas produjo ese número**. Depende de un control persistido en `localStorage`
(`index.html:1015`) *y* del sensor del registro, y ninguna de las dos cosas queda
estampada junto al valor. Dos personas mirando la misma noche pueden ver magnitudes
distintas sin ningún indicio de por qué. Es el eslabón más barato de cerrar de todo
este informe.

## Nota de método

Verifiqué por mi cuenta (A48) los cuatro hallazgos de alto impacto: el `grep` vacío
sobre `frontend/`; la distribución MODIS de referencia recontada desde
`latest_consolidado.csv` (94 alertas, 88 en Láscar); la clasificación `summit`/`far`
de PCC y Llaima contada sobre los JSON publicados; y la reimplementación de ambos
criterios de artefacto sobre los 57.696 registros. Ninguna cifra de este informe fue
transcrita de otro documento.
