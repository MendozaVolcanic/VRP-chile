# MIROVA Vulcano (Campus et al. 2024) — ground truth de Npix en régimen débil

**Fuente**: OSF https://osf.io/jepv6/ (abierto) · Paper: Campus, Coppola, Laiolo et al.
(2024), *Bulletin of Volcanology* 86:25, https://doi.org/10.1007/s00445-024-01721-z

**Descargado**: S124 (2026-08-26). Verificado: tamaños exactos vs la API de OSF
(27.703 y 80.768 bytes), CSV ASCII, no truncado.

## Por qué importa para VRP Chile

Es la **única publicación del grupo MIROVA que expone `Npix`** — el número de
píxeles que su sistema alerta por imagen — sobre un blanco de **señal débil**
(campo fumarólico de Vulcano, VIIRS 375 m, VRP 0,02-1,1 MW). Es el análogo más
cercano al régimen donde VRP Chile sub-reporta (Lascar/Isluga/Lastarria).

**Columnas S1**: Date · Zenith · Azimuth · **Npix** · L_MIRhot · L_MIRbk · VRP [W]
**S2**: serie de BT de dos píxeles de referencia (cráter y fondo), con o sin alerta.

## El dato que refuta la hipótesis del halo (S124)

Sobre 354 alertas:

| Npix | alertas | % |
|---|---|---|
| **1** | 191 | **54,0 %** |
| 2 | 97 | 27,4 % |
| 3 | 38 | 10,7 % |
| 4-6 | 28 | 7,9 % |

**Mediana = 1 píxel.** MIROVA tampoco integra un halo en régimen débil. Por lo
tanto el déficit de VRP Chile no viene del conteo de píxeles sino del **exceso de
radiancia por píxel** (ΔL = L_hot − L_bk).

Verificación de la Eq. 3 con estos datos: `VRP = 18,0 × 140.625 × ΔL` reproduce
la columna VRP al dígito (fila 1: 18,0 × 140625 × 0,0240415 = 60.855,05 W ✓).

Su ΔL mediano en alertas de 1 px = 0,0434 W m⁻² µm⁻¹ sr⁻¹, o sea el **13,1 %**
de la radiancia del píxel.
