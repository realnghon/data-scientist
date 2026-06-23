"""Classification helpers for the data-scientist skill.

Wraps scikit-learn with the skill's standardized result shape: dicts that own
their effect sizes, assumption flags, rejected alternatives.

Method choices follow `references/method-registry.md` section 6 (Classification):

- Binary, interpretability needed -> logistic regression (L2).
- Binary, predictive performance -> gradient-boosted trees.
- Multi-class -> multinomial logistic or GBT (one-vs-rest handled internally).
- Imbalanced minority -> class_weight="balanced" (cost-sensitive loss).

All public functions return dicts (not dataclasses) to minimize calling overhead.
"""

from __future__ import annotations

from typing import Any, Literal

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def class_balance_check(y: pd.Series, min_per_class: int = 30) -> dict:
    """Inspect class distribution and flag imbalance / undersampled classes.

    Returns a dict with counts, imbalance ratio (max/min), warnings, and
    recommendations. Pure function, no IO.
    """
    if y is None or len(y) == 0:
        raise ValueError("class_balance_check requires a non-empty target series.")

    y = pd.Series(y).dropna()
    if len(y) == 0:
        raise ValueError("All target values are NaN; cannot assess class balance.")

    counts = y.value_counts().sort_index()
    n_per_class = {str(k): int(v) for k, v in counts.items()}
    sizes = counts.to_numpy(dtype=float)
    smallest = float(sizes.min())
    largest = float(sizes.max())
    imbalance_ratio = float(largest / smallest) if smallest > 0 else float("inf")

    min_class_warning = smallest < float(min_per_class)
    recommendations: list[str] = []
    if min_class_warning:
        recommendations.append(
            f"Smallest class has n={int(smallest)} (< {min_per_class}); "
            "consider stratified CV and class_weight='balanced'."
        )
    if imbalance_ratio > 10:
        recommendations.append(
            f"Imbalance ratio {imbalance_ratio:.1f}:1 is severe; "
            "consider SMOTE (training fold only) or cost-sensitive loss."
        )
    elif imbalance_ratio > 3:
        recommendations.append(
            f"Imbalance ratio {imbalance_ratio:.1f}:1 is moderate; "
            "use stratified CV and prefer F1/AUC over accuracy."
        )
    if len(counts) < 2:
        recommendations.append(
            "Only one class observed; classification is undefined."
        )

    return {
        "n_per_class": n_per_class,
        "n_classes": int(len(counts)),
        "imbalance_ratio": imbalance_ratio,
        "smallest_class_size": int(smallest),
        "largest_class_size": int(largest),
        "min_class_warning": bool(min_class_warning),
        "recommendations": recommendations,
    }


def fit_classifier(
    df: pd.DataFrame,
    target: str,
    features: list[str],
    method: Literal["logistic", "random_forest", "gradient_boosting"] = "logistic",
    cv_folds: int = 5,
    stratify: bool = True,
    class_weight: Literal["balanced", None] = "balanced",
    random_state: int = 0,
) -> dict[str, Any]:
    """Fit a classifier with CV metrics and return a dict.

    Uses StratifiedKFold when ``stratify=True``. Computes macro and per-class
    precision/recall/F1, accuracy, and AUC (binary -> single value; multi-class
    -> one-vs-rest macro AUC). Stores predicted probabilities and true labels
    so :func:`tune_threshold` can sweep operating points without refitting.
    """
    if df is None or len(df) == 0:
        raise ValueError("fit_classifier requires a non-empty DataFrame.")
    if target not in df.columns:
        raise ValueError(f"target column '{target}' not in DataFrame.")
    missing = [f for f in features if f not in df.columns]
    if missing:
        raise ValueError(f"feature columns not in DataFrame: {missing}")
    if not features:
        raise ValueError("fit_classifier requires at least one feature.")
    if cv_folds < 2:
        raise ValueError("cv_folds must be >= 2.")

    # Lazy sklearn import.
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import (
        accuracy_score,
        confusion_matrix,
        f1_score,
        precision_score,
        recall_score,
        roc_auc_score,
    )
    from sklearn.model_selection import KFold, StratifiedKFold

    work = df[[target] + list(features)].dropna()
    if len(work) == 0:
        raise ValueError("All rows dropped after removing NaNs in target/features.")

    y = pd.Series(work[target])
    features_frame = pd.DataFrame(work[list(features)])
    X = features_frame.to_numpy(dtype=float)

    balance = class_balance_check(y, min_per_class=30)
    classes_sorted = sorted(y.unique().tolist(), key=lambda v: str(v))
    n_classes = len(classes_sorted)
    if n_classes < 2:
        raise ValueError("Need at least 2 distinct classes to fit a classifier.")

    # Ensure each fold can contain every class when stratifying.
    smallest = balance["smallest_class_size"]
    effective_folds = max(2, min(cv_folds, smallest)) if stratify else cv_folds

    if method == "logistic":
        def make_model() -> Any:
            return LogisticRegression(
                max_iter=1000,
                class_weight=class_weight,
                random_state=random_state,
            )
    elif method == "random_forest":
        def make_model() -> Any:
            return RandomForestClassifier(
                n_estimators=200,
                class_weight=class_weight,
                random_state=random_state,
            )
    elif method == "gradient_boosting":
        # GradientBoostingClassifier does not accept class_weight; ignore it
        # and emit a recommendation instead.
        def make_model() -> Any:
            return GradientBoostingClassifier(random_state=random_state)
    else:
        raise ValueError(
            f"Unsupported method '{method}'. Use 'logistic', 'random_forest', or 'gradient_boosting'."
        )

    splitter = (
        StratifiedKFold(n_splits=effective_folds, shuffle=True, random_state=random_state)
        if stratify
        else KFold(n_splits=effective_folds, shuffle=True, random_state=random_state)
    )

    # Map class labels to indices so AUC handling is consistent.
    class_to_idx = {c: i for i, c in enumerate(classes_sorted)}
    y_idx = np.array([class_to_idx[v] for v in y.tolist()], dtype=int)

    fold_metrics: list[dict[str, float]] = []
    all_true: list[int] = []
    all_pred: list[int] = []
    all_proba: list[np.ndarray] = []
    feature_importance_sum = np.zeros(len(features), dtype=float)
    importance_folds = 0

    for train_idx, test_idx in splitter.split(X, y_idx):
        model = make_model()
        model.fit(X[train_idx], y_idx[train_idx])
        pred = model.predict(X[test_idx])
        true = y_idx[test_idx]

        try:
            proba = model.predict_proba(X[test_idx])
        except Exception:
            proba = None

        all_true.extend(true.tolist())
        all_pred.extend(pred.tolist())
        if proba is not None:
            all_proba.append(proba)

        # Per-fold metrics; zero_division=0 keeps macro metrics defined when
        # a fold misses a tiny class.
        metrics = {
            "accuracy": float(accuracy_score(true, pred)),
            "precision_macro": float(
                precision_score(true, pred, average="macro", zero_division=0.0)  # type: ignore[arg-type]
            ),
            "recall_macro": float(
                recall_score(true, pred, average="macro", zero_division=0.0)  # type: ignore[arg-type]
            ),
            "f1_macro": float(f1_score(true, pred, average="macro", zero_division=0.0)),  # type: ignore[arg-type]
        }

        # AUC: binary -> probability of positive class, multi-class -> macro OVR.
        if proba is not None and len(np.unique(true)) > 1:
            try:
                if n_classes == 2:
                    metrics["auc"] = float(roc_auc_score(true, proba[:, 1]))
                else:
                    metrics["auc"] = float(
                        roc_auc_score(
                            true,
                            proba,
                            multi_class="ovr",
                            average="macro",
                            labels=list(range(n_classes)),
                        )
                    )
            except Exception:
                metrics["auc"] = float("nan")
        else:
            metrics["auc"] = float("nan")

        fold_metrics.append(metrics)

        # Feature importance: coefficient magnitudes for logistic, native
        # ``feature_importances_`` otherwise.
        if method == "logistic":
            coef = getattr(model, "coef_", None)
            if coef is not None:
                # Scale by each feature's train-fold std so the importance is the
                # standardized-coefficient magnitude (|beta_j| * sd(x_j)). Raw
                # |beta_j| on unstandardized features ranks by measurement unit,
                # not predictive contribution.
                feat_std = np.asarray(X[train_idx].std(axis=0), dtype=float)
                imp = np.mean(np.abs(coef), axis=0) * feat_std
                feature_importance_sum += imp
                importance_folds += 1
        else:
            imp = getattr(model, "feature_importances_", None)
            if imp is not None:
                feature_importance_sum += imp
                importance_folds += 1

    # Aggregate CV metrics (mean + std).
    cv_metrics: dict[str, dict[str, float]] = {}
    for key in ("accuracy", "precision_macro", "recall_macro", "f1_macro", "auc"):
        values = np.array(
            [m[key] for m in fold_metrics if not np.isnan(m[key])], dtype=float
        )
        if len(values) == 0:
            cv_metrics[key] = {"mean": float("nan"), "std": float("nan")}
        else:
            cv_metrics[key] = {"mean": float(values.mean()), "std": float(values.std(ddof=0))}

    # Per-class precision/recall/F1 from concatenated out-of-fold predictions.
    per_class_precision = precision_score(
        all_true, all_pred, average=None, zero_division=0.0, labels=list(range(n_classes))  # type: ignore[arg-type]
    )
    per_class_recall = recall_score(
        all_true, all_pred, average=None, zero_division=0.0, labels=list(range(n_classes))  # type: ignore[arg-type]
    )
    per_class_f1 = f1_score(
        all_true, all_pred, average=None, zero_division=0.0, labels=list(range(n_classes))  # type: ignore[arg-type]
    )
    for i, cls in enumerate(classes_sorted):
        key = f"class_{cls}"
        cv_metrics[key] = {
            "precision": float(per_class_precision[i]),  # type: ignore[index]
            "recall": float(per_class_recall[i]),  # type: ignore[index]
            "f1": float(per_class_f1[i]),  # type: ignore[index]
        }

    cm = confusion_matrix(all_true, all_pred, labels=list(range(n_classes)))
    cm_list = cm.astype(int).tolist()

    feature_importance: dict[str, float] | None = None
    if importance_folds > 0:
        avg = feature_importance_sum / importance_folds
        feature_importance = {f: float(v) for f, v in zip(features, avg)}

    recommendations = list(balance["recommendations"])
    if method == "gradient_boosting" and class_weight == "balanced":
        recommendations.append(
            "gradient_boosting does not accept class_weight; "
            "consider sample_weight or switch to logistic / random_forest for cost-sensitive loss."
        )
    if balance["imbalance_ratio"] > 10 and not balance["min_class_warning"]:
        recommendations.append(
            "Severe imbalance: prefer PR-AUC and F1 over accuracy; "
            "consider tuning the decision threshold (see tune_threshold)."
        )
    if effective_folds < cv_folds:
        recommendations.append(
            f"cv_folds reduced from {cv_folds} to {effective_folds} because "
            f"the smallest class only has n={smallest}."
        )

    # Stash arrays needed for threshold tuning.
    if all_proba:
        proba_matrix = np.vstack(all_proba)
    else:
        proba_matrix = None
    true_array = np.array(all_true, dtype=int)

    return {
        "method": method,
        "classes": classes_sorted,
        "n_per_class": balance["n_per_class"],
        "cv_metrics": cv_metrics,
        "feature_importance": feature_importance,
        "confusion_matrix": cm_list,
        "imbalance_ratio": float(balance["imbalance_ratio"]),
        "min_class_warning": bool(balance["min_class_warning"]),
        "recommendations": recommendations,
        "_probabilities": proba_matrix,
        "_true_labels": true_array,
    }


def tune_threshold(
    result: dict[str, Any],
    criterion: Literal["f1", "youden", "cost"] = "f1",
    cost_matrix: dict | None = None,
) -> dict[str, Any]:
    """Sweep the decision threshold for a *binary* classifier.

    Criterion:
    - ``"f1"``: maximize F1 on the positive class.
    - ``"youden"``: maximize TPR - FPR (Youden's J).
    - ``"cost"``: minimize expected cost using ``cost_matrix`` keys
      ``fp_cost`` and ``fn_cost`` (defaults to 1.0 each).
    """
    if result is None:
        raise ValueError("tune_threshold requires a classification result dict.")
    if len(result["classes"]) != 2:
        raise ValueError(
            "tune_threshold currently supports binary classifiers only "
            f"(got {len(result['classes'])} classes)."
        )
    if result.get("_probabilities") is None or result.get("_true_labels") is None:
        raise ValueError(
            "Classification result is missing probabilities/true labels; "
            "re-run fit_classifier to populate them."
        )

    proba = np.asarray(result["_probabilities"])
    if proba.ndim != 2 or proba.shape[1] < 2:
        raise ValueError("Probability matrix shape is unexpected for binary classification.")
    positive_proba = proba[:, 1]
    y_true = np.asarray(result["_true_labels"], dtype=int)

    fp_cost = 1.0
    fn_cost = 1.0
    if criterion == "cost":
        cm = cost_matrix or {}
        fp_cost = float(cm.get("fp_cost", 1.0))
        fn_cost = float(cm.get("fn_cost", 1.0))
    elif criterion not in {"f1", "youden"}:
        raise ValueError(
            f"Unsupported criterion '{criterion}'. Use 'f1', 'youden', or 'cost'."
        )

    thresholds = np.linspace(0.01, 0.99, 99)
    sweep: list[dict[str, float]] = []
    best_threshold = 0.5
    best_score = -np.inf

    for t in thresholds:
        pred = (positive_proba >= t).astype(int)
        tp = int(((pred == 1) & (y_true == 1)).sum())
        fp = int(((pred == 1) & (y_true == 0)).sum())
        fn = int(((pred == 0) & (y_true == 1)).sum())
        tn = int(((pred == 0) & (y_true == 0)).sum())
        tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tpr
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )

        entry = {
            "threshold": float(t),
            "tpr": float(tpr),
            "fpr": float(fpr),
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
        }
        sweep.append(entry)

        if criterion == "f1":
            score = f1
        elif criterion == "youden":
            score = tpr - fpr
        else:  # cost: maximize negative cost (minimize cost).
            score = -(fp * fp_cost + fn * fn_cost)

        if score > best_score:
            best_score = score
            best_threshold = float(t)

    best_entry = next(s for s in sweep if s["threshold"] == best_threshold)
    metrics_at_optimum = dict(best_entry)
    if criterion == "cost":
        cm = cost_matrix or {}
        fp_cost = float(cm.get("fp_cost", 1.0))
        fn_cost = float(cm.get("fn_cost", 1.0))
        pred = (positive_proba >= best_threshold).astype(int)
        fp = int(((pred == 1) & (y_true == 0)).sum())
        fn = int(((pred == 0) & (y_true == 1)).sum())
        metrics_at_optimum["expected_cost"] = float(fp * fp_cost + fn * fn_cost)

    return {
        "criterion_used": criterion,
        "optimal_threshold": float(best_threshold),
        "metrics_at_optimum": metrics_at_optimum,
        "sweep": sweep,
    }
