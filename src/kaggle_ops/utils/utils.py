import os
from pathlib import Path

from git import Repo


def get_run_env() -> str:
    """Detect and return the current runtime environment.

    Returns:
        str: One of 'kaggle', 'vertex', or 'local'
    """
    if os.getenv("KAGGLE_DATA_PROXY_TOKEN"):
        return "kaggle"
    elif os.getenv("BUCKET_NAME"):
        # Check if running in Vertex AI (GCSFuse mounted)
        bucket_name = os.getenv("BUCKET_NAME")
        if Path(f"/gcs/{bucket_name}").exists():
            return "vertex"
    return "local"


def get_default_exp_name(use_commit_hash: bool = False) -> str:
    repo = Repo(search_parent_directories=True)
    branch = repo.active_branch
    commit_hash = repo.head.object.hexsha[:7] if use_commit_hash else ""
    return f"{branch}{'-' + commit_hash if commit_hash else ''}"


def get_kaggle_authentication() -> tuple[str, str]:
    kaggle_username = os.getenv("KAGGLE_USERNAME")
    kaggle_key = os.getenv("KAGGLE_KEY")

    if not kaggle_username:
        raise ValueError("KAGGLE_USERNAME is not set. Please set it in your environment variables.")
    if not kaggle_key:
        raise ValueError("KAGGLE_KEY is not set. Please set it in your environment variables.")

    return kaggle_username, kaggle_key


def get_kaggle_competition_name() -> str:
    kaggle_competition_name = os.getenv("KAGGLE_COMPETITION_NAME")

    if not kaggle_competition_name:
        raise ValueError("KAGGLE_COMPETITION_NAME is not set. Please set it in your environment variables.")

    return kaggle_competition_name
