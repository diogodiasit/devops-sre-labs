terraform {
  required_version = ">= 1.5"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0" # aceita 4.x; a 5.0 pode trazer mudanças incompatíveis
    }
  }
}

provider "azurerm" {
  features {} # obrigatório no azurerm, mesmo vazio
}
