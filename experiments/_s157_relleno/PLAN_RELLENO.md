# Plan de relleno del historico con K (S157)

Generado por `armar_relleno.py`; CMR y LAADS consultados el 2026-10-20T11:32:20Z (APIs publicas, sin credenciales).
NO despachado: lo lanza la sesion duena del loop.

## Antes de despachar

1. **El PR del merge que conserva la base tiene que estar mergeado.** Con el merge anterior, relanzar
   unos pocos dias de un volcan escribe su JSON SOLO con esos dias y borra el resto del historico en main.
2. **En serie, uno a la vez**, esperando que termine cada run (incluido su job `merge`): todos usan el
   perfil `_s154_reproc_k_historico`, que es el grupo de concurrencia `reproc-chunked-_s154_reproc_k_historico`, el mismo de los
   relanzamientos de NevadosDeChillan. GitHub guarda UN solo run pendiente por grupo: un tercero
   despachado mientras otro espera lo EXPULSA.
3. Despues de cada run, contar las pasadas del volcan en la ventana contra la serie operacional (A108):
   un run verde con un corte de CMR puede volver a no traerlas.

## Resumen por version del record operacional

Decision por pasada: CMR si respondio (es donde busca `fetch.py`); si CMR no dio dato, el listado
publico del archivo LAADS DAAC (donde se baja el estandar). `existe` exige L1B **y** geolocalizacion.

| product_version | decision (fuente) | pasadas |
|---|---|---|
| `nrt` | no_existe (LAADS (CMR sin dato)) | 58 |
| `standard` | existe (LAADS (CMR sin dato)) | 31 |

**CMR no respondio en 89 de 89 pasadas** (HTTP 500 en la busqueda de
granulos). Esas decisiones salen de LAADS: antes de despachar, volver a correr este script y
confirmar con CMR, porque un archivo en LAADS que CMR no indexa no lo encontraria el pipeline.

## Despachos (en este orden, uno a la vez)

1. PlanchonPeteroa, 2025-04-09 a 2025-04-09 (1 dias)

```bash
gh workflow run reproc-chunked.yml --repo MendozaVolcanic/VRP-chile --ref main -f profile=_s154_reproc_k_historico -f volcanoes=PlanchonPeteroa -f start=2025-04-09 -f end=2025-04-09 -f max_days=1
```

2. PlanchonPeteroa, 2025-10-01 a 2025-10-01 (1 dias)

```bash
gh workflow run reproc-chunked.yml --repo MendozaVolcanic/VRP-chile --ref main -f profile=_s154_reproc_k_historico -f volcanoes=PlanchonPeteroa -f start=2025-10-01 -f end=2025-10-01 -f max_days=1
```

3. Chaiten, 2025-10-18 a 2025-10-18 (1 dias)

```bash
gh workflow run reproc-chunked.yml --repo MendozaVolcanic/VRP-chile --ref main -f profile=_s154_reproc_k_historico -f volcanoes=Chaiten -f start=2025-10-18 -f end=2025-10-18 -f max_days=1
```

4. Copahue, 2026-03-07 a 2026-03-07 (1 dias)

```bash
gh workflow run reproc-chunked.yml --repo MendozaVolcanic/VRP-chile --ref main -f profile=_s154_reproc_k_historico -f volcanoes=Copahue -f start=2026-03-07 -f end=2026-03-07 -f max_days=1
```

5. PuyehueCordonCaulle, 2026-04-25 a 2026-04-25 (1 dias)

```bash
gh workflow run reproc-chunked.yml --repo MendozaVolcanic/VRP-chile --ref main -f profile=_s154_reproc_k_historico -f volcanoes=PuyehueCordonCaulle -f start=2026-04-25 -f end=2026-04-25 -f max_days=1
```

6. Copahue, 2026-07-02 a 2026-07-02 (1 dias)

```bash
gh workflow run reproc-chunked.yml --repo MendozaVolcanic/VRP-chile --ref main -f profile=_s154_reproc_k_historico -f volcanoes=Copahue -f start=2026-07-02 -f end=2026-07-02 -f max_days=1
```

7. Copahue, 2026-07-05 a 2026-07-05 (1 dias)

```bash
gh workflow run reproc-chunked.yml --repo MendozaVolcanic/VRP-chile --ref main -f profile=_s154_reproc_k_historico -f volcanoes=Copahue -f start=2026-07-05 -f end=2026-07-05 -f max_days=1
```

8. PuyehueCordonCaulle, 2026-07-13 a 2026-07-13 (1 dias)

```bash
gh workflow run reproc-chunked.yml --repo MendozaVolcanic/VRP-chile --ref main -f profile=_s154_reproc_k_historico -f volcanoes=PuyehueCordonCaulle -f start=2026-07-13 -f end=2026-07-13 -f max_days=1
```

9. PlanchonPeteroa, 2026-07-27 a 2026-07-27 (1 dias)

```bash
gh workflow run reproc-chunked.yml --repo MendozaVolcanic/VRP-chile --ref main -f profile=_s154_reproc_k_historico -f volcanoes=PlanchonPeteroa -f start=2026-07-27 -f end=2026-07-27 -f max_days=1
```

10. PuyehueCordonCaulle, 2026-09-11 a 2026-09-11 (1 dias)

```bash
gh workflow run reproc-chunked.yml --repo MendozaVolcanic/VRP-chile --ref main -f profile=_s154_reproc_k_historico -f volcanoes=PuyehueCordonCaulle -f start=2026-09-11 -f end=2026-09-11 -f max_days=1
```

## Pasadas sin producto estandar (repetir el trozo no las traeria)

- Chaiten 2026-08-05 05:30 VIIRS_SNPP (record `nrt`, LAADS (CMR sin dato))
- Chaiten 2026-08-05 05:30 VIIRS_SNPP_750 (record `nrt`, LAADS (CMR sin dato))
- Chaiten 2026-08-06 05:12 VIIRS_SNPP (record `nrt`, LAADS (CMR sin dato))
- Chaiten 2026-08-06 05:12 VIIRS_SNPP_750 (record `nrt`, LAADS (CMR sin dato))
- Chaiten 2026-08-06 06:54 VIIRS_SNPP (record `nrt`, LAADS (CMR sin dato))
- Chaiten 2026-08-06 06:54 VIIRS_SNPP_750 (record `nrt`, LAADS (CMR sin dato))
- Copahue 2026-08-05 05:30 VIIRS_SNPP (record `nrt`, LAADS (CMR sin dato))
- Copahue 2026-08-05 05:30 VIIRS_SNPP_750 (record `nrt`, LAADS (CMR sin dato))
- Copahue 2026-08-06 05:12 VIIRS_SNPP (record `nrt`, LAADS (CMR sin dato))
- Copahue 2026-08-06 05:12 VIIRS_SNPP_750 (record `nrt`, LAADS (CMR sin dato))
- Copahue 2026-08-06 06:48 VIIRS_SNPP (record `nrt`, LAADS (CMR sin dato))
- Copahue 2026-08-06 06:48 VIIRS_SNPP_750 (record `nrt`, LAADS (CMR sin dato))
- Isluga 2026-08-05 05:24 VIIRS_SNPP (record `nrt`, LAADS (CMR sin dato))
- Isluga 2026-08-05 05:24 VIIRS_SNPP_750 (record `nrt`, LAADS (CMR sin dato))
- Isluga 2026-08-06 05:06 VIIRS_SNPP (record `nrt`, LAADS (CMR sin dato))
- Isluga 2026-08-06 05:06 VIIRS_SNPP_750 (record `nrt`, LAADS (CMR sin dato))
- Isluga 2026-08-06 06:42 VIIRS_SNPP (record `nrt`, LAADS (CMR sin dato))
- Isluga 2026-08-06 06:42 VIIRS_SNPP_750 (record `nrt`, LAADS (CMR sin dato))
- Lascar 2026-08-05 05:24 VIIRS_SNPP (record `nrt`, LAADS (CMR sin dato))
- Lascar 2026-08-05 05:24 VIIRS_SNPP_750 (record `nrt`, LAADS (CMR sin dato))
- Lascar 2026-08-06 05:06 VIIRS_SNPP (record `nrt`, LAADS (CMR sin dato))
- Lascar 2026-08-06 05:06 VIIRS_SNPP_750 (record `nrt`, LAADS (CMR sin dato))
- Lascar 2026-08-06 06:48 VIIRS_SNPP (record `nrt`, LAADS (CMR sin dato))
- Lascar 2026-08-06 06:48 VIIRS_SNPP_750 (record `nrt`, LAADS (CMR sin dato))
- Lastarria 2026-08-05 05:24 VIIRS_SNPP (record `nrt`, LAADS (CMR sin dato))
- Lastarria 2026-08-05 05:24 VIIRS_SNPP_750 (record `nrt`, LAADS (CMR sin dato))
- Lastarria 2026-08-06 05:06 VIIRS_SNPP (record `nrt`, LAADS (CMR sin dato))
- Lastarria 2026-08-06 05:06 VIIRS_SNPP_750 (record `nrt`, LAADS (CMR sin dato))
- Lastarria 2026-08-06 06:48 VIIRS_SNPP (record `nrt`, LAADS (CMR sin dato))
- Lastarria 2026-08-06 06:48 VIIRS_SNPP_750 (record `nrt`, LAADS (CMR sin dato))
- Llaima 2026-08-05 05:30 VIIRS_SNPP (record `nrt`, LAADS (CMR sin dato))
- Llaima 2026-08-05 05:30 VIIRS_SNPP_750 (record `nrt`, LAADS (CMR sin dato))
- Llaima 2026-08-06 05:12 VIIRS_SNPP (record `nrt`, LAADS (CMR sin dato))
- Llaima 2026-08-06 05:12 VIIRS_SNPP_750 (record `nrt`, LAADS (CMR sin dato))
- Llaima 2026-08-06 06:48 VIIRS_SNPP (record `nrt`, LAADS (CMR sin dato))
- Llaima 2026-08-06 06:48 VIIRS_SNPP_750 (record `nrt`, LAADS (CMR sin dato))
- PlanchonPeteroa 2026-08-05 05:30 VIIRS_SNPP (record `nrt`, LAADS (CMR sin dato))
- PlanchonPeteroa 2026-08-05 05:30 VIIRS_SNPP_750 (record `nrt`, LAADS (CMR sin dato))
- PlanchonPeteroa 2026-08-06 05:06 VIIRS_SNPP (record `nrt`, LAADS (CMR sin dato))
- PlanchonPeteroa 2026-08-06 05:06 VIIRS_SNPP_750 (record `nrt`, LAADS (CMR sin dato))
- PlanchonPeteroa 2026-08-06 06:48 VIIRS_SNPP (record `nrt`, LAADS (CMR sin dato))
- PlanchonPeteroa 2026-08-06 06:48 VIIRS_SNPP_750 (record `nrt`, LAADS (CMR sin dato))
- PuyehueCordonCaulle 2026-08-05 05:30 VIIRS_SNPP (record `nrt`, LAADS (CMR sin dato))
- PuyehueCordonCaulle 2026-08-05 05:30 VIIRS_SNPP_750 (record `nrt`, LAADS (CMR sin dato))
- PuyehueCordonCaulle 2026-08-06 05:12 VIIRS_SNPP (record `nrt`, LAADS (CMR sin dato))
- PuyehueCordonCaulle 2026-08-06 05:12 VIIRS_SNPP_750 (record `nrt`, LAADS (CMR sin dato))
- PuyehueCordonCaulle 2026-08-06 06:48 VIIRS_SNPP (record `nrt`, LAADS (CMR sin dato))
- PuyehueCordonCaulle 2026-08-06 06:48 VIIRS_SNPP_750 (record `nrt`, LAADS (CMR sin dato))
- PuyehueCordonCaulle 2026-08-06 06:54 VIIRS_SNPP (record `nrt`, LAADS (CMR sin dato))
- PuyehueCordonCaulle 2026-08-06 06:54 VIIRS_SNPP_750 (record `nrt`, LAADS (CMR sin dato))
- Tupungatito 2026-08-05 05:24 VIIRS_SNPP (record `nrt`, LAADS (CMR sin dato))
- Tupungatito 2026-08-05 05:24 VIIRS_SNPP_750 (record `nrt`, LAADS (CMR sin dato))
- Tupungatito 2026-08-05 05:30 VIIRS_SNPP (record `nrt`, LAADS (CMR sin dato))
- Tupungatito 2026-08-05 05:30 VIIRS_SNPP_750 (record `nrt`, LAADS (CMR sin dato))
- Tupungatito 2026-08-06 05:06 VIIRS_SNPP (record `nrt`, LAADS (CMR sin dato))
- Tupungatito 2026-08-06 05:06 VIIRS_SNPP_750 (record `nrt`, LAADS (CMR sin dato))
- Tupungatito 2026-08-06 06:48 VIIRS_SNPP (record `nrt`, LAADS (CMR sin dato))
- Tupungatito 2026-08-06 06:48 VIIRS_SNPP_750 (record `nrt`, LAADS (CMR sin dato))

## Pasadas faltantes

| Volcan | Pasada | Sensor | Trozo | Record | Decision | CMR L1B / GEO | LAADS L1B / GEO | CMR NRT L1B |
|---|---|---|---|---|---|---|---|---|
| Chaiten | 2025-10-18 05:00 | VIIRS_NOAA20 | 7 | `standard` | existe (LAADS (CMR sin dato)) | sin dato / sin dato | VJ102IMG.A2025291.0500.021.2025291112216.nc / VJ103IMG.A2025291.0500.021.2025291100424.nc | sin dato |
| Chaiten | 2025-10-18 06:36 | VIIRS_NOAA20 | 7 | `standard` | existe (LAADS (CMR sin dato)) | sin dato / sin dato | VJ102IMG.A2025291.0636.021.2025291135439.nc / VJ103IMG.A2025291.0636.021.2025291122227.nc | sin dato |
| Chaiten | 2025-10-18 06:42 | VIIRS_NOAA20 | 7 | `standard` | existe (LAADS (CMR sin dato)) | sin dato / sin dato | VJ102IMG.A2025291.0642.021.2025291133011.nc / VJ103IMG.A2025291.0642.021.2025291122250.nc | sin dato |
| Chaiten | 2026-08-05 05:30 | VIIRS_SNPP | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Chaiten | 2026-08-05 05:30 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Chaiten | 2026-08-06 05:12 | VIIRS_SNPP | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Chaiten | 2026-08-06 05:12 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Chaiten | 2026-08-06 06:54 | VIIRS_SNPP | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Chaiten | 2026-08-06 06:54 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Copahue | 2026-03-07 07:35 | MODIS_AQUA | 11 | `standard` | existe (LAADS (CMR sin dato)) | sin dato / sin dato | MYD021KM.A2026066.0735.061.2026066191026.hdf / MYD03.A2026066.0735.061.2026066153019.hdf | sin dato |
| Copahue | 2026-07-02 04:42 | VIIRS_NOAA20_750 | 14 | `standard` | existe (LAADS (CMR sin dato)) | sin dato / sin dato | VJ102MOD.A2026183.0442.021.2026183114516.nc / VJ103MOD.A2026183.0442.021.2026183103325.nc | sin dato |
| Copahue | 2026-07-02 06:24 | VIIRS_NOAA20_750 | 14 | `standard` | existe (LAADS (CMR sin dato)) | sin dato / sin dato | VJ102MOD.A2026183.0624.021.2026183130544.nc / VJ103MOD.A2026183.0624.021.2026183121825.nc | sin dato |
| Copahue | 2026-07-05 05:06 | VIIRS_SNPP | 14 | `standard` | existe (LAADS (CMR sin dato)) | sin dato / sin dato | VNP02IMG.A2026186.0506.002.2026186131009.nc / VNP03IMG.A2026186.0506.002.2026186125120.nc | sin dato |
| Copahue | 2026-07-05 06:48 | VIIRS_SNPP | 14 | `standard` | existe (LAADS (CMR sin dato)) | sin dato / sin dato | VNP02IMG.A2026186.0648.002.2026186151805.nc / VNP03IMG.A2026186.0648.002.2026186145731.nc | sin dato |
| Copahue | 2026-08-05 05:30 | VIIRS_SNPP | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Copahue | 2026-08-05 05:30 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Copahue | 2026-08-06 05:12 | VIIRS_SNPP | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Copahue | 2026-08-06 05:12 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Copahue | 2026-08-06 06:48 | VIIRS_SNPP | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Copahue | 2026-08-06 06:48 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Isluga | 2026-08-05 05:24 | VIIRS_SNPP | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Isluga | 2026-08-05 05:24 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Isluga | 2026-08-06 05:06 | VIIRS_SNPP | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Isluga | 2026-08-06 05:06 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Isluga | 2026-08-06 06:42 | VIIRS_SNPP | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Isluga | 2026-08-06 06:42 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Lascar | 2026-08-05 05:24 | VIIRS_SNPP | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Lascar | 2026-08-05 05:24 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Lascar | 2026-08-06 05:06 | VIIRS_SNPP | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Lascar | 2026-08-06 05:06 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Lascar | 2026-08-06 06:48 | VIIRS_SNPP | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Lascar | 2026-08-06 06:48 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Lastarria | 2026-08-05 05:24 | VIIRS_SNPP | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Lastarria | 2026-08-05 05:24 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Lastarria | 2026-08-06 05:06 | VIIRS_SNPP | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Lastarria | 2026-08-06 05:06 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Lastarria | 2026-08-06 06:48 | VIIRS_SNPP | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Lastarria | 2026-08-06 06:48 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Llaima | 2026-08-05 05:30 | VIIRS_SNPP | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Llaima | 2026-08-05 05:30 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Llaima | 2026-08-06 05:12 | VIIRS_SNPP | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Llaima | 2026-08-06 05:12 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Llaima | 2026-08-06 06:48 | VIIRS_SNPP | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Llaima | 2026-08-06 06:48 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| PlanchonPeteroa | 2025-04-09 04:30 | VIIRS_SNPP_750 | 2 | `standard` | existe (LAADS (CMR sin dato)) | sin dato / sin dato | VNP02MOD.A2025099.0430.002.2025099124749.nc / VNP03MOD.A2025099.0430.002.2025099122620.nc | sin dato |
| PlanchonPeteroa | 2025-04-09 04:36 | VIIRS_SNPP_750 | 2 | `standard` | existe (LAADS (CMR sin dato)) | sin dato / sin dato | VNP02MOD.A2025099.0436.002.2025099124758.nc / VNP03MOD.A2025099.0436.002.2025099122622.nc | sin dato |
| PlanchonPeteroa | 2025-04-09 04:54 | VIIRS_NOAA20 | 2 | `standard` | existe (LAADS (CMR sin dato)) | sin dato / sin dato | VJ102IMG.A2025099.0454.021.2025099111108.nc / VJ103IMG.A2025099.0454.021.2025099100039.nc | sin dato |
| PlanchonPeteroa | 2025-04-09 04:54 | VIIRS_NOAA20_750 | 2 | `standard` | existe (LAADS (CMR sin dato)) | sin dato / sin dato | VJ102MOD.A2025099.0454.021.2025099111108.nc / VJ103MOD.A2025099.0454.021.2025099100039.nc | sin dato |
| PlanchonPeteroa | 2025-04-09 05:48 | VIIRS_NOAA21 | 2 | `standard` | existe (LAADS (CMR sin dato)) | sin dato / sin dato | VJ202IMG.A2025099.0548.021.2025099124726.nc / VJ203IMG.A2025099.0548.021.2025099100853.nc | sin dato |
| PlanchonPeteroa | 2025-04-09 05:48 | VIIRS_NOAA21_750 | 2 | `standard` | existe (LAADS (CMR sin dato)) | sin dato / sin dato | VJ202MOD.A2025099.0548.021.2025099124726.nc / VJ203MOD.A2025099.0548.021.2025099100853.nc | sin dato |
| PlanchonPeteroa | 2025-04-09 06:12 | VIIRS_SNPP_750 | 2 | `standard` | existe (LAADS (CMR sin dato)) | sin dato / sin dato | VNP02MOD.A2025099.0612.002.2025099145555.nc / VNP03MOD.A2025099.0612.002.2025099143424.nc | sin dato |
| PlanchonPeteroa | 2025-04-09 06:36 | VIIRS_NOAA20 | 2 | `standard` | existe (LAADS (CMR sin dato)) | sin dato / sin dato | VJ102IMG.A2025099.0636.021.2025099130221.nc / VJ103IMG.A2025099.0636.021.2025099122646.nc | sin dato |
| PlanchonPeteroa | 2025-04-09 06:36 | VIIRS_NOAA20_750 | 2 | `standard` | existe (LAADS (CMR sin dato)) | sin dato / sin dato | VJ102MOD.A2025099.0636.021.2025099130221.nc / VJ103MOD.A2025099.0636.021.2025099122646.nc | sin dato |
| PlanchonPeteroa | 2025-10-01 04:54 | VIIRS_SNPP_750 | 7 | `standard` | existe (LAADS (CMR sin dato)) | sin dato / sin dato | VNP02MOD.A2025274.0454.002.2025274131217.nc / VNP03MOD.A2025274.0454.002.2025274123629.nc | sin dato |
| PlanchonPeteroa | 2025-10-01 05:18 | VIIRS_NOAA20_750 | 7 | `standard` | existe (LAADS (CMR sin dato)) | sin dato / sin dato | VJ102MOD.A2025274.0518.021.2025274111444.nc / VJ103MOD.A2025274.0518.021.2025274101037.nc | sin dato |
| PlanchonPeteroa | 2025-10-01 06:06 | VIIRS_NOAA21_750 | 7 | `standard` | existe (LAADS (CMR sin dato)) | sin dato / sin dato | VJ202MOD.A2025274.0606.021.2025274121346.nc / VJ203MOD.A2025274.0606.021.2025274115500.nc | sin dato |
| PlanchonPeteroa | 2025-10-01 06:36 | VIIRS_SNPP_750 | 7 | `standard` | existe (LAADS (CMR sin dato)) | sin dato / sin dato | VNP02MOD.A2025274.0636.002.2025274150833.nc / VNP03MOD.A2025274.0636.002.2025274144505.nc | sin dato |
| PlanchonPeteroa | 2026-07-27 05:18 | VIIRS_NOAA20_750 | 15 | `standard` | existe (LAADS (CMR sin dato)) | sin dato / sin dato | VJ102MOD.A2026208.0518.021.2026208111143.nc / VJ103MOD.A2026208.0518.021.2026208101657.nc | sin dato |
| PlanchonPeteroa | 2026-08-05 05:30 | VIIRS_SNPP | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| PlanchonPeteroa | 2026-08-05 05:30 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| PlanchonPeteroa | 2026-08-06 05:06 | VIIRS_SNPP | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| PlanchonPeteroa | 2026-08-06 05:06 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| PlanchonPeteroa | 2026-08-06 06:48 | VIIRS_SNPP | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| PlanchonPeteroa | 2026-08-06 06:48 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| PuyehueCordonCaulle | 2026-04-25 05:06 | VIIRS_NOAA21 | 12 | `standard` | existe (LAADS (CMR sin dato)) | sin dato / sin dato | VJ202IMG.A2026115.0506.021.2026115103004.nc / VJ203IMG.A2026115.0506.021.2026115101102.nc | sin dato |
| PuyehueCordonCaulle | 2026-04-25 06:00 | VIIRS_NOAA20_750 | 12 | `standard` | existe (LAADS (CMR sin dato)) | sin dato / sin dato | VJ102MOD.A2026115.0600.021.2026115122752.nc / VJ103MOD.A2026115.0600.021.2026115114402.nc | sin dato |
| PuyehueCordonCaulle | 2026-04-25 06:48 | VIIRS_NOAA21 | 12 | `standard` | existe (LAADS (CMR sin dato)) | sin dato / sin dato | VJ202IMG.A2026115.0648.021.2026115120003.nc / VJ203IMG.A2026115.0648.021.2026115115031.nc | sin dato |
| PuyehueCordonCaulle | 2026-07-13 02:05 | MODIS_TERRA | 14 | `standard` | existe (LAADS (CMR sin dato)) | sin dato / sin dato | MOD021KM.A2026194.0205.061.2026194131825.hdf / MOD03.A2026194.0205.061.2026194093425.hdf | sin dato |
| PuyehueCordonCaulle | 2026-07-13 07:00 | MODIS_AQUA | 14 | `standard` | existe (LAADS (CMR sin dato)) | sin dato / sin dato | MYD021KM.A2026194.0700.061.2026194193117.hdf / MYD03.A2026194.0700.061.2026194152315.hdf | sin dato |
| PuyehueCordonCaulle | 2026-07-13 08:40 | MODIS_AQUA | 14 | `standard` | existe (LAADS (CMR sin dato)) | sin dato / sin dato | MYD021KM.A2026194.0840.061.2026194191852.hdf / MYD03.A2026194.0840.061.2026194164612.hdf | sin dato |
| PuyehueCordonCaulle | 2026-08-05 05:30 | VIIRS_SNPP | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| PuyehueCordonCaulle | 2026-08-05 05:30 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| PuyehueCordonCaulle | 2026-08-06 05:12 | VIIRS_SNPP | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| PuyehueCordonCaulle | 2026-08-06 05:12 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| PuyehueCordonCaulle | 2026-08-06 06:48 | VIIRS_SNPP | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| PuyehueCordonCaulle | 2026-08-06 06:48 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| PuyehueCordonCaulle | 2026-08-06 06:54 | VIIRS_SNPP | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| PuyehueCordonCaulle | 2026-08-06 06:54 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| PuyehueCordonCaulle | 2026-09-11 05:36 | VIIRS_SNPP | 16 | `standard` | existe (LAADS (CMR sin dato)) | sin dato / sin dato | VNP02IMG.A2026254.0536.002.2026254120727.nc / VNP03IMG.A2026254.0536.002.2026254114313.nc | sin dato |
| PuyehueCordonCaulle | 2026-09-11 05:54 | VIIRS_NOAA20 | 16 | `standard` | existe (LAADS (CMR sin dato)) | sin dato / sin dato | VJ102IMG.A2026254.0554.021.2026254132052.nc / VJ103IMG.A2026254.0554.021.2026254123047.nc | sin dato |
| PuyehueCordonCaulle | 2026-09-11 07:25 | MODIS_AQUA | 16 | `standard` | existe (LAADS (CMR sin dato)) | sin dato / sin dato | MYD021KM.A2026254.0725.061.2026254194954.hdf / MYD03.A2026254.0725.061.2026254152820.hdf | sin dato |
| Tupungatito | 2026-08-05 05:24 | VIIRS_SNPP | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Tupungatito | 2026-08-05 05:24 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Tupungatito | 2026-08-05 05:30 | VIIRS_SNPP | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Tupungatito | 2026-08-05 05:30 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Tupungatito | 2026-08-06 05:06 | VIIRS_SNPP | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Tupungatito | 2026-08-06 05:06 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Tupungatito | 2026-08-06 06:48 | VIIRS_SNPP | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
| Tupungatito | 2026-08-06 06:48 | VIIRS_SNPP_750 | 15 | `nrt` | no_existe (LAADS (CMR sin dato)) | sin dato / sin dato | no / no | sin dato |
