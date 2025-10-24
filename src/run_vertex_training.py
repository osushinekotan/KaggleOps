from pathlib import Path

import tyro
from google.cloud import aiplatform
from pydantic import BaseModel, Field


class VertexTrainingConfig(BaseModel):
    script_path: str = Field(..., description="Path to the training script to execute")
    project_id: str = Field(..., description="GCP project ID")
    region: str = Field("us-central1", description="GCP region for Vertex AI")
    image_uri: str = Field(..., description="Container image URI (e.g., gcr.io/PROJECT/IMAGE:TAG)")
    display_name: str | None = Field(None, description="Display name for the training job")
    machine_type: str = Field("n1-standard-4", description="Machine type for training")
    service_account: str | None = Field(None, description="Service account for the job")


def run_vertex_training(config: VertexTrainingConfig) -> None:
    """Run training script on Vertex AI Custom Training Job."""
    aiplatform.init(project=config.project_id, location=config.region)

    display_name = config.display_name or f"training-{Path(config.script_path).stem}"

    job = aiplatform.CustomJob(
        display_name=display_name,
        worker_pool_specs=[
            {
                "machine_spec": {
                    "machine_type": config.machine_type,
                },
                "replica_count": 1,
                "container_spec": {
                    "image_uri": config.image_uri,
                    "command": ["python"],
                    "args": [config.script_path],
                },
            }
        ],
    )

    print(f"Starting Vertex AI Custom Training Job: {display_name}")
    job.run(service_account=config.service_account)
    print(f"Job completed: {job.resource_name}")


if __name__ == "__main__":
    config = tyro.cli(VertexTrainingConfig)
    run_vertex_training(config)
