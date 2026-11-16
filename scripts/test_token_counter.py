from app.services.token_counter import TokenCounter

counter = TokenCounter()

text = "KnowledgeForge is a document intelligence platform."

print("Estimated tokens:", counter.count(text))

text = (
           "KnowledgeForge processes large documents. "
           "It generates summaries and extracts structured information. "
       ) * 500

segments = counter.split_text(text, max_tokens=500)

for index, segment in enumerate(segments):
    print(
        f"Segment {index}: "
        f"{counter.count(segment)} tokens"
    )

assert all(counter.count(segment) <= 500 for segment in segments)
