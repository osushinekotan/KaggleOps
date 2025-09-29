import logging
from pathlib import Path

import dotenv
from kaggle import KaggleApi
from pydantic import BaseModel, Field
from tyro.extras import SubcommandApp

from ..settings import KaggleSettings, LocalDirectorySettings
from .utils.customhub import dataset_upload, model_upload

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

dotenv.load_dotenv()
client = KaggleApi()
client.authenticate()

app = SubcommandApp()
local_directory_settings = LocalDirectorySettings()  # type: ignore


class UploadCodeSettings(BaseModel):
    """
    Settings for uploading code to Kaggle.
    """

    kaggle_settings: KaggleSettings = Field(
        KaggleSettings(),  # type: ignore
        description="Kaggle settings for the upload process.",
    )


class UploadArtifactSettings(BaseModel):
    """
    Settings for uploading to Kaggle.
    """

    exp_name: str = Field(..., description="Experiment name for uploading artifacts.")
    kaggle_settings: KaggleSettings = Field(
        KaggleSettings(),  # type: ignore
        description="Kaggle settings for the upload process.",
    )


@app.command()
def codes(settings: UploadCodeSettings) -> None:
    """
    Upload the code to Kaggle.
    """
    dataset_upload(
        client=client,
        handle=settings.kaggle_settings.CODES_HANDLE,
        local_dataset_dir=local_directory_settings.ROOT_DIR,
        update=True,
    )


@app.command()
def artifacts(settings: UploadArtifactSettings) -> None:
    """
    Upload the artifacts to Kaggle.
    """
    exp_name = settings.exp_name
    kaggle_settings = settings.kaggle_settings
    model_upload(
        client=client,
        handle=f"{kaggle_settings.BASE_ARTIFACTS_HANDLE}/{exp_name}",
        local_model_dir=str(
            Path(local_directory_settings.ARTIFACT_DIR)
            / str(exp_name)
            / "1",  # output dir に存在する artifact をアップロード
        ),
        update=False,
    )


@app.command()
def sources(settings: UploadArtifactSettings) -> None:
    """
    Upload the codes and artifacts to Kaggle.
    """
    codes(settings=UploadCodeSettings(kaggle_settings=settings.kaggle_settings))
    artifacts(settings)


if __name__ == "__main__":
    """Run the upload commands.

    Help:
    >>> uv run python -m src.kaggle_utils.upload codes -h
    >>> uv run python -m src.kaggle_utils.upload artifacts -h
    >>> uv run python -m src.kaggle_utils.upload sources -h
    """
    app.cli()
