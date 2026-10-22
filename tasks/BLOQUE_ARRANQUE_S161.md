# Bloque de arranque S161 (cierre de la sesión nocturna S160, dueña única del loop, 2026-10-22 03:27 a 07:30 UTC)

Escrito el 2026-10-22 ~07:30 UTC sobre `loop/activo`. Nicolás durmió toda la sesión: **no se tomó ninguna decisión
suya**; todo lo que la necesita quedó en la cola `tasks/LOOP_OBJETIVOS.md` §5 (D-35 a D-43) con recomendación. El
estado se fijó **sin trabajo en curso**: ningún agente vivo (los de S159 entregaron todos; los míos también). Lo único
que corre es el CI de #890 sobre `29831d7bc` (`pytest` pendiente al cerrar, run 39740189157). El bloque anterior
(`tasks/BLOQUE_ARRANQUE_S160.md`) queda como historia; varias filas suyas ya cambiaron (ver tabla a).

## a. Todo en una pantalla

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

## b. Decisiones que espera Nicolás

Todas en `tasks/LOOP_OBJETIVOS.md` §5 con su evidencia. En orden de urgencia:

| # | pregunta | recomendación |
|---|---|---|
| D-37 | Merge de #892 (vigilancia por plataforma y aviso del cese) antes del **2026-11-02 13:00 UTC**; y si el issue informativo sale una sola vez aunque se cierre | **mergear ya**; una sola vez |
| D-35 | Brazo de sensibilidad de D25 sobre el 17 al 19-oct por NRT. **Plazo: LANCE purga el 17-oct cerca del 2026-10-24 ~16:00 UTC** (retención medida ~7,7 días) | **correrlo**, desde un tag de código (no hace falta el de lectura) |
| D-42 | Calibrar P2 de D25 antes del tag (bloquea la lectura) | **calibrar P2 como M** (nulo con el signo de cada noche al azar, 1.000 repeticiones, INDECIDIBLE si los falsos pasan de 5 %) en una cuarta adenda sellada, más los candados que faltan (V34-03 y V29-01); después verificador limpio y recién el tag |
| D-43 | Las nueve decisiones de `docs/AUDIT_S160.md` §5 (#891, mensaje «Cobertura: completa» del NRT, llevar S157 y S158 a `main`, guardas de referencia y token, etc.) | las de ese documento; la más urgente es la 3 (con el cese) |
| D-39 | Bucle de push del scraper Mirova-v1 (pierde filas de la tabla) | **R1+R2+R3** y reponer filas (R4); R13 en el sync de VRP Chile |
| D-40 | Arreglos de operación y OCR de Mirova-v1 | R5 a R7 primero; R9 + R10 (marcar el método de grupo, no apagarlo) |
| D-41 | Alertas sólo OCR en el criterio de victoria | sólo las del método de la estrella, nocturnas y desde V29.2; el resto aparte |
| D-36 | Ampliar el port con 300 a 400 negativos del estrato `neg_resto` por sensor | **sí**, con pre-registro |
| D-38 | Alarma de plataforma callada: comentario diario o patrón S123 | **patrón S123** |
| heredadas | las del bloque S160 §b que no se tocaron: `fetch.py` sin SNPP tras el 2-nov (con tag), sello de MxD03 v2, OCR y `latest.php`, tope de cordura de `store.py`, D-10 diurno, #813, λ de B22, PAT, aviso a OVDAS | ver `tasks/BLOQUE_ARRANQUE_S160.md` §b |

## c. Lo aprendido

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

## d. Problemas abiertos e hipótesis

| problema | estado |
|---|---|
| P2 de D25 decide al azar con pocas noches | **CONFIRMADO** (medido con la función real sobre sintéticos, n = 2.000) |
| Bajo el nulo, BLOQUEA de P2 apaga CUMPLE en 37 a 48 % | **CONFIRMADO** (lo pide la adenda; leerlo como moneda) |
| El candado de D-29 no atrapa 5 de 9 mutaciones | **CONFIRMADO** (V29-01) |
| El «gana a K» del port en MODIS | **SIN RESOLVER** (cota de Wilson hasta 9,4 % de silencio roto) |
| 2 de las 6 protegidas que pierde el port en V375 son un píxel débil real del cráter | **SOSPECHA** (no se distingue de «distancia de otra pasada») |
| NRT de LANCE de Suomi NPP también se corta el 2-nov | **SOSPECHA** fuerte; confirmar el 3-nov |
| «Cobertura: completa» del NRT sin gránulos de una plataforma | **CONFIRMADO** por la auditoría S160 (241); #892 no lo cambia |

## e. Lo que ya está cerrado y no hay que rehacer

- **El código del evaluador de D25 cumple D-28, D-30, D-32, D-34 y D-29** (dos verificadores limpios). Lo que falta es
  la regla de P2 (D-42) y los candados, no la implementación.
- **El censo del oráculo V750 está contado y verificado** (tablas byte a byte, recuento propio desde los crudos).
- **#892 está verificado en el navegador**; el desborde de diario y mosaico a 375 px es previo al PR.
- **El plazo de LANCE para el 17-19 está medido** (retención ~7,7 días al 2026-10-22).
- Las ~60 corridas en rojo de `vigilar-osf-mirova.yml` en ramas de prueba son la versión vieja del yml (comillas
  dobles en `if:`); #888 ya la corrige. No es un fallo de producción.

## f. Prompt para la próxima sesión

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
- D-35 tiene plazo: el 17-oct sale de LANCE cerca del 2026-10-24 16:00 UTC. Si Nicolás dijo sí, despachar el brazo
  de sensibilidad de D25 sobre el 17 al 19 desde un tag de código del evaluador, declarado aparte.
- D-37: si dijo sí, merge de #892 antes del 2-nov 13:00 UTC; el 3-nov confirmar el corte con
  experiments/_s159/cese_snpp/cmr_colecciones_y_granulos.py (rama s159-pruebas).
- D-42: si eligió calibrar P2, cuarta adenda sellada + código con prueba roja + candados de V34-03 y V29-01 (un caso
  de punta a punta como experiments/_s159/instrumentos/verificador_d29/cobertura_sintetica.py) + verificador limpio
  del cambio; recién entonces tag de lectura y relectura de D25 con la referencia congelada por hash, informando
  también la tabla de latest.php sola. Nunca leas el veredicto antes del tag.
- D-43 (auditoría S160) y D-39 a D-41 (Mirova-v1): aplicar sólo lo que Nicolás apruebe, cada uno con tag y prueba.

Reglas duras: nada en pipeline/, data/ ni frontend/ sin tag y sí de Nicolás (A45); sólo EARTHDATA_TOKEN (A71);
nada de gh run watch ni bucles de gh; disco justo (C: 13 GB, D: 8,3 GB al cierre; parada bajo 3 GB); git add por
archivo; no git en C:\vrp-trabajo\s159-pruebas (worktree de la auditoría S160, en la rama s160-auditoria); esperar el
CI con conclusión antes de dar un PR por listo; español de Chile sin voseo ni guiones largos; rutas absolutas.

Si la sesión no alcanza: commitea lo que haya, anota en la bitácora qué quedó corriendo (run id) y cierra con /cierre.
```
