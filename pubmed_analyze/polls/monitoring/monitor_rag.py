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
def handle_rag_pipeline(request):
    try:
        query = request.GET.get('query')
        if not query:
            return JsonResponse({'error': 'Missing query parameters'}, status=400)
        rag_requests_total.inc()  # Incrémenter le compteur de requêtes RAG
        # Mesurer la latence de la recherche
        with search_latency.time():
            documents = search_articles(request.GET.get('query'), request.GET.get('index_choice'))
        # Mesurer la latence de la génération LLM
        with llm_latency.time():
            response = generation(request.GET.get('query'), request.GET.get('index_choice'))
        return JsonResponse({
            'documents': documents,
            'response': response,
        })
    except Exception as e:
        rag_errors_total.inc()  # Incrémenter le compteur d'erreurs RAG
        return JsonResponse({'error': str(e)}, status=500)