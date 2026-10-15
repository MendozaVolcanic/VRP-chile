# Verificación del probe D25 en VIIRS 750 (run 38679955131)

Scripts: `C:\Users\nmend\AppData\Local\Temp\claude\verifd25\` (v2.py a v5.py, rerun.txt).

**1. Reproducción. CONFIRMADO.** `analizar_probe.py` vuelve a dar una salida idéntica (`diff` vacío) a `probe_resultado.txt`.

**2. El 100 % del brazo a viene de la selección del detector, no del cableado.**
- La magnitud es el exceso de UN píxel. En los cúmulos de un píxel da 0,072 MW/K en los negativos y 0,085 en las alertas (el README dice ~0,08). La mediana de 0,172 MW son unos 2,5 K. No hay nada que sume de más.
- El fondo NO queda bajo el píxel por construcción: 403 de los 1.555 píxeles alertados de los negativos quedan bajo sus vecinos. Pero las 268 pasadas tienen al menos un píxel positivo, y su cúmulo primario sale positivo. El píxel ya se eligió por estar sobre sus vecinos en NTI (inferido del diseño, SIN VERIFICAR píxel a píxel).
- Lectura que sostienen los datos: «todo cúmulo que hoy alertamos publica con D25», no «D25 contra MIROVA». D25 sí separa por magnitud: el AUC del VRP del brazo a entre alertas y negativos es 0,861. En las 28 rescatadas, nuestra magnitud dividida por la de MIROVA tiene mediana 1,19, y 13 caen entre 0,8 y 1,25. Lo que falla es la detección, que alerta donde MIROVA no alerta (A98); D25 sólo lo destapa porque el piso de magnitud es 0.

**3. C-P1. CONFIRMADO, sin efecto en el veredicto.**
- Isluga 2026-06-10 05:36 (entre los 268): el control elige un cúmulo `far` a 24,9 km. Sin ella quedan 267 de 267.
- Llaima 2026-06-07 (control_publica): mismos 21 píxeles, 0,17 MW contra 1,335 (`focal_degraded`).
- Las 14 con L1B reprocesado se comportan igual que el resto.

**4. Las 2 que apaga b. No son protegidas** (sin alerta de MIROVA): Puyehue Cordón Caulle 2026-08-07 05:54 y Villarrica 2026-07-17 06:42. La variante saca los vecinos fríos, el fondo se arma con píxeles más lejanos y tibios, y queda sobre el píxel.

**5. Wilson. CONFIRMADO** (recalculado aparte): en a, 24,62 contra 268; en b, 20,39 contra 200,9.

**6. VIIRS 375: SIN EVIDENCIA.** No medí cuántas pasadas de V375 en negativos limpios quedan detectadas pero en cero. Se transfiere sólo la forma: con piso 0, D25 hace publicar todo cúmulo alertado que supere a sus vecinos.

**Veredicto global: PARCIAL.** Los números y el NO VALE de los dos brazos, sobre la detección de hoy, quedan CONFIRMADOS. Lo que no se sostiene es cerrar D25 en V750 como «fondo equivocado»: la magnitud que da en las alertas se parece a la de MIROVA. El cierre debe quedar condicionado a la detección actual (A95, A114), y medirse de nuevo si esta cambia (conectiva, caja, D22).

**Defectos propios:**
- El analizador reescribió `resultado_probe.json` en el worktree. Es un archivo no rastreado y quedó idéntico byte a byte (`cmp`).
- El píxel del cúmulo lo emparejé por temperatura.
- No revisé la posición de los rescates (A107).
