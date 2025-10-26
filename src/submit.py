import json
import subprocess
import time
from pathlib import Path

from kaggle_ops.check import CheckNecessaryArtifactsSettings, nessesary_artifacts_exist
from kaggle_ops.upload import UploadArtifactSettings, UploadCodeSettings, artifacts, codes
from kaggle_ops.utils.utils import get_run_env
from settings import SUBMISSION_CODE_DIR


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


def push_submission() -> None:
    """Upload artifacts, code, and push submission to Kaggle."""
    run_env = get_run_env()
    print(f"Running in {run_env} environment")

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
        artifact_settings = UploadArtifactSettings(exp_name=exp_name, run_env=run_env)
        artifacts(artifact_settings)

    print("Waiting 60s for artifacts to be processed...")
    time.sleep(60)

    # Check necessary artifacts exist
    print("Checking artifacts...")
    check_settings = CheckNecessaryArtifactsSettings()
    if not nessesary_artifacts_exist(check_settings):
        raise RuntimeError("Necessary artifacts do not exist. Cannot proceed with submission.")

    # Upload codes
    print("Uploading code...")
    code_settings = UploadCodeSettings(run_env=run_env)
    codes(code_settings)

    print("Waiting 30s...")
    time.sleep(30)

    # Push submission
    print("Pushing submission...")
    submission_dir = SUBMISSION_CODE_DIR
    if not submission_dir.exists():
        raise FileNotFoundError(f"Submission directory not found: {submission_dir}")

    result = subprocess.run(
        ["kaggle", "k", "push"], cwd=str(submission_dir), check=True, capture_output=True, text=True
    )
    print(result.stdout)
    if result.stderr:
        print("Stderr:", result.stderr)

    print("Submission pushed successfully")


if __name__ == "__main__":
    push_submission()
