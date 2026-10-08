# RBAC only: the app uses its managed identity, people use Entra (shared keys off, private containers).
# The network default stays Allow: storage IP rules don't apply to same-region App Service traffic,
# and hosts browse photos from anywhere. Access is gated by Entra auth + RBAC.
resource "azurerm_storage_account" "main" {
  name                             = local.storage_name
  resource_group_name              = data.azurerm_resource_group.app.name
  location                         = local.location
  account_tier                     = "Standard"
  account_replication_type         = "LRS"
  account_kind                     = "StorageV2"
  min_tls_version                  = "TLS1_2"
  shared_access_key_enabled        = false
  default_to_oauth_authentication  = true
  allow_nested_items_to_be_public  = false
  cross_tenant_replication_enabled = false
  public_network_access_enabled    = true
  tags                             = local.tags

  blob_properties {
    delete_retention_policy {
      days = 14 # spec §7
    }
    container_delete_retention_policy {
      days = 14
    }
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "azurerm_storage_container" "photos" {
  name                  = "photos"
  storage_account_id    = azurerm_storage_account.main.id
  container_access_type = "private"
}

resource "azurerm_storage_container" "images" {
  name                  = "images"
  storage_account_id    = azurerm_storage_account.main.id
  container_access_type = "private"
}

# Memories-album PDFs, one per finished run (issue #33); the app renders and deletes them.
resource "azurerm_storage_container" "albums" {
  name                  = "albums"
  storage_account_id    = azurerm_storage_account.main.id
  container_access_type = "private"
}
