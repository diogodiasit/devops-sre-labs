variable "location" {
  description = "Regiao do Azure onde os recursos serao criados"
  type        = string
  default     = "brazilsouth"
}

variable "projeto" {
  description = "Nome do projeto, usado nos nomes dos recursos"
  type        = string
  default     = "lab-tf"
}

# Sem default de propósito: o nome do Storage Account precisa ser único no mundo,
# então cada pessoa que rodar o lab informa o próprio sufixo no terraform.tfvars.
variable "sufixo_unico" {
  description = "Sufixo para o Storage Account (unico no mundo, so letras minusculas e numeros)"
  type        = string
}
