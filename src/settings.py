from pathlib import Path

import rootutils
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = rootutils.setup_root(".", indicator="pyproject.toml", cwd=True, dotenv=True)
DATA_DIR = Path(ROOT_DIR) / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"


class KaggleSettings(BaseSettings):
    """
    Settings for Kaggle operations.
    """

    KAGGLE_USERNAME: str = Field(...)
    KAGGLE_KEY: str = Field(...)
    KAGGLE_COMPETITION_NAME: str = Field(...)

    BASE_ARTIFACTS_HANDLE: str = Field("", description="Base handle for Kaggle artifacts.")
    CODES_HANDLE: str = Field("", description="Handle for Kaggle codes.")

    @model_validator(mode="after")
    def set_handles(self):
        self.CODES_HANDLE = f"{self.KAGGLE_USERNAME}/{self.KAGGLE_COMPETITION_NAME}-codes"
        self.BASE_ARTIFACTS_HANDLE = f"{self.KAGGLE_USERNAME}/{self.KAGGLE_COMPETITION_NAME}-artifacts/other"
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
