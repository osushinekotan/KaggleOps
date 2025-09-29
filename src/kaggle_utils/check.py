import json
import logging

import dotenv
from kaggle import KaggleApi
from pydantic import BaseModel, Field
from tyro.extras import SubcommandApp

from ..settings import SUBMISSION_CODE_DIR, KaggleSettings, LocalDirectorySettings
from .utils.customhub import check_if_exist_model_instance

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

dotenv.load_dotenv()
client = KaggleApi()
client.authenticate()

app = SubcommandApp()
local_directory_settings = LocalDirectorySettings()  # type: ignore


class CheckNecessaryArtifactsSettings(BaseModel):
    """
    Settings for checking if the necessary artifacts for the submission code exist.
    """

    kaggle_settings: KaggleSettings = Field(
        default_factory=lambda: KaggleSettings(),  # type: ignore
        description="Kaggle settings for the check process.",
    )


@app.command()
def nessesary_artifacts_exist(settings: CheckNecessaryArtifactsSettings) -> bool:
    """Check if the necessary artifacts for the submission code exist."""
    kaggle_settings = settings.kaggle_settings
    metadata_path = SUBMISSION_CODE_DIR / "kernel-metadata.json"
    if not metadata_path.exists():
        logger.error(f"Metadata file not found: {metadata_path}")
        return False

    with open(metadata_path) as f:
        metadata = json.load(f)

    model_sources = metadata.get("model_sources", [])
    for handle in model_sources:
        if not handle.startswith(kaggle_settings.BASE_ARTIFACTS_HANDLE):
            logger.error(f"Invalid model source handle: {handle}")
            return False
        if not check_if_exist_model_instance(client, handle):
            logger.error(f"Model instance does not exist: {handle}")
            return False

    return True


if __name__ == "__main__":
    """
    Command line interface for checking necessary artifacts for the submission code.
    Example:
    >>> uv run python -m src.kaggle_utils.check nessesary-artifacts-exist
    """
    app.cli()
