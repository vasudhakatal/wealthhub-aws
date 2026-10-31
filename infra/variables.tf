variable "region" {
  description = "AWS region for all resources."
  type        = string
  default     = "ap-southeast-2"
}

variable "project" {
  description = "Short name used as a prefix for resource names."
  type        = string
  default     = "wealthhub"
}

variable "environment" {
  description = "Environment name, for example dev."
  type        = string
  default     = "dev"
}

variable "log_retention_days" {
  description = "How long CloudWatch logs are kept."
  type        = number
  default     = 365
}

variable "pdf_retention_days" {
  description = "Generated welcome PDFs are deleted after this many days (they are demo data)."
  type        = number
  default     = 30
}

variable "force_destroy_pdfs" {
  description = "Allow terraform destroy to delete the PDF bucket even if it contains objects."
  type        = bool
  default     = false
}
