import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Lasso, LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "airbnb_numeric_only.csv"
OUTPUT_DIR = ROOT

RANDOM_STATE = 42


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    safe_y = np.where(y_true == 0, 1.0, y_true)
    return float(np.mean(np.abs((y_true - y_pred) / safe_y)) * 100)


def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    return {
        "RMSE": rmse(y_true, y_pred),
        "MAE": float(mean_absolute_error(y_true, y_pred)),
        "R2": float(r2_score(y_true, y_pred)),
        "MAPE_%": mape(y_true, y_pred),
    }


def save_plot(fig_name: str) -> None:
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / fig_name, dpi=180, bbox_inches="tight")
    plt.close()


def plot_price_distribution(df: pd.DataFrame) -> None:
    plt.figure(figsize=(11, 5))

    plt.subplot(1, 2, 1)
    sns.histplot(df["price"], bins=80, kde=True, color="#d95f02")
    plt.title("Full Data: Raw Price Distribution")
    plt.xlabel("Price")

    plt.subplot(1, 2, 2)
    sns.histplot(np.log1p(df["price"]), bins=80, kde=True, color="#1b9e77")
    plt.title("Full Data: Log(1 + Price) Distribution")
    plt.xlabel("log(1 + price)")

    save_plot("bonus_full_price_distribution.png")


def plot_corr_heatmap(df: pd.DataFrame) -> pd.DataFrame:
    corr = df.corr(numeric_only=True)
    plt.figure(figsize=(13, 10))
    sns.heatmap(corr, cmap="coolwarm", center=0, linewidths=0.4)
    plt.title("Full Data Correlation Matrix")
    save_plot("bonus_full_corr_heatmap.png")
    return corr


def top_correlated_pairs(corr: pd.DataFrame, threshold: float = 0.7) -> pd.DataFrame:
    cols = corr.columns.tolist()
    rows = []
    for i, c1 in enumerate(cols):
        for c2 in cols[i + 1 :]:
            if c1 == "price" or c2 == "price":
                continue
            v = corr.loc[c1, c2]
            if abs(v) >= threshold:
                rows.append({"feature_1": c1, "feature_2": c2, "corr": float(v), "abs_corr": abs(float(v))})

    out = pd.DataFrame(rows).sort_values("abs_corr", ascending=False)
    out.to_csv(OUTPUT_DIR / "bonus_top_correlated_pairs.csv", index=False)

    plt.figure(figsize=(10, 4 if len(out) < 8 else 6))
    if len(out) == 0:
        plt.text(0.5, 0.5, "No pair above threshold", ha="center", va="center", fontsize=12)
        plt.axis("off")
    else:
        top_n = out.head(12).copy()
        labels = top_n["feature_1"] + " vs " + top_n["feature_2"]
        sns.barplot(x=top_n["corr"], y=labels, palette="vlag")
        plt.axvline(0, color="black", linewidth=1)
        plt.title("Top Highly Correlated Feature Pairs (|corr| >= 0.7)")
        plt.xlabel("Correlation")
        plt.ylabel("")

    save_plot("bonus_top_correlated_pairs.png")
    return out


def plot_model_rmse(metrics_df: pd.DataFrame, file_name: str, title: str) -> None:
    order = metrics_df.sort_values("RMSE", ascending=True)
    plt.figure(figsize=(9, 5))
    sns.barplot(data=order, x="RMSE", y="Model", palette="viridis")
    plt.title(title)
    save_plot(file_name)


def plot_metric_panels(metrics_df: pd.DataFrame, file_name: str, title: str) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    metric_cfg = [
        ("RMSE", True, "crest"),
        ("MAE", True, "flare"),
        ("MAPE_%", True, "mako"),
        ("R2", False, "viridis"),
    ]

    for ax, (metric, ascending, palette) in zip(axes.flatten(), metric_cfg):
        order = metrics_df.sort_values(metric, ascending=ascending)
        sns.barplot(data=order, x=metric, y="Model", ax=ax, palette=palette)
        ax.set_title(metric)
        ax.set_ylabel("")

    fig.suptitle(title, fontsize=14)
    save_plot(file_name)


def plot_metrics_table(metrics_df: pd.DataFrame, file_name: str, title: str) -> None:
    shown = metrics_df.copy()
    for col in ["RMSE", "MAE", "R2", "MAPE_%"]:
        if col in shown.columns:
            shown[col] = shown[col].map(lambda x: f"{x:.3f}")

    plt.figure(figsize=(11, 0.9 + 0.55 * len(shown)))
    plt.axis("off")
    plt.title(title, fontsize=13, pad=10)
    table = plt.table(
        cellText=shown.values,
        colLabels=shown.columns,
        cellLoc="center",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.0, 1.2)
    save_plot(file_name)


def plot_target_prediction_comparison(target_df: pd.DataFrame) -> None:
    local = target_df.sort_values("Target_Predicted_Price", ascending=True)
    plt.figure(figsize=(10, 5))
    sns.barplot(data=local, x="Target_Predicted_Price", y="Model", palette="Spectral")
    plt.title("Bondi Target Prediction by Model")
    plt.xlabel("Predicted price ($/night)")
    plt.ylabel("")
    save_plot("bonus_target_prediction_comparison.png")


def plot_toy_model_examples() -> None:
    rng = np.random.default_rng(RANDOM_STATE)

    # Toy example 1: Linear vs RandomForest on non-linear data.
    x = np.linspace(0, 10, 150)
    y = 120 + 28 * np.sin(x) + 1.8 * x + rng.normal(0, 4.5, size=x.shape[0])
    x_2d = x.reshape(-1, 1)

    linear = LinearRegression().fit(x_2d, y)
    forest = RandomForestRegressor(n_estimators=300, random_state=RANDOM_STATE, max_depth=7).fit(x_2d, y)

    grid = np.linspace(0, 10, 400).reshape(-1, 1)
    linear_pred = linear.predict(grid)
    forest_pred = forest.predict(grid)

    plt.figure(figsize=(10, 5))
    plt.scatter(x, y, s=16, alpha=0.45, color="#636363", label="Toy data")
    plt.plot(grid.ravel(), linear_pred, color="#e41a1c", linewidth=2, label="Linear fit")
    plt.plot(grid.ravel(), forest_pred, color="#1b9e77", linewidth=2, label="RandomForest fit")
    plt.title("Toy Example: Linear vs RandomForest on Non-linear Pattern")
    plt.xlabel("Feature x")
    plt.ylabel("Target y")
    plt.legend()
    save_plot("bonus_toy_linear_vs_rf.png")

    # Toy example 2: Effect of Ridge/Lasso regularization on correlated features.
    n = 280
    x1 = rng.normal(0, 1, n)
    x2 = x1 + rng.normal(0, 0.08, n)
    x3 = rng.normal(0, 1, n)
    x4 = rng.normal(0, 1, n)

    toy_X = pd.DataFrame({"x1": x1, "x2": x2, "x3": x3, "x4": x4})
    toy_y = 4.5 * x1 + 0.7 * x3 + rng.normal(0, 0.7, n)

    scaler = RobustScaler()
    toy_X_scaled = scaler.fit_transform(toy_X)

    mdl_linear = LinearRegression().fit(toy_X_scaled, toy_y)
    mdl_ridge = Ridge(alpha=5.0, random_state=RANDOM_STATE).fit(toy_X_scaled, toy_y)
    mdl_lasso = Lasso(alpha=0.08, random_state=RANDOM_STATE, max_iter=8000).fit(toy_X_scaled, toy_y)

    coef_df = pd.DataFrame(
        {
            "Feature": toy_X.columns,
            "Linear": mdl_linear.coef_,
            "Ridge": mdl_ridge.coef_,
            "Lasso": mdl_lasso.coef_,
        }
    )
    coef_long = coef_df.melt(id_vars="Feature", var_name="Model", value_name="Coefficient")

    plt.figure(figsize=(10, 5))
    sns.barplot(data=coef_long, x="Feature", y="Coefficient", hue="Model", palette="Set2")
    plt.axhline(0, color="black", linewidth=1)
    plt.title("Toy Example: Coefficient Shrinkage (Linear vs Ridge vs Lasso)")
    save_plot("bonus_toy_regularization_coeffs.png")

    # Toy example 3: Single tree vs RandomForest smoothing.
    tree = DecisionTreeRegressor(max_depth=3, random_state=RANDOM_STATE).fit(x_2d, y)
    tree_pred = tree.predict(grid)

    plt.figure(figsize=(10, 5))
    plt.scatter(x, y, s=16, alpha=0.4, color="#8c8c8c", label="Toy data")
    plt.plot(grid.ravel(), tree_pred, color="#377eb8", linewidth=2, label="Single Decision Tree")
    plt.plot(grid.ravel(), forest_pred, color="#1b9e77", linewidth=2, label="RandomForest (avg of many trees)")
    plt.title("Toy Example: Single Tree vs RandomForest")
    plt.xlabel("Feature x")
    plt.ylabel("Target y")
    plt.legend()
    save_plot("bonus_toy_tree_vs_forest.png")


def plot_linear_fail_evidence(y_true: np.ndarray, y_pred: np.ndarray) -> None:
    residuals = y_true - y_pred

    plt.figure(figsize=(6, 6))
    sns.scatterplot(x=y_true, y=y_pred, alpha=0.35, s=25, color="#386cb0")
    mx = max(np.max(y_true), np.max(y_pred))
    plt.plot([0, mx], [0, mx], linestyle="--", color="red", linewidth=1.2)
    plt.title("Linear Regression: Actual vs Predicted (Full Data)")
    plt.xlabel("Actual price")
    plt.ylabel("Predicted price")
    save_plot("bonus_linear_actual_vs_pred.png")

    plt.figure(figsize=(6, 5))
    sns.scatterplot(x=y_pred, y=residuals, alpha=0.35, s=20, color="#e41a1c")
    plt.axhline(0, linestyle="--", color="black", linewidth=1)
    plt.title("Linear Regression Residuals vs Fitted")
    plt.xlabel("Fitted values")
    plt.ylabel("Residuals (actual - predicted)")
    save_plot("bonus_linear_residuals_vs_fitted.png")

    plt.figure(figsize=(6, 5))
    stats.probplot(residuals, dist="norm", plot=plt)
    plt.title("Linear Regression Residual Q-Q Plot")
    save_plot("bonus_linear_qqplot.png")


def plot_error_by_decile(y_true: np.ndarray, model_predictions: dict[str, np.ndarray]) -> pd.DataFrame:
    df_plot = pd.DataFrame({"actual": y_true})
    df_plot["decile"] = pd.qcut(df_plot["actual"], q=10, labels=False, duplicates="drop") + 1

    rows = []
    for model_name, preds in model_predictions.items():
        local = df_plot.copy()
        local["ae"] = np.abs(local["actual"] - preds)
        grouped = local.groupby("decile", as_index=False)["ae"].mean()
        grouped["Model"] = model_name
        rows.append(grouped)

    out = pd.concat(rows, ignore_index=True)
    out.rename(columns={"ae": "MAE"}, inplace=True)
    out.to_csv(OUTPUT_DIR / "bonus_error_by_price_decile.csv", index=False)

    plt.figure(figsize=(10, 5))
    sns.lineplot(data=out, x="decile", y="MAE", hue="Model", marker="o")
    plt.title("MAE by Actual Price Decile")
    plt.xlabel("Actual price decile (1=cheapest, 10=most expensive)")
    save_plot("bonus_error_by_price_decile.png")

    return out


def plot_high_price_segment(mae_rows: list[dict]) -> None:
    df_mae = pd.DataFrame(mae_rows)
    plt.figure(figsize=(9, 5))
    sns.barplot(data=df_mae.sort_values("HighPrice_MAE"), x="HighPrice_MAE", y="Model", palette="rocket")
    plt.title("MAE on Top-10% Price Segment")
    plt.xlabel("MAE (Top-10% actual prices)")
    plt.ylabel("")
    save_plot("bonus_high_price_segment_mae.png")


def grouped_feature_experiment(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train_log: np.ndarray,
    y_test: np.ndarray,
    target_df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, np.ndarray], pd.DataFrame, dict[str, float]]:
    groups = {
        "capacity_group": ["accommodates", "bedrooms", "beds", "bathrooms"],
        "host_group": ["host_days", "number_of_reviews", "review_scores_rating", "host_is_superhost", "host_identity_verified"],
        "fee_policy_group": ["security_deposit", "cleaning_fee", "minimum_nights"],
        "geo_group": ["latitude", "longitude"],
        "availability_group": ["availability_365"],
    }

    group_corr_basis = pd.DataFrame(index=X_train.index)

    train_grouped = pd.DataFrame(index=X_train.index)
    test_grouped = pd.DataFrame(index=X_test.index)
    target_grouped = pd.DataFrame(index=target_df.index)

    for group_name, cols in groups.items():
        missing_cols = [c for c in cols if c not in X_train.columns]
        if missing_cols:
            continue

        if len(cols) == 1:
            col = cols[0]
            train_grouped[group_name] = X_train[col]
            test_grouped[group_name] = X_test[col]
            target_grouped[group_name] = target_df[col]
            group_corr_basis[group_name] = X_train[col]
            continue

        transformer = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", RobustScaler()),
                ("pca", PCA(n_components=1, random_state=RANDOM_STATE)),
            ]
        )
        train_comp = transformer.fit_transform(X_train[cols]).ravel()
        test_comp = transformer.transform(X_test[cols]).ravel()

        train_grouped[group_name] = train_comp
        test_grouped[group_name] = test_comp
        target_grouped[group_name] = transformer.transform(target_df[cols]).ravel()
        group_corr_basis[group_name] = train_comp

    grouped_corr = group_corr_basis.corr(numeric_only=True)
    plt.figure(figsize=(8, 6))
    sns.heatmap(grouped_corr, cmap="coolwarm", center=0, annot=True, fmt=".2f", linewidths=0.4)
    plt.title("Correlation Between Grouped Features")
    save_plot("bonus_grouped_feature_correlation.png")

    grouped_models = {
        "Linear (Grouped Features)": LinearRegression(),
        "Ridge (Grouped Features)": Ridge(alpha=5.0, random_state=RANDOM_STATE),
        "RandomForest (Grouped Features)": RandomForestRegressor(
            n_estimators=700,
            max_depth=22,
            min_samples_leaf=2,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
    }

    metrics = []
    predictions = {}
    target_predictions = {}

    for name, model in grouped_models.items():
        model.fit(train_grouped, y_train_log)
        pred_log = model.predict(test_grouped)
        pred_price = np.expm1(pred_log)
        pred_price = np.clip(pred_price, 0, None)

        row = evaluate_predictions(y_test, pred_price)
        row["Model"] = name
        metrics.append(row)
        predictions[name] = pred_price

        pred_target = np.expm1(model.predict(target_grouped)[0])
        target_predictions[name] = float(max(0.0, pred_target))

    metrics_df = pd.DataFrame(metrics).sort_values("RMSE")
    metrics_df.to_csv(OUTPUT_DIR / "bonus_grouped_model_metrics.csv", index=False)

    return metrics_df, predictions, train_grouped, target_predictions


def main() -> None:
    sns.set_theme(style="whitegrid")
    plot_toy_model_examples()

    df = pd.read_csv(DATA_PATH)
    df = df.drop_duplicates()

    # Keep full data (no top-1% trimming) and only ensure numeric integrity.
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["price"])

    plot_price_distribution(df)
    corr = plot_corr_heatmap(df)
    top_correlated_pairs(corr, threshold=0.7)

    y = df["price"].astype(float).values
    X = df.drop(columns=["price", "room_id"], errors="ignore")

    target_home = {
        "latitude": -33.889087,
        "longitude": 151.274506,
        "accommodates": 10,
        "bathrooms": 3,
        "bedrooms": 5,
        "beds": 7,
        "security_deposit": 1500,
        "cleaning_fee": 370,
        "minimum_nights": 4,
        "availability_365": 255,
        "number_of_reviews": 53,
        "review_scores_rating": 95,
        "host_days": 3200,
        "host_identity_verified": 1,
        "host_is_superhost": 1,
    }

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE
    )

    target_df = pd.DataFrame([target_home]).reindex(columns=X.columns)

    y_train_log = np.log1p(y_train)

    numeric_features = X.columns.tolist()

    linear_preprocessor = ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", RobustScaler()),
                    ]
                ),
                numeric_features,
            )
        ]
    )

    full_models = {
        "Linear (Full Features)": Pipeline(
            steps=[("prep", linear_preprocessor), ("model", LinearRegression())]
        ),
        "Ridge (Full Features)": Pipeline(
            steps=[("prep", linear_preprocessor), ("model", Ridge(alpha=5.0, random_state=RANDOM_STATE))]
        ),
        "Lasso (Full Features)": Pipeline(
            steps=[("prep", linear_preprocessor), ("model", Lasso(alpha=0.0005, random_state=RANDOM_STATE, max_iter=8000))]
        ),
        "RandomForest (Full Features)": Pipeline(
            steps=[
                ("prep", ColumnTransformer(transformers=[("num", SimpleImputer(strategy="median"), numeric_features)])),
                (
                    "model",
                    RandomForestRegressor(
                        n_estimators=700,
                        max_depth=24,
                        min_samples_leaf=2,
                        random_state=RANDOM_STATE,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
    }

    full_metrics = []
    full_predictions = {}
    target_predictions = []

    for name, model in full_models.items():
        model.fit(X_train, y_train_log)
        pred_log = model.predict(X_test)
        pred_price = np.expm1(pred_log)
        pred_price = np.clip(pred_price, 0, None)

        row = evaluate_predictions(y_test, pred_price)
        row["Model"] = name
        full_metrics.append(row)
        full_predictions[name] = pred_price

        pred_target = np.expm1(model.predict(target_df)[0])
        target_predictions.append({"Model": name, "Target_Predicted_Price": float(max(0.0, pred_target))})

    full_metrics_df = pd.DataFrame(full_metrics).sort_values("RMSE")
    full_metrics_df.to_csv(OUTPUT_DIR / "bonus_full_model_metrics.csv", index=False)

    plot_model_rmse(full_metrics_df, "bonus_full_model_rmse_comparison.png", "RMSE Comparison on Full Data")
    plot_metric_panels(full_metrics_df, "bonus_full_metric_panels.png", "Full-Feature Model Comparison")
    plot_metrics_table(full_metrics_df, "bonus_full_metrics_table.png", "Full-Feature Model Metrics")

    linear_pred = full_predictions["Linear (Full Features)"]
    plot_linear_fail_evidence(y_test, linear_pred)

    decile_models = {
        "Linear (Full Features)": full_predictions["Linear (Full Features)"],
        "Lasso (Full Features)": full_predictions["Lasso (Full Features)"],
        "RandomForest (Full Features)": full_predictions["RandomForest (Full Features)"],
    }
    plot_error_by_decile(y_test, decile_models)

    threshold = np.quantile(y_test, 0.9)
    high_mask = y_test >= threshold

    high_price_rows = []
    for name, preds in full_predictions.items():
        high_price_rows.append(
            {
                "Model": name,
                "HighPrice_MAE": float(mean_absolute_error(y_test[high_mask], preds[high_mask])),
            }
        )

    grouped_metrics_df, grouped_predictions, train_grouped, grouped_target_predictions = grouped_feature_experiment(
        X_train, X_test, y_train_log, y_test, target_df
    )
    plot_metric_panels(grouped_metrics_df, "bonus_grouped_metric_panels.png", "Grouped-Feature Model Comparison")
    plot_metrics_table(grouped_metrics_df, "bonus_grouped_metrics_table.png", "Grouped-Feature Model Metrics")

    for name, value in grouped_target_predictions.items():
        target_predictions.append({"Model": name, "Target_Predicted_Price": value})

    target_df_out = pd.DataFrame(target_predictions).sort_values("Target_Predicted_Price")
    target_df_out.to_csv(OUTPUT_DIR / "bonus_target_predictions.csv", index=False)
    plot_target_prediction_comparison(target_df_out)

    for name, preds in grouped_predictions.items():
        high_price_rows.append(
            {
                "Model": name,
                "HighPrice_MAE": float(mean_absolute_error(y_test[high_mask], preds[high_mask])),
            }
        )

    pd.DataFrame(high_price_rows).to_csv(OUTPUT_DIR / "bonus_high_price_segment_mae.csv", index=False)

    plot_high_price_segment(high_price_rows)

    compare_rows = [
        {
            "Setting": "Full Features + Linear",
            "RMSE": float(full_metrics_df.loc[full_metrics_df["Model"] == "Linear (Full Features)", "RMSE"].iloc[0]),
            "MAE": float(full_metrics_df.loc[full_metrics_df["Model"] == "Linear (Full Features)", "MAE"].iloc[0]),
            "R2": float(full_metrics_df.loc[full_metrics_df["Model"] == "Linear (Full Features)", "R2"].iloc[0]),
        },
        {
            "Setting": "Grouped Features + Linear",
            "RMSE": float(grouped_metrics_df.loc[grouped_metrics_df["Model"] == "Linear (Grouped Features)", "RMSE"].iloc[0]),
            "MAE": float(grouped_metrics_df.loc[grouped_metrics_df["Model"] == "Linear (Grouped Features)", "MAE"].iloc[0]),
            "R2": float(grouped_metrics_df.loc[grouped_metrics_df["Model"] == "Linear (Grouped Features)", "R2"].iloc[0]),
        },
        {
            "Setting": "Full Features + RandomForest",
            "RMSE": float(full_metrics_df.loc[full_metrics_df["Model"] == "RandomForest (Full Features)", "RMSE"].iloc[0]),
            "MAE": float(full_metrics_df.loc[full_metrics_df["Model"] == "RandomForest (Full Features)", "MAE"].iloc[0]),
            "R2": float(full_metrics_df.loc[full_metrics_df["Model"] == "RandomForest (Full Features)", "R2"].iloc[0]),
        },
        {
            "Setting": "Grouped Features + RandomForest",
            "RMSE": float(grouped_metrics_df.loc[grouped_metrics_df["Model"] == "RandomForest (Grouped Features)", "RMSE"].iloc[0]),
            "MAE": float(grouped_metrics_df.loc[grouped_metrics_df["Model"] == "RandomForest (Grouped Features)", "MAE"].iloc[0]),
            "R2": float(grouped_metrics_df.loc[grouped_metrics_df["Model"] == "RandomForest (Grouped Features)", "R2"].iloc[0]),
        },
    ]

    compare_df = pd.DataFrame(compare_rows)
    compare_df.to_csv(OUTPUT_DIR / "bonus_grouping_impact.csv", index=False)

    plt.figure(figsize=(9, 5))
    plot_df = compare_df.melt(id_vars="Setting", value_vars=["RMSE", "MAE"], var_name="Metric", value_name="Value")
    sns.barplot(data=plot_df, x="Value", y="Setting", hue="Metric", palette="Set2")
    plt.title("Grouping Correlated Features: Metric Impact")
    save_plot("bonus_grouping_impact.png")

    print("=== Full Model Metrics ===")
    print(full_metrics_df.to_string(index=False))
    print("\n=== Grouped Feature Model Metrics ===")
    print(grouped_metrics_df.to_string(index=False))
    print("\nArtifacts created in:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
