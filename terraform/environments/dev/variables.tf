variable "project_id" {
  type        = string
  description = "The ID of the project in which to deploy resources."
}

variable "region" {
  type        = string
  description = "The region in which to deploy resources."
}

variable "service_accounts" {
  description = "The service accounts to create."
  type = map(object({
    account_id   = string
    display_name = string
    description  = string
    roles        = list(string)
  }))
}

variable "gcs_buckets" {
  description = "The GCS buckets to create."
  type = map(object({
    name                        = string
    location                    = string
    storage_class               = optional(string)
    versioning_enabled          = optional(bool, false)
    uniform_bucket_level_access = optional(bool, true)
  }))
}
