from pathlib import Path

import tyro
from google.cloud import aiplatform
from pydantic import BaseModel, Field


class VertexTrainingConfig(BaseModel):
    script_path: str = Field(..., description="Path to the local training script to execute")
    project_id: str = Field(..., description="GCP project ID")
    region: str = Field("us-central1", description="GCP region for Vertex AI")
    staging_bucket: str = Field(..., description="GCS bucket for staging (e.g., gs://your-bucket)")
    container_uri: str = Field(..., description="Container image URI (e.g., gcr.io/PROJECT/IMAGE:TAG)")
    display_name: str | None = Field(None, description="Display name for the training job")
    machine_type: str = Field("n1-standard-4", description="Machine type for training")
    service_account: str | None = Field(None, description="Service account for the job")


def run_vertex_training(config: VertexTrainingConfig) -> None:
    """Run training script on Vertex AI Custom Training Job using from_local_script."""
    aiplatform.init(project=config.project_id, location=config.region, staging_bucket=config.staging_bucket)

    display_name = config.display_name or f"training-{Path(config.script_path).stem}"

    job = aiplatform.CustomJob.from_local_script(
        display_name=display_name,
        script_path=config.script_path,
        container_uri=config.container_uri,
        machine_type=config.machine_type,
    )

    print(f"Starting Vertex AI Custom Training Job: {display_name}")
    job.run(service_account=config.service_account)
    print(f"Job completed: {job.resource_name}")


if __name__ == "__main__":
    config = tyro.cli(VertexTrainingConfig)
    run_vertex_training(config)
