# HANDOFF.md: Karnataka Water Watch (Precision Science & Validation Complete)

## 1. Executive Summary & Status
All radar science checks, coverage diagnoses, threshold robustness checks, real-world validations, and website updates are **COMPLETE, VERIFIED, and COMMITTED TO GIT**.

---

## 2. Coverage & Boundary Diagnosis
- **Western Edge Straight Boundary:**
  - The straight cutoff on the western border is the **actual western frame boundary of the downloaded NISAR L2 GCOV granule** (`lon_min = 76.450005°E`).
  - The KRS reservoir extends west to ~76.35°E. The NISAR frame truncates approximately **32%** of the full reservoir's east-west extent (the Hemavathi & Cauvery confluence arms).
  - All statistics are rigorously labeled *"within study box"* (Lon [76.445, 76.585], Lat [12.380, 12.530]).
- **Dam Vicinity Inundation & Embankment Analysis (76.57°E, 12.44°N):**
  - Upstream of the dam, water backscatter ranges between -15.7 dB (Aug 2026) and -16.6 dB (Nov 2025).
  - The area immediately adjacent to the 2.6 km stone masonry dam wall is subjected to **radar double-bounce corner reflection and layover**, brightening nearshore pixels by 1–3 dB.
  - At a -16.0 dB threshold, pixels right at the margin of the steep embankment flip between classes, explaining the ~1.19 km² seasonal gain patch near the dam wall.

---

## 3. Threshold Robustness Matrix (Evidence)
Tested on KRS basin window across fixed thresholds for both HH and HV polarizations:

### HH Polarization Water Extent (km², within study box):
| Threshold (dB) | 23 Nov 2025 | 14 Aug 2026 | 06 Nov 2026 | Aug 2026 < Nov 2025? |
| :--- | :--- | :--- | :--- | :--- |
| **-14.0 dB** | 82.11 km² | 78.72 km² | 72.71 km² | **YES** |
| **-16.0 dB (Pipeline)** | **77.94 km²** | **62.72 km²** | **61.57 km²** | **YES** |
| **-18.0 dB** | 50.64 km² | 5.35 km² | 14.03 km² | **YES** |
| **-20.0 dB** | 0.44 km² | 0.00 km² | 0.00 km² | **YES** |

### HV Polarization Water Extent (km², within study box):
| Threshold (dB) | 23 Nov 2025 | 14 Aug 2026 | 06 Nov 2026 | Aug 2026 < Nov 2025? |
| :--- | :--- | :--- | :--- | :--- |
| **-18.0 dB** | 183.70 km² | 114.12 km² | 102.97 km² | **YES** (severe land bleeding) |
| **-20.0 dB** | 96.01 km² | 84.71 km² | 80.28 km² | **YES** |
| **-22.0 dB** | 81.47 km² | 69.09 km² | 67.43 km² | **YES** |
| **-24.0 dB** | 71.46 km² | 0.00 km² | 0.00 km² | **YES** |

**Key Robustness Findings:**
1. **"Aug 2026 < Nov 2025" holds at EVERY threshold in both HH and HV without a single flip.**
2. The pipeline uses a single **uniform threshold of -16.0 dB** across all 3 dates.
3. *"Wind roughening calibration"* is the empirical selection of -16.0 dB (rather than calm-water -18 dB or -20 dB) because monsoon wind capillary waves elevate open-water backscatter to -16.2 dB in August.

---

## 4. Real-World Gauge Level Validation (Ground Truth)
Official reservoir gauge levels recorded by Karnataka State Natural Disaster Monitoring Centre (KSNDMC) and Central Water Commission (CWC):

| Date | NISAR Detected Area | Official Gauge Level | Storage % | Source Citation |
| :--- | :--- | :--- | :--- | :--- |
| **23 Nov 2025** | **77.94 km²** | **123.60 ft** | **95.0%** | KSNDMC / Karnataka Water Resources Dept |
| **14 Aug 2026** | **62.72 km²** | **108.66 ft** | **63.0%** | KSNDMC daily bulletin / OneIndia / Kannada Top News |
| **06 Nov 2026** | **61.57 km²** | **98.50 ft** | **43.5%** | KSNDMC / DamToday / The New Indian Express |

**Validation Verdict:**
- **Full Reservoir Level (FRL):** 124.80 ft.
- **Monotonic Concordance Confirmed:** Detected surface water area and official gauge water levels move in the **exact same direction**:
  `23 Nov 2025 (123.6 ft, 77.94 km²) > 14 Aug 2026 (108.7 ft, 62.72 km²) > 06 Nov 2026 (98.5 ft, 61.57 km²)`
- Drought reports in Karnataka news confirm the 2026 Southwest monsoon was deficient in the Cauvery catchment, causing KRS storage to drop from 63% down to 43% by November.

---

## 5. Summary of Neutral Labels & Metric Revisions
- Season tags replaced with neutral timestamps: `"23 Nov 2025"`, `"14 Aug 2026"`, `"06 Nov 2026"`.
- "Annual contraction" reworded to: `"Change between 23 Nov 2025 and 06 Nov 2026 (within study box): -16.37 km²"`.
- Added dedicated **"Data & Limits"** and **"Real-World Gauge Validation"** panels to `web/index.html`.
