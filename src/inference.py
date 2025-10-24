import polars as pl

from settings import DirectorySettings
from train import Config, preprocess, test_fn


def _build_submission(sample_df: pl.DataFrame, pred_df: pl.DataFrame) -> pl.DataFrame:
    pred_labels = pred_df.select(
        "PassengerId",
        pl.col("pred").alias("Transported"),
    )
    return sample_df.select("PassengerId").join(pred_labels, on="PassengerId", how="left")


if __name__ == "__main__":
    import rootutils

    rootutils.setup_root(".", cwd=True)
    config = Config()
    settings = DirectorySettings(exp_name=config.name)

    test_df = pl.read_csv(settings.COMP_DATASET_DIR / "test.csv")
    test_df = preprocess(config, test_df)

    pred_df = test_fn(config, test_df, out_dir=settings.ARTIFACT_EXP_DIR)

    sample_df = pl.read_csv(settings.COMP_DATASET_DIR / "sample_submission.csv")
    assert len(sample_df) == len(pred_df), "Sample submission and prediction dataframe must have the same length"

    submission_df = _build_submission(sample_df, pred_df)
    submission_df.write_csv(settings.OUTPUT_DIR / "submission.csv")
    print("✔︎ Submission saved to: ", settings.OUTPUT_DIR / "submission.csv")
