output "workload_identity_pool_id" {
  value       = google_iam_workload_identity_pool.github.workload_identity_pool_id
  description = "The ID of the Workload Identity Pool"
}

output "workload_identity_pool_name" {
  value       = google_iam_workload_identity_pool.github.name
  description = "The full resource name of the Workload Identity Pool"
}

output "workload_identity_provider_name" {
  value       = google_iam_workload_identity_pool_provider.github.name
  description = "The full resource name of the Workload Identity Provider"
}

output "provider_resource_name" {
  value       = google_iam_workload_identity_pool_provider.github.name
  description = "The provider resource name to use in GitHub Actions (WIF_PROVIDER secret)"
}
