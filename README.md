# Karnataka Water Watch: Reservoir Surface Dynamics from Space

> **NASA International Space Apps Challenge 2026 — "Dancing with the SARs"**  
> Tracking seasonal surface-water fluctuations and multi-year drought contraction at Krishnaraja Sagara (KRS) Reservoir using NASA-ISRO Synthetic Aperture Radar (NISAR) L2 GCOV imagery.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: NISAR](https://img.shields.io/badge/Platform-NISAR%20L2%20GCOV-orange.svg)](https://nisar.jpl.nasa.gov/)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-GitHub%20Pages-brightgreen.svg)](https://github.com/)

---

## 1. Problem Statement
Optical Earth observation satellites are blinded by persistent monsoon cloud decks at the exact moments when tropical reservoirs fill, spill, or experience rapid hydrologic drawdown.

## 2. Why Radar? (All-Weather Cloud Penetration)
Synthetic Aperture Radar (SAR) transmits active microwave signals (L-band, $\lambda \approx 24\text{ cm}$) that penetrate atmospheric cloud cover, monsoon rain, smoke, and nighttime darkness. Smooth, calm open water acts as a specular reflector, bouncing radar energy away from the sensor to produce low backscatter ($<-16\text{ dB}$, dark pixels), whereas surrounding rough terrain and vegetation cause diffuse volume scattering (brighter pixels), enabling robust water boundary delineation regardless of cloud conditions.

## 3. Study Site
- **Target:** Krishnaraja Sagara (KRS) Reservoir, Mandya District, Southern Karnataka, India (`12.42°N, 76.57°E`).
- **Hydrological Significance:** Primary impoundment on the Cauvery River controlling downstream agricultural irrigation across the Cauvery Delta and municipal drinking water for Mysuru and Bengaluru (~14 million people).
- **Study Boundary:** Bounding box $[76.445^\circ\text{E}, 76.585^\circ\text{E}]$ by $[12.380^\circ\text{N}, 12.530^\circ\text{N}]$ (UTM Zone 43N).

---

## 4. Data Used
- **Sensor:** NASA-ISRO SAR (NISAR) L-band Synthetic Aperture Radar
- **Product:** L2 GCOV (Geocoded Backscatter)
- **Geometry:** Relative Orbit Track 12 (descending orbit pass)
- **Polarization:** HH (co-polarized, delivering $>8\text{ dB}$ higher land-water contrast than HV cross-pol)
- **Spatial Resolution:** $10.0\text{ m} \times 10.0\text{ m}$ pixel spacing ($\Delta x = 10.0\text{ m}, \Delta y = -10.0\text{ m}$)
- **Acquisitions (3 Dates):**
  1. **2025-11-23:** Post-monsoon full reservoir baseline
  2. **2026-08-14:** Monsoon peak inflow and reservoir refill phase
  3. **2026-11-06:** Post-monsoon regional drought contraction

---

## 5. Methodology (4 Steps)
```
[ L2 GCOV GeoTIFFs ] ──> Step 1: Linear-to-dB Power Conversion
                     ──> Step 2: Calibrated Backscatter Thresholding (-16.0 dB)
                     ──> Step 3: Morphological Cleanup & Dam Cutoff Filtering
                     ──> Step 4: Disjoint Bitmask Change Classification
```

1. **Linear-to-dB Conversion:** Extract geocoded backscatter power grids ($\gamma^0$) and convert to decibels: $\gamma^0_{\text{dB}} = 10 \cdot \log_{10}(\gamma^0)$.
2. **Calibrated Thresholding:** Apply an empirically calibrated uniform threshold of **$-16.0\text{ dB}$** across all dates. This cleanly separates water from surrounding agriculture ($-11.0$ to $-13.3\text{ dB}$) while accommodating monsoon wind-roughened capillary waves.
3. **Morphological Cleanup & Dam Wall Clipping:**
   - 5×5 spatial median filter for speckle reduction.
   - Binary hole filling for interior gaps $< 2000\text{ px}$ ($0.20\text{ km}^2$).
   - Small-blob removal for isolated false positives $< 500\text{ px}$ ($0.05\text{ km}^2$).
   - Connected-component analysis retaining bodies $> 5\%$ of the primary basin.
   - **Dam Wall Polyline Filter:** Exclude downstream water detections east of the 2.6 km KRS stone masonry dam crest ($12.418^\circ\text{N}, 76.571^\circ\text{E}$ to $12.437^\circ\text{N}, 76.572^\circ\text{E}$), eliminating $0.95\text{ km}^2$ of false water in the Visvesvaraya Canal headworks and downstream paddy fields.
4. **Disjoint Overlap Classification:** Bitmask partitioning into 7 mutually exclusive classes (single-date, pairwise intersections, and permanent core) to ensure exact additivity without alpha-blending distortion.

---

## 6. Key Scientific Results (Within Study Box)
*All statistics strictly measured within the study box and upstream of the dam crest:*

| Epoch Date | Detected Area | Reservoir State | Change vs. Nov 2025 Baseline |
| :--- | :---: | :--- | :---: |
| **23 Nov 2025** | **77.93 km²** | Near Full Reservoir Level (FRL) | *Baseline* |
| **14 Aug 2026** | **62.72 km²** | Monsoon refill / wind-roughened open water | -15.21 km² (-19.5%) |
| **06 Nov 2026** | **60.62 km²** | Post-monsoon drought contraction | **-17.31 km² (-22.2%)** |

### 7-Class Disjoint Overlap Partition

| Class Code | Class Description | Hex Color | Mapped Area |
| :---: | :--- | :---: | :---: |
| `001` | Water on 23 Nov 2025 only | `#0072B2` | **10.36 km²** |
| `010` | Water on 14 Aug 2026 only | `#E69F00` | **0.06 km²** |
| `100` | Water on 06 Nov 2026 only | `#009E73` | **0.71 km²** |
| `011` | Water on both 23 Nov 2025 & 14 Aug 2026 | `#CC79A7` | **7.68 km²** |
| `101` | Water on both 23 Nov 2025 & 06 Nov 2026 | `#00E5FF` | **4.92 km²** |
| `110` | Water on both 14 Aug 2026 & 06 Nov 2026 | `#D55E00` | **0.01 km²** |
| `111` | In all three dates (Permanent Core) | `#2B2D42` (translucent) | **54.98 km²** |

> **Key Finding:** Comparing **23 Nov 2025** and **06 Nov 2026** isolates genuine annual environmental change under identical viewing geometry (Track 12) and identical post-monsoon seasonality. Within the study box, the reservoir contracted by **-17.31 km² (-22.2%)**, showing dewatering of **18.03 km²** of shoreline over a persistent **54.98 km² core**.

---

## 7. Ground Truth Validation & Gauge Attributions

| Acquisition Date | NISAR Detected Area | Nearest Gauge Report | Storage Basis | Source & Documentation |
| :--- | :---: | :---: | :---: | :--- |
| **23 Nov 2025** | **77.93 km²** | **~123–124 ft** | ~93–95% gross | [KSNDMC Daily Bulletins](https://ksndmc.org) & [CWC Daily Reports](https://cwc.gov.in) |
| **14 Aug 2026** | **62.72 km²** | **102.09 ft** *(03 Aug)*<br>*(mid-Aug report: 108.66 ft)* | ~52.5% gross on 03 Aug;<br>~63% gross mid-Aug | [Deccan Herald (04 Aug 2026)](https://www.deccanherald.com)<br>[OneIndia Kannada (mid-Aug 2026)](https://kannada.oneindia.com) |
| **06 Nov 2026** | **60.62 km²** | **~98–99 ft** | ~43.0–43.5% gross | [The New Indian Express](https://www.newindianexpress.com)<br>[KSNDMC Drought Reports](https://ksndmc.org) |

- **Storage Capacity Basis:** Full Reservoir Level is $124.80\text{ ft}$. Gross Storage Capacity is **49.452 TMC** (total impounded volume); Live Storage Capacity is **45.070 TMC** (excluding dead storage below sill level). Media reports frequently interchange these figures.
- **Concordance:** Water spread and gauge heights move monotonically across all three acquisitions.

---

## 8. Honest Limitations & Caveats
1. **Frame Boundary Truncation:** The NISAR Track 12 frame cuts off at $76.450^\circ\text{E}$. The study box captures $60.2\%$ ($77.93\text{ km}^2$) of the published $129.5\text{ km}^2$ FRL spread, truncating **~40% of the reservoir's full FRL water surface area** (~45% of its linear east-west extent up to the Hemavathi/Cauvery confluence).
2. **Temporal Sparsity:** Only three NISAR acquisitions were available during the early operational phase.
3. **Threshold-Based Binary Masking:** In August 2026, wind capillary waves elevated median backscatter by $+1.24\text{ dB}$ ($-15.68\text{ dB}$ vs $-16.93\text{ dB}$ in Nov 2025) across a $4.92\text{ km}^2$ near-dam patch, causing partial undercounting at $-16.0\text{ dB}$.
4. **Lack of In-Situ Ground Truth:** Gauge figures are drawn from regional daily news bulletins and disaster centre logs; exact-minute gauge logs and simultaneous cloud-free optical validation imagery were unavailable.

---

## 9. How to Run Locally

### Prerequisites
- Python 3.10+
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Installation
```bash
# Clone the repository
git clone https://github.com/<your-username>/karnataka-water-watch.git
cd karnataka-water-watch

# Install pipeline dependencies
pip install -r requirements.txt
```

### Launch Interactive Dashboard
```bash
# Serve the web application locally
python -m http.server 8000 --directory docs
```
Open your browser at: `http://localhost:8000`

---

## 10. Credits & Acknowledgements
- **NASA-ISRO Synthetic Aperture Radar (NISAR) Mission:** Public L2 GCOV products courtesy of NASA and ISRO.
- **Alaska Satellite Facility (ASF) DAAC:** Radar data archive and search APIs (`asf_search`).
- **Esri World Imagery:** High-resolution optical satellite basemap tiles.
- **Karnataka State Natural Disaster Monitoring Centre (KSNDMC) & Central Water Commission (CWC):** Daily reservoir water level telemetry.

---

## 11. Live Deployment
- **Interactive Application:** `https://<your-username>.github.io/<repo-name>/` (hosted directly from the `/docs` branch deployment).
