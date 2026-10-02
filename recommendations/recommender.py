from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from store.models import Product

def get_recommendations(product_id, num_recommendations=4):
    # Get all available products
    products = list(
        Product.objects.filter(is_available=True)
        .select_related('category')
    )
    # Need at least two products
    if len(products) <= 1:
        return []
    # Find the current product
    current_product = next(
        (product for product in products if product.id == product_id),
        None
    )
    if current_product is None:
        return []
    # Create text for TF-IDF
    product_text = []

    for product in products:

        text = (
            f"{product.product_name} "
            f"{product.description}"
        )

        product_text.append(text)
    # Convert product text into TF-IDF vectors
    vectorizer = TfidfVectorizer(
        stop_words='english'
    )
    try:
        tfidf_matrix = vectorizer.fit_transform(product_text)
    except ValueError:
        # Handles cases where there is no usable text
        return []
    # Calculate cosine similarity
    similarity_matrix = cosine_similarity(tfidf_matrix)
    # Find index of current product
    current_index = products.index(current_product)
    # Get similarity scores
    similarity_scores = list(
        enumerate(similarity_matrix[current_index])
    )
    recommendations = []
    for index, text_similarity in similarity_scores:
        recommended_product = products[index]
        # Don't recommend the product currently being viewed
        if recommended_product.id == product_id:
            continue
        # Category bonus
        if (
            recommended_product.category_id
            == current_product.category_id
        ):
            category_bonus = 0.20
        else:
            category_bonus = 0
        # Final recommendation score
        final_score = text_similarity + category_bonus
        recommendations.append(
            (recommended_product, final_score)
        )
    recommendations.sort(
        key=lambda x: x[1],
        reverse=True
    )
    # Return only products
    return [
        product
        for product, score in recommendations[:num_recommendations]
    ]