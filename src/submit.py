import json
import os
import subprocess
import time
from pathlib import Path

import tyro
from pydantic import BaseModel

from kaggle_utils.check import CheckNecessaryArtifactsSettings, nessesary_artifacts_exist
from kaggle_utils.upload import UploadArtifactSettings, UploadCodeSettings, artifacts, codes
from settings import SUBMISSION_CODE_DIR


class PushSubmissionConfig(BaseModel):
    """Configuration for pushing submission to Kaggle."""

    # exp_name is no longer required - will be read from kernel-metadata.json
    pass


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
    with open(kernel_metadata_path, "r") as f:
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


def push_submission(config: PushSubmissionConfig) -> None:
    """
    Upload artifacts, code, and push submission to Kaggle.

    This script works in both local and Vertex AI environments.

    Steps:
    1. Parse exp_names from kernel-metadata.json
    2. Uploads artifacts for each exp_name to Kaggle
    3. Waits for 60 seconds
    4. Checks that necessary artifacts exist
    5. Uploads code to Kaggle
    6. Waits for 30 seconds
    7. Pushes the submission using kaggle CLI
    """
    bucket_name = os.environ.get("BUCKET_NAME")
    if bucket_name:
        print(f"Running in GCS-enabled environment. Bucket: {bucket_name}")
    else:
        print("Running in local environment (no GCS bucket)")

    # Parse exp_names from kernel-metadata.json
    kernel_metadata_path = SUBMISSION_CODE_DIR / "kernel-metadata.json"
    if not kernel_metadata_path.exists():
        raise FileNotFoundError(f"kernel-metadata.json not found: {kernel_metadata_path}")

    exp_names = parse_exp_names_from_kernel_metadata(kernel_metadata_path)
    if not exp_names:
        raise ValueError("No exp_names found in kernel-metadata.json's model_sources")

    print(f"Found {len(exp_names)} experiment(s) to upload: {exp_names}")

    # Step 1: Upload artifacts for each exp_name
    for exp_name in exp_names:
        print(f"Uploading artifacts for experiment: {exp_name}")
        artifact_settings = UploadArtifactSettings(exp_name=exp_name)
        artifacts(artifact_settings)
        print(f"Artifacts for {exp_name} uploaded successfully")

    # Step 2: Wait for 60 seconds
    print("Waiting for 60 seconds for artifacts to be processed...")
    time.sleep(60)

    # Step 3: Check necessary artifacts exist
    print("Checking if necessary artifacts exist...")
    check_settings = CheckNecessaryArtifactsSettings()
    if not nessesary_artifacts_exist(check_settings):
        raise RuntimeError("Necessary artifacts do not exist. Cannot proceed with submission.")

    # Step 4: Upload codes
    print("Uploading code to Kaggle...")
    code_settings = UploadCodeSettings()
    codes(code_settings)

    # Step 5: Wait for 30 seconds
    print("Waiting for 30 seconds...")
    time.sleep(30)

    # Step 6: Push submission
    print("Pushing submission to Kaggle...")
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
    config = tyro.cli(PushSubmissionConfig)
    push_submission(config)
