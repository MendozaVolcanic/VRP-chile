# caminos.md: por dónde podría estar mal cada afirmación de la regla borrador

Verificador VR, S173. Escrito ANTES de abrir ningún archivo citado por la regla. Sólo leí el prompt
(`D:/vrp-trabajo/temporales/s173_aud/prompts/verificador_vr.txt`) y la regla misma
(`origin/loop/activo:experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md`, copia en
`D:/vrp-trabajo/temporales/s173_aud/vr/regla_copia_origen_loop_activo.md`, sha256 77f7f37c...).
Las líneas (l.) son de esa copia.

## Caminos generales (aplican a toda afirmación de la regla)

- G1. El nombre citado no existe en la punta de B (c9525f994) o existe con otro nombre: la regla se
  escribió contra `main 478d9c086` y contra S172 a medio camino; el PR final pudo renombrar.
- G2. La línea citada se corrió: `archivo:línea` escrito contra un commit anterior (A101).
- G3. El flag se lee de otro lado que el YAML: `pipeline.profile` resuelve `extends` un solo nivel y
  lee `thresholds`; un perfil derivado puede sobrescribir. Vara: `VRP_PROFILE=... python -c` (A89).
- G4. La cota numérica viene de un archivo que no está en ninguna rama o cuyo sha256 no coincide con
  el que la regla cita; o el script que la produjo no se puede re-correr.
- G5. El denominador o la ventana no están declarados (A90): un «12 discordantes» sin saber de
  cuántas pasadas no permite fijar «2 en 120 días».
- G6. La regla deja un caso sin decisión (caso ciego): la regla dice qué dispara pero no qué pasa
  cuando falta el insumo (sin record, guardia muerta, referencia sólo VIIRS, cero pares, upgrade NRT a
  estándar que reescribe el record y cambia `processed_utc`).
- G7. Dos lectores decidirían distinto: términos sin definir («publica» para la guardia, cuyo perfil no
  lo lee el tablero; «calla»; «confirmada en la cabecera de la imagen de MIROVA»; quién confirma; qué
  pasa si la imagen no existe).
- G8. La acción pre-autorizada no es ejecutable tal cual: «`git revert` del PR de encendido» supone
  un merge commit o un squash identificable; si PR A y PR B se mergean juntos o por separado cambia
  qué se revierte; conflictos sobre el main del día; tests que fijan el flag en True quedarían rojos
  o se revierten con él.
- G9. El texto conserva dos versiones (original + corrección S172) sin decir cuál rige: un lector
  podría aplicar la versión tachada.
- G10. La copia local atrasada: `origin/loop/activo` vs el árbol local de la coordinadora; la regla
  que se selle podría no ser la que leí (sha256 anotado para fijarla).

## Por afirmación (l. de la copia)

- l. 3 «Escrito el 2026-10-31»: podría no coincidir con el commit que la introdujo (git log). Bajo.
- l. 10 cita de Nicolás en `tasks/LOOP_OBJETIVOS.md` §6: la frase podría no estar verbatim o no en §6.
- l. 12 `experiments/_s151_prereg_fk_11/REGLA_ADOPCION.md` l. 137 a 175 «paso 9», decisiones (a) a
  (f) del 2026-10-19: las líneas pueden no ser el paso 9; las letras (a)-(f) que la regla usa después
  (l. 94, 95, 110, 113) pueden no corresponder a lo que dice el modelo.
- l. 17-18 recall 62,5 % en 16 noches, audit 2026-10-26, 60 días, `data/audit_continuous/latest.json`:
  el `latest.json` de hoy ya no es el del 26-oct (corpus vivo, A90); el 62,5 % puede ser por noche o
  por pasada; «MODIS» puede ser la suma de Terra+Aqua o por plataforma.
- l. 19 Chillán 0,56 y «tres alertas protegidas de octubre»: sin fuente citada; la ventana de octubre
  puede estar truncada; SOSPECHA hasta encontrar el script.
- l. 20-21 A/B MOD-D PROPONER ADOPCIÓN, tag `s170-modd-f4-lectura`: el tag puede no existir o apuntar
  a un commit sin ese veredicto.
- l. 21 «sombra prospectiva de 28 noches»: puede ser 28 noches de VIIRS, no de MODIS.
- l. 26-28 descarte de gránulos (100 celdas a 45 km, centro a más de 5 km), `mirova_v750_codigo.py:805-808`
  en `main 478d9c086`: en la punta de B la línea puede haberse movido; el corte puede ser otro para
  MODIS (grilla de 1 km = 51 celdas, no 100 de 450 m); el informe `ver_s171_171_01` puede no estar.
- l. 32-34 `profile.py:909` y l. 79: líneas corridas en B; el flag puede leerse también de otra sección.
  La regla misma dice «falta comprobarlo importando pipeline.profile» (A89): si sigue sin comprobar,
  la regla se selló con una verificación pendiente.
- l. 34-35 «tres flags de MxD03», programa §12.3 punto 4: nombres y sección a comprobar.
- l. 39 `sombra_codigo_mirova.yaml`: puede no tener `enable_modis_codigo_mirova: true` hoy.
- l. 42-44 regla B7, programa §12.6, tag `s170-v375e-lector`: comprobar existencia; el lector sellado
  hoy es el RE-sellado (`s172-v375e-lector-resellado`), así que lo que dice de `SHA_SELLO_LECTOR`
  l. 63-77, `RAIZ` l. 47, `RUTAS_REGIMEN`, `PERFILES_REGIMEN` puede estar corrido o cambiado.
- l. 50-52 `.github/workflows/sombra-codigo-mirova.yml` l. 110 `assert ... ENABLE_MODIS_CODIGO_MIROVA`:
  línea y aserción a comprobar; si PR B la cambió, el S8 del lector re-sellado podría dispararse.
- l. 69 ventana P empieza 2026-11-03; l. 87 «~19 UTC»: fuente a localizar.
- l. 71-72 y l. 139 pre-mortem 171-03, «75 min», «1,1 a 1,25 veces K»: fuente a localizar (puede estar
  fuera del repo, en D:/vrp-trabajo/temporales).
- l. 74-77 consumidores de los flags «sólo process_modis.py y process_viirs_mod.py» (git grep en
  origin/main): en B hay más consumidores (guardia, workflow, tests, tablero): la afirmación envejeció.
- l. 80 rama `claude/s172-v375e-relector` y worktree `s172-relector`: pueden no existir ya.
- l. 82-87 `guardia_k_modis.yaml` con `extends: mirova_equivalent`, `enable_modis_codigo_mirova: false`,
  `data_subdir` propio, workflow nuevo: (a) ¿existe con ese nombre en B?; (b) `extends` un solo nivel:
  ¿hereda lo que debe?; (c) ¿el workflow nuevo corre sólo MODIS y en qué cron?; (d) ¿está en
  `PERFILES_REGIMEN`/`RUTAS_REGIMEN` del lector re-sellado? (la regla dice que no).
- l. 93 `CAMBIO_DETECTOR_MODIS_UTC`: ¿existe esa constante en B? ¿Dónde? ¿Qué valor (vacío hasta el
  merge)? ¿Quién la llena «al segundo»?
- l. 95 «Unidad: la pasada»: ¿cómo se parea una pasada de MODIS con la fila de MIROVA (Terra/Aqua,
  hora)? Sin instrumento, dos lectores parean distinto.
- l. 96-97 condición de disparo: cuatro cláusulas (MIROVA publica, guardia publica, producción calla,
  cabecera de imagen). Caminos: (a) «publica» del tablero no aplica a la guardia (data_subdir propio,
  el tablero no lo lee); (b) la imagen de MIROVA puede no existir o estar congelada (los TIF de MIROVA
  están congelados desde el 2026-09-22 según la memoria del proyecto: a VERIFICAR hoy); (c) no dice qué
  pasa si MIROVA publica y la guardia TAMBIÉN calla (no dispara: bien, pero debe decirlo); (d) no dice
  qué pasa si la guardia no tiene record de esa pasada (guardia muerta); (e) no dice si una pasada
  diurna cuenta (MODIS diurno: MIR sólo nocturno en el pipeline).
- l. 98 «`git revert` del PR de encendido»: ver G8; además «la hace la sesión que la detecte» sin decir
  cómo se detecta (¿hay lector de MODIS? ¿`sombra_pasadas_juzgadas_modis.json` existe?).
- l. 99 «MODIS no tiene canal de Suomi NPP, así que N-3 no aplica»: N-3 a localizar en el modelo de K.
- l. 100-109 cotas: `resultado_f4.json` en rama `claude/s170-modd-f4-procedencia`, sha256
  `312e2050...4129d`: (a) la rama puede no existir o estar borrada tras merge; (b) el sha256 puede no
  coincidir; (c) los conteos 12/10/2, 42/39/3, neto -44, B 53, p_gana [1, 10001] a reproducir del JSON;
  (d) la ventana «marzo a octubre de 2026» a comprobar en el JSON; (e) «p_gana [1, 10001]» es un
  intervalo raro (¿1 de 10001?); (f) el denominador `bajo1` dicho SIN DATO: entonces la cota «2 en
  120 días» no es proporcional a nada (A90); (g) «propuesta, la fija Nicolás» deja el número sin fijar:
  una regla sellada con «propuesta» no decide sola.
- l. 110 `sombra_pasadas_juzgadas_modis.json`: ¿existe? ¿Quién lo escribe?
- l. 111-112 «29 protegidas A nocturnas» y «una de cada diez se ve con 95 %»: 1-0,9^29 = 0,953, a
  calcular; «nocturnas»: ¿la regla SN y la lectura A filtran por noche? ¿Cómo se cuenta una protegida
  que la guardia ve: por pasada o por noche?
- l. 114 «16 noches con alerta en 60 días»: mismo `latest.json`.
- l. 119-123 tests citados con líneas: `test_mirova_modis_codigo_s164.py` l. 54-81 y 321-426,
  `test_guard_declarado_vs_efectivo_s131.py` l. 158, `test_guard_perfiles_congelados_s153.py`: en B
  pueden haber cambiado (el PR B los debía actualizar).
- l. 126-127 ficha SDA y marcas A113: ¿PR B las trae?
- l. 128 marca en las tres vistas: ¿PR B la trae en las tres o sólo en `index.html`?
- l. 132 tag `pre-s171-adopcion-modd`: ¿existe ya? Si no, está pendiente (bien, es pre-merge).
- l. 5 «Lo marcado A COMPLETAR»: no veo ninguna marca «A COMPLETAR» en el texto: o se completaron todas
  o la frase quedó huérfana.

## Lo que NO voy a poder medir con certeza (declararlo como SIN DATO si pasa)

- El comportamiento real de la guardia en Actions (no despacho workflows).
- La «cabecera de la imagen de MIROVA» de una pasada futura.
- El valor de `CAMBIO_DETECTOR_MODIS_UTC` después del merge (aún no hay merge).

## Controles del instrumento

- Control positivo de existencia: buscar un nombre que SÉ que existe (`ENABLE_MODIS_CODIGO_MIROVA` en
  `pipeline/profile.py`) con el mismo comando que uso para los nombres dudosos.
- Control positivo de las cotas: recontar del JSON con un script propio y comprobar que un conteo
  cambiado (p. ej. filtrar otra clase) da otro número.
- Control de la reversión: el revert simulado debe dejar `ENABLE_MODIS_CODIGO_MIROVA == False` leído
  por `pipeline.profile` (no sólo el YAML).

---
sha256 (antes de esta nota): 60e854bf9e74059b31722b41efb11584c8c198ee8f3dfbc1c94ba6852f7f28a5
hora del servidor: Date: Mon, 02 Nov 2026 12:22:28 GMT
