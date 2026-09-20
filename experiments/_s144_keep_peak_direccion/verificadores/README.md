# Scripts de los siete verificadores del frente `keep_peak` con dirección (S144)

**Por qué están acá.** Los números del cierre del frente
(`docs/CIERRE_FRENTE_KEEP_PEAK_S144.md`) no salieron de la medida pre-registrada, que nunca se corrió:
salieron de los **nulos y controles** que cada verificador con contexto limpio midió para decidir si el
diseño de esa ronda servía. Esos scripts vivían en carpetas temporales de la sesión y se iban a borrar.
Quedan acá para que cualquiera pueda reproducir un número del cierre sin creerle a un documento.

**Qué es cada carpeta** (una por ronda; el informe de cada una está en
`docs/PREREGISTRO_KEEP_PEAK_DIRECCION_S144_VERIFICADOR*.md`):

| carpeta | ronda | qué midió que quedó en el cierre |
|---|---|---|
| `r1` | 1 | semillas de Lastarria en alertas y RUTINA; control G; perfil radial del exceso local |
| `r2` | 2 | alcanzabilidad de las clases; compatibilidad de radio por volcán (1 de 19 fuera de Lastarria, 12 de 15 en Lastarria) |
| `r3` | 3 | el nulo del control reflejado (+0,10): el máximo sobre el disco mide textura del flanco |
| `r4` | 4 | la maldición del ganador con el control temporal (+0,0835) y la persistencia de los sitios |
| `r5` | 5 | imagen propia contra cruzada (+0,1091 contra +0,0145); residuo por banda de separación; brazo de otra noche (+0,0005) |
| `r6` | 6 | descomposición del estrato hermano (+0,0120 = -0,0355 de suelo + 0,0476 de sitio); potencia de la regla |
| `r7` | 7 | el estadístico final sobre el estrato hermano (+0,0514, de los cuales +0,0441 permanente); nulo N1 en cero |

**Cómo correrlos.** Esperan los datos que `experiments/_s144_conteo_tif/conteo_tif.py` deja en
`experiments/_s144_conteo_tif/_dl_tif/` (índice, TIF y referencia CONS/OCR), que **no** están
versionados por tamaño. Bajarlos primero con ese script. Varios scripts escriben `.pkl` intermedios en
su propia carpeta; esos no se versionaron.

**Qué NO son.** No son código de producción ni de la medida pre-registrada: son instrumentos de
auditoría, escritos por agentes distintos con contexto limpio, sin revisión cruzada entre ellos. Cada
número que usa el cierre dice de qué ronda viene, y el informe de esa ronda dice con qué script se
reproduce.
