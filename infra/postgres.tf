resource "azurerm_postgresql_flexible_server" "db" {
  name                          = local.pg_server_name
  resource_group_name           = data.azurerm_resource_group.app.name
  location                      = local.location
  version                       = "16"
  sku_name                      = "B_Standard_B1ms"
  storage_mb                    = 32768
  storage_tier                  = "P4"
  backup_retention_days         = 7
  geo_redundant_backup_enabled  = false
  public_network_access_enabled = true # clarify: public endpoint + firewall, Entra-only auth
  tags                          = local.tags

  authentication {
    active_directory_auth_enabled = true
    password_auth_enabled         = false
    tenant_id                     = data.azurerm_client_config.current.tenant_id
  }

  lifecycle {
    prevent_destroy = true
    ignore_changes  = [zone] # Azure picks the zone; don't fight it
  }
}

# The database itself is created by `db-setup` (owned by the shared owner role), not here: a database
# created through ARM gets an owner the Entra admin (not a superuser) cannot grant from.

resource "azurerm_postgresql_flexible_server_active_directory_administrator" "admin" {
  server_name         = azurerm_postgresql_flexible_server.db.name
  resource_group_name = data.azurerm_resource_group.app.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  object_id           = var.admin_principal_object_id
  principal_name      = var.admin_principal_name
  principal_type      = var.admin_principal_type
}

# 0.0.0.0 = "allow Azure services": needed by App Service (outbound IPs are shared/changeable).
resource "azurerm_postgresql_flexible_server_firewall_rule" "azure_services" {
  name             = "allow-azure-services"
  server_id        = azurerm_postgresql_flexible_server.db.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

resource "azurerm_postgresql_flexible_server_firewall_rule" "admin" {
  for_each         = var.admin_ip_addresses
  name             = "admin-${each.key}"
  server_id        = azurerm_postgresql_flexible_server.db.id
  start_ip_address = each.value
  end_ip_address   = each.value
}
