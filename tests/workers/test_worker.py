def test_worker_imports_all_tasks():
    from app.workers import worker

    assert worker.embed_document is not None
    assert worker.generate_document_summary is not None
    assert worker.extract_document is not None
    assert worker.generate_document_comparison is not None
    assert worker.recover_embedding_jobs is not None
