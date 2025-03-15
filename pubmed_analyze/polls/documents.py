from elasticsearch_dsl import Document, DenseVector, Index
from .models import Article
from polls.es_config import INDEX_NAME


index = INDEX_NAME
article_index = Index(index)

article_index.settings(
    number_of_shards=1,
    number_of_replicas=0,
    elastiknn=True  
)

@article_index.document
class ArticleDocument(Document):
    
    title_abstract_vector = DenseVector(dims=768)  

    class Django:
        model = Article 
        fields = [
            'title',  
            'abstract',
        ]



