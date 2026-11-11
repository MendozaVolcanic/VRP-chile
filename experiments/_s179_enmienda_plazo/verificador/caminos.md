# Caminos por los que el borrador ENMIENDA_PLAZO.md podria estar mal
(escrito ANTES de abrir el borrador, el instrumento, el vigilante o el JSON)

## A. Lectura del vigilante (scripts/vigilancia_guardia_modis.py::disparadores)
A1. El plazo no se cuenta como dice: puede ser por noches, por pasadas, por dias calendario o por
    numero de protegidas vistas; el borrador puede confundir "N protegidas" con "N noches".
A2. "vistas" puede no ser lo que el borrador cree (puede exigir record de la guardia, o prod_via,
    o excluir OCR, o deduplicar por noche/volcan/satelite).
A3. "orden": el corte de las primeras N puede ordenarse por fecha de pasada, por fecha de
    proceso o por orden del CSV; empates y orden no determinista.
A4. "dentro_de_plazo" puede aplicarse a cada candidata y no al conjunto; un tope por volcan
    cambiaria que candidatas quedan dentro, no solo cuando cierra.
A5. "duracion" puede ser un tope de dias ademas del conteo (cierre por lo que ocurra primero),
    y el borrador puede ignorar uno de los dos.
A6. vigilancia_guardia_viirs.py puede NO usar la misma funcion (copia en linea, parametros
    distintos, otro N, otro inicio), aunque importe el modulo.
A7. El codigo de main puede diferir del de loop/activo o del worktree: el borrador puede haber
    leido una rama equivocada.

## B. El instrumento ritmo_protegidas.py
B1. Cuenta protegidas de la referencia MIROVA sin exigir que haya record de la guardia (el
    vigilante puede exigirlo): ritmo sobreestimado, cierre mas temprano que el real.
B2. No filtra prod_via (el vigilante puede contar solo pasadas con via), o al reves.
B3. Trata el OCR distinto que el vigilante (lo deja fuera o lo incluye).
B4. Umbral de protegida (>=1 MW), sensor (MODIS vs VIIRS), y dedupe distintos al vigilante.
B5. Ventana 2026-04-09 a 2026-11-09: "fuera de la erupcion" puede depender de donde se corta
    la erupcion de Chillan; la conclusion puede ser artefacto de la ventana elegida.
B6. El tope de 10 por volcan: la conclusion "casi no mueve el cierre fuera de erupcion" puede
    ser cierta solo en mediana y falsa en cola (otros volcanes con rachas: Villarrica, Lascar).
B7. La salida guardada puede no ser reproducible (CSV vivo, corpus que crece, A90).
B8. El script puede leer datos del arbol de trabajo (loop/activo) y no de main.
B9. Con tope por volcan, si solo 1 o 2 volcanes dan protegidas MODIS, el plazo podria no
    cerrar nunca (o en meses): riesgo que el borrador puede no decir.
B10. Simulacion del cierre: puede usar un ritmo medio en vez de reproducir la ventana movil.

## C. Estado de hoy
C1. "13 de 29 en MODIS, todas de Chillan": el JSON de origin/main puede decir otro numero, otro
    denominador (29 puede ser otro N), o no todas de Chillan.
C2. "cierre hacia el 2026-11-20" puede ser extrapolacion con ritmo de erupcion que no dura.
C3. El JSON puede estar atrasado respecto del remoto (A25, regla 5 frescura).
C4. El plazo de VIIRS puede tener otro estado y el borrador lo omite.

## D. Implementacion propuesta (§5)
D1. "el orden se recalcula cada corrida": puede haber estado persistido (lista de vistas en
    el JSON) que no se recalcula; un tope cambiaria retroactivamente candidatas ya contadas.
D2. "sin cambiar dentro_de_plazo una candidata de un volcan con tope quedaria fuera de plazo":
    depende de como dentro_de_plazo decide (por indice en el orden o por fecha de corte).
D3. El tope puede romper la regla de reversion sellada de VIIRS (misma funcion compartida).
D4. Tests/guards que fijan el comportamiento actual y que el borrador no menciona.
D5. Un tope hace que una protegida perdida de Chillan despues de la 10a no dispare: riesgo de
    apagar la vigilancia justo en el volcan en erupcion. El borrador puede minimizarlo.

## E. Marca A113 (§4)
E1. Dice mas que lo medido (generaliza de MODIS a VIIRS, de la ventana a "siempre", de un tope
    a "cualquier tope").
E2. Cita numeros que no salen del script.
E3. No conserva el texto viejo o no propaga a los hijos (regla sellada, ficha, bloque).

## F. Forma
F1. Numeros transcritos a mano que no coinciden con ritmo_protegidas_salida.txt.
F2. Guiones largos, voseo, rutas relativas.
