# インフラストラクチャのセットアップ

このガイドでは、Terraform を使用した GCP インフラストラクチャのセットアップ方法を説明する。

## 前提条件

- Google Cloud SDK がインストール済みであること
- GCP プロジェクトが作成済みであること
- Terraform がインストール済みであること
- Git リポジトリが初期化され、remote origin が設定済みであること

## セットアップ手順

### 1. 認証

```bash
make auth
```

このコマンドは以下を実行する:
- Google Cloud への認証 (application-default と gcloud CLI)
- GitHub CLI への認証

### 2. 環境変数の設定

`.env.example` をコピーして `.env` を作成し、以下を設定する:

- PROJECT_ID: GCP プロジェクト ID
- REGION: GCP リージョン (例: asia-northeast1)
- BUCKET_NAME: データストレージ用 GCS バケット名
- KAGGLE_USERNAME: Kaggle ユーザー名
- KAGGLE_KEY: Kaggle API キー
- KAGGLE_COMPETITION_NAME: コンペティション名

KAGGLE_COMPETITION_NAME の設定方法は、data tab 下部のダウンロードコマンドにある competition name を設定する。

例: `kaggle competitions download -c spaceship-titanic` の場合は `spaceship-titanic`

### 3. インフラストラクチャの初期化

```bash
make init-infra
```

このコマンドは以下を実行する:
- Terraform State 用 GCS バケットの作成
- Terraform の初期化 (tfvars の生成と terraform init)

### 4. インフラストラクチャのセットアップ

```bash
# 変更内容を確認 (オプション)
make tf-plan

# インフラストラクチャのセットアップ
make setup-infra
```

`make setup-infra` は以下を実行する:
- Terraform apply によるリソースの作成
- Terraform の出力を .env にエクスポート
- GitHub Secrets の設定

作成されるリソースは以下の通りである:
- サービスアカウント (Vertex AI 用、GitHub Actions 用)
- データストレージ用 GCS バケット
- Docker イメージ用 Artifact Registry
- GitHub Actions 用 Workload Identity Pool と Provider

### 5. Docker イメージの GAR へのプッシュ

```bash
make push-image
```

- Cloud Build を使用した Docker イメージのビルド
- Google Artifact Registry (GAR) へのイメージプッシュ
- vertex custom training job, Github Actions で使用
