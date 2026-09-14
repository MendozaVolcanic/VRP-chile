**MIROVA Global VRP Database**

*Database Schema*

Version 2.5 · Last updated: February 2026

**Overview**

The MIROVA Global Volcanic Radiative Power (VRP) Database provides observation-level satellite measurements of volcanic thermal activity derived from the MIROVA processing system. The database is distributed in two equivalent formats:

* **SQL (.sql)** — full relational schema including table structure, data types, primary key, and indexes.
* **CSV (.csv)** — flat file version of the same records, suitable for direct use in analytical environments.

Both formats contain identical data records.

**Online Data Exploration Dashboard**

An interactive web-based dashboard is available for rapid visualization and exploratory analysis:

<https://www.mirovaweb.it/ARCHIVE/Explore_Archive.php>

The dashboard allows users to query, filter, and visualize temporal and volcano-specific records. It is intended for exploratory use. Reproducible scientific analyses must rely on the archived, versioned dataset provided in this repository.

**Database Structure**

**Table: VRP\_GLOBAL\_ARCHIVE**

**Purpose and Granularity**

VRP\_GLOBAL\_ARCHIVE is an observation-level table. Each row corresponds to a single satellite overpass associated with a target volcano. Records include volcano metadata, acquisition geometry, radiometric aggregates, VRP estimates, and spatial metrics of detected hot pixels.

Multiple records may exist for the same volcano on a given day if multiple satellite overpasses occurred.

**SQL Schema Description**

The SQL version includes explicit data types, constraints, and indexing to ensure structural integrity and prevent duplicate volcano–time entries.

**Primary Key and Timestamp**

**id — INT(11)**
Primary key, NOT NULL, AUTO\_INCREMENT.
Unique internal identifier for each record.

**timeUTC — DATETIME**
Acquisition time in Coordinated Universal Time (UTC).

**Volcano Identification and Metadata**

**IDvolc — FLOAT**
Volcano identifier (GVP-based ID used within the MIROVA framework).

**Volc\_Name — VARCHAR(30)**
Volcano name.

**Volc\_LAT — FLOAT**
Volcano summit latitude (decimal degrees, WGS84).

**Volc\_LON — FLOAT**
Volcano summit longitude (decimal degrees, WGS84).

**Acquisition Conditions and Sensor Information**

**Dayflag — FLOAT**
Day/night acquisition flag (categorical indicator stored numerically).

**Satellite — FLOAT**
Sensor/platform code (categorical identifier stored numerically).

**Resolution — FLOAT**
Nominal pixel size (meters).

**class — INT**
Automated binary classification label
(1 = volcanic detection; 0 = non-volcanic detection).

**Viewing Geometry**

**SatZen — FLOAT**
Satellite zenith angle (degrees).

**SatAzi — FLOAT**
Satellite azimuth angle (degrees).

**Pixel Statistics and Radiometric Aggregates**

**Npix — FLOAT**
Number of alerted pixels contributing to the detection.

**Tot\_Lmir\_hot — FLOAT**
Total MIR radiance over alerted pixels (hot component).

**Tot\_Lmir\_bk — FLOAT**
Total MIR radiance over alerted pixels (background component).

**VRP — FLOAT**
Volcanic Radiative Power estimate (Watts).

**Spatial Attributes**

**LAT — FLOAT**
Latitude of the hottest alerted pixel (decimal degrees, WGS84).

**LON — FLOAT**
Longitude of the hottest alerted pixel (decimal degrees, WGS84).

**Max\_Dist — FLOAT**
Maximum distance between the volcano summit and the farthest alerted pixel (meters).

**Data Notes**

* All times are expressed in **UTC**.
* Geographic coordinates use **WGS84 decimal degrees**.
* Radiance values are integrated over the set of alerted pixels.
* VRP is computed using the MIR method from the difference between hot-spot and background radiance.
* Missing or invalid detections may appear as empty fields or NaN.
* High VRP values at large satellite zenith angles may appear spatially dispersed due to viewing geometry.
* The class field represents an automated classification and should be treated as a screening indicator rather than a definitive label.

**Disclaimer**

The MIROVA Global VRP Database is made publicly available to support scientific research and reproducibility. While substantial quality control procedures are applied, the dataset may contain classification inaccuracies, missing values, incomplete records, or artefacts related to satellite acquisition geometry and processing algorithms.

The database is provided “as is” without warranty of any kind. Users are solely responsible for verifying data suitability for their applications and for any interpretation, analysis, decision, or publication derived from its use. The developers of MIROVA and affiliated institutions assume no liability for direct or indirect consequences resulting from the use of the data.

Automated classification labels and derived parameters (including VRP estimates) are analytical products generated according to the methods described in the companion publication. They are intended to facilitate systematic analyses and screening, and should not be considered definitive without independent validation where appropriate.

All scientific publications using this dataset must cite:

* The dataset DOI: **[DOI]**
* The companion *Scientific Data* publication: **[citation]**

For further information or reporting potential data issues:
**diego.coppola@unito.it**