# WealthHub AWS foundations.
#
# Scope: the building blocks the app needs before it can run on AWS (encryption key, private PDF
# storage, image registries, logging, scoped IAM roles, a secret container). The compute and
# database layer (ECS Fargate, RDS, load balancer) is deliberately not here yet because it costs
# money; see docs/aws-design.md. Everything below is formatted, statically validated and scanned
# in CI. It has not been applied.

data "aws_caller_identity" "current" {}

locals {
  name       = "${var.project}-${var.environment}"
  account_id = data.aws_caller_identity.current.account_id
  services   = toset(["api", "worker", "dashboard"])
}

# ---------------------------------------------------------------------------------------------
# Encryption key (one key for the PDF bucket, image registries, logs and the secret)
# ---------------------------------------------------------------------------------------------

data "aws_iam_policy_document" "key" {
  statement {
    sid       = "AccountAdministration"
    actions   = ["kms:*"]
    resources = ["*"]

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${local.account_id}:root"]
    }
  }

  statement {
    sid = "AllowCloudWatchLogs"
    actions = [
      "kms:Encrypt*",
      "kms:Decrypt*",
      "kms:ReEncrypt*",
      "kms:GenerateDataKey*",
      "kms:Describe*",
    ]
    resources = ["*"]

    principals {
      type        = "Service"
      identifiers = ["logs.${var.region}.amazonaws.com"]
    }

    condition {
      test     = "ArnLike"
      variable = "kms:EncryptionContext:aws:logs:arn"
      values   = ["arn:aws:logs:${var.region}:${local.account_id}:log-group:/${var.project}/*"]
    }
  }
}

resource "aws_kms_key" "app" {
  description             = "${local.name} encryption key"
  enable_key_rotation     = true
  deletion_window_in_days = 7
  policy                  = data.aws_iam_policy_document.key.json
}

resource "aws_kms_alias" "app" {
  name          = "alias/${local.name}"
  target_key_id = aws_kms_key.app.key_id
}

# ---------------------------------------------------------------------------------------------
# Private PDF storage. This replaces the shared Docker volume used locally, because separate
# ECS tasks cannot share a Docker named volume.
# ---------------------------------------------------------------------------------------------

resource "aws_s3_bucket" "pdfs" {
  bucket        = "${local.name}-pdfs-${local.account_id}"
  force_destroy = var.force_destroy_pdfs
}

resource "aws_s3_bucket_public_access_block" "pdfs" {
  bucket                  = aws_s3_bucket.pdfs.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "pdfs" {
  bucket = aws_s3_bucket.pdfs.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_versioning" "pdfs" {
  bucket = aws_s3_bucket.pdfs.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "pdfs" {
  bucket = aws_s3_bucket.pdfs.id

  rule {
    bucket_key_enabled = true

    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.app.arn
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "pdfs" {
  bucket = aws_s3_bucket.pdfs.id

  rule {
    id     = "expire-demo-pdfs"
    status = "Enabled"

    filter {
      prefix = "pdfs/"
    }

    expiration {
      days = var.pdf_retention_days
    }

    noncurrent_version_expiration {
      noncurrent_days = 7
    }

  }

  rule {
    id     = "abort-failed-uploads"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = 1
    }
  }

  depends_on = [aws_s3_bucket_versioning.pdfs]
}

data "aws_iam_policy_document" "pdfs_bucket" {
  statement {
    sid       = "DenyInsecureTransport"
    effect    = "Deny"
    actions   = ["s3:*"]
    resources = [aws_s3_bucket.pdfs.arn, "${aws_s3_bucket.pdfs.arn}/*"]

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "pdfs" {
  bucket = aws_s3_bucket.pdfs.id
  policy = data.aws_iam_policy_document.pdfs_bucket.json

  depends_on = [aws_s3_bucket_public_access_block.pdfs]
}

# ---------------------------------------------------------------------------------------------
# Container registries: immutable tags, scan on push, encrypted, old images expire
# ---------------------------------------------------------------------------------------------

resource "aws_ecr_repository" "service" {
  for_each             = toset(["api", "dashboard"])
  name                 = "${var.project}/${each.key}"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = aws_kms_key.app.arn
  }
}

resource "aws_ecr_lifecycle_policy" "service" {
  for_each   = aws_ecr_repository.service
  repository = each.value.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep the 10 most recent images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = { type = "expire" }
    }]
  })
}

# ---------------------------------------------------------------------------------------------
# Logs
# ---------------------------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "service" {
  for_each          = local.services
  name              = "/${var.project}/${var.environment}/${each.key}"
  retention_in_days = var.log_retention_days
  kms_key_id        = aws_kms_key.app.arn
}

# ---------------------------------------------------------------------------------------------
# Secret container. The value is set outside Terraform so it never lands in state or Git.
# ---------------------------------------------------------------------------------------------

resource "aws_secretsmanager_secret" "jwt" {
  name                    = "${local.name}/jwt-secret"
  description             = "JWT signing secret for the WealthHub API. Value is set manually."
  kms_key_id              = aws_kms_key.app.arn
  recovery_window_in_days = 7
}

# ---------------------------------------------------------------------------------------------
# IAM: separate roles for starting the container (execution) and for what the app may do (task)
# ---------------------------------------------------------------------------------------------

data "aws_iam_policy_document" "ecs_trust" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [local.account_id]
    }
  }
}

# Task role: what the running API and worker may do. Nothing beyond their own PDF prefix.
resource "aws_iam_role" "task" {
  name               = "${local.name}-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_trust.json
}

data "aws_iam_policy_document" "task" {
  statement {
    sid       = "ReadWritePdfObjects"
    actions   = ["s3:GetObject", "s3:PutObject"]
    resources = ["${aws_s3_bucket.pdfs.arn}/pdfs/*"]
  }

  statement {
    sid       = "ListPdfPrefix"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.pdfs.arn]

    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["pdfs/*"]
    }
  }

  statement {
    sid       = "UseEncryptionKey"
    actions   = ["kms:Decrypt", "kms:GenerateDataKey"]
    resources = [aws_kms_key.app.arn]
  }
}

resource "aws_iam_role_policy" "task" {
  name   = "pdf-storage"
  role   = aws_iam_role.task.id
  policy = data.aws_iam_policy_document.task.json
}

# Execution role: pulls images, writes logs, injects the JWT secret into the container.
resource "aws_iam_role" "execution" {
  name               = "${local.name}-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_trust.json
}

resource "aws_iam_role_policy_attachment" "execution_managed" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

data "aws_iam_policy_document" "execution_secret" {
  statement {
    sid       = "ReadJwtSecret"
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [aws_secretsmanager_secret.jwt.arn]
  }

  statement {
    sid       = "DecryptSecret"
    actions   = ["kms:Decrypt"]
    resources = [aws_kms_key.app.arn]
  }
}

resource "aws_iam_role_policy" "execution_secret" {
  name   = "read-jwt-secret"
  role   = aws_iam_role.execution.id
  policy = data.aws_iam_policy_document.execution_secret.json
}
