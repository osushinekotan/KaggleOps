import os

from git import Repo


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
