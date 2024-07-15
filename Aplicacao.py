from arango import ArangoClient

# Conectar ao ArangoDB
client = ArangoClient(hosts='http://localhost:8529')
db = client.db('aplicacao', username='root', password='password123')

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

# Inserir Usuários (exemplo)
users.insert_many([
    {"_key": "user1", "name": "Alice", "age": 30, "preferences": ["electronics", "books"]},
    {"_key": "user2", "name": "Bob", "age": 25, "preferences": ["electronics", "games"]},
    {"_key": "user3", "name": "Charlie", "age": 35, "preferences": ["books", "clothing"]}
])

# Inserir Produtos (exemplo)
products.insert_many([
    {"_key": "product1", "name": "Laptop", "category": "electronics"},
    {"_key": "product2", "name": "Smartphone", "category": "electronics"},
    {"_key": "product3", "name": "Book A", "category": "books"},
    {"_key": "product4", "name": "T-Shirt", "category": "clothing"}
])

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


# Exemplo de uso para obter recomendações para 'user1'
recommended_products = get_recommendations('user1')

# Definir função para inserir recomendações
def insert_recommendations(user_key, recommendations):
    recommendation_edges = [
        {"_from": f'users/{user_key}', "_to": product, "score": 1.0}
        for product in recommendations
    ]
    recommendations_collection = db.collection('recommendations')
    recommendations_collection.insert_many(recommendation_edges)

# Inserir recomendações para 'user1'
insert_recommendations('user1', recommended_products)

# Definir função para visualizar recomendações
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

# Exemplo de uso para visualizar recomendações para 'user1'
print(view_recommendations('user1'))
