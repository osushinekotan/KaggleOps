from git import Repo


def get_default_exp_name(use_commit_hash: bool = False) -> str:
    repo = Repo(search_parent_directories=True)
    branch = repo.active_branch
    commit_hash = repo.head.object.hexsha[:7] if use_commit_hash else ""
    return f"{branch}{'-' + commit_hash if commit_hash else ''}"
