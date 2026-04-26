output "managed_repository" {
  description = "Imported repository full name"
  value       = github_repository.course_repo.full_name
}
