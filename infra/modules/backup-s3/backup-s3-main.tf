

resource "aws_s3_bucket" "backup" {
  bucket = var.bucket
}

resource "aws_s3_bucket_policy" "state_bucket" {
  bucket = aws_s3_bucket.backup.id
  policy = templatefile(
    "${path.module}/policies/bucket_policy.tmpl.json",
    {
      TARGET_BUCKET = aws_s3_bucket.backup.id
    }
  )
}

resource "aws_s3_bucket_acl" "state_bucket" {
  bucket = aws_s3_bucket.backup.id
  acl    = "private"
}

resource "aws_s3_bucket_versioning" "state_bucket" {
  bucket = aws_s3_bucket.backup.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "state_bucket" {
  bucket = aws_s3_bucket.backup.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "state_bucket" {
  bucket = aws_s3_bucket.backup.id

  rule {
    id     = "VersionCleanup"
    status = "Enabled"

    filter {
      prefix = ""
    }

    expiration {
      expired_object_delete_marker = true
    }

    noncurrent_version_expiration {
      noncurrent_days = 90
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }

  }

  depends_on = [
    # versioning must be set before lifecycle configuration
    aws_s3_bucket_versioning.state_bucket
  ]
}