# arangoDB


## Documentação de Software

##c Componentes 
Anthony Anderson Freitas da Silva
Arthur Gabriel de Moura Lemos
Caio Anderson Bezerra Fernandes
Gustavo Henrique Bezerra de Medeiros
Samuel Lima Souza
### Índice

1. Introdução
2. Requisitos
3. Configuração do Ambiente
4. Descrição do Código
5. Inserção de Dados
6. Recomendações
7. Visualização de Recomendações

---

### Introdução

Este documento descreve a implementação de um sistema de recomendação utilizando ArangoDB e Python. O objetivo é demonstrar como conectar-se a um banco de dados ArangoDB, criar coleções, inserir dados e gerar recomendações baseadas nas preferências dos usuários.

---

### Requisitos

- Python 3.x
- Biblioteca `python-arango`
- ArangoDB

---

### Configuração do Ambiente

1. **Instalação do ArangoDB:**
   Siga as instruções de instalação no site oficial do ArangoDB: https://www.arangodb.com/

2. **Instalação da Biblioteca `python-arango`:**
   ```bash
   pip install python-arango
   ```

3. **Configuração do Banco de Dados:**
   - Inicie o servidor ArangoDB.
   - Crie uma database chamada `aplicacao`.
   - Configure as credenciais de acesso (username e password).

---

### Descrição do Código

#### Conexão com ArangoDB

O código conecta-se ao banco de dados ArangoDB utilizando as credenciais fornecidas:

```python
from arango import ArangoClient

client = ArangoClient(hosts='http://localhost:8529')
db = client.db('aplicacao', username='root', password='password123')
```

#### Definição e Criação das Coleções

Define as coleções `users`, `products`, `purchases` e `recommendations`. Se as coleções não existirem, elas são criadas:

```python
# Definir coleções globalmente
users = db.collection('users')
products = db.collection('products')
purchases = db.collection('purchases')
recommendations = db.collection('recommendations')

# Verificar e criar coleções se não existirem
if not db.has_collection('users'):
    users = db.create_collection('users')
if not db.has_collection('products'):
    products = db.create_collection('products')
if not db.has_collection('purchases'):
    purchases = db.create_collection('purchases', edge=True)
if not db.has_collection('recommendations'):
    recommendations = db.create_collection('recommendations', edge=True)
```

---

### Inserção de Dados

#### Usuários

Insere múltiplos usuários na coleção `users`:

```python
users.insert_many([
    {"_key": "user1", "name": "Alice", "age": 30, "preferences": ["electronics", "books"]},
    {"_key": "user2", "name": "Bob", "age": 25, "preferences": ["electronics", "games"]},
    {"_key": "user3", "name": "Charlie", "age": 35, "preferences": ["books", "clothing"]}
])
```

#### Produtos

Insere múltiplos produtos na coleção `products`:

```python
products.insert_many([
    {"_key": "product1", "name": "Laptop", "category": "electronics"},
    {"_key": "product2", "name": "Smartphone", "category": "electronics"},
    {"_key": "product3", "name": "Book A", "category": "books"},
    {"_key": "product4", "name": "T-Shirt", "category": "clothing"}
])
```

---

### Recomendações

#### Obtenção de Recomendações

A função `get_recommendations` obtém recomendações de produtos com base nas preferências do usuário e nos produtos comprados por usuários com preferências semelhantes:

```python
def get_recommendations(user_key):
    # Obter preferências do usuário
    user = users[user_key]
    user_preferences = user['preferences']
    print(f"Usuário: {user_key}, Preferências: {user_preferences}")

    # Obter produtos comprados pelo usuário
    purchased_products = db.aql.execute('''
        FOR purchase IN purchases
            FILTER purchase._from == @user
            RETURN purchase._to
    ''', bind_vars={'user': f'users/{user_key}'})
    purchased_products = [product for product in purchased_products]
    print(f"Produtos Comprados por {user_key}: {purchased_products}")

    # Encontrar produtos similares comprados por outros usuários
    recommendations = db.aql.execute('''
        LET userPreferences = @userPreferences
        LET purchasedProducts = @purchasedProducts
        LET recommendations = (
            FOR similarUser IN users
                FILTER similarUser._key != @userKey
                FILTER LENGTH(INTERSECTION(similarUser.preferences, userPreferences)) > 0
                FOR purchase IN purchases
                    FILTER purchase._from == similarUser._id
                    FILTER purchase._to NOT IN purchasedProducts
                    RETURN DISTINCT purchase._to
        )
        RETURN recommendations
    ''', bind_vars={
        'userPreferences': user_preferences,
        'purchasedProducts': purchased_products,
        'userKey': user_key
    })

    recommendations_list = list(recommendations)
    print(f"Recomendações para {user_key}: {recommendations_list}")
    
    return recommendations_list
```

#### Inserção de Recomendações

A função `insert_recommendations` insere as recomendações geradas para um usuário específico na coleção `recommendations`:

```python
def insert_recommendations(user_key, recommendations):
    recommendation_edges = [
        {"_from": f'users/{user_key}', "_to": product, "score": 1.0}
        for product in recommendations
    ]
    recommendations_collection = db.collection('recommendations')
    recommendations_collection.insert_many(recommendation_edges)
```

---

### Visualização de Recomendações

A função `view_recommendations` permite visualizar as recomendações para um usuário específico:

```python
def view_recommendations(user_key):
    recommended_products = db.aql.execute('''
        FOR recommendation IN recommendations
            FILTER recommendation._from == @user
            FOR product IN products
                FILTER recommendation._to == product._id
                RETURN {
                    user: recommendation._from,
                    product: product.name,
                    category: product.category,
                    score: recommendation.score
                }
    ''', bind_vars={'user': f'users/{user_key}'})
    
    return list(recommended_products)
```

---

### Exemplo de Uso

1. **Obtenção de Recomendações para `user1`:**

    ```python
    recommended_products = get_recommendations('user1')
    ```

2. **Inserção de Recomendações para `user1`:**

    ```python
    insert_recommendations('user1', recommended_products)
    ```

3. **Visualização de Recomendações para `user1`:**

    ```python
    print(view_recommendations('user1'))
    ```

---

### Observações

- A inserção manual das coleções no ArangoDB pode ser necessária caso o script não consiga criá-las automaticamente.
- Este exemplo é básico e serve como ponto de partida para sistemas de recomendação mais complexos. Ajustes e otimizações podem ser necessários dependendo do caso de uso específico.

---

**Arquivo de Observação**

Referência a observações sobre o comportamento do código ao ser executado pode ser encontrada no arquivo `obs.txt`.
