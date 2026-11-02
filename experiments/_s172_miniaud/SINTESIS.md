# Mini auditoría S172: encendido de la vía «código MIROVA» en MODIS (PR A y PR B)

## Encabezado

- Hora del servidor: lanzamiento 2026-11-02 00:41 UTC, síntesis 2026-11-02 01:47 UTC (header `Date` de `gh api -i repos/MendozaVolcanic/VRP-chile`).
- Commits medidos:
  - base main `d3cd0b2aeee70b99fbc5bd90e5fd2b0dff284f54` (tag `pre-s171-adopcion-modd`); origin/main al lanzar: `14fb62030` (un commit de sincronización de datos);
  - PR A `claude/s172-modd-encendido` en `c83882fcfdbd7fdb441e61a54a03c8f5fb3707b2`;
  - PR B `claude/s172-modd-flip` en `b4282319446cfea944aa1a4621c0fec7da8649a0`. Su primer commit cuelga de `da67fa417`, no de la punta de A: c83882fcf, que sólo trae el informe del implementador y la salida de pruebas, no está en la historia de B;
  - re-sellado del lector de V375-E en `aa3fdcf1e`.
- Modelos y esfuerzos:
  - Se pidieron tres auditores Opus a esfuerzo alto. Los tres declaran haber corrido como Opus 5.5 a esfuerzo **bajo**, que fijó el arnés.
  - Se pidieron tres verificadores Sonnet a esfuerzo alto. V2 y V3 declaran Sonnet 5.5 a esfuerzo **bajo** (el arnés lo fijó). V1 declara esfuerzo alto.
  - Queda registrado así: el esfuerzo que vale es el declarado, no el pedido.
- Consumo (lo que informa el harness):

  | Agente | Tokens | Llamadas a herramientas | Duración |
  |---|---|---|---|
  | F1 | 407 k | 132 | 48 min |
  | F2 | 397 k | 98 | 25 min |
  | F3 | 408 k | 103 | 21 min |
  | V1 | 288 k | 56 | 9 min |
  | V2 | 311 k | 63 | 12 min |
  | V3 | 301 k | 62 | 12 min |

  Total: unos 2,1 M tokens de subagentes. Llamadas a la API de GitHub: cada agente se mantuvo bajo el tope de 30.
- Prompts armados: D:/vrp-trabajo/temporales/s172_miniaud/prompts/.
  - Auditores (sha256): f1 `abcb8d15…`, f2 `642b9b43…`, f3 `ca533a12…`.
  - Verificadores (sha256): v1 `acb6e6cf…`, v2 `abe6e1f6…`, v3 `83f96bf7…`.
  - `grep -nE "«[A-Z_]+»"` dio 0 líneas en los seis.
- caminos.md de los verificadores, escritos antes de abrir lo citado (sha256 del contenido previo a la nota de cierre):

  | Verificador | sha256 | Ruta |
  |---|---|---|
  | V1 | `2cb9a5f5…` | D:/vrp-trabajo/temporales/s172_miniaud/v1/caminos.md |
  | V2 | `0f7a7ac5…` | D:/vrp-trabajo/temporales/s172_miniaud/v2/caminos.md |
  | V3 | `ca5b99de…` | D:/vrp-trabajo/temporales/s172_miniaud/v3/caminos.md |

- Worktrees: los dos se crearon y se borraron al final con `git worktree remove`. `D:/vrp-trabajo/worktrees/s172-miniaud-b` quedó limpio en b42823194 antes de borrarlo. `D:/vrp-trabajo/worktrees/s172-miniaud-rev`, el desechable de la reversión, guardaba los commits de la simulación y no se empujó nada. No hubo commit, push, merge ni tags en el repo, ni se despachó ningún workflow.
- Dato del coordinador durante la corrida: «`extends` resuelve un solo nivel». Se verificó como ítem DATO-COORD en V3.
- Qué NO se miró:
  - Ninguna vista se abrió en un navegador real; las vistas se ejecutaron con node.
  - No hay corrida real de la vía en el runner de GitHub: el costo de la vía en tiempo del NRT es SIN DATO.
  - No se vio el CI del PR B en GitHub.
  - V2 no re-corrió la simulación de reversión: el «revert limpio» lo verificó sólo F2 (Opus).
  - El detector VIA_MODIS del audit semanal se miró sólo en F3 (MA172-304).

## En una pantalla

**Veredicto: LISTO CON CAMBIOS.** Mergear hoy el PR B tal como está deja a MODIS mudo en producción en los 11 volcanes, con el NRT en verde.

1. **Bloqueante (gravedad 5).** Lo encontraron los tres frentes y lo confirmaron V2 y V3; lo comprobé también en `nrt.yml` l. 140 a 143.
   - El NRT no instala `pyproj`, y la vía lo importa en cada gránulo MODIS (`pipeline/mirova_v750_codigo.py` l. 204).
   - `scripts/run_pipeline.py` l. 279 y 280 atrapa la excepción: no se escribe record, la vía no cae a K y el workflow sale verde.
   - Arreglo: agregar pyproj en `nrt.yml`, `backfill-tier-a.yml` y `reproc-chunked.yml`, en el PR A.
2. **Bloquean el PR B (gravedad 2 y 3).**
   - `scripts/vigilancia_sombra.py` l. 432 toma los records de la vía por K. Puede abrir un issue que pide revertir K (#850) por una pérdida de la vía.
   - El tablero no reconoce `final_hotspot_source = "codigo_mirova"`: el marcador de un record summit de Chillán cae a km del cúmulo.
   - `tests/test_guard_adopcion_k_s153.py` queda rojo en la punta de B.
3. El PR A es inerte con el flag apagado; nada lo bloquea. Su vigilancia tiene huecos que conviene cerrar antes del encendido (MA172-202, 208, 204 y 206), porque es la red de la regla de reversión.
4. El revert del PR B sale limpio en las cuatro simulaciones de F2: merge commit y squash, sobre la base y sobre origin/main. No lo re-verificó un segundo modelo. Exige mergear A antes que B.

## Hallazgos verificados

Todos los encontró Opus (auditores F1, F2 y F3). El veredicto es de Sonnet (V1, V2 y V3). La columna «bloquea» es la del verificador.

| ID | Encontró | Verificó | Hallazgo | Veredicto | Grav. aud. → verif. | Bloquea |
|---|---|---|---|---|---|---|
| MA172-201 = MA172-301 = VMA172-301 | Opus F2, Opus F3 (V3 lo halló además como propio) | Sonnet V2, V3 | El NRT no instala pyproj y la vía lo importa en cada gránulo. Producción deja de escribir MODIS en los 11 volcanes, sin caída a K y con el job verde. Log real del run 41353423746 sin pyproj. Control con pyproj: 11 de 11 con record | CONFIRMADO | 5 / 4 → 5 | PR B (el arreglo va en el PR A) |
| VMA172-201 | Sonnet V2 (propio) | sin segundo verificador | `backfill-tier-a.yml` l. 73 corre producción sin pyproj (V3 suma `reproc-chunked.yml`) | CONFIRMADO (sin verificar por otro modelo) | 3 | junto con 201 |
| MA172-101 = MA172-302 | Opus F1, Opus F3 | Sonnet V1 | `vigilancia_sombra.py:432` filtra «records de K» sólo por `sha`, y los records de la vía también lo traen. Si C0 publica una protegida y la vía calla, se abre el issue que pide `git revert` de K (#850) (`vigilancia-sombra.yml:134-135`) | CONFIRMADO | 3 → 3 | PR B |
| MA172-102 | Opus F1 | Sonnet V1 | El tablero no reconoce `codigo_mirova` como ancla (`frontend/index.html:1630-1631` y otras listas). En los records reales de la vía en Chillán, el cúmulo está a 0,567 km y el marcador a 2,233 km; con un segundo foco sintético, 16,15 km | CONFIRMADO | 3 → 3 | PR B |
| MA172-103 | Opus F1 | Sonnet V1 | `tests/test_guard_adopcion_k_s153.py:45-48` queda rojo en b42823194 (1 failed y 2 passed) y verde en da67 (3 passed). El CI del PR B saldría rojo (no visto en GitHub) | CONFIRMADO | 2 → 2 | PR B |
| MA172-202 | Opus F2 | Sonnet V2 | La vigilancia de la guardia trata de modo distinto los dos casos de producción. Si producción tiene record y calla: REVERSION_CANDIDATA. Si producción no tiene record: VERDE, aunque la guardia publique la protegida. El peor caso de la regla queda ciego | CONFIRMADO | 4 → 3 | ninguno (corregir antes de sellar la regla) |
| MA172-203 | Opus F2 | Sonnet V2 | Con la guardia muerta hasta 3 días la vigilancia sigue en VERDE, y el rojo del job no se vuelve issue | CONFIRMADO EN PARTE: la guardia reprocesa 8 días hacia atrás, así que es retraso, no pérdida | 3 → 2 | ninguno |
| MA172-204 | Opus F2 | Sonnet V2 | La frescura de la referencia se mide sobre todas las filas: una referencia sólo VIIRS fresca da VERDE para MODIS | CONFIRMADO EN PARTE: el mecanismo existe; desde marzo hay 0 días con VIIRS y sin MODIS | 3 → 2 | ninguno |
| MA172-205 | Opus F2 | Sonnet V3 | Tras una reversión, la marca de `cambio_detector.js` da la misma fecha y sigue diciendo «viene de la vía». El escalón de vuelta a K no lleva marca: en Chillán se leería como declinación | CONFIRMADO | 3 → 2 | ninguno |
| MA172-206 | Opus F2 | Sonnet V2 | El upgrade de NRT a estándar hereda `first_processed_utc` de K: el «encendido desde los datos» cae antes del merge | CONFIRMADO EN PARTE: los «~4,5 días» son SOSPECHA | 2 → 2 | ninguno |
| MA172-207 | Opus F2 | Sonnet V2 | La regla de reversión (l. 93) cuenta desde `CAMBIO_DETECTOR_MODIS_UTC`, constante que no existe en A ni en B | CONFIRMADO | 2 → 2 | ninguno (texto de la regla) |
| MA172-208 | Opus F2 | Sonnet V2 | El nulo de la guardia con 0 pares da VERDE sin aviso | CONFIRMADO | 2 → 2 | ninguno |
| MA172-209 | Opus F2 | Sonnet V2 | El factor «1,1 a 1,25 veces K» sale de una corrida de la sombra con tres vías en Láscar y no aísla MODIS. VR172-04 se confirma: un solo paso de 50 min para todos los sensores. Holgura de hoy: unos 20 de 50 min | CONFIRMADO EN PARTE | 2 → 1 | ninguno |
| MA172-104 | Opus F1 | Sonnet V1 | `_s154_reproc_k_historico` («reproceso con K») hereda la vía, y su prueba de identidad sigue verde. Ningún workflow lo nombra | CONFIRMADO | 2 → 2 | ninguno |
| MA172-105 | Opus F1 | Sonnet V1 | `README.md:52-56`, `docs/SINTOMAS.md:25-28` y el aviso de `frontend/index.html:544` dicen que producción es K, sin marca A113 | CONFIRMADO EN PARTE: incompletos, no falsos como historia de K | 2 → 2 | ninguno |
| MA172-106 | Opus F1 | Sonnet V1 | La cabecera FICHA de `pipeline/mirova_v750_codigo.py:5-6` titula APAGADA con el flag en true. `store.py:351-356` es cierto, pero incompleto | CONFIRMADO EN PARTE | 2 → 2 | ninguno (es ficha SDA: conviene en B) |
| MA172-110 | Opus F1 | Sonnet V1 | `experimental_lowT` hereda la vía; no lo cubre ni el guard ni la declaración | CONFIRMADO | 1 → 1 | ninguno |
| MA172-303 | Opus F3 | Sonnet V3 | 55 a 56 perfiles derivados pasan de la vía apagada a encendida sin escribirlo (cargador real). 46 tienen MODIS efectivo; 8 workflows vivos nombran a 20 de ellos y ninguno instala pyproj | CONFIRMADO | 2 → 2 | ninguno |
| MA172-304 | Opus F3 | Sonnet V3 | Tras un revert, el audit semanal manda los records K de las noches posteriores a la frontera a `fuera_de_detector`, y el recall MODIS queda en None sin aviso en `avisos_detector` (el conteo sí sale en el JSON) | CONFIRMADO | 2 → 2 | ninguno |
| MA172-305 | Opus F3 | Sonnet V3 | Los cron diarios llegan entre 2,8 y 8 h tarde (sombra n = 3, experimental-diario n = 23). La separación de horarios de las 17:40 que promete el comentario de la guardia no existe. La vigilancia va por `workflow_run` y no se atrasa | CONFIRMADO EN PARTE: la guardia nunca corrió, es extrapolación | 2 → 1 | ninguno |
| MA172-211 = MA172-307 | Opus F2, Opus F3 | Sonnet V3 | El nulo de la guardia no tiene tolerancia ni lee `product_version`: con la función real, 1 par distinto en 112 da INVESTIGAR | CONFIRMADO EN PARTE: que NRT contra estándar produzca un par distinto es SIN DATO | 1 → 1 | ninguno |
| DATO-COORD = VMA172-302 | dato del coordinador | Sonnet V3 | `_load_profile` (`pipeline/profile.py:49-66`) resuelve un solo nivel de `extends`. Un perfil de dos niveles falla con KeyError (ruidoso); ninguno de los 60 perfiles reales es de dos niveles, así que el censo no cambia | CONFIRMADO | sin grav. → 1 | ninguno |

Hallazgos propios de los verificadores que nadie más verificó:

- VMA172-101 (V1, gravedad 1): el comentario de `pipeline/profile.py:905-909` dice APAGADA.
- VMA172-102 (V1, gravedad 2, SOSPECHA): orden de merge. B contiene el código de A hasta da67fa417, pero no c83882fcf. F2 simuló A antes que B, con revert limpio.
- VMA172-202 (V2, gravedad 2): ante cualquier excepción de la vía no hay respaldo a K, aunque el comentario promete caer a K.
- VMA172-203 (V2, gravedad 2): el stale-gate A57 del NRT y `nrt-healthcheck.yml:73` miran el último record de cualquier sensor; una caída sólo de MODIS no los dispara.

Lo que salió limpio, verificado por el auditor (no pasó por verificador porque no era hallazgo):

- La vía en sí está bien cubierta por pruebas: siete mutaciones semánticas fallan por aserción, el control de caída sale distinto y la línea base da cero (F1).
- El cambio del PR B en `pipeline/process_modis.py` es sólo de comentarios: AST idéntico (F1).
- G4 y G5 miran los dos workflows nuevos, y G4 falla con mutantes (F3).
- El S8 del lector de V375-E re-sellado pasa con base→A, base→A más B y A→A más B, y marca régimen en los 7 casos construidos para fallar (F3).
- La sombra de V750 ve la vía de MODIS en True antes y después: no cambia (F3).
- Las tres marcas del tablero conviven, medido con node (F3).
- Suite completa tras el revert (F2): 2888 verdes y 2 rojas. Las 2 rojas (`test_guard_libro_de_pruebas_s146` g1d y g2c) son de entorno, temporal de pytest en C: y repo en D:. También salen rojas en la base, y dan verde con `--basetemp` en D:.

## No verificados (6)

Gravedad 1, bajo el corte, sin papel en la decisión de merge:

| ID | Hallazgo |
|---|---|
| MA172-107 | El cuerpo del PR B no declara el cambio en `_s146_ab_control.yaml` ni los ajustes de arneses |
| MA172-108 | El conteo «28 pruebas, 26 fijan K» no se reproduce: el flag rompe 33 pruebas en 82 archivos, todas arregladas en B |
| MA172-109 | El reconocimiento del volcán por coordenadas (`process_modis.py:640`) sólo lo vigila una caída: la mutación M9 dio 0 fallas por aserción |
| MA172-111 | El perfil deprecado `mirova_equivalent_villarrica_test1` escribe en `data/mirova_equivalent/` con la vía apagada |
| MA172-210 | La caída de la vía a K por gránulo no se ve en el tablero |
| MA172-306 | Si coincidieran en el mismo minuto, las líneas de MODIS y del cese de Suomi NPP caerían en el mismo píxel |

Son la puerta de entrada de la auditoría siguiente. Además, cada informe de auditor trae SEGUIMIENTOS propios, que no se cuentan aquí.

## Cambios mínimos antes del merge

### PR A (se mergea primero; todo lo que sigue es inerte con el flag apagado y no debe revertirse con B)

1. Agregar `pyproj` a la línea `pip install` de `.github/workflows/nrt.yml` (l. 143), `backfill-tier-a.yml` (l. 73) y `reproc-chunked.yml` (MA172-201/301, VMA172-201). Agregar también una guarda que ligue cualquier flag `*_codigo_mirova` encendido en un perfil con pyproj instalado en los workflows que corren ese perfil.
2. `scripts/vigilancia_sombra.py:432`: filtrar los records de K por algo que los distinga de los de la vía, por ejemplo excluir `via_codigo_mirova` o `final_hotspot_source == "codigo_mirova"` en MODIS (MA172-101/302). Antes, verificar qué campo persiste el record de la vía: V1 vio que `banco_paridad.cargar_nuestros` no copia `via_codigo_mirova`.
3. Tablero: agregar `codigo_mirova` a las listas de anclas honestas de `frontend/index.html` (l. 1631, 1697, 2735, 2766, 3283, 3677, 3683) y replicarlo en las vistas que tengan la misma lista (MA172-102).
4. Recomendado antes del encendido, porque es la red de la regla de reversión:
   - (MA172-202) Protegida posterior al encendido con guardia que publica y producción sin record pasadas N horas: INVESTIGAR. N lo fija Nicolás.
   - (MA172-208) Aviso en `evaluar()` si el nulo tiene 0 pares.
   - (MA172-204) Frescura de la referencia filtrada a MODIS.
   - (MA172-206) Usar `processed_utc` y no `first_processed_utc` en `encendido_desde_datos`.
   - (MA172-203) Un paso `if: failure()` en `guardia-k-modis.yml` que abra el issue «Guardia K de MODIS:».

### PR B (sólo después de que A esté en main)

1. Rebasar B sobre el main que ya trae A, o fijar su base en la rama de A, para que su diff sea sólo el encendido. Así el revert del merge de B no se lleva el código de A (VMA172-102).
2. Arreglar `tests/test_guard_adopcion_k_s153.py`: laboratorio y producción ahora difieren en cuatro flags (MA172-103). Esperar el CI con conclusión verde (`gh pr checks --watch`; «0 checks» es SIN DATO).
3. Cabecera FICHA de `pipeline/mirova_v750_codigo.py:5-6` y comentario de `pipeline/profile.py:905-909`: dejar de decir APAGADA (MA172-106, VMA172-101). Es ficha SDA, así que entra con el encendido.
4. Recomendado, propagación A113:
   - (MA172-105) Marca en `README.md:52-56`, `docs/SINTOMAS.md:25-28` y el aviso de `frontend/index.html:544`.
   - (MA172-104) Fijar el flag en false en `_s154_reproc_k_historico`, o declarar por qué no.
   - (MA172-110) Lo mismo para `experimental_lowT`.
   - (MA172-107) Declarar en el cuerpo del PR el cambio en `_s146_ab_control` y en los arneses.
5. Regla de reversión, antes de sellarla:
   - (MA172-207) Reescribir la l. 93 con la frontera que usa el código.
   - (MA172-209) Reescribir el pre-mortem del tiempo del NRT con la holgura medida (unos 20 de 50 min), no con el 1,1 a 1,25.
   - (MA172-205) Decir qué marca muestra el tablero tras una reversión.

## Cola de pruebas de campo (día del encendido)

1. **Primer NRT después del merge de B.**
   - En el log del paso «Run VRP pipeline» de cada uno de los 11 volcanes: ningún `ModuleNotFoundError` ni `ERROR processing` en MODIS.
   - En `data/mirova_equivalent/`: records MODIS nuevos con `via_codigo_mirova` en los 11. Si un volcán con pasada MODIS no tiene record nuevo, MODIS está mudo; el stale-gate no lo ve (VMA172-203).
2. **Duración del paso del NRT** con la vía en Láscar y Chillán, contra el timeout de 50 min. Hoy la holgura es de unos 20 min.
3. **Chillán en las tres vistas** (index, diario y mosaico):
   - el escalón de magnitud de MODIS lleva la marca de la vía, en la fecha de los datos y no antes del merge (MA172-206);
   - el marcador del mapa cae sobre el cúmulo y no a km de él (MA172-102).
4. **Ningún issue «Sombra de K: candidata a reversión»** abierto por un record de la vía (MA172-101).
5. **Primera corrida de la guardia K y de su vigilancia** (`workflow_run`):
   - hora real de arranque frente al NRT y a la sombra (MA172-305);
   - nulo con más de 0 pares (MA172-208);
   - ningún INVESTIGAR por versión de producto (MA172-307).
6. **Primera semana del audit semanal**: el detector VIA_MODIS no manda records a `fuera_de_detector` sin aviso (MA172-304).
7. **Si hay que revertir**:
   - `git revert` del merge de B sobre el main del día; la suite, con `--basetemp` en el disco del repo;
   - la marca del tablero tras la reversión, porque hoy queda diciendo «vía» (MA172-205).

## Rutas

- Síntesis: D:/vrp-trabajo/temporales/s172_miniaud/SINTESIS.md
- Informes de los auditores:
  - D:/vrp-trabajo/temporales/s172_miniaud/f1/INFORME.md
  - D:/vrp-trabajo/temporales/s172_miniaud/f2/INFORME.md
  - D:/vrp-trabajo/temporales/s172_miniaud/f3/INFORME.md
- Informes de los verificadores:
  - D:/vrp-trabajo/temporales/s172_miniaud/v1/INFORME.md
  - D:/vrp-trabajo/temporales/s172_miniaud/v2/INFORME.md
  - D:/vrp-trabajo/temporales/s172_miniaud/v3/INFORME.md
- Veredictos por ítem: D:/vrp-trabajo/temporales/s172_miniaud/v1/veredictos.csv, D:/vrp-trabajo/temporales/s172_miniaud/v2/veredictos.csv y D:/vrp-trabajo/temporales/s172_miniaud/v3/veredictos.csv
- Prompts: D:/vrp-trabajo/temporales/s172_miniaud/prompts/
