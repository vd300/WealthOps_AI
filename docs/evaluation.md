# WealthOps AI — Evaluation Plan

## 1. Why Evaluation Matters

LLM applications cannot be judged only by whether they produce fluent text.

For a regulated financial AI system, the output must be:

- grounded
- accurate
- citation-backed
- safe
- consistent
- low-latency
- cost-aware

## 2. Evaluation Areas

Evaluate:

1. Retrieval quality
2. Answer quality
3. Citation quality
4. Compliance quality
5. Latency
6. Cost
7. Reliability

## 3. Retrieval Metrics

### Top-k Recall

Measures whether the correct chunk appears in top-k retrieved chunks.

Example:

- top-3 recall
- top-5 recall
- top-10 recall

### Mean Reciprocal Rank

Measures how high the first relevant chunk appears.

### Empty Retrieval Rate

Percentage of queries where no useful chunks are found.

### Retrieval Latency

Time taken to search vector database.

## 4. Answer Quality Metrics

### Groundedness

Does the answer only use retrieved context?

### Correctness

Is the answer factually correct based on source documents?

### Completeness

Does the answer address all parts of the question?

### Clarity

Is the answer easy to understand?

### Refusal Quality

Does the system correctly say when there is not enough information?

## 5. Citation Metrics

### Citation Coverage

Percentage of claims that have citations.

### Citation Accuracy

Whether the cited chunk actually supports the answer.

### Missing Citation Rate

Percentage of answers with no citations.

## 6. Compliance Metrics

Track:

- number of SAFE responses
- number of NEEDS_REVIEW responses
- number of BLOCKED responses
- prompt injection detection rate
- PII detection rate
- financial advice warning rate

## 7. Performance Metrics

Track:

- API p50 latency
- API p95 latency
- API p99 latency
- vector search latency
- LLM latency
- document ingestion time
- embedding generation time

## 8. Cost Metrics

Track:

- prompt tokens
- completion tokens
- total tokens
- estimated cost per query
- cost per document ingestion
- cost per user session

## 9. Evaluation Dataset

Create a small test set.

Example format:

```json
{
  "question": "What are the key liquidity risks mentioned in the document?",
  "expected_chunks": ["chunk_1", "chunk_9"],
  "expected_answer_points": [
    "liquidity risk",
    "market volatility",
    "redemption pressure"
  ]
}
```

## 10. RAG Evaluation DAG

Airflow should run RAG evaluation regularly.

Steps:

1. Load evaluation questions.
2. Run retrieval.
3. Generate answer.
4. Score retrieval quality.
5. Score citation coverage.
6. Save results.
7. Generate dashboard metrics.

## 11. Prompt Optimization

Prompt versions should be tracked.

Track:

- prompt version
- model name
- retrieval settings
- answer quality score
- citation score
- compliance status

Prompt optimization means improving the prompt so that answers become:

- more grounded
- less verbose
- better cited
- safer
- more consistent

## 12. Interview Explanation

Say this:

"I treated the LLM feature like a production ML product, not a simple API call. I measured retrieval quality, citation coverage, groundedness, latency, token cost, and compliance outcomes. This helped me improve prompts and retrieval settings systematically."