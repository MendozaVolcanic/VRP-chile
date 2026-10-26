# Caminos por los que los arreglos de la segunda vuelta podrian estar mal (tercera vuelta, escritos ANTES de abrir el codigo)

Hora del servidor de GitHub: Mon, 26 Oct 2026 12:59:12 GMT. Material: commit 1166cea70 (rama s162-modd-candado), diff ff2ced531..1166cea70.
Antes de escribir esto solo lei el informe de la segunda vuelta (VCR-01 a VCR-11) y la lista de archivos cambiados; no abri codigo.

## A. Arreglos de la bateria (VCR-01, VCR-02, VCR-07, VCR-08)
1. Una prueba nueva pasa por la razon equivocada: usa una fila cuyo resultado no depende del orden de las reglas, o exige un
   texto que el codigo produce por otra via. Se ve mutando: la mutacion que debia caer sigue viva o cae por excepcion, no por aserción.
2. La prueba de VCR-01 junta veto de P1 y protegida fuera, pero el veto sale por un camino donde la regla (b) ni se evalua.
3. La prueba de VCR-02 no cubre negativos y bajo 1 MW con K publicando (las dos etiquetas), solo una.
4. Las pruebas de `externos_de_entrada` usan monkeypatch tan fuerte que no ejercen el `--commit` ni el manifiesto reales.
5. `probar_probe_paquete.py` exige `k33_slim` pero la mutacion que lo quita no cae por aserción.
6. Las mutaciones nuevas (6) tienen sustituciones que ya no aparecen exactamente una vez en el codigo de hoy (SUSTITUCION INVALIDA),
   o su "identidad" (sin mutar) no pasa todas las pruebas, o cuentan una caida por excepcion como atrapada.
7. Las 31 anteriores se corrieron sobre ff2ced531: alguna sustitucion toca una zona que cambió (`control_cobertura`, `veredicto`,
   `externos_de_entrada`, `main`) y hoy ya no hace lo mismo, o ya no aplica.

## B. Logica nueva de `control_cobertura` (VCR-06)
8. Pasar las protegidas fuera del denominador por el predicado del evaluador falla (excepcion, None, KeyError) cuando la fila no
   tiene `k_slim`/`slim` (volcan fuera del granulo, escena invalida, error de bajada): un rojo falso que deja INDECIDIBLE un censo sano.
9. La comparacion predicado vs runner usa tipos distintos (0/1, bool, None) y difiere por forma, no por contenido.
10. El caso que antes daba DECIDE NICOLAS ahora cae en rojo y se pierde la regla (b) aprobada; o el rojo se reporta pero el
    veredicto no lo toma (control en rojo sin `_rojo`).
11. Una protegida con el predicado en un lado y el runner en el otro al reves (predicado dice si, runner dice no) no se detecta.
12. Costo: el predicado llama a node por fila; para 1.232 granulos puede disparar el tiempo, o el predicado se llama sin lote.

## C. `--commit` exacto (VCR-04)
13. Exige 40 caracteres pero la cabecera trae el sha en mayusculas, con espacios o corto; o rechaza el sha valido del tag anotado
    (sha del tag vs sha del commit al que apunta).
14. La comparacion exacta contra una lista: con varios commits en cabeceras un caso valido se rechaza, o un invalido pasa.
15. La prueba de `--commit` pasa un sha de 40 caracteres inventado y no el flujo de `main`.

## D. Apendice de la adenda 4 y reglas selladas
16. El apendice cambia una regla sellada (umbral, definicion de «K publica», orden del §6, denominador) diciendo que no.
17. El apendice contradice el codigo (dice una cosa del control 5 y el codigo hace otra) o la adenda 3.6.
18. La fecha o la hora declarada es anterior al commit; o cita numeros (31, 37, 41 archivos) que no coinciden con el repo.
19. Se reabrio una decision aprobada por la coordinadora (regla (b)) al reformularla.

## E. M con la regla de MATLAB (`m_con_regla_matlab.py`, `delaunay_perturbado.py`)
20. El script SI edita el evaluador (reescribe `evaluar_paquete.py` o lo monkeypatchea en el archivo) en vez de ser aparte.
21. Su prueba pasa vacuamente: usa un caso donde la regla vieja y la de MATLAB dan igual, o compara el resultado consigo mismo;
    no tiene un caso que pueda fallar (sin control negativo ni mutacion).
22. «regla de MATLAB» aqui es una aproximacion (Delaunay perturbado) que no reproduce fillmissing2 en bloques 2x2, y el script
    lo presenta como identica; el 191/191 de la comparacion no es lo que el script ejecuta.
23. Lee datos por ruta absoluta de otro proyecto, o escribe fuera de su carpeta, o depende de scipy no fijada.
24. El script no esta en el manifiesto y alguien lo puede cambiar tras el tag sin que se vea (o esta y es innecesario).

## F. Manifiesto y workflow
25. El manifiesto de 41 archivos no coincide con los blobs de 1166cea70 (se regeneró antes del ultimo commit y quedo desfasado).
26. Los archivos nuevos (m_con_regla_matlab.py, delaunay_perturbado.py, verificadores) no estan en el manifiesto aunque los lee el evaluador, o sobran.
27. El workflow: la clave `on` quedo sin comillas y se lee como booleano; el paso de la bateria del vacio agrega una linea tras el
    `grep` y se rompe el truco de VCR-09; el job usa un manifiesto distinto del que `--comprobar` valida.
28. El workflow dispara por una rama/ruta que no existe o por `push` sin filtro y corre el humo sin querer.
29. Salidas guardadas (probar_*_salida.txt, ensayo_en_seco_salida.txt) son anteriores al ultimo cambio de codigo y ya no reflejan el commit.

## G. Efecto cruzado
30. Los arreglos movieron lineas y los comentarios `file:line` del PREREGISTRO ya no apuntan donde dicen.
31. Docstrings y textos de VCR-10 corregidos pero con otra contradiccion nueva (ej. «adendas 1 a 4» pero el codigo hace la 5).
32. El diff incluye cambios fuera de lo pedido (alguna regla sellada tocada de paso).
