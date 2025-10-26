variable "project_id" {
  type        = string
  description = "The ID of the project"
}

variable "pool_id" {
  type        = string
  description = "The ID of the Workload Identity Pool"
  default     = "github"
}

variable "pool_display_name" {
  type        = string
  description = "The display name of the Workload Identity Pool"
  default     = "GitHub Actions Pool"
}

variable "pool_description" {
  type        = string
  description = "The description of the Workload Identity Pool"
  default     = "Workload Identity Pool for GitHub Actions"
}

variable "provider_id" {
  type        = string
  description = "The ID of the Workload Identity Pool Provider"
  default     = "github-provider"
}

variable "provider_display_name" {
  type        = string
  description = "The display name of the Workload Identity Pool Provider"
  default     = "GitHub Provider"
}

variable "provider_description" {
  type        = string
  description = "The description of the Workload Identity Pool Provider"
  default     = "OIDC provider for GitHub Actions"
}

variable "repository" {
  type        = string
  description = "The GitHub repository in the format 'owner/repo'"
}

variable "service_account_id" {
  type        = string
  description = "The ID of the service account to bind Workload Identity"
}
