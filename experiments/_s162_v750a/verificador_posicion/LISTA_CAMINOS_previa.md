# Lista previa de caminos de falla (escrita ANTES de abrir el código nuevo)

Hora del servidor (header Date de gh api): Wed, 28 Oct 2026 02:05:37 GMT. Vara: PREREGISTRO_V750A.md §3 y §6 bis (leídos antes de esta lista; el código del diff, no).

## A. Los brazos de posición no miden lo que dicen
A1. P-cercano y P-pico no comparten detección ni VRP con P (recalculan el .m o filtran píxeles distintos).
A2. P-cercano elige el alertado más cercano a la celda central de la grilla en vez de al cráter (el vent), o mide en grados / en índices de celda sin la métrica UTM.
A3. P-cercano mide la distancia desde el centro de la grilla (la regla GEO: centro = cráter?) cuando el vent_lat/lon difiere de él.
A4. P-pico: "mayor M13" confundido con mayor contraste, mayor NTI, mayor VRP de celda, o mayor radiancia en M15; empates de M13 resueltos por orden de índice (inestable) en vez de por una regla declarada.
A5. P-pico promedia el cúmulo 8-conexo (el pre-registro dice "el píxel solo, sin promediar su cúmulo").
A6. P-cercano / P-pico usan distancia a la celda en vez de al centroide, o clasifican con el inner_radius equivocado (3 a 20 km por volcán).
A7. Pasada sin alertados: los brazos de posición producen None/NaN y rompen la métrica, o publican algo.
A8. La clase summit/far se calcula con `<` vs `<=` distinto entre brazos y el predicado del tablero.
A9. Los brazos nuevos no entran a los controles de §7 (nulo, placebo) o entran al placebo K×1,2 por error.

## B. E_lejana no es lo que dice el §6 bis
B1. far_ref mal definida: debía ser "fila FALSO_POSITIVO de la tabla y NINGUNA ALERTA" en la pasada; el código puede incluir pasadas con ALERTA, con RUTINA, o excluir por el lado contrario.
B2. Con la tabla sola, las FALSO_POSITIVO del OCR no deben contar (el canal OCR); si el código mezcla canales, E_lejana con tabla sola estaría contaminada.
B3. E_lejana cuenta pasadas en que el brazo "publica", pero usa el predicado equivocado (el de hotspot detectado en vez del del tablero: summit + isValidDetection).
B4. E_lejana no entra a P2' en el mismo bloque noche-volcán (se suma por pasada, o en bloques propios), o se suma a E en la dirección equivocada (el signo del par P contra brazo).
B5. P2' no usa `regla_signos_p2` de D-45 (tag s161-d25-lectura) sino una variante.
B6. Las pasadas far_ref que sólo existen en el canal de V750-B (adenda 2) se cuelan a las métricas P1, P1b, M, P2 y negativos limpios existentes: negativos limpios, denominadores, "elegibles".
B7. Ventana ±120 s de pareo: far_ref pareadas con la tolerancia de las protegidas.
B8. Si no hay far_ref (adenda 2 sin sellar / sin corrida), el analizador debe declarar SIN DATO, no 0.

## C. La regla elige mal en alguna rama
C1. "Elegible": P1 = 0 en T y en O, con tabla sola Y con tabla más OCR. Puede mirar sólo un canal, o sólo T.
C2. "Gana": P2' contra P sobre T ∪ O con el canal que decide (¿cuál?), Y tabla sola no peor (GANA o EMPATE o SIN SUSTRATO con neto en 0 o a favor). Ramas: SIN SUSTRATO con neto en contra, PIERDE/BLOQUEA tratados como empate.
C3. Si ganan los dos, menor E + E_lejana; empate: P-pico. Puede resolver al revés, o comparar sólo E sin E_lejana.
C4. Si ninguno gana: P si es elegible. Si P no elegible: elegible no peor que P (en ambos canales). Si ninguno: NINGUNA POSICIÓN ELEGIBLE, y P no se adopta (el §6 no debe poder devolver ADOPTAR).
C5. Cuando P no es elegible, un brazo elegible "gana" se evalúa contra P (no elegible): la rama del "no peor" no es la de "gana".
C6. El §6 se evalúa después sobre P "con la posición elegida"; el código puede seguir evaluando P radiante, o dejar el brazo elegido sin reemplazar P también en M y en equivalencia.
C7. Multiplicidad: dos contrastes, 5 % una cola, sin corregir, declarada la probabilidad; el código puede aplicar Bonferroni (contra pre-registro) o no declararla.
C8. Descriptivas (pasadas que cambian, alertados en far_ref, distancia desde la celda central vs Distancia_km con OCR sólo desde 2026-06-13) afectan el veredicto por accidente.

## D. Lecturas L20 a L27
D1. Contradicen el texto del §3/§6 bis (vara cambiada por la lectura sin pasar por Nicolás).
D2. Abren un veredicto falso (p. ej. una lectura que permite "gana" con SIN SUSTRATO en el canal decisor).
D3. Resuelven una ambigüedad a favor del brazo candidato (en vez de lo conservador).
D4. Citan líneas/escenarios que no existen.

## E. Contaminación de métricas existentes
E1. Las far_ref se suman a los denominadores de P1/P2/M o a los negativos limpios.
E2. Un cambio en cómo se indexa la referencia cambia las salidas de los 61 escenarios viejos (la batería 74/74 pasa, pero ¿con salida idéntica a la anterior en los viejos? comparar con probar_evaluar_v750a_salida.txt de 699e2d04f).
E3. El orden de impresión/estructura cambia y rompe consumidores (verificador, verificador_v2).

## F. Escenarios y mutaciones pasan por la razón equivocada
F1. Un escenario "rojo antes" que cae por excepción (KeyError) y no por aserción sobre el valor.
F2. Escenarios con datos tan degenerados que cualquier regla da el mismo resultado (el escenario no discrimina radiante/cercano/pico).
F3. Mutaciones que "se atrapan" porque rompen todo (crash), no por la aserción del escenario concernido (el autor dice "por aserción": comprobar).
F4. Mutaciones equivalentes (cambio sin efecto) contadas como atrapadas, o mutaciones que no tocan la línea que dicen.
F5. El control de caída / identidad: la identidad (mutación nula) debe dar 0 caídas.
F6. Piezas sin cubrir declaradas: (a) E_lejana con tabla sola excluye FALSO_POSITIVO del OCR; (b) "elegible" mira también tabla más OCR.
F7. Determinismo: empates, orden de dict/set, argsort inestable (A152) en la elección de cercano/pico.

## G. Otros
G1. Unidades: km vs m, haversine vs plano UTM, grados.
G2. Los archivos de salida *_salida.txt guardados no corresponden al código del commit (md5 / hora).
G3. Mensajes con guiones largos (guion largo y guion medio) en archivos nuevos (regla del dueño).
G4. El pre-registro §11 dice "74 de 74" y "18 de 18": verificar.
