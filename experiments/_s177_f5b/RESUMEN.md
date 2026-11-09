# S177: F5b re-corrido con la mancha saturada conservada

Encargo aprobado por Nicolás el 2026-11-08 (decisión 17 de la auditoría S175). Autor: agente Sonnet, `INFORME.md` y scripts de esta carpeta.
Verificador limpio Opus: `verificador/INFORME.md`, veredicto **SE SOSTIENE EN PARTE**. Lo que vale es este resumen: donde el `INFORME.md` del autor dice más, manda el verificador.

## Qué se puede decir de las láminas PNG en Chillán

Durante la erupción, el foco satura la paleta de la lámina y aparece como una mancha blanca de varias celdas. F5b la borraba y elegía un píxel del borde. Corregida la máscara:

- **Nuestro punto cae dentro o al lado de la mancha saturada** de la lámina (CONFIRMADO, cifras reproducidas por el verificador con selector propio).
- **Eso no prueba que el foco de MIROVA coincida con el nuestro.** El foco está fijo en el cráter y la lámina tiene una celda de precisión, así que una identidad perfecta y una coincidencia de cráter dan casi el mismo resultado: la prueba contra el nulo con igual geometría no tiene poder para decidirlo (V177-01, gravedad 3).
- **«Las 4 protegidas del hallazgo 351 ya no están desplazadas» no se sostiene como CONFIRMADO** (V177-02, gravedad 3): con control por centroide 1 pasa a la clase de coincidencia y 3 quedan fuera. Si la mancha contiene el foco de MIROVA o no, depende de qué celda se tome: SOSPECHA.
- MODIS, fuera de Chillán, y cuál píxel de la mancha es «el» foco: SIN DATO.

## Decisión práctica

**No se publica ninguna posición de MIROVA en Chillán como medición de posición.** La frase honesta es «nuestro punto cae en la mancha saturada». Cerrarlo necesita un par TIF y lámina con anomalía fuerte en Chillán, y MIROVA tiene los TIF congelados desde el 2026-09-22.
