output "resource_group_nome" {
  description = "Nome do Resource Group criado"
  value       = azurerm_resource_group.rg.name
}

output "vnet_id" {
  description = "ID da VNet criada"
  value       = azurerm_virtual_network.vnet.id
}

output "storage_account_nome" {
  description = "Nome do Storage Account criado"
  value       = azurerm_storage_account.sa.name
}
