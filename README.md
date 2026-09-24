# 📦 Estoque Fácil - Sistema de Controle de Estoque para Pequenos Negócios

O **Estoque Fácil** é uma solução leve, rápida e intuitiva desenvolvida para substituir cadernos de anotações e planilhas complexas do Excel. O sistema não é apenas um cadastro (CRUD) de produtos, mas uma ferramenta gerencial completa com **controle de permissões por perfil (RBAC)**, **alertas de reposição**, **histórico de entradas/saídas** e **relatórios em tempo real preparados para Power BI**.

---

## 🚀 Funcionalidades Principais

### 🔒 1. Permissões de Acesso (RBAC)
- **👑 Administrador (`ADMIN`):**
  - Cadastrar, editar e excluir produtos.
  - Definir e alterar preços de custo e de venda.
  - Visualizar valuation financeiro do estoque e margem estimada.
  - Criar e gerenciar usuários do sistema.
- **👤 Funcionário (`EMPLOYEE`):**
  - Consultar saldo de estoque e preço de venda.
  - Registrar vendas/saídas de produtos.
  - Registrar recebimento/entrada de mercadorias.
  - *Bloqueado para:* Exclusão de produtos, acesso a dados de custo/financeiro e gestão de usuários.

### 📦 2. Gestão Inteligente de Estoque
- **Catálogo de Produtos:** Código de barras/SKU, nome, categoria, unidade (un, kg, cx, l, pct) e preço.
- **Entradas e Saídas:** Atualização atômica do saldo de estoque com registro de motivo/observação e operador.
- **Alertas de Estoque Baixo:** Identificação automática de itens atingindo ou abaixo do limite mínimo recomendado.

### 📊 3. Relatórios Gerenciais & Power BI
- **Produtos mais vendidos:** Ranking e gráfico de curva de giro.
- **Produtos parados:** Identificação de itens sem movimentação há mais de 30 dias.
- **Valuation:** Valor total do estoque (Custo vs. Venda) e lucro potencial imobilizado.
- **Conexão SQL / Power BI:** Estrutura SQLite pronta para importação no Power BI com queries SQL otimizadas em `docs/power_bi_sql.md`.

---

## 🔑 Credenciais Padrão (Ambiente de Testes)

Ao iniciar o sistema pela primeira vez, as seguintes contas são criadas automaticamente:

| Perfil | Usuário | Senha | Permissão |
|---|---|---|---|
| **Administrador** | `admin` | `admin123` | Total |
| **Funcionário** | `funcionario` | `123456` | Operacional (Vendas / Entradas) |

---

## 🛠️ Como Executar o Projeto

### Pré-requisitos
- Python 3.10+ instalado no computador.

### Passo a Passo

1. **Navegar até a pasta do backend:**
   ```bash
   cd backend
   ```

2. **Ativar o ambiente virtual (se necessário):**
   ```bash
   .\venv\Scripts\activate
   ```

3. **Iniciar o servidor Backend FastAPI:**
   ```bash
   python -m uvicorn main:app --host 127.0.0.1 --port 8000
   ```

4. **Acessar o Sistema no Navegador:**
   Abra o seu navegador e acesse:
   [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 📂 Estrutura do Projeto

```text
Estoque_Facil/
├── backend/
│   ├── main.py              # API FastAPI, Endpoints e Servidor de Estáticos
│   ├── models.py            # Modelos do Banco de Dados SQLite (SQLAlchemy)
│   ├── schemas.py           # DTOs e Validações de entrada/saída (Pydantic)
│   ├── auth.py              # Autenticação JWT, Hash Bcrypt e Guardas RBAC
│   ├── database.py          # Conexão e Sessão SQLite
│   └── estoque_facil.db     # Arquivo de Banco de Dados SQLite
├── frontend/
│   ├── index.html           # Tela de Login
│   ├── dashboard.html       # Painel de Métricas e Alertas
│   ├── produtos.html        # Catálogo e Gestão de Produtos
│   ├── movimentacoes.html   # Registro de Entradas e Saídas
│   ├── relatorios.html      # Gráficos de Venda, Itens Parados e SQL
│   └── usuarios.html        # Gestão de Usuários (Admin)
├── docs/
│   └── power_bi_sql.md      # Guia de Modelagem e Queries para Power BI
└── README.md
```
