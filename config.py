# Configuração de usuários e perfis de acesso
# Para adicionar usuários: copie um bloco e altere nome/senha/perfil
from dotenv import load_dotenv
import os
import json

load_dotenv()

USUARIOS = {
    "financeiro": {
        "senha": os.getenv('PASSWORD_FINANCEIRO'),
        "perfil": os.getenv('USER_FINANCEIRO'),
        "nome": "Setor Financeiro",
    },
    "suporte": {
        "senha": os.getenv('PASSWORD_SUPORTE'),
        "perfil": os.getenv('USER_SUPORTE'),
        "nome": "Suporte Operacional",
    },
    "admin": {
        "senha": os.getenv('PASSWORD_ADMIN'),
        "perfil": os.getenv('USER_ADMIN'),  # admin vê tudo
        "nome": "Administrador",
    },
}

# Páginas disponíveis por perfil
PAGINAS_POR_PERFIL = json.loads(os.getenv('PERMISSIONS'))

# Arquivos de dados (relativos à pasta data/)
ARQUIVOS = {
    "base": os.getenv('BASE_ATIVOS_INATIVOS'),
    "financeiro": os.getenv('BASE_FINANCEIRO'),
    "performance": os.getenv('BASE_PERFOMANCE'),
}

# Regras SLA — número de critérios atingidos → percentual variável
SLA_PERCENTUAIS = json.loads(os.getenv('SLA_PERCENTUAL'))

# Royalties sobre faturamento bruto
ROYALTIES_PERCENTUAL = os.getenv('PERCENTUAL_ROYALTIES')
