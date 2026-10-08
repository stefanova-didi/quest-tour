# App (managed identity) -> photos/images, incl. creating containers on startup (main._ensure_containers).
resource "azurerm_role_assignment" "app_blob" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_linux_web_app.app.identity[0].principal_id
  principal_type       = "ServicePrincipal"
}

# Admin -> sync-config uploads pictures (spec §6 Admin).
resource "azurerm_role_assignment" "admin_blob" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = var.admin_principal_object_id
}

# Hosts -> read/delete photos only (spec §5, §6). Reader lets them find the account in the Portal.
resource "azurerm_role_assignment" "host_photos" {
  for_each             = toset(var.host_principal_object_ids)
  scope                = azurerm_storage_container.photos.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = each.value
}

# Hosts -> the stored memories albums as well (issue #33), same rights as on photos.
resource "azurerm_role_assignment" "host_albums" {
  for_each             = toset(var.host_principal_object_ids)
  scope                = azurerm_storage_container.albums.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = each.value
}

resource "azurerm_role_assignment" "host_reader" {
  for_each             = toset(var.host_principal_object_ids)
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Reader"
  principal_id         = each.value
}

# GitHub deploy identity -> zip deploy to this web app only.
resource "azurerm_role_assignment" "deploy" {
  scope                = azurerm_linux_web_app.app.id
  role_definition_name = "Website Contributor"
  principal_id         = var.deploy_principal_object_id
  principal_type       = "ServicePrincipal"
}
