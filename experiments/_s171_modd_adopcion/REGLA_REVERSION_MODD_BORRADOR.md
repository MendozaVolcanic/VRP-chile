# Regla de adopción y reversión de la vía «código MIROVA» en MODIS (MOD-D), BORRADOR S171

Estado: **BORRADOR, sin sellar.** Escrito el 2026-10-31 por la coordinadora S171, después de leer el A/B de MOD-D y
antes de cualquier encendido. Se sella con un verificador limpio de otro modelo y la frase de Nicolás; el encendido
pide además el tag defensivo y su sí de A45 (dos frases distintas). Lo marcado **A COMPLETAR** sale de un archivo
citado, no se llena de memoria.

Decisión que lo origina: Nicolás, 2026-10-31, ante «¿Adelantamos MODIS así?» (encender sin esperar la parada de la
sombra, con K de guardia): «hagamos todo lo recomiendas, analiza diferentes perspectivas, tenemos que probar todo y
acercanos a los objetivos» (`tasks/LOOP_OBJETIVOS.md` §6, entrada S171).

Modelo: el paso 9 de la regla con que se adoptó K, `experiments/_s151_prereg_fk_11/REGLA_ADOPCION.md` l. 137 a 175
(main), con las decisiones (a) a (f) de Nicolás del 2026-10-19. Se cambia lo que MODIS pide y nada más.

## 1. Por qué, como geólogo

Hoy MODIS en producción (detector K) pierde más de un tercio de las noches en que MIROVA alerta (recall 62,5 % en
16 noches, audit del 2026-10-26, ventana de 60 días, `data/audit_continuous/latest.json`) y subestima la magnitud
donde más importa: Chillán en erupción queda en 0,56 de MIROVA y pierde tres alertas protegidas de octubre. La vía que
corre el código publicado por MIROVA ganó el A/B pre-registrado de MOD-D (PROPONER ADOPCIÓN, verificador limpio
confirmado; tag `s170-modd-f4-lectura`). La sombra prospectiva de 28 noches daría la prueba más limpia, pero cada mes
de espera es un mes de alertas de MODIS perdidas. Se adopta antes y la sombra pasa a ser guardia: si la vía calla una
alerta protegida que K habría publicado, se vuelve atrás sin esperar a nadie.

El peor caso a vigilar es el mismo que con K, visto desde el otro lado: una señal **débil o de borde de barrido** que
K publica y la vía no. La vía descarta en silencio los gránulos que no cubren el volcán (100 celdas a 45 km, centro a
más de 5 km; hallazgo 171-01 del pre-mortem S171, `D:/vrp-trabajo/temporales/ver_s171_171_01/INFORME.md`); en MODIS
el corte de 5 km aplica (`pipeline/mirova_v750_codigo.py:805-808`, main `478d9c086`).

## 2. Qué se enciende

`ENABLE_MODIS_CODIGO_MIROVA: true` en `pipeline/profiles/mirova_equivalent.yaml` (clave y sección exactas: **A
COMPLETAR** leyendo `pipeline.profile`, nunca el YAML a ojo, A89). Los tres flags de MxD03 quedan como están (se
deciden aparte, programa §12.3 punto 4). VIIRS 375 y VIIRS 750 de producción no cambian.

## 3. La guardia: K de MODIS corriendo aparte

**Opción preferida (a verificar):** que la sombra existente (`pipeline/profiles/sombra_codigo_mirova.yaml`) pase a
correr MODIS con K (vía de MODIS apagada en ese perfil) desde el mismo commit del encendido. Así la sombra de MODIS
queda como K y producción como la vía, con el mismo workflow, la misma ventana y los mismos gránulos. Por qué no
contamina VIIRS: los lectores de sombra comparan sólo lo que lee su vía (regla B7 del verificador del lector de
VIIRS 375, programa §12.6); **comprobar en el lector sellado `s170-v375e-lector` que un cambio en las claves de MODIS
no marca régimen nuevo en VIIRS 375** antes de elegir esta opción. Alternativa: un perfil de guardia nuevo, aislado
(`data_subdir` propio, A47), sumado al workflow de la sombra; cuesta tiempo de runner (pre-mortem 171-03: el paso
tiene 75 min).

La excepción al congelamiento de `pipeline/` (§12.6) se anota en la bitácora con el commit y el sensor (MODIS).

## 4. Reversión e investigación

- **Cuenta desde el encendido** (`CAMBIO_DETECTOR_MODIS_UTC`, la hora del merge al segundo). Lo anterior se informa
  como retrospectivo y no dispara (decisión (b) de K).
- **Unidad: la pasada** (decisión (a) de K).
- **Reversión inmediata, pre-autorizada:** una alerta protegida de MODIS (lectura A, 1 MW o más, regla SN de D-9) que
  MIROVA publica, la guardia K publica y producción (la vía) calla, confirmada en la cabecera de la imagen de MIROVA.
  Se ejecuta con `git revert` del PR de encendido (nunca un reset), la hace la sesión que la detecte, abre un issue y
  avisa a Nicolás el mismo día. MODIS no tiene canal de Suomi NPP, así que N-3 no aplica.
- **Investigación, sin reversión automática:** (i) alertas Muy Bajo (sobre 0,05 MW y bajo 1 MW) que MIROVA publica,
  la guardia publica y producción calla, con cota de pérdida esperada **A COMPLETAR** desde el A/B de MOD-D
  (`experiments/_s166_modd_f4/` y `experiments/_s168/modd_f4_candado/lectura_ab2/resultado_f4.json` en la rama
  `claude/s170-modd-f4-procedencia`); (ii) publicación de MODIS en negativos limpios por sobre lo que midió el A/B
  (cota **A COMPLETAR** desde el mismo resultado); (iii) pasadas que la guardia registra y producción no (el descarte
  de 171-01), contadas por semana.
- **Pasadas juzgadas y rachas:** como (d) y (f) de K, en un `sombra_pasadas_juzgadas_modis.json` junto a esta regla.
- **Duración:** hasta ver **29 protegidas A nocturnas de MODIS** en la guardia o 120 días, lo que ocurra primero
  (misma potencia que K: una pérdida de una de cada diez se ve con 95 %). Cumplido el plazo, una candidata se sigue
  informando pero ya no está pre-autorizada: decide Nicolás (decisión (e) de K). Riesgo declarado: MODIS ve menos
  protegidas que VIIRS (16 noches con alerta en 60 días en el audit del 2026-10-26), así que lo probable es que mande
  el plazo de 120 días; se informa cuántas hubo.

## 5. Lista del PR de encendido (sobre el modelo del paso 8 de K)

- el flag, con un guard que lo fije;
- los tests que hoy fijan el flag apagado, actualizados diciendo por qué (**A COMPLETAR** con `grep -rn
  ENABLE_MODIS_CODIGO_MIROVA tests/`);
- el cambio de la guardia (§3) y su prueba;
- el auto-audit: decidir en el PR si las bandas de MODIS se recalibran o se acepta que salten, antes de ver el issue;
- la ficha `docs/FICHA_SDA_VRP_CHILE.md` (cambia el detector de MODIS de un SDA en producción) y las marcas A113 donde
  MODIS aparece como K (`docs/MISSION.md`, `CLAUDE.md`, `docs/MIROVA_DIVERGENCES.md`);
- una marca visible de la fecha del cambio en las tres vistas (`index.html`, `diario.html`, `mosaico.html`): con la
  vía la magnitud de MODIS sube y aparecen alertas que K callaba; en Chillán ese escalón no debe leerse como «la
  erupción crece»;
- el aviso a los consumidores (OVDAS, Integracion_Plataformas, `MAPA_WORKSPACE.md`);
- tag defensivo `pre-s171-adopcion-modd` en el commit de main previo, empujado, y el sí de Nicolás antes del merge
  (A45), que incluye la pre-autorización de la reversión de §4.

## 6. Pre-mortem (borrador)

Si la adopción está mal, se vería como: (a) una protegida que la guardia publica y producción calla (dispara §4); (b)
la publicación de MODIS en negativos limpios subiendo sobre lo medido; (c) el job del NRT pasando su tiempo (la vía
cuesta 1,1 a 1,25 veces K, pre-mortem 171-03); (d) pasadas de borde que producción deja de registrar (171-01).
