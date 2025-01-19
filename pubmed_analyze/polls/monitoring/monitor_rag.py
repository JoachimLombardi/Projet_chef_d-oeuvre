from django.http import JsonResponse
import prometheus_client
from polls.business_logic import search_articles, generation

# Définir des métriques Prometheus
rag_pipeline_latency = prometheus_client.Summary('rag_pipeline_latency_seconds', 'Latency of the RAG pipeline')
search_latency = prometheus_client.Summary('search_latency_seconds', 'Latency of document retrieval')
llm_latency = prometheus_client.Summary('llm_latency_seconds', 'Latency of LLM generation')
rag_requests_total = prometheus_client.Counter('rag_requests_total', 'Total number of RAG requests')
rag_errors_total = prometheus_client.Counter('rag_errors_total', 'Total number of RAG errors')

# Vue pour gérer le pipeline RAG
@rag_pipeline_latency.time()
def handle_rag_pipeline(query, index):
    try:
        rag_requests_total.inc()  # Incrémenter le compteur de requêtes RAG
        # Mesurer la latence de la recherche
        with search_latency.time():
            documents, query = search_articles(query, index)
        # Mesurer la latence de la génération LLM
        with llm_latency.time():
            response = generation(query, documents, index)
        return documents, response
    except Exception as e:
        rag_errors_total.inc()  # Incrémenter le compteur d'erreurs RAG
        return JsonResponse({'error': str(e)}, status=500)
