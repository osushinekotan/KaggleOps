# GitHub Actions のセットアップ

## 前提条件

- Terraform で GCP リソースをデプロイ済みであること ([01_infrastructure.md](01_infrastructure.md) を参照)
- GitHub リポジトリへの管理者アクセス権があること
- GitHub CLI がインストール済みであること

## セットアップ手順

### 1. Terraform の適用

インフラストラクチャのセットアップについては [01_infrastructure.md](01_infrastructure.md) を参照。

```bash
cd terraform/environments/dev
terraform output
```

### 2. GitHub Secrets の設定

Terraform の出力を .env ファイルに追加した後 ([01_infrastructure.md](01_infrastructure.md) を参照)、以下のいずれかの方法で GitHub Secrets を設定する。

#### 方法 A: 自動設定 (推奨)

```bash
# GitHub CLI で認証
gh auth login

# .env からすべてのシークレットを設定
./scripts/set_github_secrets.sh
```

このスクリプトは .env から以下のシークレットを設定する。

- PROJECT_ID
- REGION
- BUCKET_NAME
- KAGGLE_USERNAME
- KAGGLE_KEY
- KAGGLE_COMPETITION_NAME
- WIF_PROVIDER (Terraform の出力から取得)
- WIF_SERVICE_ACCOUNT (Terraform の出力から取得)

#### 方法 B: 手動設定

Settings > Secrets and variables > Actions に移動し、.env ファイルからすべてのシークレットを手動で追加する。
