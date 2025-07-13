import json
import logging

from pydantic import BaseModel, Field
from tyro.extras import SubcommandApp

from ..settings import DEPS_CODE_DIR, SUBMISSION_CODE_DIR, KaggleSettings

app = SubcommandApp()
logger = logging.getLogger(__name__)


class MakeDepsCodeMetadataSettings(BaseModel):
    """
    Settings for creating metadata for the Kaggle code that installs dependencies.
    """

    kaggle_settings: KaggleSettings = Field(
        default_factory=KaggleSettings, description="Kaggle settings for the metadata creation."
    )


class MakeSubmissionCodeMetadataSettings(BaseModel):
    """
    Settings for creating metadata for the Kaggle submission code.
    """

    kaggle_settings: KaggleSettings = Field(
        default_factory=KaggleSettings, description="Kaggle settings for the metadata creation."
    )

    enable_gpu: bool = Field(False, description="Whether to enable GPU for the Kaggle code.")
    enable_tpu: bool = Field(False, description="Whether to enable TPU for the Kaggle code.")
    model_source_names: list[str] = Field(
        default_factory=list,
        description="List of model source names for the Kaggle code. (experiment names)",
    )

    dataset_sources: list[str] = Field(default_factory=list, description="List of dataset sources for the Kaggle code.")


@app.command()
def deps_metadata(settings: MakeDepsCodeMetadataSettings) -> None:
    """
    Create metadata for the Kaggle code that installs dependencies.
    """
    logger.info("Creating metadata for the Kaggle code that installs dependencies...")
    kaggle_settings = settings.kaggle_settings
    metadata = {
        "id": f"{kaggle_settings.KAGGLE_USERNAME}/{kaggle_settings.DEPS_CODE_NAME}",
        "title": kaggle_settings.DEPS_CODE_NAME,
        "code_file": "code.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": "true",
        "enable_gpu": "false",
        "enable_tpu": "false",
        "enable_internet": "true",
        "dataset_sources": [],
        "competition_sources": [],
        "kernel_sources": [],
        "model_sources": [],
    }
    metadata_path = DEPS_CODE_DIR / "kernel-metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info(json.dumps(metadata, indent=2))


@app.command()
def submission_metadata(settings: MakeSubmissionCodeMetadataSettings) -> None:
    """
    Create metadata for the Kaggle submission code.
    """
    logger.info("Creating metadata for the Kaggle submission code...")
    kaggle_settings = settings.kaggle_settings

    model_sources = [f"{kaggle_settings.BASE_ARTIFACTS_HANDLE}/{name}/1" for name in settings.model_source_names]
    metadata = {
        "id": f"{kaggle_settings.KAGGLE_USERNAME}/{kaggle_settings.SUBMISSION_CODE_NAME}",
        "title": f"{kaggle_settings.SUBMISSION_CODE_NAME}",
        "code_file": "code.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": "true",
        "enable_gpu": "false" if not settings.enable_gpu else "true",
        "enable_tpu": "false" if not settings.enable_tpu else "true",
        "enable_internet": "false",
        "dataset_sources": settings.dataset_sources,
        "competition_sources": [kaggle_settings.KAGGLE_COMPETITION_NAME],
        "kernel_sources": [f"{kaggle_settings.KAGGLE_USERNAME}/{kaggle_settings.DEPS_CODE_NAME}"],
        "model_sources": model_sources,
    }
    metadata_path = SUBMISSION_CODE_DIR / "kernel-metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    """Run the code metadata creation commands.

    Help:
    >>> uv run python -m src.kaggle.write deps-metadata -h
    >>> uv run python -m src.kaggle.write submission-metadata -h
    """
    app.cli()
