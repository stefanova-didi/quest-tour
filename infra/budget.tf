locals {
  # First day of the month of the first apply (Azure refuses budget start dates in past months);
  # ignore_changes below keeps the stored value fixed afterwards.
  budget_start_date = coalesce(var.budget_start_date, formatdate("YYYY-MM-01'T'00:00:00'Z'", plantimestamp()))
}

resource "azurerm_consumption_budget_resource_group" "monthly" {
  name              = "budget-${var.app_name}-monthly"
  resource_group_id = data.azurerm_resource_group.app.id
  amount            = var.budget_amount # billing currency (EUR assumed), spec §7
  time_grain        = "Monthly"

  time_period {
    start_date = local.budget_start_date
  }

  notification {
    enabled        = true
    threshold      = 80
    operator       = "GreaterThanOrEqualTo"
    threshold_type = "Actual"
    contact_emails = var.budget_contact_emails
  }

  notification {
    enabled        = true
    threshold      = 100
    operator       = "GreaterThanOrEqualTo"
    threshold_type = "Forecasted"
    contact_emails = var.budget_contact_emails
  }

  lifecycle {
    ignore_changes = [time_period]
  }
}
