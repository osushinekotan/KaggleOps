from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.kaggle_ops.utils.utils import get_run_env

CODES_DIR = Path("./codes")
DEPS_CODE_DIR = CODES_DIR / "deps"
SUBMISSION_CODE_DIR = CODES_DIR / "submission"


class KaggleSettings(BaseSettings):
    """
    Settings for Kaggle operations.
    """

    KAGGLE_USERNAME: str = Field("")
    KAGGLE_KEY: str = Field("")
    KAGGLE_COMPETITION_NAME: str = Field("")

    BASE_ARTIFACTS_NAME: str = Field("", description="Base name for Kaggle artifacts.")
    BASE_ARTIFACTS_HANDLE: str = Field("", description="Base handle for Kaggle artifacts.")
    CODES_NAME: str = Field("", description="Name of the Kaggle codes.")
    CODES_HANDLE: str = Field("", description="Handle for Kaggle codes.")

    DEPS_CODE_NAME: str = Field("", description="Name of the Deps Kaggle code.")
    SUBMISSION_CODE_NAME: str = Field("", description="Name of the Submission Kaggle code.")

    @model_validator(mode="after")
    def set_handles(self) -> "KaggleSettings":
        self.CODES_NAME = f"{self.KAGGLE_COMPETITION_NAME}-codes"
        self.CODES_HANDLE = f"{self.KAGGLE_USERNAME}/{self.CODES_NAME}"

        self.BASE_ARTIFACTS_NAME = f"{self.KAGGLE_COMPETITION_NAME}-artifacts/other"
        self.BASE_ARTIFACTS_HANDLE = f"{self.KAGGLE_USERNAME}/{self.BASE_ARTIFACTS_NAME}"
        return self

    @model_validator(mode="after")
    def set_code_name(self) -> "KaggleSettings":
        self.DEPS_CODE_NAME = f"{self.KAGGLE_COMPETITION_NAME}-deps"
        self.SUBMISSION_CODE_NAME = f"{self.KAGGLE_COMPETITION_NAME}-submission"
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class LocalDirectorySettings(BaseSettings):
    ROOT_DIR: str = Field(".", description="Root directory of the project.")
    INPUT_DIR: str = Field("./data/input", description="Input directory for Kaggle datasets.")
    ARTIFACT_DIR: str = Field("./data/output", description="Output directory for Kaggle artifacts.")
    OUTPUT_DIR_TEMPLATE: str = Field("./data/output/{exp_name}/1", description="Output directory for Kaggle artifacts.")


class KaggleDirectorySettings(BaseSettings):
    ROOT_DIR: str = Field("/kaggle/working", description="Root directory in Kaggle environment.")
    INPUT_DIR: str = Field("/kaggle/input", description="Input directory for Kaggle datasets.")
    ARTIFACT_DIR: str = Field("", description="Output directory for Kaggle artifacts.")
    OUTPUT_DIR: str = Field("/kaggle/working", description="Output directory for Kaggle artifacts.")


class VertexDirectorySettings(BaseSettings):
    BUCKET_NAME: str = Field(..., description="GCS bucket name for Vertex AI training.")
    ROOT_DIR: str = Field("/gcs/{bucket}/working", description="Root directory in Vertex AI environment.")
    INPUT_DIR: str = Field("/gcs/{bucket}/input", description="Input directory in Vertex AI environment.")
    ARTIFACT_DIR: str = Field("/gcs/{bucket}/output", description="Artifact directory in Vertex AI environment.")
    OUTPUT_DIR_TEMPLATE: str = Field(
        "/gcs/{bucket}/output/{exp_name}/1", description="Output directory template in Vertex AI environment."
    )


class DirectorySettings(BaseSettings):
    """
    Settings for directory paths in the project.
    """

    exp_name: str = Field(..., description="Experiment name for the output directory.")
    run_env: str | None = Field(None, description="Environment type, either 'local' or 'kaggle' or 'vertex'.")
    kaggle_settings: KaggleSettings = Field(
        KaggleSettings(),  # type: ignore
        description="Kaggle settings for the download process.",
    )

    COMP_DATASET_DIR: str | Path = Field("", description="Directory for Kaggle competition datasets.")
    ROOT_DIR: str | Path = Field("", description="Root directory of the project.")
    INPUT_DIR: str | Path = Field("", description="Input directory for datasets.")
    OUTPUT_DIR: str | Path = Field("", description="Output directory for artifacts.")
    ARTIFACT_DIR: str | Path = Field("", description="Directory for artifacts.")
    ARTIFACT_EXP_DIR: str | Path = Field("", description="Directory for experiment artifacts.")

    @model_validator(mode="after")
    def set_directories(self) -> "DirectorySettings":
        if self.run_env is None:
            self.run_env = get_run_env()

        if self.run_env == "local":
            dir_setting = LocalDirectorySettings()  # type: ignore
            self.ROOT_DIR = Path(dir_setting.ROOT_DIR)
            self.INPUT_DIR = Path(dir_setting.INPUT_DIR)
            self.OUTPUT_DIR = Path(dir_setting.OUTPUT_DIR_TEMPLATE.format(exp_name=self.exp_name))
            self.ARTIFACT_DIR = Path(dir_setting.ARTIFACT_DIR)
            self.COMP_DATASET_DIR = Path(dir_setting.INPUT_DIR) / self.kaggle_settings.KAGGLE_COMPETITION_NAME
            self.ARTIFACT_EXP_DIR = self.ARTIFACT_DIR / self.exp_name / "1"

        elif self.run_env == "kaggle":
            dir_setting = KaggleDirectorySettings()  # type: ignore
            self.ROOT_DIR = Path(dir_setting.ROOT_DIR)
            self.INPUT_DIR = Path(dir_setting.INPUT_DIR)
            self.OUTPUT_DIR = Path(dir_setting.OUTPUT_DIR)  # type: ignore
            self.ARTIFACT_DIR = Path(f"{dir_setting.INPUT_DIR}/{self.kaggle_settings.BASE_ARTIFACTS_NAME.lower()}")
            self.COMP_DATASET_DIR = Path(dir_setting.INPUT_DIR) / self.kaggle_settings.KAGGLE_COMPETITION_NAME
            self.ARTIFACT_EXP_DIR = self.ARTIFACT_DIR / self.exp_name / "1"

        elif self.run_env == "vertex":
            dir_setting = VertexDirectorySettings()  # type: ignore
            bucket = dir_setting.BUCKET_NAME
            self.ROOT_DIR = Path(dir_setting.ROOT_DIR.format(bucket=bucket))
            self.INPUT_DIR = Path(dir_setting.INPUT_DIR.format(bucket=bucket))
            self.OUTPUT_DIR = Path(dir_setting.OUTPUT_DIR_TEMPLATE.format(bucket=bucket, exp_name=self.exp_name))
            self.ARTIFACT_DIR = Path(dir_setting.ARTIFACT_DIR.format(bucket=bucket))
            self.COMP_DATASET_DIR = self.INPUT_DIR / self.kaggle_settings.KAGGLE_COMPETITION_NAME
            self.ARTIFACT_EXP_DIR = self.ARTIFACT_DIR / self.exp_name / "1"

        else:
            raise ValueError(f"Invalid environment type. Must be 'local', 'kaggle', or 'vertex'. Got: {self.run_env}")

        print(f"OUTPUT_DIR: {self.OUTPUT_DIR}")
        print(f"ARTIFACT_DIR: {self.ARTIFACT_DIR}")
        print(f"ARTIFACT_EXP_DIR: {self.ARTIFACT_EXP_DIR}")
        print(f"COMP_DATASET_DIR: {self.COMP_DATASET_DIR}")

        return self
