variable "aws_region" {
  default = "us-west-2"
}

variable "dir_deep_archive" {
  description = "Map of prexies in the S3 bucket that will have deep archive applied"
  default     = ["photos", "video", "home", "dxc"]
  type        = list(string)
}

variable "dir_standard_ia" {
  description = "Map of prexies in the S3 bucket that will have standard ia applied"
  default     = []
  type        = list(string)
}

variable "dir_glacier" {
  description = "Map of prexies in the S3 bucket that will have standard clacier applied"
  default     = []
  type        = list(string)
}
