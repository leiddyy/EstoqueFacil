# Guia de Conexão SQL & Integração Power BI - Estoque Fácil

Este documento apresenta a estrutura relacional do banco de dados SQLite (`estoque_facil.db`) do **Estoque Fácil**, desenvolvido especialmente para análises avançadas no **Power BI** ou exportação para Dashboards Gerenciais.

---

## 🗄️ Estrutura do Banco de Dados Relacional (SQLite)

O arquivo de banco de dados se encontra na pasta do projeto em:
`backend/estoque_facil.db`

### Diagrama de Tabelas

1. **`products`**: Tabela de Cadastro de Produtos
   - `id` (INTEGER PRIMARY KEY)
   - `code` (TEXT - SKU / Código de Barras)
   - `name` (TEXT - Nome do Produto)
   - `category` (TEXT - Categoria do Produto)
   - `unit` (TEXT - Unidade de Medida, ex: un, kg, cx)
   - `cost_price` (REAL - Preço de Custo)
   - `selling_price` (REAL - Preço de Venda)
   - `quantity` (INTEGER - Saldo Atual de Estoque)
   - `min_quantity` (INTEGER - Estoque Mínimo / Ponto de Pedido)
   - `created_at` (DATETIME)

2. **`stock_movements`**: Tabela Fato de Movimentações (Entradas e Saídas)
   - `id` (INTEGER PRIMARY KEY)
   - `product_id` (INTEGER FOREIGN KEY -> products.id)
   - `user_id` (INTEGER FOREIGN KEY -> users.id)
   - `type` (TEXT - 'IN' para Entrada, 'OUT' para Saída/Venda)
   - `quantity` (INTEGER - Quantidade Movimentada)
   - `unit_price` (REAL - Valor praticado)
   - `notes` (TEXT - Observações/NF/Motivo)
   - `created_at` (DATETIME - Data e hora da operação)

3. **`users`**: Tabela de Usuários e Permissões
   - `id` (INTEGER PRIMARY KEY)
   - `username` (TEXT)
   - `name` (TEXT)
   - `role` (TEXT - 'ADMIN' ou 'EMPLOYEE')

---

## 📊 Queries SQL Prontas para Conexão no Power BI / SQL Server / SQLite

### 1. Faturamento Total e Vendas por Produto (Curva ABC)
```sql
SELECT 
    p.code AS [SKU],
    p.name AS [Produto],
    p.category AS [Categoria],
    SUM(m.quantity) AS [Quantidade Vendida],
    SUM(m.quantity * m.unit_price) AS [Faturamento Total (R$)],
    SUM(m.quantity * (m.unit_price - p.cost_price)) AS [Lucro Bruto (R$)]
FROM stock_movements m
INNER JOIN products p ON m.product_id = p.id
WHERE m.type = 'OUT'
GROUP BY p.id, p.code, p.name, p.category
ORDER BY [Faturamento Total (R$)] DESC;
```

### 2. Produtos Necessitando de Reposição (Estoque Baixo)
```sql
SELECT 
    code AS [SKU],
    name AS [Produto],
    category AS [Categoria],
    quantity AS [Estoque Atual],
    min_quantity AS [Estoque Mínimo],
    (min_quantity - quantity) AS [Quantidade Sugerida de Compra]
FROM products
WHERE quantity <= min_quantity
ORDER BY (min_quantity - quantity) DESC;
```

### 3. Valuation Total de Estoque (Capital Imobilizado)
```sql
SELECT 
    COUNT(id) AS [Total de Produtos],
    SUM(quantity) AS [Total de Peças/Unidades],
    SUM(quantity * cost_price) AS [Custo Total Imobilizado (R$)],
    SUM(quantity * selling_price) AS [Valor Potencial de Venda (R$)],
    SUM(quantity * (selling_price - cost_price)) AS [Margem Potencial (R$)]
FROM products;
```

---

## 🔌 Como Conectar no Power BI Desktop

1. Abra o **Power BI Desktop**.
2. Clique em **Obter Dados** -> **Mais...** -> Escolha **SQLite** ou **ODBC**.
3. Selecione o arquivo `backend/estoque_facil.db`.
4. Importe as tabelas `products`, `stock_movements` e `users`.
5. Crie a relação entre `stock_movements.product_id` -> `products.id` (Muitos para Um).
6. Monte seus relatórios visuais com facilidade!
