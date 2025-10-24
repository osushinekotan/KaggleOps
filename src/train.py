# %%
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import polars as pl
import xgboost as xgb
from pydantic import BaseModel
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold

from settings import DirectorySettings


# %%
class Config(BaseModel):
    name: str = "example_xgb"

    categorical_features: list[str] = [
        "HomePlanet",
        "Cabin",
        "Destination",
    ]
    numerical_features: list[str] = [
        "CryoSleep",
        "Age",
        "VIP",
        "RoomService",
        "FoodCourt",
        "ShoppingMall",
        "Spa",
        "VRDeck",
    ]
    target_col: str = "Transported"

    n_splits: int = 5
    seed: int = 42

    params: dict[str, Any] = {
        "objective": "binary:logistic",
        "n_estimators": 100,
        "eval_metric": "auc",
        "seed": 42,
        "enable_categorical": True,
        "early_stopping_rounds": 10,
    }


def preprocess(config: Config, df: pl.DataFrame) -> pl.DataFrame:
    # cast
    df = df.with_columns(
        pl.col(config.categorical_features).cast(pl.Categorical),
        pl.col(config.numerical_features).cast(pl.Float64),
    )

    return df


def add_fold(config: Config, train_df: pl.DataFrame) -> pl.DataFrame:
    # add fold column
    cv_strategy = StratifiedKFold(
        n_splits=config.n_splits,
        shuffle=True,
        random_state=config.seed,
    )
    folds = np.zeros(len(train_df), dtype=np.int32)
    for fold, (_, valid_idx) in enumerate(cv_strategy.split(X=train_df, y=train_df[config.target_col])):
        folds[valid_idx] = fold
    train_df = train_df.with_columns(pl.Series(values=folds, name="fold"))
    return train_df


def score_fn(config: Config, pred_df: pl.DataFrame) -> dict[str, float]:
    return {
        "roc_auc": roc_auc_score(pred_df[config.target_col], pred_df["pred"]),
    }


def train_fn(
    config: Config,
    train_df: pl.DataFrame,
    out_dir: Path,
) -> tuple[list[xgb.XGBModel], pl.DataFrame, dict[int, float]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    feature_cols = config.categorical_features + config.numerical_features

    best_models, scores = [], {}
    val_pred_df = pl.DataFrame()
    for fold in range(config.n_splits):
        print(f"🚀 Training fold {fold}...")
        tr_df = train_df.filter(pl.col("fold") != fold)
        val_df = train_df.filter(pl.col("fold") == fold)

        tr_x, tr_y = tr_df.select(feature_cols).to_pandas(), tr_df[config.target_col]
        val_x, val_y = val_df.select(feature_cols).to_pandas(), val_df[config.target_col]

        model = xgb.XGBClassifier(**config.params)
        model.fit(
            tr_x,
            tr_y,
            eval_set=[(val_x, val_y)],
            verbose=10,
        )
        joblib.dump(model, out_dir / f"model_{fold}.pkl")
        best_models.append(model)

        # validate
        va_pred = model.predict(val_x)
        val_df = val_df.with_columns(pl.Series(values=va_pred, name="pred"))
        val_pred_df = pl.concat([val_pred_df, val_df], how="diagonal_relaxed")

        # score
        score = score_fn(config, val_pred_df)
        scores[fold] = score
        print(f"🏆 Score: {score}\n")

    return best_models, val_pred_df, scores


def test_fn(config: Config, test_df: pl.DataFrame, out_dir: Path) -> pl.DataFrame:
    feature_cols = config.categorical_features + config.numerical_features
    best_models = [joblib.load(out_dir / f"model_{fold}.pkl") for fold in range(config.n_splits)]
    test_x = test_df.select(feature_cols).to_pandas()

    test_preds = np.zeros(len(test_df))
    for model in best_models:
        pred = model.predict(test_x)
        test_preds += pred

    test_preds /= len(best_models)
    test_pred_df = test_df.with_columns(pl.Series(values=test_preds, name="pred"))
    return test_pred_df


if __name__ == "__main__":
    import rootutils

    rootutils.setup_root(".", cwd=True)
    config = Config()
    settings = DirectorySettings(exp_name=config.name)

    # %%
    # train
    train_df = pl.read_csv(settings.COMP_DATASET_DIR / "train.csv")
    train_df = preprocess(config, train_df)
    train_df = add_fold(config, train_df)

    best_models, val_pred_df, scores = train_fn(config, train_df, out_dir=settings.OUTPUT_DIR)
    val_pred_df.write_csv(settings.OUTPUT_DIR / "val_pred.csv")
    with open(settings.OUTPUT_DIR / "scores.json", "w") as f:
        json.dump(scores, f, indent=4, sort_keys=True)

    # %%
    # inference
    test_df = pl.read_csv(settings.COMP_DATASET_DIR / "test.csv")
    test_df = preprocess(config, test_df)
    test_pred_df = test_fn(config, test_df, out_dir=settings.OUTPUT_DIR)

    test_pred_df.write_csv(settings.OUTPUT_DIR / "test_pred.csv")

# %%
