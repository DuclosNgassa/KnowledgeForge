# AI Research & Content Intelligence Platform

is a backend-focused application that helps users **research a topic and generate high-quality content**. The system can retrieve information from uploaded documents, a knowledge base, and external tools, then use AI to analyze the information and generate reports or articles. The project combines key GenAI concepts such as **LLMs, RAG, embeddings, vector databases, AI agents, tool calling, structured outputs, and content evaluation**. Instead of being a simple chatbot, it orchestrates several AI components in a complete workflow:

**Research → Analyze → Plan → Generate → Verify.**

The knowledge base is the collection of information the AI can search and use to answer questions or generate content.

We have several usage options.

1.  User-uploaded documents

Users can upload:  PDFs / DOCX files / TXT files / Markdown files / Research papers / Company documents / Technical documentation

2.  Technical documentation knowledge base

Python FastAPI Spring Boot React PostgreSQL Docker

Then a user could ask:

"How does dependency injection work in FastAPI?"

The system retrieves relevant documentation before generating the answer.

3.  Research papers and articles

The knowledge base could contain:

-   AI research papers
-   Scientific articles
-   Technology articles
-   Industry reports

4.  A company knowledge base

A company could upload:

-   Employee handbook
-   Internal documentation
-   Product documentation
-   Policies
-   Meeting notes

Users can then ask:

"What is the company's remote work policy?"

The knowledge base is user-specific:

```
User
 │
 ├── Knowledge Base
 │    |
 │    ├── AI Research
 │    │    ├── paper1.pdf
 │    │    └── paper2.pdf
 │    |
 │    ├── Software Engineering
 │    │    ├── architecture.md
 │    │    └── spring_boot.pdf
 │    |
 │    └── Personal Documents
 │
 └── Research Requests
```

The user can create multiple knowledge bases. Then, when generating content, the user selects which knowledge base to use.

### Example workflow for knowledge base creation

A user uploads: document1.pdf, document2.pdf, document3.pdf

Then the user creates:

`Knowledge Base: "Generative AI"`

and adds those documents to it.

The system processes them:

```
Documents
    ↓
Extract text
    ↓
Split into chunks
    ↓
Create embeddings
    ↓
Store vectors
    ↓
Knowledge Base
```

## Supported use case

### 1. Ask a Question About a Knowledge Base

```
User Question
      │
      ▼
┌──────────────────┐
│ Request Analyzer │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Query Rewriter   │
└────────┬─────────┘
         │
         ▼
Create Query Embedding
         │
         ▼
┌──────────────────┐
│ Vector Search    │
│ Knowledge Base   │
└────────┬─────────┘
         │
         ▼
Relevant Chunks
         │
         ▼
Optional Reranking
         │
         ▼
┌──────────────────┐
│ LLM Generation   │
└────────┬─────────┘
         │
         ▼
Answer + Sources
```

#### GenAI concepts used

-   Embeddings
-   Vector database
-   RAG
-   Query rewriting
-   Reranking
-   Citations

### 2. Analyze a Single Uploaded Document

The user uploads `research_paper.pdf`

Then asks: `"Summarize this paper and explain the main findings."`

```
Upload PDF
     │
     ▼
┌─────────────────┐
│ Document Loader │
└────────┬────────┘
         │
         ▼
Text Extraction
         │
         ▼
Document Analysis
         │
         ▼
┌─────────────────┐
│ Summarization   │
│ Workflow        │
└────────┬────────┘
         │
         ▼
Main Findings
         │
         ▼
Final Summary
```

For very large documents:

```
Large Document
      │
      ▼
Split into Chunks
      │
      ▼
Summarize Each Chunk
      │
      ▼
Combine Summaries
      │
      ▼
Final Summary
```

#### GenAI concepts used

-   Document processing
-   Chunking
-   Map-reduce summarization
-   LLM structured output

### 3. Research a Topic and Generate a Report

This is one of the main KnowledgeForge workflows.

User requests: `"Create a report about the impact of AI agents on software engineering."`

```
User Request
      │
      ▼
┌──────────────────┐
│ Request Analyzer │
└────────┬─────────┘
         │
         ▼
Extract Requirements
         │
         ▼
┌──────────────────┐
│ Research Planner │
└────────┬─────────┘
         │
         ▼
Research Plan
         │
         ▼
┌──────────────────┐
│ Research Agent   │
└────────┬─────────┘
         │
         ├─────────────┐
         │             │
         ▼             ▼
   Knowledge Base    Web Search
         │             │
         └──────┬──────┘
                ▼
        Research Results
                │
                ▼
          Research Analysis
                │
                ▼
           Report Planner
                │
                ▼
           Report Outline
                │
                ▼
             Writer
                │
                ▼
             Critic
                │
                ▼
          Final Report
```

### 4. Generate an Article from a Knowledge Base

Use case

The user selects: `Knowledge Base: Generative AI`

Then requests: `"Write a beginner-friendly article explaining AI agents."`

```
User Request
      │
      ▼
Understand Topic
      │
      ▼
Search Knowledge Base
      │
      ▼
Retrieve Relevant Information
      │
      ▼
Create Article Outline
      │
      ▼
Generate Sections
      │
      ▼
Combine Sections
      │
      ▼
Review Article
      │
      ▼
Final Article
```

The important idea here is:

The LLM does not invent all information from scratch.

It uses the selected knowledge base.

### 5. Multi-Document Comparison

The user selects three documents:

```
Document A: Spring Boot Architecture
Document B: FastAPI Architecture
Document C: Node.js Architecture
```

The user asks: `"Compare these architectures."`

```
User Request
      │
      ▼
┌──────────────────┐
│ Comparison Agent │
└────────┬─────────┘
         │
         ├──────────────┐
         │              │
         ▼              ▼
    Document A      Document B
         │              │
         ▼              ▼
     Extract         Extract
    Information     Information
         │              │
         └──────┬───────┘
                │
                ▼
           Document C
                │
                ▼
         Extract Information
                │
                ▼
        Compare Information
                │
                ▼
       Generate Comparison
```

#### GenAI concepts

-   Multi-document RAG
-   Structured extraction
-   Comparison
-   LLM reasoning

### 6. Research Using Multiple Sources

The user asks:

`"Research the future of autonomous AI agents."`

The App searches:

```
Knowledge base
User documents
External search tools
```

```
                   Research Request
                          │
                          ▼
                   Research Planner
                          │
           ┌──────────────┼──────────────┐
           ▼              ▼              ▼
     Knowledge Base    Documents       Web
           │              │              │
           ▼              ▼              ▼
        Results         Results        Results
           │              │              │
           └──────────────┼──────────────┘
                          │
                          ▼
                   Source Aggregator
                          │
                          ▼
                    Remove Duplicates
                          │
                          ▼
                    Analyze Sources
                          │
                          ▼
                   Research Summary
```

#### GenAI concepts

-   Tool calling
-   Multiple data sources
-   Source aggregation
-   Deduplication
-   Agent workflows

### 7. Content Improvement

The user provides an article and asks: `"Improve this article about RAG."`

```
User Content
      │
      ▼
┌─────────────────┐
│ Content Analyzer│
└────────┬────────┘
         │
         ▼
Analyze:

- Grammar
- Structure
- Clarity
- Relevance
- Missing Information

         │
         ▼
┌─────────────────┐
│ Improvement Plan│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Editor Agent    │
└────────┬────────┘
         │
         ▼
Improved Content
```

### 8. Content Generation with a Multi-Agent Workflow

The user requests:

`"Write a technical article about RAG."`

```
                     USER REQUEST
                           │
                           ▼
                   ┌───────────────┐
                   │    PLANNER    │
                   └───────┬───────┘
                           │
                           ▼
                      ARTICLE PLAN
                           │
                           ▼
                   ┌───────────────┐
                   │   RESEARCHER  │
                   └───────┬───────┘
                           │
                           ▼
                    RESEARCH DATA
                           │
                           ▼
                   ┌───────────────┐
                   │    WRITER     │
                   └───────┬───────┘
                           │
                           ▼
                         DRAFT
                           │
                           ▼
                   ┌───────────────┐
                   │    CRITIC     │
                   └───────┬───────┘
                           │
                  ┌────────┴────────┐
                  │                 │
                GOOD              PROBLEMS
                  │                 │
                  │                 ▼
                  │            WRITER
                  │                 │
                  └────────┬────────┘
                           ▼
                     FINAL ARTICLE
```

### 9. Generate Multiple Types of Content

The same research can generate different outputs.

Use case

User researches: `"AI agents in software engineering"`

The App produces:

```
Research Results
       │
       ├──────────────► Technical Article
       │
       ├──────────────► Executive Summary
       │
       ├──────────────► LinkedIn Post
       │
       ├──────────────► Learning Material
       │
       └──────────────► Presentation Outline
```

#### Workflow

```
Topic
  │
  ▼
Research
  │
  ▼
Research Knowledge
  │
  ▼
Content Type Selector
  │
  ├── Article Generator
  ├── Report Generator
  ├── Summary Generator
  └── Learning Generator
```

### 10. Knowledge Base Research

Use case

The user has a knowledge base:

```
AI Research
│
├── RAG.pdf
├── AI Agents.pdf
├── LLM.pdf
└── Prompt Engineering.pdf
```

The user asks:

`"What topics are missing from my knowledge base?"`

#### Workflow

```
Knowledge Base
      │
      ▼
Extract Metadata
      │
      ▼
Analyze Documents
      │
      ▼
Identify Topics
      │
      ▼
Cluster Topics
      │
      ▼
Knowledge Map
      │
      ▼
Identify Missing Areas
```

#### Possible output:

```
Knowledge Base Topics:

✓ RAG
✓ AI Agents
✓ Prompt Engineering

Missing Topics:

✗ Fine-Tuning
✗ AI Evaluation
✗ Guardrails
✗ Model Context Protocol
```

### 11. Ask the AI to Create a Research Plan

Use case

The user asks:

`"I want to research AI in education."`

Before starting research, the App creates a plan.

Workflow

```
Research Topic
      │
      ▼
Research Planner
      │
      ▼
Generate Research Questions
      │
      ▼
Generate Search Queries
      │
      ▼
Determine Sources
      │
      ▼
Research Plan
```

### 12. Verify Generated Content

Use case

The AI generates a report.

The App verifies the report before returning it.

```
Generated Report
       │
       ▼
Claim Extractor
       │
       ▼
Extract Claims
       │
       ├── Claim 1
       ├── Claim 2
       └── Claim 3
       │
       ▼
Evidence Retrieval
       │
       ▼
Compare Claim with Evidence
       │
       ▼
┌─────────────────────┐
│ Verification Agent  │
└──────────┬──────────┘
           │
           ▼
     Verification Result
```

### 13. Conversational Research Assistant

Use case

The user has a conversation with The AI.

```
User:
What are AI agents?

AI:
[Answer]

User:
How are they used in software development?

AI:
[Answer]

User:
Give me examples of the second use case you mentioned.
```

#### Workflow

```
New User Question
       │
       ▼
Conversation Memory
       │
       ▼
Retrieve Relevant History
       │
       ▼
Rewrite Question
       │
       ▼
Search Knowledge Base
       │
       ▼
Generate Answer
```

#### GenAI Concept:

-   Conversation memory
-   Context management
-   Query rewriting