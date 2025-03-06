from django.http import JsonResponse
import prometheus_client
from polls.business_logic import search_articles, generation

rag_pipeline_latency = prometheus_client.Summary('rag_pipeline_latency_seconds', 'Latency of the RAG pipeline')
search_latency = prometheus_client.Summary('search_latency_seconds', 'Latency of document retrieval')
llm_latency = prometheus_client.Summary('llm_latency_seconds', 'Latency of LLM generation')
rag_requests_total = prometheus_client.Counter('rag_requests_total', 'Total number of RAG requests')
rag_errors_total = prometheus_client.Counter('rag_errors_total', 'Total number of RAG errors')

@rag_pipeline_latency.time()
def handle_rag_pipeline(query, llm, index):
    try:
        rag_requests_total.inc()  
        with search_latency.time():
            documents, query = search_articles(query, index)
        with llm_latency.time():
            response, documents_formated = generation(query, documents, llm, index)
        return response, documents_formated
    except Exception as e:
        rag_errors_total.inc()
        response = f"error: {str(e)}"
        documents = ""
        return response, documents
