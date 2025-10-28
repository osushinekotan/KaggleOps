import json
import logging
from pathlib import Path

import dotenv
import tyro

from ..settings import SUBMISSION_CODE_DIR, KaggleSettings
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


def push_artifacts(run_env: str = "local", exp_names: str = "") -> None:
    """
    Upload artifacts to Kaggle for specified experiments.

    This command:
    1. Uses provided exp_names or parses them from kernel-metadata.json
    2. Uploads artifacts for each experiment
    3. Waits 60s for processing
    4. Checks that all necessary artifacts exist

    Args:
        run_env: Environment type: 'local' or 'vertex'
        exp_names: Comma-separated experiment names (optional, defaults to parsing from kernel-metadata.json)
    """
    print(f"Running in {run_env} environment")

    # Initialize Kaggle settings
    kaggle_settings = KaggleSettings()  # type: ignore

    # Determine exp_names: use provided argument or parse from kernel-metadata.json
    if exp_names:
        exp_names_list = [name.strip() for name in exp_names.split(",")]
        print(f"Using provided exp_names: {exp_names_list}")
    else:
        # Parse exp_names from kernel-metadata.json
        kernel_metadata_path = SUBMISSION_CODE_DIR / "kernel-metadata.json"
        if not kernel_metadata_path.exists():
            raise FileNotFoundError(f"kernel-metadata.json not found: {kernel_metadata_path}")

        exp_names_list = parse_exp_names_from_kernel_metadata(kernel_metadata_path)
        if not exp_names_list:
            raise ValueError("No exp_names found in kernel-metadata.json's model_sources")
        print(f"Parsed exp_names from kernel-metadata.json: {exp_names_list}")

    print(f"Experiments to upload: {exp_names_list}")

    # Upload artifacts for each exp_name
    for exp_name in exp_names_list:
        print(f"Uploading artifacts: {exp_name}")
        artifact_settings = UploadArtifactSettings(exp_name=exp_name, run_env=run_env, kaggle_settings=kaggle_settings)
        artifacts(artifact_settings)

    print("All artifacts uploaded successfully")


if __name__ == "__main__":
    """Run the push commands.

    Help:
    >>> uv run python -m src.kaggle_ops.push --help

    Example:
    >>> uv run python -m src.kaggle_ops.push --run-env local
    >>> uv run python -m src.kaggle_ops.push --run-env vertex
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s", force=True)
    tyro.cli(push_artifacts)
