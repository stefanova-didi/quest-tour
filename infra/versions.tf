terraform {
  required_version = ">= 1.9"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.81"
    }
  }

  # Partial configuration: resource_group_name, storage_account_name, container_name and key come
  # from -backend-config (infra.yml, infra/README.md). The state account has shared keys disabled.
  backend "azurerm" {
    use_azuread_auth = true
  }
}
