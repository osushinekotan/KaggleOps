# インフラストラクチャのセットアップ

このガイドでは、Terraform を使用した GCP インフラストラクチャのセットアップ方法を説明する。

## 前提条件

- Google Cloud SDK がインストール済みであること
- GCP プロジェクトが作成済みであること
- Terraform がインストール済みであること
- Git リポジトリが初期化され、remote origin が設定済みであること

## セットアップ手順

### 1. Google Cloud への認証

```bash
# ローカル開発用の認証
gcloud auth application-default login

# gcloud CLI の認証
gcloud auth login

# GitHub への認証
gh auth login
```

### 2. 環境変数の設定

```bash
# .env ファイルのコピーと編集
cp .env.example .env

# .env を編集して以下を設定
# - PROJECT_ID: GCP プロジェクト ID
# - REGION: GCP リージョン (例: asia-northeast1)
# - BUCKET_NAME: データストレージ用 GCS バケット名
# - KAGGLE_USERNAME: Kaggle ユーザー名
# - KAGGLE_KEY: Kaggle API キー
# - KAGGLE_COMPETITION_NAME: コンペティション名
```

KAGGLE_COMPETITION_NAME の設定方法は、data tab 下部のダウンロードコマンドにある competition name を設定する。

例: `kaggle competitions download -c spaceship-titanic` の場合は `spaceship-titanic`

### 3. Terraform State 用 GCS バケットの作成

```bash
PROJECT_ID=your-project-id
REGION=asia-northeast1
BUCKET_NAME=${PROJECT_ID}-terraform-state

# バケットを作成
gsutil mb -p ${PROJECT_ID} -l ${REGION} gs://${BUCKET_NAME}

# バージョニングを有効化
gsutil versioning set on gs://${BUCKET_NAME}
```

### 4. Terraform の初期化

```bash
cd terraform/environments/dev

# .env から terraform.tfvars を生成
# このスクリプトは git remote origin から GitHub リポジトリを自動検出する
/workspace/scripts/init_tfvars.sh /workspace/.env

# アクセストークンを設定して初期化
export GOOGLE_OAUTH_ACCESS_TOKEN=$(gcloud auth application-default print-access-token)
terraform init
```

### 5. Terraform 設定の確認と適用

```bash
# 変更内容を確認
terraform plan

# 変更を適用
terraform apply
```

作成されるリソースは以下の通りである。

- サービスアカウント (Vertex AI 用、GitHub Actions 用)
- データストレージ用 GCS バケット
- Docker イメージ用 Artifact Registry
- GitHub Actions 用 Workload Identity Pool と Provider

### 6. Terraform の出力を .env にエクスポート

```bash
cd ../../..

cat >> .env << EOF

# Workload Identity Federation (terraform output から取得)
WIF_PROVIDER=$(cd terraform/environments/dev && terraform output -raw workload_identity_provider)
WIF_SERVICE_ACCOUNT=$(cd terraform/environments/dev && terraform output -json service_account_emails | jq -r '.github_actions')
EOF
```

## 次のステップ

### GitHub Actions のセットアップ

1. GitHub CLI がインストールされていない場合はインストールする
2. 自動化されたシークレット設定スクリプトを実行する

```bash
# リポジトリのルートから実行
gh auth login
./scripts/set_github_secrets.sh
```

このスクリプトは、.env ファイルから Workload Identity Federation の認証情報を含むすべてのシークレットを自動的に設定する。

詳細は [02_github_actions.md](02_github_actions.md) を参照。

### ローカル開発環境

Docker イメージを Artifact Registry に push する場合は以下を実行する。

```bash
# 環境変数が設定されていることを確認 (.env から読み込む)
source .env

# Cloud Build を使用してイメージをビルドして push
make push-image
```
