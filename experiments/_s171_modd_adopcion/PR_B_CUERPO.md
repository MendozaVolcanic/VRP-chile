# Borrador del cuerpo del PR B: encender la vía «código MIROVA» en MODIS (S172)

Borrador escrito por el implementador de S172. No es el PR: lo abre la coordinadora cuando Nicolás dé las dos frases
(el sí de A45 con la pre-autorización de abajo, y la frase de merge). Rama `claude/s172-modd-flip`, nacida de la punta
de `claude/s172-modd-encendido` (PR A). Tag defensivo `pre-s171-adopcion-modd` (`d3cd0b2ae`, ya empujado).

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
- Nada más: VIIRS 375 y VIIRS 750 de producción no cambian, los tres flags de MxD03 siguen apagados, no hay reproceso
  histórico (la vía corre desde el merge hacia adelante).

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
