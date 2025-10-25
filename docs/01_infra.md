```bash
gcloud auth application-default login
gcloud auth login
```

create gcs bucket for terraform state

```bash
PROJECT_ID=osushinekotan-development
REGION=asia-northeast1
BUCKET_NAME=${PROJECT_ID}-terraform-state

gsutil mb -p ${PROJECT_ID} -l ${REGION} gs://${BUCKET_NAME}
gsutil versioning set on gs://${BUCKET_NAME}
```

init terraform

```bash
cd terraform/environments/dev
/workspace/scripts/init_tfvars.sh /workspace/.env
```

```bash
export GOOGLE_OAUTH_ACCESS_TOKEN=$(gcloud auth application-default print-access-token)
terraform init
```

plan terraform

```bash
terraform plan
```

apply terraform

```bash
terraform apply
```
