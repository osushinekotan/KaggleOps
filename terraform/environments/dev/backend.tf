terraform {
  backend "gcs" {
    bucket = "osushinekotan-development-terraform-state"
    prefix = "terraform/state/dev"
  }
}
