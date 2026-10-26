# CAMINOS: cómo podría estar mal el veredicto DECIDE NICOLÁS del censo MOD-D

Escrito ANTES de medir nada. Hora del servidor de GitHub: 2026-10-26 16:00:28 GMT (cabecera `Date` de
`gh api -i repos/MendozaVolcanic/VRP-chile`). Verificador con contexto limpio (Fable 5.1). Lo único que vi hasta
aquí: el pre-registro sellado, el código del evaluador (`evaluar_paquete.py`, `m_con_regla_matlab.py`,
`contar_tanda.py`), el manifiesto del candado, la estructura de un record y las salidas de texto que la tarea me
entregó. No he recalculado nada todavía.

## A. Instrumento (el número sale mal aunque los datos estén bien)

1. **La magnitud mostrada del PM no es la del record sintético.** `record_port` arma un record con varios campos
   de magnitud; `mirovaEqVrpDisplay` elige uno (pc.vrp_mw, f5_core, vrp_mw). Si eligiera otro distinto del VRP del
   port, P1b y M estarían midiendo un número que no es el del PM. Comprobar: `mag` de la tabla contra
   `port.fisica.vrp_mw` del record en los pares.
2. **P1b es un artefacto de redondeo o de un umbral de display.** Si la magnitud mostrada se redondea (2 decimales)
   o si K y PM quedan a milésimas de 1 MW, la fila 5 se dispararía por ruido. Comprobar los valores crudos (1,245 y
   0,973) en el record, sin pasar por el texto.
3. **P2 cuenta bloques por pasada y no por noche-volcán.** Si `_bloque` usara `dt` entero, B sería el número de
   pasadas discordantes y la prueba de signos tendría más poder del sellado. Comprobar que B = número de
   (vol, noche) distintos entre las discordantes, y que 49 y 8 son conteos de pasadas con error, no de bloques.
4. **P2 cuenta mitades de pasada partida dos veces** (adenda 3.7 las deja entrar): si una pasada partida aparece en
   dos records con el mismo (vol, dt) habría doble conteo. Comprobar duplicados de (vol, dt) en el total.
5. **M usa la magnitud mostrada y `m_con_regla_matlab` usa el VRP del port recalculado**: si el display del PM no
   coincide con `port.fisica.vrp_mw`, las dos columnas de M no serían comparables y «regla sobre port mediana 1,000»
   sería casualidad. Comprobar `d_port` contra `mag` del PM.
6. **El coeficiente de `m_con_regla_matlab` (1,89e7 × 1 km²) no es el del port** (el port podría usar otro k o un
   área distinta). La prueba de identidad `probar()` lo cubre sólo si corre; re-correrla.
7. **El caso 1,112 MW «alerta de un solo píxel» sale de una grilla equivocada** (`grilla_NNNN.npz` indexada por `id`,
   y el `id` podría no ser único entre partes o entre tandas). Comprobar unicidad de `id` y que la grilla del caso
   P1b corresponda al volcán y hora.

## B. Población y cobertura (se evalúa otra cosa que la sellada)

8. **La población no es la sellada.** `poblacion.json` en D: y el del tag (`experiments/_s162_mxd03/poblacion.json`,
   blob `95950685`) podrían diferir; el evaluador lee el del tag por defecto. Comprobar sha del archivo en D: contra
   el blob del tag, y 5.465 records / 1.232 gránulos / 24 partes.
9. **Partes repetidas o faltantes entre tandas**: `contar_tanda` mira cada tanda por separado; una parte podría
   estar en dos runs (t1 y t2) o faltar en el total. Comprobar que el conjunto de `ab_parteNN` bajo `censo/` sea
   exactamente 00 a 23, una vez cada uno, y que los (vol, dt) sumen 5.465 sin repetidos.
10. **Un denominador excluye protegidas.** Los 189 fuera del denominador (144 + 45) podrían contener una protegida
    que K publica; el evaluador la listaría en `protegidas_fuera_del_denominador` y la mandaría a la fila 5, pero
    la lista salió vacía: comprobar por mi cuenta que ninguno de los 189 tenga `lab == protegida`, y además que
    los motivos sean los que dicen (`port_estado` y `motivo_vacio`), no una falla del port disfrazada.
11. **«Volcán fuera del gránulo» podría ser un defecto del arnés** (por ejemplo, grilla de GEO mal leída) y no una
    propiedad de la escena: comprobar que esos 144 tengan K con `n_anom = 0` o sean escenas donde el cráter cae en
    el borde (`crater_mxd03.borde`), y si alguno tiene K publicando.
12. **El commit no es el del tag**: las cabeceras dicen `865174abe` pero el tag podría apuntar a otro sha o el
    árbol del worktree estar sucio. Comprobar `git rev-parse s162-modd-tag^{commit}`, `git status`, y el blob del
    manifiesto contra `git ls-tree`.

## C. Controles verdes por la razón equivocada

13. **K = producción verde porque no comparó nada**: «0 records re-corridos en su codigo_sha» puede significar
    0 diferencias o 0 comparaciones. Comprobar en `resultado_censo.json` cuántas pasadas comparó `control_arnes`
    contra `data/` y que las diferencias sean 0 sobre un n grande.
14. **PM = S159 verde sin píxeles**: si las 148 comunes tuvieran todas `npix = 0`, el control pasaría sin medir
    el VRP. Comprobar `comunes_con_pixeles` (91 según el texto) y que las 148 sean las de la población del lote
    39712862945 (149 menos una con escena inválida).
15. **Placebo verde por construcción**: d′ = 0 sale de K × 1,2 contra K; no puede fallar salvo cableado roto. Es
    control de cableado, no de resultado. Anotar como límite, no como hallazgo.
16. **Contador verde pero con menos de 50 inyectados** (si hubiera menos de 50 negativos no publicados por el PM)
    o con `s_despues - s_antes` distinto de 50. Comprobar `inyectados`, `s_pm_antes`, `s_pm_con_inyeccion`.
17. **Referencia y re-etiquetado**: la referencia en D: podría ser otra copia con el mismo nombre. Comprobar
    sha256 LF de los dos CSV contra `poblacion.json["referencia"]`.
18. **Predicado**: el `sha256_frontend_index` de los jobs es el del árbol del tag, pero el tag se cortó de
    `s162-mxd03-codigo` (main congelado `80b819828`): si `frontend/index.html` del tag no fuera el de ese main, «el
    predicado del tablero» sería otro. Comprobar el blob de `frontend/index.html` en los dos commits.
19. **Manifiesto**: el blob usado (`c3bc1c3a`) tiene que ser el de `git ls-tree s162-modd-tag` y cubrir el
    evaluador y el arnés.

## D. Lectura del §6 y de lo informativo

20. **La fila 5 se dispara por P1b y nada más**: comprobar que no haya P1 VETADO (fila 2), ni P2 PIERDE (3), ni SIN
    SUSTRATO (4), y que `prot_k` esté vacío; si P1 estuviera VETADO en PM, el veredicto correcto sería NO
    CANDIDATO, y P1b no debería tapar eso.
21. **Chillán**: «6 de 7 a favor, p = 8/128» exige n = 7 pares sin empate; si hubiera un empate exacto o un par con
    `vrp_mirova` nulo, el n sería otro. Y las 3 recuperadas tienen que ser las tres que el §5 nombra (2026-09-29
    07:20, 2026-10-12 07:20, 2026-10-15 01:05) y no otras.
22. **Lo informativo contradice lo que decide**: la curva de cenit del PM podría mostrar razones lejos de 1 en los
    tramos altos (lo que un «M MEJORA» agregado esconde); el soporte de la adenda 1 podría decir que las 8
    publicaciones del PM en negativos son calor real (lo que cambia la lectura de P2 GANA, no su regla); S-1 con
    identidad que falla; costura y borde con protegidas que K publica y el PM no.
23. **El P1b 1 de PM-pixel y 5 de PM-geo5 cambian la atribución**: si la protegida de P1b también baja de 1 MW en
    PM-geo5 y PM-sens, es del detector; si sólo en PM, es de MxD03. Informa, no decide.
24. **M MEJORA se apoya en 70 de 78 pares de Láscar**: un solo volcán domina; por volcán podría haber EMPEORA
    (Villarrica n = 1). La regla sellada sólo mira el agregado, así que no cambia el veredicto, pero debe quedar
    dicho.

## E. Lo que NO voy a poder verificar (lo digo antes)

- Que el `.m` de MIROVA sea el que MIROVA usa para MODIS (SIN DATO declarado en la adenda 4).
- Que `data/` de producción (el K) sea correcto: el control 1 lo compara con lo que está en el repo, no con la
  física.
- La ejecución de los jobs en GitHub: sólo veo sus artefactos descargados en D:.
