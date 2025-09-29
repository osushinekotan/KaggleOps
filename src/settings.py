import os
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

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


class DirectorySettings(BaseSettings):
    """
    Settings for directory paths in the project.
    """

    exp_name: str = Field(..., description="Experiment name for the output directory.")
    run_env: str | None = Field(None, description="Environment type, either 'local' or 'kaggle'.")
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
        self.run_env = self.run_env or ("kaggle" if os.getenv("KAGGLE_DATA_PROXY_TOKEN") else "local")

        if self.run_env == "local":
            dir_setting = LocalDirectorySettings()  # type: ignore
        elif self.run_env == "kaggle":
            dir_setting = KaggleDirectorySettings()  # type: ignore
        else:
            raise ValueError(f"Invalid environment type. Must be either 'local' or 'kaggle'. Got: {self.run_env}")

        self.ROOT_DIR = Path(dir_setting.ROOT_DIR)
        self.INPUT_DIR = Path(dir_setting.INPUT_DIR)
        self.OUTPUT_DIR = (
            Path(dir_setting.OUTPUT_DIR)  # type: ignore
            if self.run_env == "kaggle"
            else Path(dir_setting.OUTPUT_DIR_TEMPLATE.format(exp_name=self.exp_name))
        )
        self.ARTIFACT_DIR = (
            Path(dir_setting.ARTIFACT_DIR)
            if self.run_env == "local"
            else Path(f"{dir_setting.INPUT_DIR}/{self.kaggle_settings.BASE_ARTIFACTS_NAME.lower()}")
        )
        self.COMP_DATASET_DIR = Path(dir_setting.INPUT_DIR) / self.kaggle_settings.KAGGLE_COMPETITION_NAME
        self.ARTIFACT_EXP_DIR = self.ARTIFACT_DIR / self.exp_name / "1"

        return self
