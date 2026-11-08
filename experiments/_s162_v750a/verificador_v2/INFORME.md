# Informe del verificador con contexto limpio, segunda vuelta: `evaluar_v750a.py` (V750-A, S162)

- Hora del servidor al empezar: `gh api -i repos/MendozaVolcanic/VRP-chile | grep -i ^date` → **Mon, 26 Oct 2026 02:24:05 GMT**.
- Commit medido: **9f9ae9259** (rama `claude/s162-viirs750-2-918174`), worktree
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs750-2-918174`.
- Modelo: Claude Fable 5.1 (la primera vuelta fue otro modelo). No vi el razonamiento de quien corrigió.
- Lista de caminos escrita ANTES de abrir el analizador, las pruebas y el medidor:
  `experiments\_s162_v750a\verificador_v2\LISTA_CAMINOS_previa.md`, sha256
  `9876a1aa95896dfd46714ca89147b48c65d54f066e4d67ec2ba51721718e9d9d`.
- `evaluar_d25.py` usado: copia del scratchpad, sha256 `2e5576973ef1df6969f517c40bedc271f76db8a8b4756613e5004fc05d976747`
  (igual al fijado en `analizar_v750b.py:48`). Node v22.16.0, Python 3.12.10, `OMP_NUM_THREADS=1`.
- Qué NO miré: el productor de los artefactos (contrato del generador), `pipeline/`, el run de V750-B, el medidor de
  mutaciones entero del autor (corre en paralelo en la misma carpeta; sólo reproduje en copias `_v2_` las 8 mutaciones
  que tocan L2, L4, L7 y L18, cada una contra los escenarios que LECTURAS dice que la fijan), el rendimiento con la
  población real, `equivalencia_v750a.py` más allá de sus líneas de salida, y las roturas V04 a V41 de la primera vuelta
  que no tocan las cuatro lecturas (el autor las cubrió con M29 a M49; sólo comprobé estáticamente que cada línea que
  mutan existe una vez en el analizador de hoy).
- Hora del servidor al cerrar: **Mon, 26 Oct 2026 03:31:46 GMT**. `git status` al cerrar muestra, además de mi carpeta
  `verificador_v2/` (sin seguimiento) y los `_mut_*` del autor, `experiments/_s162_v750b/PREREGISTRO_V750B.md` modificado:
  no es mío (no abrí ese archivo), viene de otra sesión que trabaja en el mismo worktree.
- No toqué ningún archivo existente del repo ni hice git. Mis copias `_v2_*_evaluar_v750a.py` se borraron al terminar
  cada corrida (`ls experiments/_s162_v750a/_v2_*` al cierre: ninguna). Los `_mut_*` del autor no se tocaron.

## En una pantalla

**Listo con cambios (de texto, no de código).** Las correcciones de VA-01 a VA-09 hacen lo que cada hallazgo pedía
(siete corregidas, dos declaradas como límite: VA-04 BLOQUEA en la sombra y VA-09 sha del módulo), sin romper otra regla:
línea base 53 de 53 en verde, y las 8 mutaciones del autor que tocan L2, L4, L7 y L18 quedan atrapadas por los escenarios
que LECTURAS nombra. Las cuatro lecturas de D-48 están implementadas como su texto dice y fijadas por pruebas; ninguna
abre un camino a un veredicto de adopción falso: L2 y L4 son más estrictas que antes, L18 saca pasadas por un criterio
que sólo mira K, y L7 sólo deja pasar diferencias que el analizador no produce. Lo que hay que cambiar antes del sello:
(1) la frase de §7 y de LECTURAS «con el predicado de hoy la segunda clase no se puede producir» es falsa (el tope de
50.000 MW de `mirovaEqVrp` la produce: un K de 45.000 MW publica y por 1,2 no, con `t_max` tibio; cierra la compuerta
sin defecto del paquete, VB-A01); (2) «salen de todos los brazos» de L18 no es literal: §6.1 y S-1 siguen mirando esas
pasadas sobre `oks0` (dirección segura, VB-A02); (3) tres roturas de una línea que las pruebas no atrapan, ninguna
abre adopción (VB-A03 a VB-A05).

## (A) Las correcciones de VA-01 a VA-09

| VA | estado | evidencia |
|---|---|---|
| VA-01 | **corregido** (como L18, no como el cero que el analizador tomó primero) | `evaluar_v750a.py:374` `k_ok = len(k_dist) <= AB.MAX_K_DISTINTO * max(1, len(oks0)) and not k_dist_prot`; `:377` saca las distintas de `oks`; `:375-376` lista por nombre. Pre-registro §7 `:149` y LECTURAS L18 `:29` lo documentan. Pruebas: E28 (1 de 109, OK, P2 pasa de 6 a 5 bloques), E50 (2 de 110, FALLA), E52 (1 protegida de 110, FALLA), E29 (`pc_vrp` a 0,01 MW, FALLA): los 4 OK en `base_salida.txt`. Mutaciones M15, M29, M53, M54, M55 ATRAPADAS (`mut_autor_v2_salida.txt`). Las roturas V01 a V03 de la primera vuelta corresponden a M53, M54 y M30. |
| VA-02 | **corregido** (como L7) | `:424-431`: `pl_todas`, `pl_frio` (`t_max_k` de K `< 278.15`), `pl_dist` (sin explicar) y `ctrl["placebo (publicación)"] = not pl_dist`. §7 `:156-165` y LECTURAS L7 `:18` corregidos. E30 OK (K 9 MW a 270 K, explicada 1, sin explicar 0). M50 ATRAPADA por E30. Lo que queda mal es una frase, no el código: ver VB-A01. |
| VA-03 | **corregido, en el sentido contrario al propuesto** (D-48 eligió la razón de P sobre todas las protegidas que P publica) | `:566-574` `razon_prot(..., exigir_k=False)`; `:602-604` imprime al lado la de K y P «informa, no decide». §6.2 `:133-137` y L4 `:15`. E31 OK (`NO CUMPLE (O/tabla: M razón 2.000; O/todo: M razón 2.000)` con `razón en protegidas que publican K y P ... 1.000 (n 10)` al lado). M52 ATRAPADA por E31. Mis C8 (razón vacía → `M razón sin protegidas`, NO CUMPLE) y C11 (12 protegidas que K no publica y P publica bien → razón 1,000 n 23, CUMPLE) salen como se espera. |
| VA-04 | **corregido en parte, el resto declarado** | `:639` «SIN PROTEGIDAS: P1 no pudo vetar» cuando `n_prot == 0` (E49 OK: `== §6.3 sombra: CUMPLE (P1 = 0; P2 tabla GANA, todo GANA; SIN PROTEGIDAS: P1 no pudo vetar)`); M51 lo vigila. BLOQUEA sigue pasando en la sombra (`:630` sólo PIERDE), y queda escrito para Nicolás en L3 `:14` «confirmar al sellar» y L19 `:30`. La línea sigue diciendo CUMPLE, como el verificador aceptó («marcado»). |
| VA-05 | **corregido** | S-1 (`:491-536`) va después de §6.1 (`:465-489`): en E00 la línea `== §6.1 equivalencia: CUMPLE` es la 17 y la primera `== S-1 par` la 18 (`v2_base/E00/stdout.txt`). JSON por pasada `salida_s1_por_pasada.json`: 145 filas en E00 con `delta_sd` (a), `margen_A_nti_eti`/`margen_B_nti_eti` (b), `publica` y `decidida_por_escena` (c). Los fixtures ahora distinguen pase 1 de 2 y zona 1 de 2 (`probar_evaluar_v750a.py:234-238`, `diag(..., u1=0.10, pase=2, u_otro_pase=0.10)`) y NTI de ETI (`:247-248`); M22, M46, M47, M48 las vigilan. El contrato de la celda decisiva sigue sin poder verificarse: declarado en L12 `:23`. |
| VA-06 | **corregido** | `:249` `str(r.get("estado") or "sin_estado")[:40]`; `:325` exige `"record" in res[i]["brazos"]["Kgeo"]`; `:347` `if a0.get("primary_cluster")`. Mis C12 (estado `null` → SIN DATO «sin_estado», cobertura INSUFICIENTE, salida 3), C13 (Kgeo `{}` → CUMPLE, «Kgeo: sin datos») y C14 (sombra, P publicado sin `primary_cluster` → nulo OK, CUMPLE): ver `casos_v2_malformados_salida.txt`. |
| VA-07 | **corregido** | 56 mutaciones + CAIDA en `mutar_evaluar_v750a.py` (cada línea vieja aparece exactamente una vez en el analizador de hoy, `chequeos_estaticos_salida.txt`); 53 escenarios (E28 a E52 por los huecos). Reproduje las 8 de D-48: 8 de 8 ATRAPADAS por los escenarios que LECTURAS cita. La salida del medidor del autor con M53 a M56 no está en el repo todavía (`mutar_evaluar_v750a_salida.txt` es de la versión de 52): SIN DATO para las otras 48 en esta vuelta. Quedan tres roturas mías sin atrapar (VB-A03 a VB-A05). |
| VA-08 | **corregido** | `probar_evaluar_v750a.py:574-584`: código fuera de {0, 3, 5, 6} sin Traceback = caída nativa, 2 reintentos, luego CAÍDA; y el medidor cuenta ATRAPADA sólo con rc 1 (`mutar_evaluar_v750a.py:178-183`), que la batería da sólo si no hubo caídas (`probar:630`). |
| VA-09 | **corregido en parte, el resto declarado como límite** | `:187-189` exige `VERDE: E1 n casos, E3 m recortes` con n ≥ 1020 y m ≥ 10 (E41 con 100 casos: salida 6); el sha del módulo queda declarado en L2 `:13` «se ata al módulo cuando exista la vía de proceso». Comprobé que el conteo por subcadena no se engaña con la salida real: `equivalencia_v750a.py:186` imprime `NO ATRAPADA` (sin «por aserción»), y `"atrapada por aserción" in "NO ATRAPADA"` es False. La `banda_triangulacion` sigue sin tope (declarado en L13). |

## (B) L2, L4, L7 y L18

| lectura | código | texto | prueba que la fija (comprobado) | ¿abre adopción falsa? |
|---|---|---|---|---|
| L2 | `MIN_MUT_LOCAL = 6` (`:75`), `n_atr >= 6` y control `caída` (`:192-194`) | §6.1 `:126-128` «6 de 6»; L2 `:13` | E51 (5 atrapadas → salida 6, «atrapadas 5 (mínimo 6)»), E38, E39, E40, E41; M56 ATRAPADA por E51 | No: más estricta. Matiz: el código acepta 7 o más líneas y no comprueba QUÉ seis (VB-A06, bajo). |
| L4 | `razon_prot(exigir_k=False)` (`:566-574`), banda `0.9 <= rz <= 1.1` (`:591`), «sin protegidas» falla (`:592`) | §6.2 `:133-137`; L4 `:15` | E31, E32, E33, E06, E48; M52 ATRAPADA por E31. Bordes: mis C1 y C2 (P = 0,9 y 1,1 × MIROVA) dan `M razón en protegidas 0.900` / `1.100` sin entrar a los motivos (`casos_v2_bordes_salida.txt`); mi rotura R1 (`<` en vez de `<=`) la atrapan C1 y C2, no la batería del autor (VB-A03) | No: más estricta que la lectura anterior (E31 lo muestra). Razón vacía → NO CUMPLE (C8). |
| L7 | `pl_frio` con `t_max_k` de K `< 278.15` (`:425`), `t_max` ausente cuenta como NO explicada (`or 1e9`), `pl_dist` cierra (`:427`) | §7 `:149-165`; L7 `:18`; LECTURAS `:40-44` | E30; M50 ATRAPADA por E30. Node directo: 9 MW/270 K publica y 10,8 no; 45 MW/276 K/150 px publica y 54 no; a 278,15 K exactos ninguno filtra (`node_tope_50000_salida.txt`), coherente con el `<` del código | No. La mitad «sin explicar» SÍ se produce (VB-A01), en la dirección segura (cierra). |
| L18 | `:374-377` | §7 `:149`; L18 `:29` | E28, E50, E52, E29, E14; M15, M29, M53, M54, M55 ATRAPADAS. Sombra: mis C5 (1 de 24 cierra), C6 (1 de 114 no cierra), C7 (protegida cierra) | No por sí sola: el criterio sólo mira K (`pub_prod` y `pc_vrp` contra el record de K), así que no puede elegir pasadas según P. Residuo no medible aquí: si la diferencia de máquina que motiva la tolerancia afectara a P y a K en la misma pasada, esa pasada sale de P1/P2/M; con el tope del 1 % y «ninguna protegida» el daño posible es de hasta 1 % de los bloques de P2. |

## Hallazgos

### VB-A01 (gravedad 3, confianza 5) La frase «con el predicado de hoy la segunda clase no se puede producir» es falsa: el tope de 50.000 MW de `mirovaEqVrp` la produce

- Dónde: `PREREGISTRO_V750A.md:163-165` («Con el predicado de hoy la segunda clase no se puede producir: esa mitad del
  control sólo atraparía un filtro nuevo del tablero») y `LECTURAS_EVALUAR_V750A.md:40-44` (misma frase; «la mutación vieja
  M50 quedó así sin escenario posible»).
- Qué pasa: `frontend/index.html:1182` (`mirovaEqVrp`: `return vmw > 50000 ? 0 : vmw`; las citas del pre-registro a
  `isCirrusArtifact :1336` e `isDiffuseFieldArtifact :1355` sí están bien) es un tercer sitio donde el
  predicado mira la magnitud, y no exige `t_max` frío. Un K de 45.000 MW publica; por 1,2 = 54.000 MW, `disp` = 0 y no
  publica; `t_max` tibio → el analizador lo cuenta «sin explicar» y cierra la compuerta (salida 3) sin defecto del paquete.
- Cómo se ve: node directo, `node_tope_50000_salida.txt`: `K 45000 MW t 300 -> [1, 1, 0, 45000, 1]` y
  `K x1,2 = 54000 MW t 300 -> [1, 1, 0, 0, 0]`. Escenario mío C3 (`v2_casos/C3/stdout.txt:11`):
  `== control placebo K×1,2 (publicación): distintas de K 1 de 50; explicadas ... 0 []; sin explicar 1 ['Lascar 2026-07-31
  05:30']: FALLA` y compuerta CERRADA. C9 muestra las dos clases juntas en una población (explicada 1, sin explicar 1, FALLA).
- Cómo reproducirlo: `python experiments/_s162_v750a/verificador_v2/ver2_casos.py --dest <tmp> --evaluador <evaluar_d25.py>
  --solo C3,C9`.
- Consecuencia para el medidor: LECTURAS `:42-43` dice que la mutación vieja M50 («el control siempre pasa») «quedó sin
  escenario posible». Mi rotura R6 es esa mutación (`ctrl["placebo (publicación)"] = True`): PASA la batería del autor (E00,
  E30) y la atrapan C3 y C9 (`roturas_v2_salida.txt`). O sea que la mitad que cierra SÍ se puede vigilar; hoy no se vigila.
- Por qué importa: la dirección es segura (cierra, no adopta), y en VIIRS 750 real un cúmulo de 41.667 a 50.000 MW es
  improbable (es el `SANITY_CAP_VRP_MW` de `store.py`), pero la afirmación de que el control no puede caer por el predicado
  está escrita en el pre-registro que se va a sellar, y es lo mismo que pasó con VA-02: el tablero mira la magnitud en más
  sitios de los que el texto dice. También dice que la nueva M50 «vieja» no tiene escenario posible, y C3 es ese escenario.
- Arreglo (texto): «cualquier otra diferencia cierra; con el predicado de hoy la única otra forma conocida es el tope de
  50.000 MW de `mirovaEqVrp`, que se trata igual (cierra y se explica a mano)». O bien excluir también esa clase (K entre
  41.667 y 50.000 MW) listándola aparte, y agregar C3 como escenario.

### VB-A02 (gravedad 2, confianza 5) «Salen de todos los brazos» (L18) no es literal: §6.1 y S-1 siguen mirando las pasadas con K distinto

- Dónde: `evaluar_v750a.py:468` (`for i in oks0:` en la equivalencia del runner), `:496`, `:508` (S-1) y `:489` («de
  {len(oks0)}»), contra `PREREGISTRO_V750A.md:149` y `LECTURAS:29` «salen de todos los brazos».
- Qué pasa: una pasada con K distinto de producción que cabe en el 1 % sigue bloqueando §6.1 si P ≠ O en ella, y sigue
  en el S-1. Es más estricto que el texto (dirección segura: §6.1 no depende de K), pero el texto y el código dicen cosas
  distintas, y una sesión futura que «arregle» el código para que coincida con el texto quitaría cobertura al §6.1.
- Cómo se ve: mi C10 (`v2_casos/C10/stdout.txt`): `control K = producción: distintas 1 de 109 ... OK` y
  `== §6.1 equivalencia: NO SE CUMPLE (runner: 1 pasadas distintas fuera de la banda ['Lascar 2026-04-20 05:00'] ...)`.
  Mi rotura R4 (`oks` en vez de `oks0` en `:468`) no la atrapa ningún escenario del autor (E08, E09, E27, E28 pasan) y sí
  C10: ver `roturas_v2_salida.txt`.
- Arreglo: decidir cuál vale y dejarlo escrito. Recomiendo el código (la identidad P = O se exige sobre TODAS las
  observadas, con K o sin K) y corregir el texto: «salen de P1, P2, M y de los controles que comparan con K; la
  equivalencia P = O y el S-1 se miden sobre todas las observadas». Agregar un escenario como C10.

### VB-A03 (gravedad 2, confianza 5) Los bordes de la banda de M (0,9 y 1,1) no están fijados por ninguna prueba del autor

- Dónde: `evaluar_v750a.py:591` (`BANDA_RAZON[0] <= rz <= BANDA_RAZON[1]`), `PREREGISTRO:133` «bordes incluidos».
- Qué pasa: E32 y E33 prueban 0,85 y 1,15; M31 y M32 mueven la banda a 0,5 y 1,25. Nada prueba el borde mismo: una
  rotura `<` en vez de `<=` pasa toda la batería del autor.
- Cómo se ve: rotura R1 (`roturas_v2_salida.txt`): PASA con E00, E06, E31, E32, E33, E48; ATRAPADA con mis C1 y C2.
  Con el analizador sin tocar, C1 y C2 dan `M razón en protegidas 0.900 (n 10)` y `1.100 (n 10)` sin entrar a los motivos
  (`casos_v2_bordes_salida.txt`). Nota de flotantes: con los VRP de la base, `round(1.1*3.0, 3)/3.0` da 1.0999999999999999
  y la mediana queda en 1.1 exacto; en datos reales una mediana que caiga justo en el borde es improbable, pero el `<=` es
  lo que el texto manda.
- Arreglo: agregar C1 y C2 (o equivalentes) a `probar_evaluar_v750a.py`.

### VB-A04 (gravedad 2, confianza 5) El control K = producción en la fase sombra no está fijado por ninguna prueba

- Dónde: `evaluar_v750a.py:368-377` corre igual en censo y sombra (correcto); `probar_evaluar_v750a.py` no tiene ningún
  escenario de sombra con K distinto de producción (E18 a E23, E47, E49 tienen `pub_prod = K`).
- Cómo se ve: rotura R2 (`k_ok = (not censo) or (...)`): PASA con E14, E18, E19, E20, E21, E23, E28, E47, E49, E50, E52;
  ATRAPADA con mis C5 y C7 (`roturas_v2_salida.txt`). Con el analizador sin tocar, C5 (1 distinta de 24 ok: 4 %) cierra, C6
  (1 de 114) no cierra y lista la pasada, C7 (una protegida con `pc_vrp` distinto) cierra: es lo que L18 dice.
- Por qué importa: la sombra es la fase que confirma; si alguien apagara el control ahí, el perfil sombra podría medirse
  contra un K que no es producción sin que nadie lo note.
- Arreglo: un escenario de sombra con una pasada K distinta (cierra) y otro con 1 de 100 o más (no cierra).

### VB-A05 (gravedad 2, confianza 5) «Ninguna protegida» de L18 se decide con `protegida` (tabla más OCR); una rotura que mire sólo la tabla pasa la batería

- Dónde: `evaluar_v750a.py:370` `k_dist_prot = [... if obj[i].get("protegida")]`. Es la lectura correcta (la más
  estricta: una protegida sólo del OCR también cierra), y mi C4 lo confirma (`distintas 1 de 111 (protegidas ['Villarrica
  2026-08-05 06:40']): FALLA`).
- Qué pasa: la rotura R3 (`prot_tabla(obj[i])` en vez de `protegida`) pasa E14, E28, E50 y E52 (todas sus protegidas son de
  tabla) y la atrapa C4 (`roturas_v2_salida.txt`).
- Arreglo: agregar C4.

### VB-A06 (gravedad 1, confianza 5) L2 acepta 7 o más líneas «atrapada por aserción» y no comprueba cuáles son las seis

- Dónde: `evaluar_v750a.py:192-194` (`n_atr >= MIN_MUT_LOCAL`, conteo por subcadena sin nombre de mutación).
- Qué pasa: §6.1 dice «6 de 6 ... (las seis del §4.1)». Un archivo con seis líneas de otras mutaciones, o con ocho, pasa.
  Es la misma familia que VA-09 (marcas de texto) y el autor ya la declaró como límite en L2; lo anoto porque el texto
  nombra las seis y el código no las mira. Dirección: podría dejar pasar una prueba local hecha con otra batería, pero esa
  prueba la escribe el mismo equipo y el archivo se adjunta al PR.
- Arreglo (barato): exigir las seis cadenas `mutación <nombre>` de `equivalencia_v750a.py:182-183` por nombre.

### VB-A07 (gravedad 1, confianza 4) El 1 % con menos de 100 pasadas ok es 0 pasadas, sin que el texto lo diga

- Dónde: `evaluar_v750a.py:374`: `len(k_dist) <= 0.01 * max(1, len(oks0))`. Con 99 ok o menos, una sola distinta cierra
  (`chequeos_estaticos_salida.txt`: 24 → 0, 99 → 0, 100 → 1, 200 → 2). Es la aritmética que V750-B heredó y es coherente
  con «hasta 1 %»; sólo conviene que §7 lo diga («con menos de 100 pasadas, ninguna»), porque la sombra de 4 semanas puede
  tener menos de 100 pasadas ok y ahí la tolerancia es cero de hecho (mi C5: 1 de 24 cierra).

## VERIFICADO LIMPIO

- **Línea base**: `probar_evaluar_v750a.py` contra `evaluar_v750a.py` (9f9ae9259): 53 de 53 OK, «TODOS LOS ESCENARIOS COMO
  SE ESPERA (53)» (`base_salida.txt`). Vara: la salida del autor `probar_evaluar_v750a_salida.txt` dice lo mismo.
- **Mutaciones de D-48** (M15, M29, M50, M52, M53, M54, M55, M56) reproducidas en copias `_v2_` contra los escenarios que
  LECTURAS cita: 8 de 8 ATRAPADAS por aserción, ninguna caída (`mut_autor_v2_salida.txt`). Vara: la columna «prueba que la
  fija» de LECTURAS L2, L4, L7 y L18.
- **Cada línea vieja de las 56 mutaciones del autor aparece exactamente una vez** en el analizador de hoy
  (`chequeos_estaticos_salida.txt`): el medidor no va a dar CAÍDA por una línea que la edición de D-48 haya movido.
- **L7, umbral y dirección**: node directo con el predicado real (`node_tope_50000_salida.txt`): el filtro de cirro corta
  entre 9 y 10,8 MW a 270 K; el de campo difuso entre 45 y 54 MW a 276 K con 150 píxeles; a 278,15 K exactos ninguno corta
  (coherente con `< TMAX_FILTROS_ARTEFACTO`); con `t_max` ausente ninguno corta (coherente con `or 1e9` → no explicada).
- **L7, explicada y sin explicar en la misma población**: C9 lista 1 explicada y 1 sin explicar y cierra.
- **L4, razón vacía**: C8 (ninguna protegida publicada en T) → `T/tabla: M razón sin protegidas` y NO CUMPLE; mi rotura R5
  (razón vacía cumple) la atrapa C8 y no la batería del autor (ver roturas; sin escenario del autor con `rz` None). Lo
  anoto como seguimiento menor, porque en la población real T tiene protegidas de Láscar y además el comparador da SIN
  SUSTRATO en el mismo caso (C8: `T/tabla: M comparador SIN SUSTRATO`), así que la rotura sola no abre adopción.
- **L4, dirección positiva**: C11 (12 protegidas que K no publica y P publica a la magnitud de MIROVA) → razón 1,000 (n 23),
  CUMPLE.
- **L18 en la sombra**: C5, C6, C7 (arriba).
- **Roturas R7 y R8 (pasan todo, y es lo esperado, no un hueco)**: R7 (`t_max` ausente cuenta como explicada) no la
  distingue ningún escenario porque con `t_max` ausente el predicado no filtra y la diferencia no existe (node:
  `K 9 MW t None -> publica 1`, `K x1,2 10,8 MW t None -> publica 1`); R8 (denominador `len(obj)` en vez de `len(oks0)`)
  sólo difiere cuando hay pasadas SIN DATO o no observadas, y la cobertura las acota al 2 % antes de la compuerta
  (`roturas_v2_salida.txt`).
- **Resumen de las 8 roturas propias**: R1 a R6 PASAN la batería del autor y las atrapan mis casos (hallazgos VB-A02 a
  VB-A05 y VB-A01 para R6; R5 anotado arriba); R7 y R8 pasan todo por las razones de la viñeta anterior. Ninguna caída.
- **VA-05 orden**: en E00 la línea de §6.1 precede a la primera de S-1 (líneas 17 y 18 de `v2_base/E00/stdout.txt`).
- **VA-06**: C12, C13, C14 sin caída (`casos_v2_malformados_salida.txt`).
- **VA-08 en el medidor**: `probar` devuelve 2 con cualquier caída (`:630`) y el medidor sólo cuenta ATRAPADA con rc 1
  (`mutar:180-181`): un crash nativo ya no infla el conteo.
- **Etiquetas, P2, M**: no las volví a auditar (la primera vuelta las dio por buenas y el commit de D-48 no las toca:
  `git show 9f9ae9259 -- evaluar_v750a.py` sólo cambia `MIN_MUT_LOCAL`, `TMAX_FILTROS_ARTEFACTO`, el bloque de K =
  producción, el del placebo y `razon_prot`).

## SIN DATO

- La corrida completa del medidor del autor con M53 a M56 (su salida en el repo es la de 52; las copias `_mut_*` en la
  carpeta tienen hora 23:22:05 local y no sé si siguen vivas). No la repetí: 57 corridas de 53 escenarios.
- Las roturas V04 a V41 de la primera vuelta que no tocan las cuatro lecturas: no las repetí (el autor las convirtió en
  M29 a M49; sólo comprobé que sus líneas existen).
- El contrato del productor (celda decisiva, `banda_triangulacion`, `pub_prod`, `pc_vrp`, `mirova_vrp` por canal): el
  analizador lo toma como dado. En particular `mirova_vrp` es un solo número por pasada, y en el canal «tabla» la protegida
  se decide con las filas CONS mientras la razón usa ese número (SOSPECHA: si el generador lo toma del OCR cuando hay fila
  CONS y OCR, la razón del canal tabla usa un VRP que no es el de la tabla).
- Rendimiento con la población real.

## SEGUIMIENTOS (fuera de los dos ejes)

- **F1. `_mirova_confirmed`**: `banco_paridad.py:22` fuerza `_mirova_confirmed = false`, así que en el analizador una
  protegida fría con VRP alto pasa por los filtros de artefacto, y en el tablero real (`index.html:1337`, `:1356`,
  `:1572-1580`) una alerta confirmada por MIROVA no pasa por ellos. Afecta igual a K y a P (no sesga la comparación), pero
  «publica» del analizador no es «publica» del tablero para esa clase. Decisión vieja de `banco_paridad`, no de este
  analizador; conviene dejarlo escrito en LECTURAS.
- **F2. El comparador d′ con P = 0,9 o 1,1 × MIROVA**: en mis C1 y C2 el comparador da NEUTRO en T (10 pares, «sube en
  promedio, no en los pares correctos») y MEJORA en O (14 pares) para una P que reproduce a MIROVA al 90 o al 110 % en
  todas las alertas. Es conducta de `evaluar_d25.decidir_estrato`, sellada en D-28, no del analizador; lo anoto porque
  §6.2 exige MEJORA en las cuatro ventanas y canales, y una P calibrada al 95 % podría no cumplir por el comparador con
  pocos pares (E44 ya muestra SIN SUSTRATO con 4 pares).
- **F3. Sensor de los records sintéticos**: `probar_evaluar_v750a.py:90` usa `VIIRS_NOAA20_750`, así que
  `mirovaEqVrpCore` (`index.html:1295-1309`) devuelve el cúmulo y F5' no entra: coherente con lo que el tablero hace con
  VIIRS 750.

## Dónde están las salidas crudas

Todo en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs750-2-918174\experiments\_s162_v750a\verificador_v2\`:
`LISTA_CAMINOS_previa.md`, `base_salida.txt` (53 escenarios), `casos_v2_salida.txt` (C1 a C11, con C1 y C2 en su primera
versión que esperaba CUMPLE), `casos_v2_bordes_salida.txt` (C1 y C2 rehechos), `casos_v2_malformados_salida.txt` (C12 a
C14), `mut_autor_v2_salida.txt` (8 mutaciones de D-48), `roturas_v2_salida.txt` (R1 a R8), `node_tope_50000_salida.txt`,
`chequeos_estaticos_salida.txt`, y los scripts `ver2_casos.py`, `ver2_roturas.py`, `ver2_mut_autor.py`. Los stdout de
cada escenario quedaron en el scratchpad de la sesión
(`C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile--claude-worktrees-s162-viirs750-2-918174\0c1274cb-99b4-4a91-a624-a9ed2be04812\scratchpad\v2_*`),
que se regeneran con los scripts.
