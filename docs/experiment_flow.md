# 実験フロー

## セットアップ

1. `make setup` を実行して以下のファイルを作成する

   - codes/submission/code.ipynb
   - codes/submission/metadata.json
   - codes/deps/code.ipynb
   - codes/deps/metadata.json

2. `make dl-comp` でデータセットをダウンロードする

## 学習スクリプトの実装

src/train.py を実装する。ファイル名は任意で構わない。

ディレクトリ設定は src/settings.py の DirectorySettings を使用する。

- COMP_DATASET_DIR: コンペティションデータセットのディレクトリ
- OUTPUT_DIR: 出力ディレクトリ

hydra などで yaml ファイルを作成し、実行時に読み込む方法なども使用可能である。

## 推論スクリプトの実装

src/inference.py を実装する。ファイル名は固定である。

ディレクトリ設定は src/settings.py の DirectorySettings を使用する。

- COMP_DATASET_DIR: コンペティションデータセットのディレクトリ
- OUTPUT_DIR: 出力ディレクトリ (kaggle 環境における kaggle/working ディレクトリ)
- ARTIFACT_EXP_DIR: 実験成果物のディレクトリ (使用したいモデル等のロード元のディレクトリ)

## 学習の実行

学習は local もしくは vertex 環境で実行可能である。

- `make train-local` もしくは `make train-vertex` で実行する
- local 実行の場合は `python src/train.py` でも実行可能である
- `make push-data` で成果物を GCS に push する (vertex 環境では自動的に gcs bucket が mount されるため不要)

## 提出

`make submit-local` もしくは `make submit-vertex` で提出可能である。

codes/submission/metadata.json の model_sources にあるモデルを使用して提出される。model_sources に使用したい実験名を追加することで、その実験の出力 (output) を使用することができるようになる。

- submit-local: local directory を参照し artifact (実験出力) を push する
- submit-vertex: gcs bucket を参照し artifact (実験出力) を push する
