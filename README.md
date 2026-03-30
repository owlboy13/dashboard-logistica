# 🛵 Dashboard Logística

Dashboard de gestão para **Soluções Logísticas LTDA** — financeiro e performance da frota.

## Instalação

```bash
# 1. Clone o repositório
git clone 
cd DashFranquia

# 2. Crie e ative o ambiente virtual
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Adicione os relatórios Excel na pasta data/
#    Os arquivos devem se chamar exatamente:
#    - Base_Ativos_.xlsx
#    - consolidado_financeiro_.xlsx
#    - perfomance_.xlsx

# 5. Execute
streamlit run app.py
```

## Usuários padrão

| Usuário     | Senha        | Acesso                        |
|-------------|--------------|-------------------------------|
| `financeiro`| `exemplosenha`  | Financeiro + Performance      |
| `suporte`   | `exemplosenha`| Somente Performance           |
| `admin`     | `exemplosenha`  | Tudo (igual ao financeiro)    |

> ⚠️ Altere as senhas em `config.py` antes de colocar em produção.

## Estrutura

```
nome_empresa/
├── app.py              # Entrada, login e roteamento
├── config.py           # Usuários, perfis e constantes
├── requirements.txt
├── assets/
│   └── style.css       # Visual personalizado Movee
├── pages/
│   ├── fin_visao_geral.py
│   ├── fin_receitas.py
│   ├── fin_despesas.py
│   ├── perf_visao_geral.py
│   ├── perf_driver.py
│   └── perf_subpracas.py
├── utils/
│   ├── loader.py       # Leitura Excel com cache
│   └── helpers.py      # Formatações e KPIs
└── data/               # Arquivos Excel (não versionar)
```

## Atualização dos dados

Basta substituir os arquivos na pasta `data/` com o novo relatório semanal.
O cache é renovado automaticamente a cada 1 hora ou ao reiniciar o app.
