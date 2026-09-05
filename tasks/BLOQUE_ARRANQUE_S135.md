# Bloque de arranque S135

## Prompt para pegar al inicio de la sesión (escrito para Claude Fable 5.1)

```
Continuamos VRP Chile desde S134. Ayer la auditoría refutó la hipótesis con la que llegamos: el
cúmulo a 2,5 km del cráter no explica que nuestra magnitud sea ~0,7 de la de MIROVA. En las
pasadas que MIROVA confirma, nuestro cúmulo ya está en el cráter y aun así sacamos menos. Y el
anillo tiene un mecanismo con archivo:línea: `keep_peak` (process_viirs.py:1777-1786) deja un
solo píxel del Test 1, el más caliente en MIR del disco de 3 km, que en un nevado es el borde del
disco, 3 K bajo el fondo global, y lo publicamos como summit «a 0,0 km» con 0,03-0,17 MW en los
11 volcanes. Está en docs/AUDIT_S134.md (§3, §5.3, D19 en MIROVA_DIVERGENCES.md).

POR QUÉ IMPORTA. Es un SDA en producción (CPLT N°372). Ese píxel fabrica un nivel base falso
«Muy Bajo» en el cráter de once volcanes, doce veces al día: un inicio real de 0,1 MW en el
cráter es indistinguible de ese fondo. Pero el mismo mecanismo devuelve pasadas que MIROVA sí
confirma en Lastarria (60 %), Tupungatito (34 %), Isluga (30 %): tocarlo a ciegas destruye
señal real (A83/A84). Por eso S134 no propuso fix: propuso medir.

OBJETIVO. Ejecutar lo que Nicolás haya decidido de la tabla docs/AUDIT_S134.md §D. Si no ha
decidido, la recomendación de S134 es empezar por D1(b): correr el probe de atribución por
etapa en GitHub Actions según experiments/_s134_audit/f3/probe_etapas_ci.md (monkeypatch
read-only sobre first_pass_tests_2_and_3 / second_pass_adjacent / cluster_hotspots /
apply_contextual_test1_filter; 3 pasadas de Villarrica y 3 de Láscar; captura el footprint del
Test 1 de 67 píxeles ANTES de keep_peak, que hoy no se persiste), con criterio pre-registrado, y
sobre ese resultado diseñar el A/B keep_peak OFF/ON estratificado focal/nevado midiendo FN
sobre cat-b real. En paralelo, si Nicolás lo aprueba: D4 (refinar vent_* de Isluga, único Tier A
a 2 decimales) y D5 (indicador de corroboración MIROVA por volcán en el dashboard, sin pipeline).

LÍMITES (no negociables):
- Nada en pipeline/ sin tag defensivo Y confirmación explícita de Nicolás (A45). El probe en CI
  se monkeypatchea en el namespace de pipeline.process_viirs (trampa A89), no edita el módulo.
- Ningún flag se enciende sin A/B con reproceso real (A18) y criterio pre-registrado en las
  unidades del objeto (A91). MISSION.md, las 3 preguntas, antes de cualquier cambio.
- Los TIF y granules no se bajan al PC (disco al 100 %); el probe corre en GitHub Actions con
  los secrets válidos ahí, nunca con el _netrc local (A71).
- Los dos xfail estrictos de tests/test_guard_keep_peak_s134.py son el tripwire: si algo los
  hace pasar, actualizar AUDIT_S134, D19 y el test en el mismo PR.

LEER, en este orden, antes de actuar:
  1. tasks/BLOQUE_ARRANQUE_S135.md                   (este bloque)
  2. docs/AUDIT_S134.md                              (resumen ejecutivo, §3, §5.3, §D)
  3. docs/MIROVA_DIVERGENCES.md                      (D19, al final)
  4. experiments/_s134_audit/f3/probe_etapas_ci.md   (diseño del probe)
  5. experiments/_s134_audit/f3/VERIFICACION.md      (lo que el verificador agregó: la pata de
     magnitud, el popup con tres píxeles, el control dentro-del-volcán)
  6. .github/workflows/_archive/                     (template de probe S110: probe_ndc_assembly)

ESTADO AL ARRANCAR. Suite 1199 passed · 3 skipped · 2 xfailed (deliberados). Tres flags
apagados de S132 siguen apagados. Nada corriendo en CI. Los artefactos del A/B del área
caducan el 2026-09-18/19 pero ya están en ~/ab_area (24/24) y ~/ab_b22 (4/4). Los worktrees
sparse de S134 fueron eliminados; la raíz está en main.

AUTONOMÍA. Nicolás no está mirando en tiempo real. Para lo reversible que siga del plan,
avanza; detente ante lo destructivo, ante pipeline/, y ante las decisiones de §D que él no haya
tomado — esas se le presentan, no se toman. Antes de terminar mira tu último párrafo: si es un
plan o una promesa, hazlo ahora.

ENTREGA. El alcance es el entregable: no lo angostes ni lo ensanches. Lo que encuentres de paso
se reporta como seguimiento. Español de Chile, sin voseo. Primero el fenómeno físico, después
el código, al final los números. Todo número con denominador y ventana (A90); un radio no es
una posición (A93).
```

---

## Lo que S134 dejó hecho (para no re-auditar)

| frente | resultado | dónde |
|---|---|---|
| F1 posición → magnitud → paridad por pasada | criterio NO CUMPLE: razón plana en distancia (0,74/0,62/0,66); el anillo vive en records <0,1 MW sin alerta MIROVA | `experiments/_s134_audit/f1/` |
| F2 TIF de MIROVA misma pasada | el «se corre» de MIROVA era el offset del ancla de grilla (PCC 7,57 km); el «0,21 km» quedó refutado como separación 2D (radio sin acimut); TIF sirve para posición sólo con inner chico y terreno seco | `f2/` |
| F3 mecanismo | `keep_peak` + second pass sin activos (D19); anillo en los 11 incl. Láscar; dos objetos por record; distancias desde el catálogo | `f3/` |
| F4 solape del barrido | f(θ) del ATBD sin parámetros deja los bins en banda (0,94/1,01) pero cola 13,8 % y C2 1/8 → NO ADOPTAR | `f4/` |
| F5 regla C | 7 abiertos · 5 cerrados con guard · 0 sin verificar; P11 corregido (chunk = ventana temporal) | `f5/REGLA_C.md` |
| verificación cruzada | 5 enunciados refutados, 14 hallazgos propios, ninguno cambió un veredicto | `f*/VERIFICACION.md`, AUDIT §5.5 |
| guards | `test_guard_regla_c_s134.py` (14) · `test_guard_anillo_s134.py` (2) · `test_guard_keep_peak_s134.py` (2 xfail) | `tests/` |

## Decisiones que esperan a Nicolás (AUDIT_S134 §D, con recomendación)

D1 keep_peak · D2 second pass sin activos · D3 flip MODIS distance_class · D4 coordenada de
Isluga · D5 corroboración MIROVA en el dashboard · D6 ley de área intermedia · D7 extensión PCC ·
D8 B22 ancho.

## Seguimientos anotados (no arreglar sin pedido)

Popup con tres píxeles (`index.html:2789`) · campos de distancia desde el catálogo · área por
píxel no persistida en el brazo geoloc · relojes del `index.csv` del archivo TIF (otro repo) ·
`audit_metrics.py` y las OCR diurnas · VegStress-v1 caído (Nicolás: no es prioridad) · PAT en
`settings.json` (pendiente rotar).
