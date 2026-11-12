resource "azurerm_resource_group" "rg" {
  name     = "rg-${var.projeto}"
  location = var.location

  tags = {
    ambiente = "estudo"
  }
}

# Região e Resource Group vêm do recurso acima: além de evitar repetição,
# a referência cria a dependência implícita (o RG é criado antes da VNet).
resource "azurerm_virtual_network" "vnet" {
  name                = "vnet-${var.projeto}"
  address_space       = ["10.10.0.0/16"]
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name

  tags = {
    ambiente = "estudo"
  }
}

resource "azurerm_storage_account" "sa" {
  # Storage Account exige nome globalmente único, de 3 a 24 caracteres, só minúsculas
  # e números. Por isso o hífen do projeto é removido e entra um sufixo: stlabtfld1015.
  name                = "st${replace(var.projeto, "-", "")}${var.sufixo_unico}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name

  account_tier             = "Standard"
  account_replication_type = "LRS" # 3 cópias no mesmo datacenter; a opção mais barata, suficiente para lab

  tags = {
    ambiente = "estudo"
  }
}
