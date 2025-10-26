variable "project_id" {
  type        = string
  description = "The ID of the project in which to deploy resources."
}

variable "repository_id" {
  type        = string
  description = "The name of the artifact registry repository to create."
}

variable "location" {
  type        = string
  description = "The location of the artifact registry repository to create."
}

variable "format" {
  type        = string
  description = "The format of the artifact registry repository to create."
  default     = "DOCKER"
}

variable "keep_image_count" {
  type        = number
  description = "Number of most recent image versions to keep. Older versions will be automatically deleted."
  default     = 3
}
