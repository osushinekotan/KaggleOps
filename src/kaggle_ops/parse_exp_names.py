import json
import logging
from pathlib import Path

import tyro

from ..settings import SUBMISSION_CODE_DIR

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def parse_exp_names(kernel_metadata_path: Path = SUBMISSION_CODE_DIR / "kernel-metadata.json") -> list[str]:
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
    if not kernel_metadata_path.exists():
        raise FileNotFoundError(f"kernel-metadata.json not found: {kernel_metadata_path}")

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


if __name__ == "__main__":
    """Parse experiment names from kernel-metadata.json.

    Help:
    >>> uv run python -m src.kaggle_ops.parse_exp_names --help

    Example:
    >>> uv run python -m src.kaggle_ops.parse_exp_names
    >>> uv run python -m src.kaggle_ops.parse_exp_names --kernel-metadata-path /path/to/kernel-metadata.json
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s',
        force=True
    )
    exp_names = tyro.cli(parse_exp_names)
    # Output as comma-separated for easy shell consumption
    print(",".join(exp_names))
