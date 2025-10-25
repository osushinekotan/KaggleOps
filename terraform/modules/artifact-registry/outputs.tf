output "repository_name" {
  value = google_artifact_registry_repository.this.name
}

output "registry_uri" {
  value = google_artifact_registry_repository.this.registry_uri
}
