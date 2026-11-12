resource "random_pet" "sufixo" {
  length = 2 # gera um nome de duas palavras, ex.: happy-otter
}

resource "local_file" "readme" {
  filename = "${path.module}/saida/${var.projeto}-${random_pet.sufixo.id}.txt"
  content  = "${var.mensagem}\n"
}

# Referencia o filename do recurso anterior: o Terraform cria o readme primeiro
# (dependência implícita, sem depends_on).
resource "local_file" "resumo" {
  filename = "${path.module}/saida/resumo.txt"
  content  = "Arquivo principal: ${local_file.readme.filename}\n"
}
