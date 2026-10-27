### Evaluation pipeline:

1. Retrieve chunks using hybrid RRF.
2. Generate the answer using your KnowledgeForge agent.
3. Evaluate that answer with RAGAS.
4. Record the scores alongside your existing retrieval metrics in Langfuse.

### Run the evaluation

Open a terminal in the KnowledgeForge project root—the directory containing app/ and evaluation/.
Run:

`uv run python -m evaluation.run_retrieval_evaluation`

Using -m ensures Python can resolve the evaluation package from the project root.