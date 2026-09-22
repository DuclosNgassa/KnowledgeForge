## MVP Workflows for 2–3 month project.

### MVP 1 — Document Upload
```
Upload
  ↓
Extract
  ↓
Chunk
  ↓
Embed
  ↓
Store
```
```
Question
  ↓
RAG
  ↓
Retrieve
  ↓
Generate Answer

```

### MVP 2 — Ask Questions
```
```

### MVP 3 — Research Topic 
```
Topic
  ↓
Research Plan
  ↓
Retrieve Information
  ↓
Research Summary
```
### MVP 4 — Generate Content
```
Research
  ↓
Content Plan
  ↓
Writer
  ↓
Article / Report
```
### MVP 5 — Review Content
```
Generated Content
  ↓
Critic
  ↓
Issues
  ↓
Improve
  ↓
Final Content
```

Stand heute:

```
                         ┌──────────────────────────┐
                         │       ResearchForge      │
                         │   AI Research Platform   │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │        FastAPI API       │
                         └────────────┬─────────────┘
                                      │
              ┌───────────────────────┼────────────────────────┐
              │                       │                        │
              ▼                       ▼                        ▼
       ┌──────────────┐       ┌──────────────┐        ┌────────────────┐
       │  Users API   │       │ Knowledge API│        │  Research API  │
       │              │       │              │        │                │
       │ POST /users  │       │ KB CRUD      │        │ POST /research │
       └──────┬───────┘       │ Documents    │        └───────┬────────┘
              │               └──────┬───────┘                │
              │                      │                        ▼
              │                      │                ┌────────────────┐
              │                      │                │ AI Orchestrator│
              │                      │                └───────┬────────┘
              │                      │                        │
              ▼                      ▼                        │
       ┌──────────────┐       ┌──────────────┐                │
       │ UserService  │       │ Document     │                │
       │              │       │ Pipeline     │                │
       └──────┬───────┘       └──────┬───────┘                │
              │                      │                        │
              ▼                      ▼                        ▼
       ┌──────────────┐       ┌──────────────┐        ┌────────────────┐
       │UserRepository│       │ Text Extract │        │ Research       │
       └──────┬───────┘       │ Chunking     │        │ Planner        │
              │               │ Embedding    │        └───────┬────────┘
              │               └──────┬───────┘                │
              │                      │                        ▼
              │                      ▼                ┌────────────────┐
              │               ┌──────────────┐        │ Research Agent │
              │               │ RAG Pipeline │◄───────┤                │
              │               │              │        │ KB Search      │
              │               │ Vector Search│        │ Document Search│
              │               │ Reranking    │        │ Web Search     │
              │               └──────┬───────┘        └───────┬────────┘
              │                      │                        │
              └──────────┐           │                        │
                         │           │                        ▼
                         ▼           ▼                ┌────────────────┐
                  ┌─────────────────────────┐         │ Content        │
                  │      PostgreSQL         │         │ Planner        │
                  │                         │         └───────┬────────┘
                  │ users                   │                 │
                  │ knowledge_bases         │                 ▼
                  │ documents               │         ┌────────────────┐
                  │ document_chunks         │         │ Writer / LLM   │
                  │ pgvector embeddings     │         └───────┬────────┘
                  └─────────────────────────┘                 │
                                                              ▼
                                                     ┌────────────────┐
                                                     │ Critic / Review│
                                                     └───────┬────────┘
                                                             │
                                                             ▼
                                                     ┌────────────────┐
                                                     │ Editor / Final │
                                                     └────────────────┘


       ┌─────────────────────────────────────────────────────────────┐
       │                    AI / External Layer                     │
       │                                                             │
       │  LLM Providers       Embedding Providers      Web Search   │
       │  ┌─────────────┐     ┌─────────────────┐     ┌──────────┐ │
       │  │ OpenAI      │     │ OpenAI          │     │ Search   │ │
       │  │ Gemini      │     │ Other Providers │     │ APIs     │ │
       │  │ Anthropic   │     └─────────────────┘     └──────────┘ │
       │  │ Ollama      │                                           │
       │  └─────────────┘                                           │
       └─────────────────────────────────────────────────────────────┘


                         MAIN AI FLOW

       User Request
            │
            ▼
        ┌───────┐
        │ Plan  │
        └───┬───┘
            ▼
        ┌──────────┐
        │ Research │
        └────┬─────┘
             ▼
        ┌──────────┐
        │ Retrieve │◄──── Knowledge Base / Documents / Web
        └────┬─────┘
             ▼
        ┌──────────┐
        │ Analyze  │
        └────┬─────┘
             ▼
        ┌──────────┐
        │ Generate │
        └────┬─────┘
             ▼
        ┌──────────┐
        │  Verify  │
        └────┬─────┘
             ▼
        ┌──────────┐
        │  Final   │
        │ Content  │
        └──────────┘
```