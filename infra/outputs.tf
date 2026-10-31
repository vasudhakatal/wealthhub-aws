output "pdf_bucket" {
  description = "Private bucket for generated PDFs."
  value       = aws_s3_bucket.pdfs.bucket
}

output "ecr_repository_urls" {
  description = "Push the api and dashboard images here."
  value       = { for name, repo in aws_ecr_repository.service : name => repo.repository_url }
}

output "task_role_arn" {
  description = "Role the running containers assume."
  value       = aws_iam_role.task.arn
}

output "execution_role_arn" {
  description = "Role ECS uses to start the containers."
  value       = aws_iam_role.execution.arn
}

output "log_groups" {
  description = "CloudWatch log group names per service."
  value       = { for name, group in aws_cloudwatch_log_group.service : name => group.name }
}

output "jwt_secret_arn" {
  description = "Set the secret value manually with the AWS CLI; it is not stored in Terraform."
  value       = aws_secretsmanager_secret.jwt.arn
}
