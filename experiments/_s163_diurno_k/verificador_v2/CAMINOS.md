# Caminos de ruptura (verificador v2), escritos ANTES de abrir el evaluador, verificador/INFORME.md y el §12

Base: sólo leí PREREGISTRO.md §0 a §11 (l. 1 a 446). No abrí evaluar_diurno_k.py, ni verificador/, ni el §12.

C1. Día/noche: el pre-registro define día por elevación solar > 0 sobre el volcán; MIROVA puede cortar día/noche con otro ángulo
    (crepúsculo). Una pasada de crepúsculo queda como "diurna" aquí y "nocturna" para MIROVA (o al revés), y se compara contra la
    vara equivocada.
C2. Negativo por periodo: (a) el periodo nocturno por día UTC mezcla dos noches distintas (madrugada y atardecer) en volcanes
    donde la noche cruza 00 UTC; (b) en el sur (Puyehue, Chaitén) el día cruza 00 UTC y se parte en dos "días"; (c) el negativo
    exige volcán-sensor-día-periodo SIN alerta: condiciona la población a días callados, y la tasa Q_d medida ahí subestima la
    tasa operacional (sesgo hacia ADOPTAR).
C3. "Observado": ¿qué es una pasada observada por el brazo? Si el store sólo escribe records cuando hay detección, observada
    == publicada y Q_d/denominadores son tautológicos; si falta record y se excluye, el denominador se achica en silencio.
C4. "Publica" por el predicado del tablero (isValidDetection): puede tener condiciones que, para un record diurno, no
    fallan/no pasan por razones ajenas (p. ej. campos nocturnos, f5_core, distance_class). Si el predicado excluye records
    diurnos, el brazo no publica nunca y se lee como callado.
C5. I2 / I6 que no pueden fallar: I2 pide "records con diag_umbrales_diurnos" (basta uno por ventana y sensor); I6 placebo con
    brazo callado da SIN SUSTRATO y no falla. La protección real queda en I4, I5, D y el nulo.
C6. Control sintético "observado, no publica" se asigna a toda pasada diurna donde el brazo tiene record: si el brazo tiene
    record en pasadas que el control no procesó por otra razón, el +1/-1 se atribuye mal; y la alerta_mb recuperada cuenta -1
    para el brazo aunque sea reflejo.
C7. Ventanas con dos regímenes: W2 a W6 cruzan #535 (2026-08-28 23:00 UTC), el OCR versión 30.0 (2026-08-06), tabla que se
    corta el 2026-10-19. El brazo corre todo con un solo código (tag), pero los records de producción que hacen de "control
    nocturno" para Q_n y el nulo vienen de #883 (reprocesado con K): ¿mismo régimen que el brazo?
C8. Referencia congelada distinta de la del sustrato: el evaluador exige sha256 iguales a sustrato_k.json; ¿se comprueba de
    verdad, y sustrato_k.json fue hecho con el mismo árbol 047bd5692? Cifras del §3 vs sustrato_k_salida.txt.
C9. Prueba de signos por bloque volcán-día con asimetría extrema (10 alertas bajo 1 MW vs 2.246 negativos): GANA exige >=5
    bloques con -1 neto; la prueba cuenta bloques, no pasadas, así que 40 falsas en un solo bloque pesan como 1; el neto cuenta
    pasadas. Dos unidades distintas en la misma regla. Bloque mixto (+1 y -1 en el mismo bloque): ¿se netea o se cuenta aparte?
C10. D (binomial): independencia falsa (declarada); con Q_d = 0 y X >= 1 cumple siempre (un solo acierto por reflejo basta);
     X mezcla protegidas y bajo 1 MW, con n observadas distinto del conjunto del que sale Q_d.
C11. Tabla de casos: huecos y precedencia. Caso b (neto <= 0, P >= 1, D) ADOPTAR con neto=0 incluye publicar tantas falsas como
     alertas_mb recuperadas; caso c con "SIN CAMBIO si el brazo no publica ninguna pasada diurna": ¿cuenta publicaciones en
     "otra"? Caso a no exige P >= 1 ni D. Publicaciones en "otra" (325 pasadas) y de >=1 MW en negativos no frenan nada.
C12. Veredicto global: combinación SIN CAMBIO + ADOPTAR / NO ADOPTAR, y que los dos sensores comparten un solo flag.
C13. Robustez 6.4: variantes que cambian el conjunto (sin W2, sin reflejo) pero comparten D y e-ii; "después de marcar los días
     con alerta" para la exclusión; la variante de reflejo de 12° usa ángulos del punto reportado (no de la escena).
C14. I4c: p_sup del nocturno de producción (0 de 2.715; 9 de 2.650) como vara de cobertura diurna; el umbral deja pasar
     hasta 6 (V375) y 21 (V750) pasadas sin record, que pueden ser justo las alertas protegidas (I4a lo cubre sólo si es por
     alerta). Y el denominador de Q_d/n se achica por esas pasadas.
C15. Nulo del §5.1: 200 repeticiones con SE ~1,5 puntos no certifica "no más de 5 %" con 5,0 % observado (e-i en V750); la
     grilla q >= 0,5 % no explora q muy bajos, que es donde el caso b es alcanzable por azar; el brazo aleatorio no tiene la
     estructura de un brazo real (agrupado en volcanes, horas, reflejo), así que el nulo mide la regla bajo un brazo que no
     existe.
C16. Mutaciones: 48 de 48 "atrapadas por aserción" pueden ser mutaciones triviales; no cubren la tabla de casos de §6.2
     por completo; mutar.py cuenta como atrapada sólo si falla por aserción, pero ¿la suite cubre fronteras (<= vs <)?
C17. Costo del §8: 11 x 83 x (2,2 + 5,5) min es una cuenta con minutos por volcán-día derivados de una corrida sobre C0 con
     Test 1; y los timeouts.
C18. Protecciones de la adenda sellada (G1, G2, G3) y del pre-registro original que se pierden al reemplazar: G2 (tan callada
     como MIROVA de día) desaparece; e-ii la compensa sólo si Nicolás decide.
C19. Cita Tabla 1 (K1 -0,6, C1 0,02, C2 15 de día) y las dos diferencias del código MIROVA (K1 -0,5, filtro 12° l. 83 a 89):
     comprobar contra PDF renderizado y .m.
C20. El criterio de victoria en MISSION.md: ¿dice que lo que importa es la clase de la alerta (protegida >= 1 MW) por pasada o por
     noche? El §6 trabaja por pasada; criterio puede decir por noche (A94: unidad que vive el operador). Y puntos 1 a 5:
     ¿falta alguno (p. ej. P1b "arriba")?
