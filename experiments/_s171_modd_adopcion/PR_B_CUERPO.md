# Borrador del cuerpo del PR B: encender la vía «código MIROVA» en MODIS (S172)

Borrador escrito por el implementador de S172. No es el PR: lo abre la coordinadora cuando Nicolás dé las dos frases
(el sí de A45 con la pre-autorización de abajo, y la frase de merge). Rama `claude/s172-modd-flip`, nacida de la punta
de `claude/s172-modd-encendido` (PR A). Tag defensivo `pre-s171-adopcion-modd` (`d3cd0b2ae`, ya empujado).

⚠️ **S173, ronda 3 (segunda pasada de auditoría, `experiments/_s173_aud/` en `loop/activo`)**: el PR B se abre desde la
rama NUEVA **`claude/s173-modd-flip`**, nacida de la punta nueva de A (`f8f37cec9`). La rama `claude/s172-modd-flip`
(`c9525f994`) queda como historia y no se abre. Qué cambió respecto de lo que dice el resto de este borrador:

- **Pasaron al PR A** (ya no son de este PR): la vigilancia de la sombra de K sin los records de la vía (MA172-101),
  `esAnclaHonesta` del tablero (MA172-102), la enmienda de `test_no_modifica_la_vigilancia_de_k` y las declaraciones
  `enable_modis_codigo_mirova: false` de `experimental`, `experimental_ndc_focus` y `_s146_ab_control` (hallazgos 161,
  162 y V1-04: así un revert de este PR no deja a esos lectores interpretando mal los records de la vía). Este PR queda
  con el flag de producción, las pruebas que lo fijan, `test_guard_adopcion_k_s153`, la ficha v1.18, las marcas A113 y
  este borrador.
- **En el PR A, además**: el audit semanal ya no cae cuando la vía publica MODIS en una noche con alerta (205,
  bloqueante: `VIA_MODIS` en `REGIMENES`) y avisa que MODIS queda «sin juzgar» mientras la vía no junta 15 noches con
  alerta (206; V2 midió 4,6 a 7,5 semanas). El issue semanal lo lista entre los sensores sin juzgar: que MODIS no salga
  en la línea de recall esas semanas no quiere decir que mejoró. Corrige el punto del §5 que decía que «se acepta que
  el issue semanal salte»: en recall se calla, y ahora lo dice.
- **En este PR**: el guard `tests/test_guard_modis_codigo_mirova_encendido_s172.py` acepta `sombra_34` de #932 cuando
  su YAML existe (201): ya no importa cuál de los dos entra segundo.
- **Órdenes de merge, medidos con `git merge-tree` sobre `origin/main` `47cdc446f` y las puntas finales** (A
  `f8f37cec9`, B `96b05bcd8`, #932 `28183712a`): A, B, #932 y A, #932, B, con merge commit y con squash, salen los
  cuatro limpios y con el mismo árbol (`dba320e87`); el revert de B (`git revert -m 1` del merge, o del squash) sale
  limpio en los cuatro y deja exactamente el árbol del mismo orden sin B (`c8ca164a7`). El choque del squash que
  describía la ronda 2 (203) ya no ocurre, porque este PR no toca `tests/test_vigilancia_guardia_modis_s172.py`.
- **Pruebas** (rutas explícitas, no la suite): A 813 pasan; B 821; A+B+#932, 922; 0 fallas en las tres
  (`INFORME_IMPLEMENTADOR.md`, ronda 3).
- **Quedan abiertos, para Nicolás**: 207 (la marca del tablero y la frontera del audit fechan el encendido por la
  primera observación de la vía, hasta ~8 a 9 días antes del merge; la vigilancia por la primera escritura; la regla
  cita `CAMBIO_DETECTOR_MODIS_UTC`, que no existe), 208 (el revert de este PR choca si otro PR toca las líneas vecinas
  del flag en `mirova_equivalent.yaml`: el revert sobre el `main` del día del revert sigue SIN VERIFICAR), 209 y V2-02
  (una excepción de la vía que no sea la falta de pyproj deja MODIS mudo con el NRT en verde; lo ve la vigilancia de la
  guardia a los 3 días por volcán).

---

## Título propuesto

S172 MOD-D: encender la vía «código MIROVA» en MODIS (producción), con K de guardia

## Por qué, como geólogo

Con el detector K, MODIS pierde más de un tercio de las noches en que MIROVA alerta (recall 62,5 % en 16 noches, audit
del 2026-10-26, #915) y en Nevados de Chillán, con el domo activo, marca 0,56 de la magnitud de MIROVA y pierde tres
alertas protegidas de octubre. La vía que corre el código publicado por MIROVA ve el volcán como lo ve MIROVA: el
gránulo pasado a su grilla de 1 km con la geolocalización de 1 km del MxD03, su detector, su fondo rellenado con la
regla de MATLAB y la suma de todos los alertados. Ganó el A/B pre-registrado de MOD-D (PROPONER ADOPCIÓN, verificador
limpio confirmado, tag `s170-modd-f4-lectura`). Nicolás decidió el 2026-10-31 no esperar la sombra de 28 noches: se
enciende ahora y K queda corriendo aparte como guardia. Si la vía calla una alerta protegida que K habría publicado, se
revierte el mismo día.

El peor caso a vigilar es una señal débil o de borde de barrido que K publica y la vía no: la vía descarta en silencio
los gránulos que no cubren el volcán (100 celdas a 45 km, centro a más de 5 km; hallazgo 171-01 del pre-mortem S171).

## Qué cambia

- `enable_modis_codigo_mirova: true` bajo `thresholds:` de `pipeline/profiles/mirova_equivalent.yaml` (leído desde
  `pipeline.profile`: `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p;
  print(p.ENABLE_MODIS_CODIGO_MIROVA)"` da `True`).
- `experimental` y `experimental_ndc_focus` declaran `enable_modis_codigo_mirova: false`: los dos heredan de
  producción y el laboratorio (congelado en C0, la sombra de K que lee `scripts/vigilancia_sombra.py`) habría pasado a
  la vía en MODIS. La guardia (`guardia_k_modis`, PR A) ya la declara apagada y la sombra (`sombra_codigo_mirova`) la
  tiene encendida a propósito. Los brazos viejos de A/B (perfiles `_s*` y similares) no se tocan: sus workflows son de
  despacho manual y ya corrieron (lista en `INFORME_IMPLEMENTADOR.md`).
- Pruebas: las que fijaban el flag apagado, actualizadas con el porqué (`tests/test_mirova_modis_codigo_s164.py`,
  `tests/test_sombra_codigo_mirova_s167.py`), y el guard nuevo
  `tests/test_guard_modis_codigo_mirova_encendido_s172.py` (producción encendida, cada perfil vivo con su valor).
- Ficha `docs/FICHA_SDA_VRP_CHILE.md` v1.18 y marcas A113 en `docs/MISSION.md`, `CLAUDE.md` y
  `docs/MIROVA_DIVERGENCES.md`; la cabecera FICHA de `pipeline/process_modis.py` (sólo el comentario, el AST no
  cambia) dice ahora que la vía está encendida.
- El ancla de las pruebas escritas sobre la producción de antes de K (`pipeline/profiles/_s146_ab_control.yaml`,
  `tests/produccion_pre_k.py`) declara la vía apagada, y los arneses que miden K de MODIS (`tests/arnes_mxd03_s165.py`,
  `tests/arnes_sin_dato_s165.py`, `tests/arnes_sintetico_s142.py`, fixture en `tests/test_process_modis_core.py`) la
  fijan apagada: el encendido rompía 33 pruebas que miden K (recuento de la mini auditoría, MA172-108; el informe
  decía 28), todas verdes en el PR A y arregladas aquí.
- S172 ronda 2 (mini auditoría): `scripts/vigilancia_sombra.py` deja de contar como K los records MODIS de la vía
  (MA172-101: si no, una pérdida de la vía abría el issue que pide revertir K); el tablero reconoce
  `final_hotspot_source = "codigo_mirova"` como ancla del marcador, en una sola función `esAnclaHonesta` (MA172-102);
  `tests/test_guard_adopcion_k_s153.py` espera la vía en la diferencia del laboratorio (MA172-103).
- Requisito del PR A, que tiene que estar en `main` antes: pyproj en todo workflow que corre un perfil con vía (sin
  él, MODIS quedaba mudo con el NRT en verde, MA172-201) y los arreglos de la vigilancia de la guardia.
- Nada más: VIIRS 375 y VIIRS 750 de producción no cambian, los tres flags de MxD03 siguen apagados, no hay reproceso
  histórico (la vía corre desde el merge hacia adelante; ojo: el upgrade de NRT a estándar re-escribe con la vía pasadas
  de hasta ~4,5 días antes del merge, MA172-206, así que el escalón de MODIS empieza unos días antes de la fecha del
  merge).

## Pre-autorización de la reversión (§4 de la regla, para el sí de A45)

Texto propuesto para que Nicolás lo confirme junto con su sí de A45:

> Pre-autorizo revertir este PR con `git revert` (nunca un reset) el mismo día en que la vigilancia de la guardia
> (`scripts/vigilancia_guardia_modis.py`, issue «Guardia K de MODIS: candidata a reversion») informe una alerta
> protegida de MODIS (lectura A, 1 MW o más, regla SN de D-9) que MIROVA publica, la guardia K publica y producción
> (la vía) calla, posterior al encendido y dentro del plazo (las primeras 29 protegidas A nocturnas de MODIS vistas en
> la guardia o 120 días desde el encendido, lo que ocurra primero), confirmada en la cabecera de la imagen de MIROVA.
> La hace la sesión que la detecte, abre un issue y me avisa el mismo día. Fuera de plazo una candidata se sigue
> informando pero ya no está pre-autorizada: decido yo. MODIS no tiene canal de Suomi NPP, así que N-3 no aplica.

Investigación sin reversión automática (las cotas son propuestas del borrador de la regla y las fija Nicolás al
sellarla): (i) más de 2 alertas Muy Bajo (sobre 0,05 MW y bajo 1 MW) que MIROVA publica, la guardia publica y
producción calla, en el plazo; (ii) más de 3 publicaciones de producción en negativos limpios donde la guardia no
publica, en el plazo; (iii) las pasadas que la guardia registra y producción no se informan por semana, sin cota.
Además, antes del encendido guardia y producción tienen que publicar lo mismo (nulo de la guardia), y una protegida
anterior al encendido cuyo record de producción ya es de la vía pide investigar.

Lo que el revert deja en pie: todo el PR A (guardia, su vigilancia, el detector VIA_MODIS del audit, la marca del
tablero). Lo que no deshace: los records MODIS ya escritos por la vía en `data/mirova_equivalent/` (igual que con K en
S157, marca (c) de `docs/MISSION.md`); tras un revert, el audit cuenta los records MODIS nuevos de K en noches de la
vía como «K en noche VIA_MODIS» y la marca del tablero sigue en la primera pasada de la vía. SIN VERIFICAR: que el
revert de este PR salga limpio sobre el `main` del día del revert (se simuló sólo sobre la punta de esta rama, ver el
informe).

## Lista del §5 de la regla

- [x] el flag, con un guard que lo fije (`tests/test_guard_modis_codigo_mirova_encendido_s172.py`);
- [x] los tests que fijaban el flag apagado, actualizados diciendo por qué (`tests/test_mirova_modis_codigo_s164.py`
      l. 71 a 93; `tests/test_sombra_codigo_mirova_s167.py`, prueba 1; `tests/test_guard_perfiles_congelados_s153.py` y
      `tests/test_guard_declarado_vs_efectivo_s131.py` revisados y verdes sin cambios);
- [x] el cambio de la guardia y su prueba (PR A: perfil, workflow, revisión y vigilancia, con sus pruebas);
- [x] el auto-audit: decidido en el PR A, las bandas de MODIS NO se recalibran (A115); se acepta que el issue semanal
      salte y se anota en #915 (la nota la escribe la coordinadora: este borrador no toca issues);
- [x] la ficha `docs/FICHA_SDA_VRP_CHILE.md` (v1.18) y las marcas A113 (`docs/MISSION.md`, `CLAUDE.md`,
      `docs/MIROVA_DIVERGENCES.md`);
- [x] una marca visible de la fecha del cambio en las tres vistas (PR A, `frontend/cambio_detector.js`, desde los
      datos);
- [x] el aviso a los consumidores (texto abajo; no se envía desde aquí);
- [ ] el sí de Nicolás antes del merge (A45), con la pre-autorización de la reversión de arriba. Tag defensivo
      `pre-s171-adopcion-modd` ya empujado.

Orden recomendado: PR A primero (inerte con el flag apagado), dejar correr la guardia unos días para medir su nulo,
y recién entonces el PR B. El re-sellado del lector de V375-E por claves (rama `claude/s172-v375e-relector`) hace que
este PR no marque régimen nuevo en VIIRS 375: el S8 compara los perfiles sin `enable_modis_codigo_mirova` y el perfil y
el workflow de la guardia no están en `PERFILES_REGIMEN` ni en `RUTAS_REGIMEN`.

## Aviso a los consumidores (borrador; no editado ni enviado desde aquí)

Para OVDAS (texto para el canal que use Nicolás):

> Desde el [fecha del merge] la serie de MODIS del tablero VRP Chile viene de un detector nuevo: el que el grupo
> MIROVA publicó en su código. VIIRS no cambia. Desde esa fecha la magnitud de MODIS sube y aparecen alertas que antes
> no salían, porque el detector anterior perdía más de un tercio de las noches en que MIROVA alertaba. Un escalón en la
> serie de MODIS en esa fecha es un cambio del detector, no del volcán: en Nevados de Chillán no quiere decir que la
> erupción crece. El tablero lo marca con una línea naranja y un aviso. Si el detector nuevo llegara a perder una
> alerta de 1 MW o más que el anterior habría visto, se vuelve atrás el mismo día y se avisa.

Para Integracion_Plataformas (nota de diseño de esa carpeta):

> VRP Chile, MODIS: desde el [fecha del merge] los records MODIS de `data/mirova_equivalent/` llevan
> `via_codigo_mirova: true` (vía «código MIROVA»); si la vía no puede correr en un gránulo, el record es de K y lo dice
> en ese mismo campo (`"sin_mxd03"`, `"sin_grilla"`, `"geo_distinta"`). Cualquier serie que cruce esa fecha mezcla dos
> detectores de MODIS. K de MODIS sigue corriendo como guardia en `data/guardia_k_modis/` (no operacional).

Para `MAPA_WORKSPACE.md` (ficha de VRP Chile, campo de salida consumible y salud):

> 2026-11-xx: MODIS de producción pasa a la vía «código MIROVA» (S172, PR B). Nuevas salidas no operacionales:
> `data/guardia_k_modis/` (guardia K de MODIS, workflow `guardia-k-modis.yml`, diario 17:40 UTC) y
> `data/audit_continuous/guardia_modis_latest.json` (vigilancia, `vigilancia-guardia-modis.yml`, issues «Guardia K de
> MODIS: ...»). Pipeline zombie a vigilar: guardia sin records frescos = issue de vigilancia ciega.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
