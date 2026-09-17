# Batería de mutaciones del evaluador

> Generada por `experiments/_s143_evaluador/mutaciones.py` el 2026-09-17T19:48:43+00:00, 1 corrida(s) por mutación. Suite de referencia: `34 passed in 2.90s`. Mueren 25 de 27; viven 2, todas declaradas como inocuas o equivalentes. Ningún número está escrito a mano.

| id | archivo | qué cambia | esperado | estado |
|---|---|---|---|---|
| M1 | evaluar.py | invierte la cota de mismo objeto | muerta | **muerta** |
| M2 | evaluar.py | no le exige la cota al brazo (revierte el hallazgo 2) | muerta | **muerta** |
| M3 | evaluar.py | da vuelta el signo del bootstrap | muerta | **muerta** |
| M4 | evaluar.py | bootstrap sin estratificar | muerta | **muerta** |
| M5 | evaluar.py | criterio 2 decide con el extremo BAJO del intervalo | muerta | **muerta** |
| M6 | evaluar.py | criterio 3 sin exigir que publiquen los dos | muerta | **muerta** |
| M7 | evaluar.py | fila de MIROVA: OCR antes que CONS | muerta | **muerta** |
| M8 | evaluar.py | cobertura ciega a las pasadas de más del brazo | muerta | **muerta** |
| M9 | evaluar.py | cobertura ciega a product_version | muerta | **muerta** |
| M10 | evaluar.py | n mínimo contado en los pares y no en las pos del control | muerta | **muerta** |
| M11 | evaluar.py | magnitud del brazo tomada del control | muerta | **muerta** |
| M12 | fusionar.py | fusión que no avisa conflictos entre tramos | muerta | **muerta** |
| M13 | evaluar.py | sólo cambia un comentario | viva | **viva** |
| M15 | evaluar.py | criterio 2 filtra por la etiqueta del brazo y no la del control | viva | **viva** |
| M16 | evaluar.py | criterio 3 con la desigualdad invertida | muerta | **muerta** |
| M17 | evaluar.py | bootstrap sin semilla | muerta | **muerta** |
| M18 | evaluar.py | sin filtro de pasada diurna | muerta | **muerta** |
| M19 | evaluar.py | la noche se acepta siempre (cota apagada) | muerta | **muerta** |
| M20 | evaluar.py | tolerancia de magnitud 0,05 a 0,10 | muerta | **muerta** |
| M21 | evaluar.py | criterio 1 cumple con hasta una pérdida | muerta | **muerta** |
| M22 | evaluar.py | los volcanes desparejos ya no se excluyen | muerta | **muerta** |
| M23 | evaluar.py | brazo sin pares decisivos deja de contar como que empeora | muerta | **muerta** |
| M24 | evaluar.py | cota por defecto 0,55 a 5,0 km | muerta | **muerta** |
| M25 | evaluar.py | campo de posición que decide, fijado en el código en vez de leerlo del archivo | muerta | **muerta** |
| M26 | evaluar.py | reancla TODOS los records al final_hotspot, no sólo los del Test 1 | muerta | **muerta** |
| M27 | evaluar.py | el criterio 1 que decide deja de seguir al parámetro | muerta | **muerta** |
| M28 | evaluar.py | las noches confirmadas dejan de seguir al parámetro | muerta | **muerta** |

## Las que viven, y por qué

- **M13**: cambia un comentario. Si muriera, la batería estaría midiendo otra cosa.
- **M15**: equivalente. La etiqueta `neg_limpio` la fija la referencia de MIROVA, que es
  la misma para el control y para el brazo en la misma pasada, así que filtrar por una o
  por otra selecciona el mismo conjunto. No es un hueco de cobertura.
