# Examples

Synthetic datasets that exercise the data-scientist plugin end to end. Each dataset is produced by a `generate_data.py` whose code documents the **ground truth** relationships, so you can check the plugin's findings against what was actually baked in.

## Layout

| Directory | Dataset | Rows | What it demonstrates |
|---|---|---|---|
| `manufacturing_yield/` | `dataset.csv` (+ `analysis.ipynb`) | 500 | Driver ranking with FDR control, regression, confounding, charts |
| `ab_test/` | `dataset.csv` | 10,000 | Conversion/revenue lift, effect size with CI, SRM check |
| `time_series/` | `dataset.csv` | 2,160 | Seasonal decomposition, change-point and anomaly detection |

## 1. Manufacturing yield

**Question:** Which process parameters drive yield, and which apparent signals are noise or confounded?

**Ground truth** (`generate_data.py`): temperature has a strong negative effect, pressure a moderate positive one, humidity a weak negative one; **line speed has no effect** (a deliberate noise variable); operator C performs better and the night shift is worse; equipment age confounds temperature. A correct analysis recovers the real drivers and rejects line speed.

```bash
# Reproducible notebook walkthrough (uses the bundled ds_skill helpers)
pip install -e ".[viz]"          # one-time: helpers + matplotlib/seaborn
jupyter notebook examples/manufacturing_yield/analysis.ipynb

# Or interactively in Claude Code:
/ds-analyze examples/manufacturing_yield/dataset.csv
```

## 2. A/B test

**Question:** Did the treatment increase conversion and revenue?

**Ground truth:** control converts at 12%, treatment at 14%, with a higher average order value in the treatment arm. Arms are balanced (5,000 each). A correct analysis confirms the lift with a confidence interval and checks for sample-ratio mismatch.

```bash
/ds-analyze examples/ab_test/dataset.csv
```

## 3. Time series anomaly detection

**Question:** When did equipment behavior change, and which readings are anomalous?

**Ground truth:** an hourly sensor signal with daily + weekly seasonality and a slow upward trend, plus three injected anomaly types — sudden spikes, a gradual drift, and a zero-value outage. A correct analysis decomposes the seasonality and flags the injected anomalies.

```bash
/ds-analyze examples/time_series/dataset.csv
```

## Prerequisites

```bash
pip install -r requirements.txt          # core analysis dependencies
pip install -e ".[viz]"                  # + matplotlib/seaborn for charts
pip install jupyter                       # only for the notebook
```

## Regenerating the data

Each dataset is checked in, but you can regenerate it from the repo root:

```bash
python examples/manufacturing_yield/generate_data.py
python examples/ab_test/generate_data.py
python examples/time_series/generate_data.py
```

The generators use fixed random seeds, so the output is deterministic.
