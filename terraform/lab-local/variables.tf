variable "projeto" {
  description = "Nome do projeto, usado no nome dos arquivos"
  type        = string
  default     = "lab-local"
}

# Sem default: o valor vem do terraform.tfvars (ou é pedido no plan/apply).
variable "mensagem" {
  description = "Texto que sera escrito dentro do arquivo"
  type        = string
}
