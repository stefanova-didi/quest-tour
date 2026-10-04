provider "azurerm" {
  # The infra identity only has rights on the app resource group; bootstrap.sh registers providers.
  resource_provider_registrations = "none"
  # Shared-key access is disabled on the storage accounts, so any data-plane call must use Entra ID.
  storage_use_azuread = true
  # subscription_id comes from ARM_SUBSCRIPTION_ID.

  features {
    storage {
      # The infra identity has no data-plane role on the app storage account (Contributor is
      # management-plane only). Containers use storage_account_id (management plane) instead.
      data_plane_available = false
    }
  }
}
