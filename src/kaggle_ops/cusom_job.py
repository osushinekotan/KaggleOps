from pathlib import Path

import tyro
from google.cloud import aiplatform
from pydantic import BaseModel, Field
from pydantic_settings import SettingsConfigDict


class VertexTrainingConfig(BaseModel):
    script_path: str = Field(..., description="Path to the local training script to execute")
    project_id: str = Field(..., description="GCP project ID")
    bucket_name: str = Field(..., description="GCS bucket name")
    container_uri: str = Field(..., description="Container image URI (e.g., gcr.io/PROJECT/IMAGE:TAG)")
    region: str = Field(..., description="GCP region for Vertex AI")

    display_name: str | None = Field(None, description="Display name for the training job")
    machine_type: str = Field("n1-standard-4", description="Machine type for training")
    service_account: str | None = Field(None, description="Service account for the job")
    args: list[str] | None = Field(None, description="Arguments to pass to the script")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


def run_job(config: VertexTrainingConfig) -> None:
    """Run job on Vertex AI Custom Training Job using from_local_script."""
    aiplatform.init(project=config.project_id, location=config.region)

    display_name = config.display_name or f"training-{Path(config.script_path).stem}"

    job = aiplatform.CustomJob.from_local_script(
        display_name=display_name,
        script_path=config.script_path,
        container_uri=config.container_uri,
        machine_type=config.machine_type,
        environment_variables={"BUCKET_NAME": config.bucket_name},
        args=config.args,
    )

    print(f"Starting Vertex AI Custom Training Job: {display_name}")
    if config.args:
        print(f"Arguments: {' '.join(config.args)}")
    job.run(service_account=config.service_account)
    print(f"Job completed: {job.resource_name}")


if __name__ == "__main__":
    config = tyro.cli(VertexTrainingConfig)
    run_job(config)
