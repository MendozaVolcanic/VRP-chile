Hora del servidor (GitHub, header Date): Wed, 28 Oct 2026 04:57:01 GMT. Escrito ANTES de abrir el pre-registro.

# Caminos por los que un pre-registro y un evaluador de este tipo pueden estar mal

C1. Una regla obliga a decidir despues de mirar los datos (umbral, corte o estrato definido en funcion del resultado; "se
    decide al ver").
C2. El evaluador implementa otra cosa que el documento (constante distinta, comparador > vs >=, denominador distinto,
    estrato distinto, orden de aplicacion).
C3. Una regla sellada heredada (P1, P1b, P2, M, Chillan) cambio sin decirlo, o el documento la declara conservada y no lo esta.
C4. Un escenario de la bateria pasa por construccion (el dato lo fabrica el mismo codigo que evalua; la asercion es tautologica).
C5. Una mutacion clasificada como atrapada solo hizo caer el programa (excepcion) y no una asercion; o el medidor
    cuenta como atrapada una mutacion que no cambia el comportamiento.
C6. Un control (nulo, positivo, negativo) que no puede fallar, o cuyo nulo no se midio (A110).
C7. Una ventana de datos que cruza un regimen (#535 2026-08-28 23:00 UTC, K 2026-09-18, #883 reproceso, calidad de
    referencia MIROVA A119, OCR hasta 2026-06-13) y mezcla dos detectores (A104).
C8. Una cifra citada (en el documento) que no esta en su fuente, o esta con otra definicion/ventana/denominador (A90, A93).
C9. Un brazo de posicion que no cambia lo que el tablero lee: el predicado de publicacion (isValidDetection/mirovaEqVrp)
    lee otros campos que los que el brazo modifica, de modo que los tres brazos publican igual (A116, A118).
C10. Un flag/geometria que no llega a todos sus consumidores en la via (A118): la via cambia en una etapa y otra etapa
    la deshace; el A/B mide cableado y no el brazo.
C11. Veredicto del documento incompatible con el criterio de victoria de MISSION.md (alerta protegida >=1 MW perdida,
    simetria bajo 1 MW, regla SN de D-9, lectura A de 439 pasadas, informar tabla sola y combinado).
C12. Cobertura despareja entre brazos (pasadas de menos por cortes NASA, A108) no contada antes del veredicto.
C13. Etiqueta positiva o negativa limpia mal definida (RUTINA vs "MIROVA no vio", clase NONE, OCR instable A119, MODIS
    plano todo el año vs VIIRS desde abril).
C14. Estratos con n tan chico que el criterio no tiene poder (un "cumple" que no podia no cumplirse); falta de poder
    declarada o no.
C15. Funcion estadistica importada (evaluar_d25) usada con otra firma/semantica, o con un default distinto al del sello.
C16. La regla "decidir sin mirar" depende de un paso humano no especificado; excepciones ("o lo que parezca razonable").
C17. El evaluador lee un archivo de resultados cuyo esquema el A/B real no produce (nombres de campos, sensor, hora UTC).
C18. Orden de aplicacion de P1/P2/M tal que una regla enmascara otra; empates; division por cero; estrato vacio que
    da "CUMPLE" por vacuidad.
C19. Dia/noche: MODIS L1B con sol (la via diurna) mezclada con la nocturna; criterio de noche inconsistente con el tablero.
C20. Semantica de "protegida" (>=1 MW de MIROVA) y de "proxy" (distancia/clase) y ventana de tiempo de pareo (+-?) distinta
    a la del censo.
