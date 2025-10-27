import json
import logging
import time
from pathlib import Path

import dotenv
import tyro

from ..settings import SUBMISSION_CODE_DIR, KaggleSettings
from .check import CheckNecessaryArtifactsSettings, nessesary_artifacts_exist
from .upload import UploadArtifactSettings, artifacts

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

dotenv.load_dotenv()


def parse_exp_names_from_kernel_metadata(kernel_metadata_path: Path) -> list[str]:
    """
    Parse experiment names from kernel-metadata.json's model_sources.

    Args:
        kernel_metadata_path: Path to kernel-metadata.json

    Returns:
        List of experiment names extracted from model_sources

    Example:
        model_sources: ["mst8823/spaceship-titanic-artifacts/other/spaceship-titanic/1"]
        -> returns: ["spaceship-titanic"]
    """
    with open(kernel_metadata_path) as f:
        metadata = json.load(f)

    model_sources = metadata.get("model_sources", [])
    exp_names = []

    for source in model_sources:
        # Format: {username}/{dataset-slug}/other/{exp_name}/{version}
        parts = source.split("/")
        if len(parts) >= 4:
            exp_name = parts[3]  # exp_name is the 4th element (index 3)
            exp_names.append(exp_name)

    return exp_names


def push_artifacts(run_env: str = "local") -> None:
    """
    Upload artifacts to Kaggle for all experiments listed in kernel-metadata.json.

    This command:
    1. Parses exp_names from kernel-metadata.json
    2. Uploads artifacts for each experiment
    3. Waits 60s for processing
    4. Checks that all necessary artifacts exist

    Args:
        run_env: Environment type: 'local' or 'vertex'
    """
    print(f"Running in {run_env} environment")

    # Initialize Kaggle settings
    kaggle_settings = KaggleSettings()  # type: ignore

    # Parse exp_names from kernel-metadata.json
    kernel_metadata_path = SUBMISSION_CODE_DIR / "kernel-metadata.json"
    if not kernel_metadata_path.exists():
        raise FileNotFoundError(f"kernel-metadata.json not found: {kernel_metadata_path}")

    exp_names = parse_exp_names_from_kernel_metadata(kernel_metadata_path)
    if not exp_names:
        raise ValueError("No exp_names found in kernel-metadata.json's model_sources")

    print(f"Experiments to upload: {exp_names}")

    # Upload artifacts for each exp_name
    for exp_name in exp_names:
        print(f"Uploading artifacts: {exp_name}")
        artifact_settings = UploadArtifactSettings(
            exp_name=exp_name, run_env=run_env, kaggle_settings=kaggle_settings
        )
        artifacts(artifact_settings)

    print("Waiting 60s for artifacts to be processed...")
    time.sleep(60)

    # Check necessary artifacts exist
    print("Checking artifacts...")
    check_settings = CheckNecessaryArtifactsSettings(kaggle_settings=kaggle_settings)
    if not nessesary_artifacts_exist(check_settings):
        raise RuntimeError("Necessary artifacts do not exist. Cannot proceed with submission.")

    print("All artifacts uploaded and verified successfully")


if __name__ == "__main__":
    """Run the push commands.

    Help:
    >>> uv run python -m src.kaggle_ops.push --help

    Example:
    >>> uv run python -m src.kaggle_ops.push --run-env local
    >>> uv run python -m src.kaggle_ops.push --run-env vertex
    """
    tyro.cli(push_artifacts)
