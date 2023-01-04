
terraform {
  required_version = ">= 1.3.0, < 1.4.0"
  required_providers {
    aws = {
      source = "hashicorp/aws"
      version = "~> 4.48"
    }
    template = {
      source  = "hashicorp/template"
      version = "~> 2.2.0"
    }
  }
  backend "s3" {}
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = local.default_tags
  }
}

# Locals
locals {
  default_tags = {
    "Environment" = "tbd",
    "Name"        = "tbd",
    "Owner"       = "tbd",
    "Application" = "infra-aws-backup"
  }
}

module "archive_bucket" {
  source           = "./modules/backup-s3"
  bucket           = "bridgetek-family-backup"
  dir_deep_archive = ["photos", "video", "home"]
  dir_standard_ia  = []
  dir_glacier      = []
}
