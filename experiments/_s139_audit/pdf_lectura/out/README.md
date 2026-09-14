# Salidas de `pdf_lectura` (S139, tanda 2)

## NO COMMITEAR LOS PNG

Los `*.png` de esta carpeta son **páginas renderizadas de papers con derechos de autor**
(Geological Society Special Publications, Taylor & Francis, Elsevier, MDPI). El repositorio
`VRP-chile` es **público**. Subirlos sería redistribuir el paper completo.

Regla: los PNG se generan cuando se necesitan y se borran o se dejan fuera del índice. Si
alguna sesión futura necesita mirar una página, la vuelve a generar con

```
PYTHONIOENCODING=utf-8 python experiments/_s139_audit/pdf_lectura/render_paginas.py sp426.5.pdf 5 6 7
```

Los PDF de origen viven en `documentacion/` (que sí está en el repo desde antes; eso es una
decisión previa y no la toca esta auditoría).

El `inventario.json` sí es seguro: son conteos por página, no contenido del paper.

## Qué hay acá

| archivo | qué es |
|---|---|
| `inventario.json` | conteos por página (imágenes, dibujos, captions, ecuaciones) de los 6 PDF de prioridad 1 |
| `sp426_5_p0NN.png` | páginas renderizadas de Coppola et al. 2016a SP 426.5 |
| `zoom_p5_*.png`, `zoom_p8_*.png`, `zoom_p4_*.png` | recortes de ecuaciones y rótulos de panel |
| `Rapid_Response_..._p0NN.png` | páginas de Coppola et al. 2025 (Fernandina) |
| `coppola2014_..._p0NN.png` | páginas de Coppola et al. 2014 IJRS |
