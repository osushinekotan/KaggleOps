import logging

import dotenv
from kaggle import KaggleApi
from pydantic import BaseModel, Field
from tyro.extras import SubcommandApp

from ..settings import KaggleSettings, LocalDirectorySettings
from .utils.customhub import competition_download, datasets_download

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

dotenv.load_dotenv()
client = KaggleApi()
client.authenticate()

app = SubcommandApp()
local_directory_settings = LocalDirectorySettings()


class DownloadCompetitionDatasetSettings(BaseModel):
    """
    Settings for downloading the Kaggle competition dataset.
    """

    kaggle_settings: KaggleSettings = Field(
        default_factory=KaggleSettings, description="Kaggle settings for the download process."
    )
    force_download: bool = Field(False, description="Whether to force download the dataset even if it already exists.")


class DownloadDatasetsSettings(BaseModel):
    """
    Settings for downloading specified Kaggle datasets.
    """

    kaggle_settings: KaggleSettings = Field(
        default_factory=KaggleSettings, description="Kaggle settings for the download process."
    )
    handles: str = Field(..., description="Comma-separated list of Kaggle dataset handles to download.")
    force_download: bool = Field(
        False, description="Whether to force download the datasets even if they already exist."
    )


@app.command()
def competition_dataset(settings: DownloadCompetitionDatasetSettings) -> None:
    """
    Download the Kaggle competition dataset.
    """

    competition_download(
        client=client,
        handle=settings.kaggle_settings.KAGGLE_COMPETITION_NAME,
        destination=local_directory_settings.INPUT_DIR,
        force_download=settings.force_download,
    )


@app.command()
def datasets(settings: DownloadDatasetsSettings) -> None:
    """
    Download the specified Kaggle datasets.
    """
    datasets_download(
        client=client,
        handles=settings.handles,
        destination=local_directory_settings.INPUT_DIR,
        force_download=settings.force_download,
    )


if __name__ == "__main__":
    """Run the command line interface for downloading datasets.

    Help:
    >>> uv run python -m src.kaggle_utils.download competition-dataset -h
    >>> uv run python -m src.kaggle_utils.download datasets -h
    """
    app.cli()
