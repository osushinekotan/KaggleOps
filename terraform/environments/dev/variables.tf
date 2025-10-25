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
