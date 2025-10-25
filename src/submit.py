import os
import subprocess
import time

import tyro
from pydantic import BaseModel, Field

from kaggle_utils.check import CheckNecessaryArtifactsSettings, nessesary_artifacts_exist
from kaggle_utils.upload import UploadArtifactSettings, UploadCodeSettings, artifacts, codes
from settings import SUBMISSION_CODE_DIR


class PushSubmissionConfig(BaseModel):
    """Configuration for pushing submission to Kaggle."""

    exp_name: str = Field(..., description="Experiment name for uploading artifacts")


def push_submission(config: PushSubmissionConfig) -> None:
    """
    Upload artifacts, code, and push submission to Kaggle.

    This script works in both local and Vertex AI environments.

    Steps:
    1. Uploads artifacts to Kaggle
    2. Waits for 60 seconds
    3. Checks that necessary artifacts exist
    4. Uploads code to Kaggle
    5. Waits for 30 seconds
    6. Pushes the submission using kaggle CLI
    """
    bucket_name = os.environ.get("BUCKET_NAME")
    if bucket_name:
        print(f"Running in GCS-enabled environment. Bucket: {bucket_name}")
    else:
        print("Running in local environment (no GCS bucket)")

    print(f"Experiment name: {config.exp_name}")

    # Step 1: Upload artifacts
    print("Uploading artifacts to Kaggle...")
    artifact_settings = UploadArtifactSettings(exp_name=config.exp_name)
    artifacts(artifact_settings)
    print("Artifacts uploaded successfully")

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
