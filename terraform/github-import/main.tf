terraform {
  required_version = ">= 1.9.0"

  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }
}

provider "github" {
  owner = var.github_owner
  token = var.github_token
}

resource "github_repository" "course_repo" {
  name        = var.repository_name
  description = var.repository_description
  visibility  = var.repository_visibility

  has_issues   = var.has_issues
  has_wiki     = var.has_wiki
  has_projects = false

  delete_branch_on_merge = false
  vulnerability_alerts   = true
}
