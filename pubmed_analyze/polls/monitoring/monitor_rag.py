import prometheus_client
from polls.business_logic import search_articles, generation

rag_pipeline_latency = prometheus_client.Histogram(
    'rag_pipeline_latency_seconds', 'Latency of the RAG pipeline', 
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0]
)
search_latency = prometheus_client.Histogram(
    'search_latency_seconds', 'Latency of document retrieval', 
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)
llm_latency = prometheus_client.Histogram(
    'llm_latency_seconds', 'Latency of LLM generation', 
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0]
)
rag_requests_total = prometheus_client.Counter(
    'rag_requests_total', 'Total number of RAG requests'
)
rag_errors_total = prometheus_client.Counter(
    'rag_errors_total', 'Total number of RAG errors'
)
document_length = prometheus_client.Histogram(
    'document_length', 'Average length of documents retrieved', 
    buckets=[100, 500, 1000, 2000, 5000, 10000, 20000]
)
rag_success_ratio = prometheus_client.Gauge(
    'rag_success_ratio', 'Ratio of successful RAG requests'
)
rag_error_type_total = prometheus_client.Counter(
    'rag_error_type_total', 'Total number of RAG errors by type', ['type']
)


@rag_pipeline_latency.time()
def handle_rag_pipeline(query, llm, index):
    """
    Handles the RAG (Retrieval-Augmented Generation) pipeline.

    This function wraps the entire RAG pipeline and monitors its latency, 
    as well as the latency of the search and LLM components. It also tracks
    the total number of RAG requests, the number of errors, and the average
    length of retrieved documents.

    Parameters:
    query (str): The user query.
    llm (str): The name of the language model to use.
    index (str): The name of the Elasticsearch index to search.

    Returns:
    response (str): The generated text.
    documents_formated (str): The formatted documents retrieved from the search engine.
    """
    try:
        rag_requests_total.inc()  
        with search_latency.time():
            documents, query = search_articles(query, index)
        avg_length = sum(len(doc) for doc in documents) / len(documents) if documents else 0
        document_length.observe(avg_length)  
        with llm_latency.time():
            response, documents_formated = generation(query, documents, llm, index)
        rag_success_ratio.set((rag_requests_total._value.get() - rag_errors_total._value.get()) / rag_requests_total._value.get())
        return response, documents_formated

    except Exception as e:
        rag_errors_total.inc()
        error_type = "unknown"
        if "search" in str(e).lower():
            error_type = "retrieval"
        elif "generation" in str(e).lower():
            error_type = "llm"
        rag_error_type_total.labels(error_type).inc()
        response = f"error: {str(e)}"
        documents = ""
        return response, documents
