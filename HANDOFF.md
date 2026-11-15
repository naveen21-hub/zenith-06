# HANDOFF.md: Karnataka Water Watch (Precision Science & Validation Complete)

## 1. Executive Summary & Status
All radar science checks, dam end audits, threshold robustness matrices, official ground truth validations, overlap exports, and dashboard updates are **COMPLETE, VERIFIED, AND COMMITTED TO GIT**.

The project delivers an end-to-end Earth Observation pipeline and responsive interactive web dashboard for monitoring water spread dynamics at Krishnaraja Sagara (KRS) Reservoir, Mandya, Karnataka, using NASA-ISRO Synthetic Aperture Radar (NISAR) L2 GCOV (Geocoded Backscatter) Track 12 acquisitions.

---

## 2. Key Scientific Finding (Headline Metric)
- **Controlled Comparison (Nov 2025 vs. Nov 2026):**
  - Comparing **23 Nov 2025** to **06 Nov 2026** isolates genuine annual hydrologic change by holding **viewing geometry constant** (identical Track 12 descending orbit) and **seasonal timing constant** (post-monsoon November).
  - **Net Water Contraction:** Detected reservoir surface area within the study box contracted by **-17.31 km² (-22.2%)**, shrinking from **77.93 km²** to **60.62 km²**.
  - **Dynamics:** Dewatering of **18.03 km²** of exposed shoreline mudflats and shallow inlets across the basin, sustained over a stable **54.98 km² permanent core**.

---

## 3. Dam End Audit & Downstream Exclusion
- **Dam Crest Alignment:**
  - Surveyed the 2.6 km KRS stone masonry dam crest:
    - South Abutment: 12.418°N, 76.5710°E
    - Main Sluice Gates: 12.426°N, 76.5718°E
    - North Spillway: 12.437°N, 76.5722°E
- **Downstream Anomaly Identification:**
  - High specular reflection east of the dam wall in the 06 Nov 2026 scene was audited against Esri World Imagery and regional hydrology.
  - The feature consists of the **Visvesvaraya Canal (VC Canal) headworks** and **downstream post-monsoon irrigated paddy fields** inundated during November release schedules.
- **Dam Wall Polyline Cutoff:**
  - Implemented an automated geometric filter in `pipeline/run_science_pipeline.py` and `pipeline/generate_overlap_products.py` clipping all water masks strictly to the reservoir (upstream) side of the dam wall.
  - **Excluded False Downstream Water:**
    - 23 Nov 2025: -0.01 km² excluded (77.94 km² → **77.93 km²**)
    - 14 Aug 2026: 0.00 km² excluded (**62.72 km²**)
    - 06 Nov 2026: -0.95 km² downstream false water excluded (61.57 km² → **60.62 km²**)

---

## 4. Spatial Coverage & Coordinate Verification
- **Pixel Spacing Verification:**
  - Verified coordinate spacing from the geocoded GeoTIFF grid: $\Delta x = +10.000000\text{ m}, \Delta y = -10.000000\text{ m}$ (EPSG:32643 UTM Zone 43N).
  - True physical pixel area = $100.00\text{ m}^2 = 0.000100\text{ km}^2$.
- **Western Frame Boundary & Truncation:**
  - The straight cutoff on the western border is the physical frame boundary of the NISAR L2 GCOV Track 12 granule (`lon_min = 76.450005°E`).
  - At Full Reservoir Level (FRL 124.80 ft), the total published reservoir water spread is **129.5 km²**.
  - The maximum detected area within the study box is **77.93 km²**, capturing **60.2%** of published FRL area.
  - The western truncation excludes approximately **~40% of the full reservoir's FRL water spread** (~45% of its linear east-west extent up to the Hemavathi & Cauvery confluence arms).
  - All statistics across code, JSON, and UI are explicitly labeled *"within study box"*.

---

## 5. August Near-Dam Gap & Threshold Robustness
- **Backscatter Audit of the 4.92 km² Near-Dam Patch:**
  - Water present in Nov 2025 and Nov 2026 but absent in Aug 2026 was audited across radar backscatter histograms:
    - 23 Nov 2025: Median = **-16.93 dB**
    - 14 Aug 2026: Median = **-15.68 dB** (+1.24 dB brighter)
    - 06 Nov 2026: Median = **-16.77 dB**
  - In August 2026, **74.7%** of this patch falls within the narrow bracket between -16.0 dB and -14.0 dB.
  - At -16.0 dB, 24.7% of the patch is classified as water; at -14.0 dB, 99.4% is classified as water.
- **Strict Monotonicity Across All Thresholds:**
  - Tested across fixed thresholds for HH and HV polarizations:

| Threshold (dB) | 23 Nov 2025 | 14 Aug 2026 | 06 Nov 2026 | Aug 2026 < Nov 2025? |
| :--- | :--- | :--- | :--- | :--- |
| **-14.0 dB (HH)** | 82.11 km² | 78.72 km² | 71.76 km² | **YES** |
| **-16.0 dB (HH Pipeline)** | **77.93 km²** | **62.72 km²** | **60.62 km²** | **YES** |
| **-18.0 dB (HH)** | 50.63 km² | 5.35 km² | 13.08 km² | **YES** |
| **-20.0 dB (HH)** | 0.44 km² | 0.00 km² | 0.00 km² | **YES** |
| **-18.0 dB (HV)** | 183.69 km² | 114.12 km² | 102.02 km² | **YES** (severe land bleeding) |
| **-20.0 dB (HV)** | 96.00 km² | 84.71 km² | 79.33 km² | **YES** |
| **-22.0 dB (HV)** | 81.46 km² | 69.09 km² | 66.48 km² | **YES** |
| **-24.0 dB (HV)** | 71.45 km² | 0.00 km² | 0.00 km² | **YES** |

- **Scientific Synthesis:**
  - "Aug 2026 < Nov 2025" holds at **every threshold** without exception.
  - Monsoon wind capillary roughening and rain-induced surface disturbance represent a scientifically supported hypothesis for backscatter elevation to -15.7 dB, but cannot be asserted as conclusive without coincident meteorological or optical truth. All site copy frames this strictly as a hypothesis and omits ungrounded claims.

---

## 6. Ground Truth & Water Gauge Attribution

| Acquisition Date | NISAR Detected Area (Study Box) | Nearest Verified Gauge Report | Report Date & Time | Storage Basis | Verified Publication Sources |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **23 Nov 2025** (Sun) | **77.93 km²** | **~123–124 ft** (near FRL) | Late Nov 2025 daily bulletins | ~93–95% gross capacity | [KSNDMC Daily Bulletins](https://ksndmc.org) & [CWC Daily Reservoir Reports](https://cwc.gov.in) |
| **14 Aug 2026** (Fri) | **62.72 km²** | **102.09 ft** *(nearest)*<br>*(mid-Aug report: 108.66 ft)* | **03 Aug 2026, 8:00 PM**<br>*(mid-Aug date unconfirmed)* | ~52.5% gross (~57% live) on 03 Aug;<br>~63% gross reported in mid-August | [Deccan Herald (04 Aug 2026)](https://www.deccanherald.com)<br>[OneIndia Kannada (mid-Aug 2026)](https://kannada.oneindia.com) |
| **06 Nov 2026** (Fri) | **60.62 km²** | **~98–99 ft** (severe drought) | Early Nov 2026 bulletins | ~43.0–43.5% gross (~47% live) | [The New Indian Express](https://www.newindianexpress.com)<br>[KSNDMC Drought Reports](https://ksndmc.org) |

- **Capacity Discrepancy Clarification:**
  - Full Reservoir Level (FRL): **124.80 ft**.
  - Gross Reservoir Capacity: **49.452 TMC** (total physical volume behind the dam).
  - Live / Effective Storage Capacity: **45.070 TMC** (excluding dead storage below the lowest river sluice sills).
  - Media reports vary: some cite gross capacity (e.g. 52.5% on 03 Aug), while others cite live capacity (e.g. 57.5%). Both conventions are documented.

---

## 7. Multi-Epoch Overlap & Disjoint Partition

The pipeline computes 7 mutually disjoint classes via bitmask partitioning. Class areas sum exactly to the individual date totals:

| Class Code | Disjoint Classification | Hex Color | Display Name | Area (km²) |
| :---: | :--- | :---: | :--- | :---: |
| `001` | Only 23 Nov 2025 | `#0072B2` | Deep Blue | **10.36 km²** |
| `010` | Only 14 Aug 2026 | `#E69F00` | Golden Orange | **0.06 km²** |
| `100` | Only 06 Nov 2026 | `#009E73` | Emerald Green | **0.71 km²** |
| `011` | Both 23 Nov 2025 & 14 Aug 2026 | `#CC79A7` | Warm Magenta | **7.68 km²** |
| `101` | Both 23 Nov 2025 & 06 Nov 2026 | `#00E5FF` | Electric Cyan | **4.92 km²** |
| `110` | Both 14 Aug 2026 & 06 Nov 2026 | `#D55E00` | Vermilion | **0.01 km²** |
| `111` | In all three dates (Permanent Core) | `#2B2D42` | Translucent Core ($\alpha=75/255$) | **54.98 km²** |

- **Sanity Sum Checks:**
  - 23 Nov 2025: $10.36 + 7.68 + 4.92 + 54.98 = \mathbf{77.94\text{ km}^2}$ (matches $77.93\text{ km}^2 \pm 0.01\text{ km}^2$)
  - 14 Aug 2026: $0.06 + 7.68 + 0.01 + 54.98 = \mathbf{62.73\text{ km}^2}$ (matches $62.72\text{ km}^2 \pm 0.01\text{ km}^2$)
  - 06 Nov 2026: $0.71 + 4.92 + 0.01 + 54.98 = \mathbf{60.62\text{ km}^2}$ (exact match)

- **UI & Visualization Features:**
  - Multi-epoch toggle chips with distinct color swatches.
  - Fill vs Outline switch: single-date fill, pairwise overlap, 3-date 7-class disjoint fill, or stacked 2px anti-aliased shoreline outlines.
  - Default overlay opacity set to **0.60**, with keyboard accessible slider.
  - Permanent core rendered semi-transparently ($\alpha=75/255$) so underlying Esri satellite water texture remains clearly visible.
  - Electric Cyan (`#00E5FF`) ensures stark visual distinction between Nov '25 + Nov '26 pair and single Nov '25 deep blue (`#0072B2`).
  - Fully responsive from mobile (390px) to desktop (1440px+).

---

## 8. Git Commit Log
- `503a016`: `fix(dam-audit): clip downstream pixels east of KRS dam wall and recompute all stats and overlays`
- `6024c94`: `fix(august-gap): audit near-dam patch backscatter, test thresholds across HH/HV, rewrite wind claims as hypothesis`
- `5ec22d9`: `fix(sources): fix gauge table attributions, remove Techpuram, add verified URLs and publication dates, document capacity divergence`
- `58ad791`: `feat(ui): set default opacity to 0.6, make permanent core semi-transparent to preserve satellite texture, make blue classes distinct with electric cyan`
- `0de3bf9`: `fix(numbers): verify exact 10.0m coordinate spacing and reconcile truncation ratio to ~40% unobserved FRL area`
- `0e0a838`: `feat(telemetry): add prominent Key Finding line comparing Nov 2025 to Nov 2026, move mismatch analysis into Data & Limits`
