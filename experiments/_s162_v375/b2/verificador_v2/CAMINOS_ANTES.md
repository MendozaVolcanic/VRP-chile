# Caminos de ruptura, escritos ANTES de leer las salidas commiteadas y el informe del verificador v1
Hora del servidor (header Date de gh api): Sat, 24 Oct 2026 19:35:18 GMT. Leí solo: PREREGISTRO_B2.md, PREREGISTRO_B.md,
PREREGISTRO_C.md §5.5, y evaluar.py (código). No he abierto aún seleccion_b2_salida, tamano_b2_salida, objetivos, ni verificador/INFORME.md.

C1 (decide B2 sola): `en_decide` toma neg_pub de S162 y el resto de `--deciden S162b`; pero `decidir()` corre también global/V375-D/valida_en_O
   sobre un conjunto sin protegidas ni pos_bajo (puede romper o imprimir basura), y `acuerdo` (4b) compara 4 claves: si B coincide pero
   `global` no, ¿"NO RESUELTO" se aplica a B o a otras? Ruptura: correr con B2 falsa y mirar si crashea y qué dice 4b para B.
C2 (pesos de neg_pub): `repesar` usa meta[neg_pub][h].N / n; ¿N de neg_pub en meta es 133 o 113? La rama "censo" (suma de pesos == n) decide
   si el IC es exacto o Wilson; si N=113 el neg_pub quedaría como censo con IC puntual y la cota 36,5 % del tamaño no se cumpliría.
   También: N_neg['neg_pub'] y tasa_k_neg (133/3456) vs el conjunto que decide.
C3 (muestra): disjunta de S159 y S162 por id, pero ¿también por pasada partida / mismo volcán-noche? ¿Del marco (neg_resto = K no publica, RUTINA/0,05 MW SN)?
   ¿Proporcional por estrato volcán x cenit? ¿Excluye 12, 13, 17-20 oct? ¿La semilla 163 reproduce el sha? ¿meta del evaluador (S162) tiene todos los estratos de B2?
   ¿La muestra es sorteada del remanente y se pondera con N completo del estrato (sesgo de muestreo sin reposición tras 4 eventos conocidos)?
C4 (potencia/error en frontera): tamano_b2.py supone tasa pareja, neg_pub fijo en su cota 36,5 %; ¿usa la misma regla que evaluar.py (Wilson sobre Kish, pesos, ponderación 133/3323)?
   ¿simula el error en la frontera con la cota de neg_pub variable (el neg_pub de S162 es observado, no sorteado)? ¿tasa observada 1,16 % ponderada es la de B (4/389 -> 1,03 % crudo)?
   Dependencia intra-noche (pasadas del mismo volcán y noche) no entra en la simulación.
C5 (workflow): ¿probe-s162-v375-b2.yml corre el mismo árbol (ca034d66e), la misma lista de brazos, 48x25=1200, apunta al objetivo b2 correcto, ruta/artefactos, timeouts, matriz max-parallel 8, y NO cae en el desfase de 'Earthdata token' (A71)?
C6 (control que no puede fallar): `vacios` para lote sin pasadas ok; cobertura por lote (umbral > 10 %: cuenta contra o a favor); el nulo/PLACEBO sobre filas de B2; el control positivo corre sobre protegidas de S162/S159 (no B2): no controla el lote B2.
   Un lote B2 que corra con un port muerto (npix=0 por falla de grilla) daría 0 de 1200 = SILENCIO ACOTADO: ¿qué impide eso? (control 6 y 4 usan otras clases).
C7 (hitos A108/A104): la tasa del lote B2 cruza el 28-ago (#535): estratos por tramo T/O1/O2 se informan, pero la regla no los separa.
C8 (la regla "pasadas partidas" y 'no observadas' de #904): re-ponderar al quitar no observadas cambia N por estrato.
