# D-47: tres lecturas de la quinta adenda, ratificadas antes del tag de lectura de D25

**Decidida por Nicolás el 2026-10-23** (hora del servidor ~19:23 UTC), antes del tag de lectura y sin haber abierto
V1, V2a, V2b ni el brazo del 17 al 19 de octubre. Origen: verificador con contexto limpio de D-45
(`experiments/_s159/instrumentos/verificador_d45/INFORME.md`, V45-01 y V45-02, y su juicio de las lecturas de A9).
Respuesta textual, registrada por la sesión dueña del loop (S161): «Sí a D-47: ratifico las tres lecturas como
recomiendas (signo común de la noche en el placebo c, orden de los bloques por su clave con la versión de numpy anotada
en el registro, y D-34 y D-42 informados con su propio mínimo), sin cambio de código.»

1. **`ADENDA_SIGNOS_P2.md` §6, placebo (c)**: lo que fija el nulo es el **signo común** de la noche (todas las pasadas
   tocadas de una noche llevan el mismo signo), no que todas se apaguen o todas se enciendan. El paréntesis «(todas se
   apagan o todas se encienden)» se lee como descripción imprecisa de eso (V45-01). Es lo que hace
   `placebo_signos.py` (LECTURA 5 del implementador).
2. **§2.5, valor-p por sorteos (B de 21 o más)**: los bloques se recorren en el orden de su clave (volcán y fecha UTC,
   la de `contribuciones_p2`), como hace el código (V45-02). La versión de numpy con que se corra la lectura se anota en
   su registro, porque el generador de numpy fija la secuencia de sorteos. Versión local al ratificar: numpy 2.4.4,
   Python 3.12.10 (`requirements.txt` pide `numpy>=1.24`).
3. **§3**: el resultado de D-34 y el de D-42 se informan cada uno con **su propio mínimo** (D-34 §5.6: menos de 5
   pasadas o menos de 3 noches, SIN SUSTRATO), no con el de D-45 (LECTURA 1 del implementador).

Sin cambio de código: las tres lecturas son las que el evaluador de `7eb91eb5e` ya implementa.
