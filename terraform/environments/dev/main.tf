provider "google" {
  project = var.project_id
  region  = var.region
}

module "service_accounts" {
  source       = "../../modules/service-account"
  for_each     = var.service_accounts
  project_id   = var.project_id
  account_id   = each.value.account_id
  display_name = each.value.display_name
  description  = each.value.description
  roles        = each.value.roles
}

output "service_account_emails" {
  value = { for k, v in module.service_accounts : k => v.service_account_email }
}

module "gcs_buckets" {
  source   = "../../modules/gcs-bucket"
  for_each = var.gcs_buckets

  project_id                  = var.project_id
  name                        = each.value.name
  location                    = each.value.location
  storage_class               = each.value.storage_class
  versioning_enabled          = each.value.versioning_enabled
  uniform_bucket_level_access = each.value.uniform_bucket_level_access
}

module "artifact_registries" {
  source   = "../../modules/artifact-registry"
  for_each = var.artifact_registries

  project_id    = var.project_id
  repository_id = each.value.repository_id
  location      = each.value.location
  format        = each.value.format
}

module "workload_identity" {
  source = "../../modules/workload-identity"

  project_id         = var.project_id
  pool_id            = var.workload_identity_pool_id
  provider_id        = var.workload_identity_provider_id
  repository         = var.github_repository
  service_account_id = module.service_accounts["github_actions"].service_account_name

  depends_on = [
    module.service_accounts
  ]
}

output "workload_identity_provider" {
  value       = module.workload_identity.provider_resource_name
  description = "Workload Identity Provider resource name for GitHub Actions (use this for WIF_PROVIDER secret)"
}
