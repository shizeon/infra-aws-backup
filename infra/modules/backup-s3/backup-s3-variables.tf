

variable "bucket" {
  description = "Full name of the destination bucket"
}

variable "dir_deep_archive" {
  description = "Directories to precreate in /deep_archive"
  type        = list(any)
}

variable "dir_standard_ia" {
  description = "Directories to precreate in /standard_ia"
}
variable "dir_glacier" {
  description = "Directories to precreate in /glacier"
}