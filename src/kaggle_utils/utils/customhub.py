import json
import logging
import os
import shutil
import subprocess
import tempfile
from fnmatch import fnmatch
from pathlib import Path

from kaggle import KaggleApi

from .utils import get_kaggle_authentication

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


KAGGLE_USERNAME, KAGGLE_KEY = get_kaggle_authentication()


IGNORE_PATTERNS = [
    ".*",
    "__pycache__",
    "data",
    "scripts",
    "pyproject.toml",
    "uv.lock",
    "catboost_info",
    "docs",
    "notebooks",
    "tests",
]


def existing_dataset(client: KaggleApi) -> list:
    """Check existing dataset in kaggle."""
    return client.dataset_list(user=KAGGLE_USERNAME)


def check_if_exist_dataset(client: KaggleApi, handle: str) -> bool:
    """Check if dataset already exist in kaggle."""
    for ds in existing_dataset(client):
        if str(ds.ref) == handle:
            return True
    return False


def existing_model(client: KaggleApi) -> list:
    """Check existing model instance in kaggle."""
    return client.model_list(owner=KAGGLE_USERNAME)


def check_if_exist_model(client: KaggleApi, handle: str) -> bool:
    """Check if model instance already exist in kaggle."""
    for model in existing_model(client):
        if str(model) == handle:
            return True
    return False


def check_if_exist_model_instance(client: KaggleApi, handle: str) -> bool:
    # handle = <username>/<model_slug>/<framework>/<variation_slug>/
    if len(handle.split("/")) == 5:
        # remove version suffix if exists
        handle = "/".join(handle.split("/")[:-1])

    logger.info(f"Checking model instance existence: {handle}")

    try:
        client.model_instance_get(model_instance=handle)
        return True
    except Exception as e:
        if "404" in str(e):
            logger.warning("Model instance not found")
            return False
        raise e


def make_dataset_metadata(handle: str) -> dict:
    """Create dataset metadata.

    Args:
        handle (str): "{USER_NAME}/{DATASET_NAME}"

    Returns:
        dict: dataset metadata
    """
    assert len(handle.split("/")) == 2, f"Invalid handle: {handle}"
    dataset_metadata = {}
    dataset_metadata["id"] = handle
    dataset_metadata["licenses"] = [{"name": "CC0-1.0"}]  # type: ignore
    dataset_metadata["title"] = handle.split("/")[-1]
    return dataset_metadata


def make_model_instance_metadata(handle: str) -> dict:
    # handle = <username>/<model_slug>/<framework>/<variation_slug>/
    assert len(handle.split("/")) == 4, f"Invalid handle: {handle}"
    owner_slug, model_slug, framework, instance_slug = handle.split("/")

    model_instance_metadata = {}
    model_instance_metadata["ownerSlug"] = owner_slug
    model_instance_metadata["modelSlug"] = model_slug
    model_instance_metadata["instanceSlug"] = instance_slug
    model_instance_metadata["framework"] = framework
    model_instance_metadata["licenseName"] = "Apache 2.0"

    return model_instance_metadata


def make_model_metadata(handle: str) -> dict:
    # handle = <username>/<model_slug>
    assert len(handle.split("/")) == 2, f"Invalid handle: {handle}"
    owner_slug, model_slug = handle.split("/")

    model_metadata = {}
    model_metadata["ownerSlug"] = owner_slug
    model_metadata["title"] = model_slug
    model_metadata["slug"] = model_slug
    model_metadata["isPrivate"] = True
    model_metadata["description"] = f"{model_slug} artifacts"

    return model_metadata


def copytree(src: str, dst: str, ignore_patterns: list | None = None) -> None:
    """Copytree with ignore patterns."""
    ignore_patterns = ignore_patterns or []

    if not os.path.exists(dst):
        os.makedirs(dst)

    for item in os.listdir(src):
        if any(fnmatch(item, pattern) for pattern in ignore_patterns):
            continue

        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            copytree(s, d, ignore_patterns)
        else:
            shutil.copy2(s, d)


def display_tree(directory: Path, file_prefix: str = "") -> None:
    """Display directory tree."""
    entries = list(directory.iterdir())
    file_count = len(entries)

    for i, entry in enumerate(sorted(entries, key=lambda x: x.name)):
        if i == file_count - 1:
            prefix = "└── "
            next_prefix = file_prefix + "    "
        else:
            prefix = "├── "
            next_prefix = file_prefix + "│   "

        line = file_prefix + prefix + entry.name
        print(line)

        if entry.is_dir():
            display_tree(entry, next_prefix)


def model_upload(
    client: KaggleApi,
    handle: str,
    local_model_dir: str,
    ignore_patterns: list[str] = IGNORE_PATTERNS,
    update: bool = False,  # 基本的に False (version 指定までしないといけないため)
) -> None:
    """Push output directory to kaggle model instance.

    handle: <username>/<model_slug>/<framework>/<variation_slug>/

    ref: https://github.com/Kaggle/kaggle-api/wiki/Model-Metadata
    """
    handle = handle.lower()

    model_handle = "/".join(handle.split("/")[:2])
    model_metadata = make_model_metadata(handle=model_handle)
    with tempfile.TemporaryDirectory() as tempdir:
        tempdir = Path(tempdir)
        with open(tempdir / "model-metadata.json", "w") as f:
            json.dump(model_metadata, f, indent=4)

        if not check_if_exist_model(client=client, handle=model_handle):
            client.model_create_new(folder=tempdir)

    model_instance_metadata = make_model_instance_metadata(handle=handle)
    is_exist_model_instance = check_if_exist_model_instance(client=client, handle=handle)

    if is_exist_model_instance and not update:
        logger.warning(f"{handle} already exist!! Stop pushing. 🛑")
        return

    with tempfile.TemporaryDirectory() as tempdir:
        tempdir = Path(tempdir)
        copytree(
            src=str(local_model_dir),
            dst=str(tempdir),
            ignore_patterns=ignore_patterns,
        )

        print(f"dst_dir={tempdir}\ntree")
        display_tree(tempdir)

        with open(tempdir / "model-instance-metadata.json", "w") as f:
            json.dump(model_instance_metadata, f, indent=4)

        if not is_exist_model_instance:
            logger.info(f"create {handle}")
            client.model_instance_create(
                folder=tempdir,
                quiet=False,
                dir_mode="zip",
            )
            return

        logger.info(f"update {handle}")
        client.model_instance_version_create(
            model_instance=handle,
            folder=tempdir,
            version_notes="latest",
            quiet=False,
            dir_mode="zip",
        )


def dataset_upload(
    client: KaggleApi,
    handle: str,
    local_dataset_dir: str,
    ignore_patterns: list[str] = IGNORE_PATTERNS,
    update: bool = False,
) -> None:
    """Push output directory to kaggle dataset."""
    handle = handle.lower()

    # model and predictions
    metadata = make_dataset_metadata(handle=handle)

    # if exist dataset, stop pushing
    if check_if_exist_dataset(client=client, handle=handle) and not update:
        logger.warning(f"{handle} already exist!! Stop pushing. 🛑")
        return

    dataset_name = handle.split("/")[-1]

    with tempfile.TemporaryDirectory() as tempdir:
        dst_dir = Path(tempdir) / dataset_name

        copytree(
            src=str(local_dataset_dir),
            dst=str(dst_dir),
            ignore_patterns=ignore_patterns,
        )

        print(f"dst_dir={dst_dir}\ntree")
        display_tree(dst_dir)

        with open(Path(dst_dir) / "dataset-metadata.json", "w") as f:
            json.dump(metadata, f, indent=4)

        if check_if_exist_dataset(client=client, handle=handle) and update:
            logger.info(f"update {handle}")
            client.dataset_create_version(
                folder=dst_dir,
                version_notes="latest",
                quiet=False,
                convert_to_csv=False,
                delete_old_versions=False,
                dir_mode="zip",
            )
            return

        logger.info(f"create {handle}")
        client.dataset_create_new(
            folder=dst_dir,
            public=False,
            quiet=False,
            dir_mode="zip",
        )


def competition_download(
    client: KaggleApi,
    handle: str,
    destination: str | Path = "./",
    force_download: bool = False,
) -> None:
    """Download competition dataset.

    Args:
        destination (str | Path): base destination directory ({destination}/{handle} is created)
        handle (str): competition name
        force_download (bool, optional): if True, overwrite existing dataset. Defaults to False.
    """
    out_dir = Path(destination) / handle
    zipfile_path = out_dir / f"{handle}.zip"
    zipfile_path.parent.mkdir(exist_ok=True, parents=True)

    if not zipfile_path.is_file() or force_download:
        client.competition_download_files(
            competition=handle,
            path=out_dir,
            quiet=False,
            force=force_download,
        )
        subprocess.run(["unzip", "-o", "-q", zipfile_path, "-d", out_dir])
    else:
        logger.info(f"Dataset ({handle}) already exists.")


def datasets_download(
    client: KaggleApi,
    handles: list[str],
    destination: str | Path = "./",
    force_download: bool = False,
) -> None:
    """Download kaggle datasets.

    Args:
        handles (list[str]): list of dataset names (e.g. ["username/dataset-name"])
        destination (str | Path, optional): destination directory. Defaults to "./".
        force_download (bool, optional): if True, overwrite existing dataset. Defaults to False.
    """
    for dataset in handles:
        dataset_name = dataset.split("/")[1]
        out_dir = Path(destination) / dataset_name
        zipfile_path = out_dir / f"{dataset_name}.zip"

        out_dir.mkdir(exist_ok=True, parents=True)

        if not zipfile_path.is_file() or force_download:
            logger.info(f"Downloading dataset: {dataset}")
            client.dataset_download_files(
                dataset=dataset,
                quiet=False,
                unzip=False,
                path=out_dir,
                force=force_download,
            )

            subprocess.run(["unzip", "-o", "-q", zipfile_path, "-d", out_dir])
        else:
            logger.info(f"Dataset ({dataset}) already exists.")
