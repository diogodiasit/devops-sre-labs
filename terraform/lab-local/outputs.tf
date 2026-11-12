output "arquivo_principal" {
  description = "Caminho do arquivo principal criado"
  value       = local_file.readme.filename
}

output "nome_aleatorio" {
  description = "Nome aleatorio gerado"
  value       = random_pet.sufixo.id
}
