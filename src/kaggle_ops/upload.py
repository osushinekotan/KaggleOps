import logging
from pathlib import Path

import dotenv
from kaggle import KaggleApi
from pydantic import BaseModel, Field
from tyro.extras import SubcommandApp

from ..settings import KaggleSettings, LocalDirectorySettings, VertexDirectorySettings
from .utils.customhub import dataset_upload, model_upload

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

dotenv.load_dotenv()
client = KaggleApi()
client.authenticate()

app = SubcommandApp()


def get_directory_settings(run_env: str):
    """Get appropriate directory settings based on environment."""
    if run_env == "vertex":
        vertex_settings = VertexDirectorySettings()  # type: ignore
        bucket_name = vertex_settings.BUCKET_NAME

        class VertexDirectoryConfig:
            ROOT_DIR = vertex_settings.ROOT_DIR.format(bucket=bucket_name)
            ARTIFACT_DIR = vertex_settings.ARTIFACT_DIR.format(bucket=bucket_name)

        return VertexDirectoryConfig()
    else:  # local
        return LocalDirectorySettings()  # type: ignore


class UploadCodeSettings(BaseModel):
    """Settings for uploading code to Kaggle."""

    run_env: str = Field("local", description="Environment type: 'local' or 'vertex'")
    kaggle_settings: KaggleSettings = Field(
        KaggleSettings(),  # type: ignore
        description="Kaggle settings for the upload process.",
    )


class UploadArtifactSettings(BaseModel):
    """Settings for uploading to Kaggle."""

    exp_name: str = Field(..., description="Experiment name for uploading artifacts.")
    run_env: str = Field("local", description="Environment type: 'local' or 'vertex'")
    kaggle_settings: KaggleSettings = Field(
        KaggleSettings(),  # type: ignore
        description="Kaggle settings for the upload process.",
    )


@app.command()
def codes(settings: UploadCodeSettings) -> None:
    """Upload the code to Kaggle."""
    directory_settings = get_directory_settings(settings.run_env)

    dataset_upload(
        client=client,
        handle=settings.kaggle_settings.CODES_HANDLE,
        local_dataset_dir=directory_settings.ROOT_DIR,
        update=True,
    )


@app.command()
def artifacts(settings: UploadArtifactSettings) -> None:
    """Upload the artifacts to Kaggle."""
    exp_name = settings.exp_name
    kaggle_settings = settings.kaggle_settings
    directory_settings = get_directory_settings(settings.run_env)

    model_upload(
        client=client,
        handle=f"{kaggle_settings.BASE_ARTIFACTS_HANDLE}/{exp_name}",
        local_model_dir=str(
            Path(directory_settings.ARTIFACT_DIR) / str(exp_name) / "1"
        ),
        update=False,
    )


@app.command()
def sources(settings: UploadArtifactSettings) -> None:
    """Upload the codes and artifacts to Kaggle."""
    codes(
        settings=UploadCodeSettings(
            run_env=settings.run_env, kaggle_settings=settings.kaggle_settings
        )
    )
    artifacts(settings)


if __name__ == "__main__":
    """Run the upload commands.

    Help:
    >>> uv run python -m src.kaggle_ops.upload codes -h
    >>> uv run python -m src.kaggle_ops.upload artifacts -h
    >>> uv run python -m src.kaggle_ops.upload sources -h
    """
    app.cli()
