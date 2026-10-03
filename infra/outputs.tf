output "web_app_name" {
  value = azurerm_linux_web_app.app.name
}

output "web_app_url" {
  value = local.public_base_url
}

output "postgres_host" {
  value = local.pg_fqdn
}

output "storage_account_url" {
  value = local.storage_url
}

output "db_setup_command" {
  description = "Run once from backend/ after the first apply (infra/README.md, first-time setup step 5)."
  value       = "uv run db-setup --host ${local.pg_fqdn} --admin-role '${var.admin_principal_name}' --app-role ${local.web_app_name} --database ${var.db_name} --owner-role ${var.db_owner_role}"
}

output "admin_sync_config_env" {
  description = "Env vars for running sync-config / alembic against prod as the admin (after az login)."

  value = <<-EOT
    DATABASE_URL=postgresql+psycopg://${urlencode(var.admin_principal_name)}@${local.pg_fqdn}:5432/${var.db_name}?sslmode=require
    DATABASE_AUTH=azure_ad
    DATABASE_OWNER_ROLE=${var.db_owner_role}
    STORAGE_BACKEND=azure
    AZURE_STORAGE_CONNECTION_STRING=
    AZURE_STORAGE_ACCOUNT_URL=${local.storage_url}
    PUBLIC_BASE_URL=${local.public_base_url}
  EOT
}
