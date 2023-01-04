

resource "aws_s3_bucket" "backup" {
  bucket = var.bucket
}

resource "aws_s3_bucket_policy" "backup" {
  bucket = aws_s3_bucket.backup.id
  policy = templatefile(
    "${path.module}/policies/bucket_policy.tmpl.json",
    {
      TARGET_BUCKET = aws_s3_bucket.backup.id
    }
  )
}

resource "aws_s3_bucket_acl" "backup" {
  bucket = aws_s3_bucket.backup.id
  acl    = "private"
}

resource "aws_s3_bucket_versioning" "backup" {
  bucket = aws_s3_bucket.backup.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "backup" {
  bucket = aws_s3_bucket.backup.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "backup" {
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
      noncurrent_days = 2
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 2
    }
  }

  rule {
    id     = "TransitionToGlacierDeepArchive"
    status = "Enabled"

    filter {
      prefix = "deep_archive/"
    }

    transition {
      days          = 0
      storage_class = "DEEP_ARCHIVE"
    }
  }

  rule {
    id     = "TransitionToGlacier"
    status = "Enabled"

    filter {
      prefix = "glacier/"
    }

    transition {
      days          = 0
      storage_class = "GLACIER"
    }
  }

  rule {
    id     = "TransitionToStandardIA"
    status = "Enabled"

    filter {
      prefix = "standard_ia/"
    }

    transition {
      days          = 30 # 30 Day min
      storage_class = "STANDARD_IA"
    }
  }

  depends_on = [aws_s3_bucket_versioning.backup]
}

resource "aws_s3_bucket_server_side_encryption_configuration" "backup" {
  bucket = aws_s3_bucket.backup.bucket

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Create deep archive base folder
resource "aws_s3_object" "deep_dir" {
  bucket                 = aws_s3_bucket.backup.id
  acl                    = "private"
  key                    = "deep_archive/"
  content_type           = "application/x-directory"
  server_side_encryption = "AES256"
  storage_class          = "DEEP_ARCHIVE"
}

resource "aws_s3_object" "deep_dir_user" {
  for_each               = toset(var.dir_deep_archive)
  bucket                 = aws_s3_bucket.backup.id
  acl                    = "private"
  key                    = "deep_archive/${each.key}/"
  content_type           = "application/x-directory"
  server_side_encryption = "AES256"
  storage_class          = "DEEP_ARCHIVE"
}

# Create glacier base folder
resource "aws_s3_object" "glacier_dir" {
  bucket                 = aws_s3_bucket.backup.id
  acl                    = "private"
  key                    = "glacier/"
  content_type           = "application/x-directory"
  server_side_encryption = "AES256"
  storage_class          = "GLACIER"
}

resource "aws_s3_object" "glacier_dir_user" {
  for_each               = toset(var.dir_glacier)
  bucket                 = aws_s3_bucket.backup.id
  acl                    = "private"
  key                    = "glacier/${each.key}/"
  content_type           = "application/x-directory"
  server_side_encryption = "AES256"
  storage_class          = "GLACIER"
}


# Create standard_ia base folder
resource "aws_s3_object" "standardia_dir" {
  bucket                 = aws_s3_bucket.backup.id
  acl                    = "private"
  key                    = "standard_ia/"
  content_type           = "application/x-directory"
  server_side_encryption = "AES256"
  storage_class          = "STANDARD_IA"
}

resource "aws_s3_object" "standard_ia_dir_user" {
  for_each               = toset(var.dir_standard_ia)
  bucket                 = aws_s3_bucket.backup.id
  acl                    = "private"
  key                    = "standard_ia/${each.key}/"
  content_type           = "application/x-directory"
  server_side_encryption = "AES256"
  storage_class          = "STANDARD_IA"
}
