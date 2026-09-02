# 📈 Bellabeat Strategic Segmentation Analysis

*Customer segmentation and growth strategy case study*

🇪🇸 [Versión en español](README.md)

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](requirements.txt)
[![Tests](https://img.shields.io/badge/tests-44%20passing-brightgreen)](tests/)
[![License](https://img.shields.io/badge/code-MIT-green)](LICENSE.MD)
[![Content](https://img.shields.io/badge/content-CC%20BY%204.0-lightgrey)](https://creativecommons.org/licenses/by/4.0/)

> **Disclaimer.** Independent academic case study, built for a portfolio. **Not affiliated
> with, sponsored by, or endorsed by Bellabeat, Fitbit or Google.** "Bellabeat" and "Fitbit"
> are trademarks of their respective owners, used here for identification and educational
> purposes only. **Not medical advice:** the WHO and JACC thresholds cited are
> population-level guidance, not individual diagnostic criteria.

---

## 🎯 Overview

A Data Analytics case study for [**Bellabeat**](https://bellabeat.com), a wellness
technology company. The goal is to inform marketing and product strategy by **segmenting
users on activity habits and consistency**.

The public FitBit dataset is used as a proxy. The central design decision is to **segment
on two dimensions at once** — step volume × effective intensity — rather than on a single
metric.

> ⚠️ The dataset contains **no sex, age or location**, so it cannot be claimed to represent
> Bellabeat's customer base. Results are presented as **hypotheses to validate**, not as
> conclusions, and the analysis uses gender-neutral language throughout.

---

## 📊 Key findings

### 1. Users cluster at two opposite poles, not along a continuum

![Customer segmentation: typical steps vs typical intensity](docs/img/segmentacion_heatmap.png)

*21 of 26 users (81 %) sit in opposite corners of the matrix. The **Traveller** quadrant
(high steps, low intensity) is empty in this sample.*

| Segment | Users | Share (95 % Wilson CI) | Conclusive? |
| :--- | :---: | :--- | :---: |
| **Healthy** | 15 | 58 % (39 – 74 %) | yes |
| **Sedentary** | 8 | 31 % (17 – 50 %) | yes |
| **Strong** | 3 | 12 % (4 – 29 %) | **no (n < 5)** |
| **Traveller** | 0 | 0 % (0 – 13 %) | — |

> At n = 26, **a single user is worth ≈ 3.8 percentage points**. Percentages are rounded and
> always carry a confidence interval; segments with n < 5 are explicitly flagged as
> inconclusive.

### 2. Risk concentrates where step volume is low

![Total days by step category and intensity compliance](docs/img/volumen_dias.png)

*325 days below the WHO minimum come from the three low-step segments (Sedentary, Minimum
and Light); 806 peak-performance days come from the two high-step ones (Optimal and Very
active).*

### 3. What the two-dimensional view found: the "Strong" customer

A group with **few steps but high intensity** — likely strength training, cycling or
swimming, activities a pedometer underestimates. A step-only segmentation would have
labelled them *at-risk* and sent them the wrong message.

> At n = 3 this is a **hypothesis**, not a conclusion. It is reported because the cost of
> wrongly treating them as sedentary is asymmetrically high.

### 4. A quarter of the sample uses the device intermittently

![Cohorts by consistency of device use](docs/img/cohortes.png)

*9 of 35 users (26 %) fell outside the behavioural cohort due to intermittent use. Five of
them retain enough data for a re-engagement campaign.*

> Do not read this backwards: the 98 % completeness *within* the analysed cohort is high
> **by construction**, because the cohort is defined by having few missing days. The
> business-relevant figure is the exclusion rate, not the completeness rate.

### 5. Validity of the constructed metric

| Correlation | r | Unit of observation |
| :--- | :---: | :--- |
| Intensity ↔ calories (raw per-minute record) | 0.91 | minute |
| Combined activity score ↔ calories | **0.76** | user-day |
| Combined activity score ↔ steps | **0.85** | user-day |

The constructed score correlates with energy expenditure enough to be coherent, and little
enough with steps to **not be redundant** with them.

> ⚠️ Daily correlations are computed over user-days, which are repeated measures of 26
> people. This is **pseudo-replication**: the effective n is closer to 26 than to 1,586. The
> notebook recomputes each correlation aggregated per user and reports both.

---

## 🛠️ Skills demonstrated

* **Data auditing.** Errors in the original dataset were found and corrected: MET values
  came **multiplied by ten**, and there were unit-conversion errors between minutes, hours
  and days. The corrected dataset was published on
  [Kaggle](https://www.kaggle.com/datasets/mvr513/fitbit-fitness-tracker-data-corrected).
* **Data engineering (ETL).** Pipeline kept in its own repository:
  [Fitbit-Data-Cleaning-ETL](https://github.com/MauricioVrx/Fitbit-Data-Cleaning-ETL).
* **Theory-driven feature engineering.** `combined_activity_score`
  (`2 × vigorous minutes + moderate minutes`) applies the exact equivalence the WHO defines:
  75 vigorous minutes ≡ 150 moderate minutes.
* **Evidence-based thresholds.** Cut-offs come from
  [WHO guidelines](https://iris.who.int/items/65310979-92e8-4c98-8092-5a16ca07fc2f) and a
  [2023 JACC meta-analysis](https://www.jacc.org/doi/10.1016/j.jacc.2023.07.029) — not the
  10,000-step target, which originated as a 1965 Japanese marketing campaign with no
  clinical basis.
* **Quantified uncertainty.** Wilson intervals on every proportion, and explicit correction
  for pseudo-replication in the correlations.
* **Tested code.** Analysis logic lives in `src/bellabeat/` with **44 pytest tests**,
  including a regression test for the empty-quadrant segmentation bug.
* **Tools:** Python · pandas · NumPy · Matplotlib · Seaborn · pytest · Jupyter.

---

## 🚀 How to run

```bash
git clone https://github.com/MauricioVrx/Bellabeat-Strategic-Segmentation-Analysis.git
cd Bellabeat-Strategic-Segmentation-Analysis

python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
```

Data is **not** bundled. Download the corrected dataset from
<https://www.kaggle.com/datasets/mvr513/fitbit-fitness-tracker-data-corrected> and lay it
out exactly as:

```
data/
├── export_3.12.16-4.11.16/{dailyActivity,minuteIntensities,minuteCalories,minuteSteps}.csv
└── export_4.12.16-5.12.16/{dailyActivity,minuteIntensities,minuteCalories,minuteSteps}.csv
```

Then:

```bash
jupyter lab bellabeat_segmentation_analysis.ipynb   # Kernel -> Restart & Run All
pytest tests -q                                     # tests need no data
```

Per-minute data is ~2.7 M rows: allow roughly **2 GB of RAM**.

---

## ⚠️ Limitations

| Limitation | Scope | Impact |
| :--- | :--- | :--- |
| **No demographics** | No sex, age or location | Representativeness of Bellabeat's base cannot be claimed. **The primary limitation** |
| **Small sample** | n = 26 after filtering (of 35) | Each user moves ≈ 3.8 pp. Segments with n < 5 are inconclusive |
| **Age of the data** | March–May **2016** | Nearly a decade of change in hardware, habits and market |
| **Short, seasonal window** | 62 days, northern spring only | No control for seasonality |
| **Self-selected sample** | Mechanical Turk volunteers already using Fitbit | Skewed toward fitness-motivated people |
| **Filtered cohort** | Only ≥ 57 recorded days | Completeness is high by construction; 26 % was excluded |
| **Repeated measures** | Correlations over user-days | Pseudo-replication; reported as descriptive only |
| **Non-medical device** | Fitbit is not a certified medical device | Thresholds are population-level, not diagnostic |

**What it would take to turn this into a business decision:** first-party data with
demographics · a ≥ 6-month window · n ≥ 200 per segment · conversion and retention data to
connect segment to customer value.

---

## 📄 Licensing

| Item | Source | License |
| :--- | :--- | :--- |
| **Code** (notebook, `src/`, `tests/`) | This repository | [MIT](LICENSE.MD) |
| **Content** (text, charts, conclusions) | This repository | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |
| Raw data | [Kaggle / Möbius](https://www.kaggle.com/datasets/arashnic/fitbit), 2016 | CC0 1.0 |
| Corrected data | [Kaggle / this author](https://www.kaggle.com/datasets/mvr513/fitbit-fitness-tracker-data-corrected) | CC0 1.0 |
| ETL code | [Fitbit-Data-Cleaning-ETL](https://github.com/MauricioVrx/Fitbit-Data-Cleaning-ETL) | MIT |

**Note on personal data.** The analysis uses pseudonymised health data published under CC0.
Although `Id` does not directly identify a person, under GDPR (Art. 4(5) and Art. 9) it
constitutes special-category personal data. In production with real customer data this
analysis would require an explicit lawful basis, data minimisation, a DPIA, and a retention
policy.

---

* **Author:** Mauricio Villanueva
* **LinkedIn:** <https://linkedin.com/in/mauricio-villanueva-rivera>
* **Tableau:** <https://public.tableau.com/app/profile/mauricio.villanueva>
* **Kaggle:** <https://www.kaggle.com/mvr513>
