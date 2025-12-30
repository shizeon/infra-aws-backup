
terraform {
  required_version = "~> 1.15.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
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
    "Environment" = "Production",
    "Owner"       = "sean@bridgetek.com",
    "Application" = "bridgetek-family-backup-storage"
  }
}

module "archive_bucket" {
  source           = "./modules/backup-s3"
  bucket           = "bridgetek-family-backup"
  dir_deep_archive = var.dir_deep_archive
  dir_standard_ia  = var.dir_standard_ia
  dir_glacier      = var.dir_glacier
}
