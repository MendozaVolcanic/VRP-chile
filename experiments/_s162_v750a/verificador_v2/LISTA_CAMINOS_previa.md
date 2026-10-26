# Lista de caminos de falla, segunda vuelta del verificador (escrita ANTES de abrir evaluar_v750a.py, probar_evaluar_v750a.py y mutar_evaluar_v750a.py)

Hora del servidor: `gh api -i repos/MendozaVolcanic/VRP-chile | grep -i ^date` → **Date: Mon, 26 Oct 2026 02:24:05 GMT**.
Commit medido: 9f9ae9259 (rama claude/s162-viirs750-2-918174). Modelo: Claude Fable 5.1 (la primera vuelta fue Sonnet).

Leído hasta aquí: PREREGISTRO_V750A.md, LECTURAS_EVALUAR_V750A.md, verificador/INFORME.md (VA-01 a VA-09),
verificador/LISTA_CAMINOS_previa.md, analizar_v750b.py entero, scripts/banco_paridad.py (predicado con node, CAMPOS_JS,
`_mirova_confirmed` = false siempre), frontend/index.html (mirovaEqVrp, mirovaEqVrpCore, isCirrusArtifact,
isDiffuseFieldArtifact, isValidDetection, isSummitDetection), equivalencia_v750a.py (sólo las líneas que imprimen) y
equivalencia_v750a_salida.txt, el mensaje del commit 9f9ae9259 y su `--stat`.

## (A) Caminos por los que las correcciones de VA-01 a VA-09 podrían no hacer lo que se pidió

A1  VA-01 → L18. El 1 % se calcula sobre un denominador equivocado (después de sacar las distintas, o sobre los objetivos
    y no sobre las ok); el `<=` con pocas pasadas (50 ok permiten 0 distintas; 100 permiten 1) y ningún escenario cruza
    justo el borde.
A2  VA-01 → L18. Las pasadas con K distinto salen de P1, P2 y M pero NO de alguno de los otros brazos o controles
    (control positivo P-def, placebo, nulo del gemelo, S-1, cobertura, lista de protegidas que nadie publica, sombra).
A3  VA-01 → L18. «Ninguna protegida» se decide con `obj.protegida` (tabla más OCR) y no por canal; una protegida sólo de
    tabla o sólo de OCR podría colarse o cerrar de más.
A4  VA-02 → L7. El umbral 278,15 se compara con `<=` en vez de `<`, o contra el `t_max_k` del record de K×1,2 y no del de K
    (son iguales, salvo que la construcción toque ese campo); `t_max_k` None.
A5  VA-02 → L7. Hay una diferencia K contra K×1,2 que NO la explican los dos filtros y el pre-registro dice que «no se
    puede producir»: el tope de 50.000 MW de `mirovaEqVrp` (`vmw > 50000 ? 0`): un K de 45.000 MW publica y por 1,2 no.
    Cerraría la compuerta sin defecto del analizador (dirección segura, pero contradice la frase de §7 y LECTURAS).
A6  VA-02 → L7. La construcción de K×1,2 escala sólo `primary_cluster.vrp_mw` y no `vrp_mw` o `f5_core_vrp_mw` (o al
    revés); el predicado mira los tres (`isSummitDetection` mira `vrp_mw === 0 && discarded_reason`).
A7  VA-03 → L4. La razón de M se calcula con un VRP de P distinto del que publica el tablero (oráculo contra record), o
    con `mirova_vrp` del canal equivocado, o sin exigir `> 0` en alguno de los dos, o la mediana se compara con `<` en
    los bordes (0,9 y 1,1 tienen que cumplir).
A8  VA-03 → L4. Con cero protegidas publicadas por P la razón queda vacía y «cumple vacío» (si K tampoco publica
    protegidas, P1 = 0 también vacío → CUMPLE con una población sin protegidas publicadas).
A9  VA-03 → L4. La razón «al lado» (protegidas que publican K y P) decide en algún canal o ventana por error, o la razón
    de la regla se exige sólo en un canal o ventana (T/O, tabla/todo).
A10 VA-04 → L19. El texto «SIN PROTEGIDAS» sale pero la línea sigue diciendo CUMPLE sin marca en el veredicto final, o
    sale con 1 protegida; BLOQUEA en la sombra sigue pasando (declarado para Nicolás; verificar que esté declarado).
A11 VA-05. S-1 sigue imprimiendo antes de §6.1 en algún camino (por ejemplo cuando §6.1 es SIN DATO), o el JSON por pasada
    no trae (a) y (b) por pasada.
A12 VA-06. Las tres caídas (estado null, Kgeo sin record, sombra sin primary_cluster) siguen cayendo o ahora pasan en
    silencio como «no publica» cambiando una métrica.
A13 VA-07. Las mutaciones nuevas M29 a M56 no reproducen las roturas V01 a V41 (misma etiqueta, otra línea), o los
    escenarios nuevos E28 a E52 están sobredeterminados (atrapan por otra razón que la escrita). Roturas propias `_v2_`
    sobre las reglas que deciden: banda de M (0,85 / 1,15), piso de sustrato de M, bloque de P2 sin volcán, simetría
    tabla/todo y T/O, sombra con la diferencia sólo en «todo».
A14 VA-08. La batería clasifica un código de salida fuera de {0, 3, 5, 6} como CAÍDA, pero el medidor del autor
    (`mutar_evaluar_v750a.py`) sigue contando ATRAPADA con «rc 1 y FALLAS en la línea» aunque haya caídas dentro.
A15 VA-09 → L2. El conteo de «atrapada por aserción» es por subcadena (una línea «NO atrapada por aserción» cuenta); el
    «caída» del control por subcadena; `VERDE:` de un archivo que también trae `ROJA:` de la corrida vieja (la salida real
    guardada tiene las dos corridas y empieza con ROJA, así que un archivo concatenado con la línea base roja no pasa).

## (B) Caminos por los que L2, L4, L7 y L18 podrían estar mal implementadas o mal fijadas

B1  L2. Exige 6 líneas pero el archivo real de `equivalencia_v750a.py` imprime 7 (6 mutaciones más el control); el control
    con «caída» no debe contar como atrapada; con 5 atrapadas y una «caída» que diga también «atrapada» en su texto.
B2  L2. El `VERDE:` viene de la corrida con el módulo y las mutaciones de la corrida `--mutaciones` (sobre el oráculo): el
    analizador no distingue; el pre-registro §6.1 dice «las seis del §4.1» y el analizador no comprueba QUÉ seis (una
    salida con 6 líneas de otra prueba pasa).
B3  L2. El pre-registro §6.1 y LECTURAS L2 dicen 6 de 6 y el código exige otro número (5, o «≥ 6» sin tope: 7 también
    pasa, lo que es defendible pero hay que decirlo).
B4  L4. Ver A7, A8, A9. Además: «publique K o no» pero la razón se restringe a pasadas `oks` tras sacar las K distintas
    (coherente con L18) y a `decide` verdadero; que E31/E32/E33 fijen de verdad la diferencia con la lectura vieja
    (`and pub(i, "K")`): rotura propia `_v2_` que agregue `pub(i, "K")`.
B5  L7. Ver A4, A5, A6. Además: que las diferencias «explicadas» se listen por nombre; que E30 fije las dos mitades (una
    rotura propia que trate todo como explicado debe caer; otra que trate todo como no explicado debe caer).
B6  L7. El placebo de M (K×1,2 en el comparador) usa la publicación de K o la de K×1,2 para armar los pares: si K×1,2 deja
    de publicar en un par, ¿sale del comparador?
B7  L18. Ver A1, A2, A3. Además: en la fase sombra el control K = producción con la misma tolerancia; que el analizador
    imprima la lista por nombre; que la tolerancia se aplique con `max(1, len)`.
B8  Veredicto de adopción falso que las cuatro abren: L18 saca hasta 1 % de pasadas por un criterio que sólo mira K (no
    sesga hacia P salvo correlación de máquina); L7 deja pasar diferencias en frío (si el analizador armara mal K×1,2 sólo
    en records fríos, no se vería); L4 es más estricta (no abre); L2 es más estricta (no abre). Comprobar con escenarios.
B9  Textos: §6.1, §6.2, §7 del pre-registro y L2, L4, L7, L18 de LECTURAS dicen lo mismo que el código (números, `<`/`<=`,
    «publique K o no», «ninguna protegida», «se listan por nombre»).

## Fuera de los dos ejes (para SEGUIMIENTOS)

F1  `_mirova_confirmed` = false en el predicado del analizador: en el tablero real una alerta confirmada por MIROVA no pasa
    por los filtros de artefacto; en el analizador sí. Afecta igual a K y a P (no sesga), pero «publica» del analizador no
    es «publica» del tablero para las protegidas frías con VRP alto.
F2  `mirovaEqVrpCore` devuelve el cúmulo para `*_750`: el predicado de V750 no pasa por F5'. Confirmar que los records
    sintéticos llevan `sensor` terminado en `_750`.
