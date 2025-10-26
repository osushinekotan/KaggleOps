resource "google_artifact_registry_repository" "this" {
  project       = var.project_id
  repository_id = var.repository_id
  location      = var.location
  format        = var.format

  cleanup_policies {
    id     = "keep-latest-versions"
    action = "DELETE"

    most_recent_versions {
      keep_count = var.keep_image_count
    }
  }
}
