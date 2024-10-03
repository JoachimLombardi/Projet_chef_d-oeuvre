from elasticsearch_dsl import Document, Text, DenseVector, Index
from .models import Article


# Define the Elasticsearch index
article_index = Index('articles')

# Enable KNN vector settings in the index
article_index.settings(
    number_of_shards=1,
    number_of_replicas=0,
    elastiknn=True  # Enables KNN support in the index
)

# Register the document to Django's registry
@article_index.document
class ArticleDocument(Document):
    
    # Add a vector field for KNN search
    title_abstract_vector = DenseVector(dims=768)  # Assuming 768 dimensions for BERT

    class Django:
        model = Article  # Specify the model associated with this document
        fields = [
            'title',  # Other fields to index
            'abstract',
        ]

    def prepare_title_vector(self, instance):
        """Prepare the vector representation for the title."""
        return instance.get_title_abstract_vector()  # Assurez-vous que cette méthode est définie dans le modèle Article

