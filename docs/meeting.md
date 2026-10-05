- Langchain
- Vector DB
- -One Agent with 2 tools
  -  1. Tool: retrieve Data
  -  2. Tool: Save Dta

CRUD for DB and Vector DB

### Next time:
- DB
- FastAPI:
  - CRUD
  - Upload for RAG
- SqLite / Alchemy

Next Week:
Tool:

- websearch
  integrate:
  - Tavily: https://docs.langchain.com/oss/python/integrations/providers/tavily
  - Langfuse:
    - Monitoring
    - Evaluation
- Add Agent-Memory

Free tier from Huggingface:

- Grok
-

Qwen from Alibaba for local model

                         ┌───────────────┐
                         │     USER      │
                         └───────┬───────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │       FastAPI API      │
                    └────────────┬───────────┘
                                 │
             ┌───────────────────┼───────────────────┐
             │                   │                   │
             ▼                   ▼                   ▼
      ┌─────────────┐     ┌─────────────┐    ┌─────────────┐
      │     Auth    │     │  Documents  │    │    Chat     │
      └─────────────┘     └──────┬──────┘    └──────┬──────┘
                                 │                  │
                                 ▼                  ▼
                       ┌─────────────────┐  ┌─────────────────┐
                       │   Ingestion     │  │ Chat Sessions   │
                       │                 │  │ Chat Messages   │
                       └────────┬────────┘  └────────┬────────┘
                                │                    │
                                ▼                    │
                       ┌─────────────────┐           │
                       │ Document Chunks │           │
                       └────────┬────────┘           │
                                │                    │
                                ▼                    │
                           ┌─────────┐               │
                           │  Redis  │               │
                           └────┬────┘               │
                                │                    │
                                ▼                    │
                       ┌─────────────────┐           │
                       │ Embedding Worker│           │
                       └────────┬────────┘           │
                                │                    │
                                ▼                    │
                       ┌─────────────────┐           │
                       │    pgvector     │           │
                       └────────┬────────┘           │
                                │                    │
                                └─────────┬──────────┘
                                          │
                                          ▼
                              ┌────────────────────┐
                              │   Hybrid Search    │
                              └─────────┬──────────┘
                                        │
                         ┌──────────────┼──────────────┐
                         ▼              ▼              ▼
                  ┌────────────┐ ┌────────────┐ ┌────────────┐
                  │   Vector   │ │  Keyword   │ │    Web     │
                  │   Search   │ │   Search   │ │   Search   │
                  └─────┬──────┘ └─────┬──────┘ └────────────┘
                        │              │
                        └──────┬───────┘
                               ▼
                        ┌─────────────┐
                        │     RRF     │
                        └──────┬──────┘
                               ▼
                        ┌─────────────┐
                        │  Reranker   │
                        └──────┬──────┘
                               ▼
                        ┌─────────────┐
                        │    Agent    │
                        └──────┬──────┘
                               │
                    ┌──────────┼──────────┐
                    ▼          ▼          ▼
              ┌──────────┐ ┌────────┐ ┌──────────┐
              │ Search   │ │  Get   │ │   Web    │
              │Documents │ │Document│ │  Search  │
              └──────────┘ └────────┘ └──────────┘
                               │
                               ▼
                         ┌────────────┐
                         │    LLM     │
                         └─────┬──────┘
                               │
                               ▼
                         ┌────────────┐
                         │  Response  │
                         └────────────┘


          ┌─────────────────────────────────────────┐
          │              OBSERVABILITY              │
          │                                         │
          │                 Langfuse                │
          └─────────────────────────────────────────┘


          ┌─────────────────────────────────────────┐
          │               EVALUATION                │
          │                                         │
          │     Retrieval │ Reranking │ RAG         │
          └─────────────────────────────────────────┘

- Next goal:
    - Evaluation pipeline
    - LLM as judge
    - Langfuse: RAGAS?