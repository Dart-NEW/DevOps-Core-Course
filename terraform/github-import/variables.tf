variable "github_owner" {
  description = "GitHub username or organization owning the repository"
  type        = string
}

variable "github_token" {
  description = "GitHub personal access token (repo scope)"
  type        = string
  sensitive   = true
}

variable "repository_name" {
  description = "Repository name to import/manage"
  type        = string
  default     = "DevOps-Core-Course"
}

variable "repository_description" {
  description = "Managed repository description"
  type        = string
  default     = "DevOps core course lab assignments"
}

variable "repository_visibility" {
  description = "Repository visibility"
  type        = string
  default     = "public"

  validation {
    condition     = contains(["public", "private", "internal"], var.repository_visibility)
    error_message = "repository_visibility must be public, private, or internal."
  }
}

variable "has_issues" {
  description = "Enable GitHub issues"
  type        = bool
  default     = true
}

variable "has_wiki" {
  description = "Enable GitHub wiki"
  type        = bool
  default     = false
}
