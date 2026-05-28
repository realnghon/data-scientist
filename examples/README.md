# Examples

This directory contains example datasets and Jupyter notebooks demonstrating the data-scientist plugin workflow.

## Available examples

### 1. Manufacturing Yield Analysis

**Directory**: `manufacturing-yield/`

**Business question**: Which process parameters drive yield? Are there confounded variables?

**Dataset**: 200 production runs with temperature, pressure, humidity, operator, shift, material batch, and yield %.

**Demonstrates**:
- Data readiness scoring
- Correlation analysis with FDR correction
- Regression with quadratic terms
- Confounding detection

**Run**:
```bash
cd examples/manufacturing-yield
jupyter notebook analysis.ipynb
```

### 2. A/B Test Analysis (Coming soon)

**Directory**: `ab-test/`

**Business question**: Did the new checkout flow increase conversion?

**Demonstrates**:
- Sample size validation
- Effect size estimation with confidence intervals
- Power analysis

### 3. Time Series Anomaly Detection (Coming soon)

**Directory**: `time-series-anomaly/`

**Business question**: When did equipment behavior change?

**Demonstrates**:
- STL decomposition
- Change-point detection
- Anomaly scoring

## Prerequisites

Install dependencies:

```bash
pip install -r ../requirements.txt
pip install jupyter matplotlib seaborn
```

## Generating synthetic data

Each example includes a `generate_data.py` script that creates the synthetic dataset. The data generation code documents the "ground truth" relationships so you can verify the plugin's findings.

```bash
python examples/manufacturing-yield/generate_data.py
```

## Using with Claude Code

You can also run these analyses interactively with Claude Code:

```bash
cd examples/manufacturing-yield
# In Claude Code:
/ds-analyze yield_data.csv
```

The plugin will walk through the same workflow as the notebook, but with LLM-guided method selection and interpretation.
