from typing import TypedDict, Literal


class RelevantChunk(TypedDict):
    document_id: str
    chunk_id: str
    page_number: int | None


class EvaluationSample(TypedDict):
    id: str
    question: str
    expected_answer: str
    relevant_chunk: list[RelevantChunk]
    question_type: Literal[
        "factual",
        "semantic",
        "multi_chunk",
        "cross_document",
        "unanswerable",
    ]
    difficulty: Literal["easy", "medium", "hard"]
    answerable: bool


# DATASET: list[EvaluationSample] = [
DATASET = [
    {
        "id": "eval-001",
        "question": "What is a list comprehension? Use my stored documents to answer. Answer in 1-2 short sentences",
        "expected_answer": (
            "A list comprehension is a concise and readable way to construct a new list by evaluating"
            " an expression over a series of looping and filtering instructions enclosed in square brackets."
        ),
        "relevant_chunks": [
            {
                "document_id": "4a119dc8-1bb0-479f-8f51-68884a57b616",
                "chunk_id": "491feec6-8e2c-4fa2-9740-87d17a56803c",
                "page_number": 39,
            },
            {
                "document_id": "341b8dd9-4da6-4979-a6ff-5ce89d63b19c",
                "chunk_id": "afb9b452-06a6-4a77-9a87-6a35e7d9e8b0",
                "page_number": 1,
            }
        ],
        "question_type": "factual",
        "difficulty": "easy",
        "answerable": True,
    },
    {
        "id": "eval-002",
        "question": "What is the difference between a tuple and a list in python?",
        "expected_answer": (
            "Tuples are immutable sequences that typically contain heterogeneous data,"
            " whereas lists are mutable and usually contain homogeneous elements."
        ),
        "relevant_chunks": [
            {
                "chunk_id": "d222a6cc-1e50-4d40-adb6-8a6038f4457e",
                "document_id": "4a119dc8-1bb0-479f-8f51-68884a57b616",
                "page_number": 42,
            }
        ],
        "question_type": "factual",
        "difficulty": "easy",
        "answerable": True,
    },
    {
        "id": "eval-003",
        "question": "How does Python handle exceptions?",
        "expected_answer": (
            "Python handles exceptions by allowing programmers to catch and manage them using `try` statements,"
            " which invoke error handlers when specific exceptions occur during execution."
        ),
        "relevant_chunks": [
            {
                "chunk_id": "e0a64b33-bd02-4cad-9420-5c1de05f0f6a",
                "document_id": "4a119dc8-1bb0-479f-8f51-68884a57b616",
                "page_number": 42,
            },
            {
                "chunk_id": "def81cf0-d948-4634-81fb-3ab21b2a094b",
                "document_id": "4a119dc8-1bb0-479f-8f51-68884a57b616",
                "page_number": 68,
            },
            {
                "chunk_id": "eeba1cc1-af0b-48d3-b1ac-ff486c4eb430",
                "document_id": "341b8dd9-4da6-4979-a6ff-5ce89d63b19c",
                "page_number": 1,
            }
        ],
        "question_type": "factual",
        "difficulty": "easy",
        "answerable": True,
    },
    {
        "id": "eval-004",
        "question": "What is the purpose of __init__.py?",
        "expected_answer": (
            "The `__init__.py` file is used to mark a directory as a Python package, allowing it to contain "
            "submodules or subpackages. When importing from a package, the `__init__.py` file is implicitly executed, "
            "which facilitates the initialization of the package."
        ),
        "relevant_chunks": [
            {
                "chunk_id": "8fd7af0d-cd11-42a5-97ab-140121308228",
                "document_id": "4a119dc8-1bb0-479f-8f51-68884a57b616",
                "page_number": 127,
            }
        ],
        "question_type": "factual",
        "difficulty": "easy",
        "answerable": True,
    },
    {
        "id": "eval-005",
        "question": "How does the with statement work?",
        "expected_answer": (
            "The `with` statement evaluates a context manager, invokes its `__enter__` method to set up resources, "
            "and guarantees that its `__exit__` method is called after the suite completes, "
            "ensuring proper cleanup even if an error occurs."
        ),
        "relevant_chunks": [
            {
                "chunk_id": "d797020c-d379-4e04-9028-b9c2c9a93e1e",
                "document_id": "341b8dd9-4da6-4979-a6ff-5ce89d63b19c",
                "page_number": 1,
            },
            {
                "chunk_id": "099032fd-a98f-490f-a7f1-751b23f9f418",
                "document_id": "341b8dd9-4da6-4979-a6ff-5ce89d63b19c",
                "page_number": 1,
            }
        ],
        "question_type": "factual",
        "difficulty": "easy",
        "answerable": True,
    },
    # Security
    {
        "id": "eval-006",
        "question": "What is Broken Access Control?",
        "expected_answer": (
            "Broken Access Control occurs when an application fails to properly enforce policies, allowing users to act "
            "outside their intended permissions. This vulnerability often leads to unauthorized information disclosure, "
            "modification, or destruction of data."
        ),
        "relevant_chunks": [
            {
                "chunk_id": "6e396380-86fb-4ef9-b72e-53784db712cc",
                "document_id": "41977992-589b-49ff-a284-68bbeb40da0d",
                "page_number": 1,
            },
            {
                "chunk_id": "546e16a2-ffe6-4ac6-b2dd-8e28ea508e2f",
                "document_id": "41977992-589b-49ff-a284-68bbeb40da0d",
                "page_number": 1,
            }
        ],
        "question_type": "factual",
        "difficulty": "easy",
        "answerable": True,
    },
    {
        "id": "eval-007",
        "question": "What is the difference between authentication and authorization? Use my stored documents "
                    "to answer. Answer in 1-2 short sentences",
        "expected_answer": (
            "Authentication is the process of verifying a user's identity, confirming that they are who they claim "
            "to be. Authorization follows successful authentication to determine what specific resources or actions "
            "that verified user is permitted to access."
        ),
        "relevant_chunks": [
            {
                "document_id": "d459bcd8-4ad3-41d6-a5fe-6fec6cf6e880",
            }
        ],
        "question_type": "factual",
        "difficulty": "easy",
        "answerable": True,
    },
    {
        "id": "eval-008",
        "question": "What are examples of injection attacks?",
        "expected_answer": (
            "Common examples of injection attacks include SQL, NoSQL, OS command, LDAP, Expression Language (EL), OGNL, "
            "and Cross-site Scripting (XSS). Additionally, prompt injection has emerged as a significant vulnerability "
            "class specifically targeting large language models (LLMs)."
        ),
        "relevant_chunks": [
            {
                "chunk_id": "5419652a-9f6f-4154-bae2-382ebebc3e16",
                "document_id": "b7b6c2ce-3e92-4c88-b583-c16e6ba556db",
                "page_number": 2
            },
            {
                "chunk_id": "1b2d891d-c3cb-463f-8068-25a1e045d337",
                "document_id": "b7b6c2ce-3e92-4c88-b583-c16e6ba556db",
                "page_number": 1
            }
        ],
        "question_type": "factual",
        "difficulty": "easy",
        "answerable": True,
    },
    {
        "id": "eval-009",
        "question": "Which OWASP category covers cryptographic failures? Use my stored documents to answer. "
                    "Answer in 1-2 short sentences",
        "expected_answer": "Cryptographic failures are covered by the A04:2025 - Cryptographic Failures category "
                           "in the OWASP Top 10:2025.",
        "relevant_chunks": [
            {
                "chunk_id": "fd50fb67-a6c4-4722-a6b4-a9190f736b9c",
                "document_id": "9b66a481-497c-4cf7-836a-8309d2940b25",
                "page_number": 2,
            }
        ],
        "question_type": "factual",
        "difficulty": "easy",
        "answerable": True,
    },
    {
        "id": "eval-010",
        "question": "How can security misconfiguration be prevented? Use my stored documents to answer. "
                    "Answer in 1-2 short sentences",
        "expected_answer": "Security misconfiguration can be prevented by implementing automated, repeatable hardening "
                           "processes that ensure secure, consistent configurations across development, QA, "
                           "and production environments. Additionally, maintain a minimal platform by removing "
                           "unnecessary features, components, and documentation, and avoid embedding static secrets by "
                           "using identity federation or role-based access mechanisms.",
        "relevant_chunks": [
            {
                "chunk_id": "36d6929f-ed4b-492a-93e6-29271a9c14f1",
                "document_id": "07a340b3-cb67-46a6-8572-511f67f9dccd",
                "page_number": 2,
            },
            {
                "chunk_id": "40a6acbe-9a44-43da-b3fd-66ce7f0d9704",
                "document_id": "07a340b3-cb67-46a6-8572-511f67f9dccd",
                "page_number": 2,
            }
        ],
        "question_type": "factual",
        "difficulty": "easy",
        "answerable": True,
    },
    {
        "id": "eval-011",
        "question": "How can authentication be implemented? Use only my stored documents to answer. Never search in "
                    "internet. Answer in 1-2 short sentences",
        "expected_answer": "Authentication can be implemented using standard protocols like OAuth2, where the frontend "
                           "sends a username and password to an API to receive a token used for verifying the user. "
                           "This process can leverage packages like PyJWT for handling tokens and pwdlib for managing "
                           "passwords within the FastAPI framework.",
        "relevant_chunks": [
            {
                "chunk_id": "3f29d5d8-2d13-4dd7-b7bd-21d9163dc173",
                "document_id": "d7298bb2-3070-464d-bbd3-0c055be1746b",
                "page_number": 1,
            },
            {
                "chunk_id": "ff0a9f18-8ab7-47a8-bc21-35384e9790fc",
                "document_id": "e4a68afa-3d63-4b60-acc4-92b24af1b4aa",
                "page_number": 1,
            }
        ],
        "question_type": "factual",
        "difficulty": "easy",
        "answerable": True,
    },
    {
        "id": "eval-012",
        "question": "What does OWASP recommend for blockchain wallet security? Use only my stored "
                    "documents to answer do not search in internet. Answer in 1-2 short sentences",
        "expected_answer": "I am sorry, but my stored documents do not contain information regarding OWASP's "
                           "recommendations for blockchain wallet security.",
        "relevant_chunks": [],
        "question_type": "factual",
        "difficulty": "easy",
        "answerable": False,
    },

    # Database
    {
        "id": "eval-013",
        "question": "What is the purpose of VACUUM? Use only my stored documents to answer do not search in internet. "
                    "Answer in 1-2 short sentences",
        "expected_answer": "The SQL command VACUUM is used to reclaim disk space occupied by old data that was not "
                           "immediately removed during UPDATE or DELETE operations. It can be applied to specific "
                           "tables or the entire database to optimize storage.",
        "relevant_chunks": [
            {
                "chunk_id": "b279efa2-3bd3-43f3-b1a9-4f22864d2d3d",
                "document_id": "60fc2f82-6fa2-4302-8f18-bd1a6c0b4e7e",
                "page_number": 55,
            }
        ],
        "question_type": "factual",
        "difficulty": "easy",
        "answerable": True,
    },
    {
        "id": "eval-014",
        "question": "What is the difference between VACUUM and VACUUM FULL? Use only my stored documents to answer do not search in internet. "
                    "Answer in 1-2 short sentences",
        "expected_answer": "VACUUM is used to reclaim disk space occupied by old data that was not immediately removed "
                           "during UPDATE or DELETE operations. While standard VACUUM performs cleanup while allowing "
                           "normal database operations, VACUUM FULL is a more intensive operation typically reserved "
                           "for when most entries in a table have been deleted, as it reorganizes the table and changes "
                           "the physical location (ctid) of row versions.",
        "relevant_chunks": [
            {
                "chunk_id": "b279efa2-3bd3-43f3-b1a9-4f22864d2d3d",
                "document_id": "60fc2f82-6fa2-4302-8f18-bd1a6c0b4e7e",
                "page_number": 55,
            },
            {
                "chunk_id": "e9f69f34-3a1e-415a-87b2-9605e6d698d2",
                "document_id": "9152ff9f-be4b-431d-b81f-a458fda57242",
                "page_number": 42,
            }
        ],
        "question_type": "factual",
        "difficulty": "easy",
        "answerable": True,
    },
    {
        "id": "eval-015",
        "question": "How does PostgreSQL handle foreign keys? Use only my stored documents to answer do not search in internet. "
                    "Answer in 1-2 short sentences",
        "expected_answer": "In PostgreSQL, foreign keys are used as constraints to enforce referential integrity "
                           "between tables by requiring that values in referencing columns exist in the referenced "
                           "table. The system does not automatically create indexes on referencing columns, so it is "
                           "often recommended to create them manually to improve performance during updates or "
                           "deletions in the referenced table.",
        "relevant_chunks": [
            {
                "chunk_id": "2b831b52-1abb-4944-b5be-23041ae61399",
                "document_id": "9152ff9f-be4b-431d-b81f-a458fda57242",
                "page_number": 38,
            },
            {
                "chunk_id": "99134daf-7f9b-4c71-a7dd-414982365c02",
                "document_id": "9152ff9f-be4b-431d-b81f-a458fda57242",
                "page_number": 41,
            }
        ],
        "question_type": "factual",
        "difficulty": "easy",
        "answerable": True,
    },
    {
        "id": "eval-016",
        "question": "What is the default isolation level? Use only my stored documents to answer do not search in internet. "
                    "Answer in 1-2 short sentences",
        "expected_answer": "PostgreSQL's default transaction isolation level is Read Committed. At this level, a "
                           "query only sees data committed before the query began, ensuring it does not read "
                           "uncommitted data from concurrent transactions.",
        "relevant_chunks": [
            {
                "chunk_id": None,
                "document_id": "9152ff9f-be4b-431d-b81f-a458fda57242",
                "page_number": None,
            }
        ],
        "question_type": "factual",
        "difficulty": "medium",
        "answerable": True,
    },
    {
        "id": "eval-017",
        "question": "How can an index be created? Use only my stored documents to answer. Never search in internet. "
                    "Answer in 1-2 short sentences",
        "expected_answer": "An index can be created using the `CREATE INDEX` command followed by the table name and "
                           "the column to be indexed. Additionally, primary key and unique constraints on a table "
                           "automatically create an index on the specified columns.",
        "relevant_chunks": [
            {
                "chunk_id": "b9354d42-048e-4b7f-8076-807b9a986cbc",
                "document_id": "9152ff9f-be4b-431d-b81f-a458fda57242",
                "page_number": 68,
            },
            {
                "chunk_id": "168988e5-7781-488e-a24a-056497fe7902",
                "document_id": "9152ff9f-be4b-431d-b81d-a458fda57242",
                "page_number": 37,
            }
        ],
        "question_type": "factual",
        "difficulty": "medium",
        "answerable": True,
    },
    {
        "id": "eval-018",
        "question": "How can an index be created? Use only my stored documents to answer. Never search in internet. "
                    "Answer in 1-2 short sentences",
        "expected_answer": "Path parameters are declared as part of the URL path, while query parameters are the "
                           "key-value pairs that appear after the `?` character in a URL. Because query parameters "
                           "are not fixed parts of the URL, they can be optional and have default values, unlike "
                           "required path parameters.",
        "relevant_chunks": [
            {
                "chunk_id": "0eaefcb1-0d42-4b62-9a48-330bfec05c5a",
                "document_id": "952baad5-154a-479d-b21a-d6b484b4ae8c",
                "page_number": 1,
            },
            {
                "chunk_id": "ef527303-aa30-46ba-a094-44190e358a3e",
                "document_id": "952baad5-154a-479d-b21a-d6b484b4ae8c",
                "page_number": 1,
            }
        ],
        "question_type": "factual",
        "difficulty": "medium",
        "answerable": True,
    },
    {
        "id": "eval-019",
        "question": "How does FastAPI validate request bodies? Use only my stored documents to answer. Never search in internet. "
                    "Answer in 1-2 short sentences",
        "expected_answer": "FastAPI validates request bodies by using Pydantic models to define the expected data "
                           "structure and types. When a request is received, FastAPI automatically parses the JSON "
                           "body, converts the types, and validates the data against the declared model.",
        "relevant_chunks": [
            {
                "chunk_id": "25357566-347a-492f-ad62-2ef84fe9a081",
                "document_id": "f2a7838e-f581-42cb-95c0-a4aa679bf0e4",
                "page_number": 1,
            },
            {
                "chunk_id": "765aa89b-9f97-4ab6-bbc9-db01eb045a1a",
                "document_id": "f2a7838e-f581-42cb-95c0-a4aa679bf0e4",
                "page_number": None,
            }
        ],
        "question_type": "factual",
        "difficulty": "medium",
        "answerable": True,
    },
    {
        "id": "eval-020",
        "question": "What is dependency injection in FastAPI? Use only my stored documents to answer. Never search in internet. "
                    "Answer in 1-2 short sentences",
        "expected_answer": "Dependency injection in FastAPI allows your path operation functions to declare required "
                           "components, which the framework then automatically provides by executing the necessary "
                           "logic before your function runs. This system simplifies tasks like sharing database "
                           "connections, enforcing security, and reusing common logic while minimizing code repetition.",
        "relevant_chunks": [
            {

                "chunk_id": "c7971f29-ddb1-4b0a-baed-3640a5d1da03",
                "document_id": "62e62ece-560d-4b80-ad7b-ca9aa5cc5b90",
                "page_number": 1,
            },
            {
                "chunk_id": "60385d40-30b0-42a9-a56c-2d6fcad4fab2",
                "document_id": "62e62ece-560d-4b80-ad7b-ca9aa5cc5b90",
                "page_number": 1,
            }
        ],
        "question_type": "factual",
        "difficulty": "medium",
        "answerable": True,
    },
    {
        "id": "eval-001",
        "question": "What is the purpose of an index in PostgreSQL?",
        "expected_answer": (
            "An index helps PostgreSQL find rows more efficiently "
            "without scanning the entire table in many cases."
        ),
        "relevant_chunks": [
            {
                "document_id": "REPLACE_WITH_DOCUMENT_UUID",
                "chunk_id": "REPLACE_WITH_CHUNK_UUID",
                "page_number": None,
            }
        ],
        "question_type": "factual",
        "difficulty": "easy",
        "answerable": True,
    },
    {
        "id": "eval-021",
        "question": "How can authentication be implemented in fastapi? Use only my stored documents to answer. "
                    "Never search in internet. Answer in 1-2 short sentences",
        "expected_answer": (
            "FastAPI provides built-in tools to implement standard authentication protocols, such as OAuth2, in a "
            "simple and flexible way. It allows you to integrate external packages like `pwdlib` and `PyJWT` directly "
            "without requiring complex mechanisms."
        ),
        "relevant_chunks": [
            {
                "chunk_id": "240c24f6-cd80-4439-ad3d-7c8e961d1e8c",
                "document_id": "d459bcd8-4ad3-41d6-a5fe-6fec6cf6e880",
                "page_number": 1,
            },
            {
                "chunk_id": "ff0a9f18-8ab7-47a8-bc21-35384e9790fc",
                "document_id": "e4a68afa-3d63-4b60-acc4-92b24af1b4aa",
                "page_number": 1,
            }
        ],
        "question_type": "factual",
        "difficulty": "easy",
        "answerable": True,
    },

    {
        "id": "eval-022",
        "question": "What is BackgroundTasks used for? Use only my stored documents to answer. Never search in "
                    "internet. Answer in 1-2 short sentences",
        "expected_answer": "BackgroundTasks is used to perform small, slow tasks in the background, such as sending "
                           "email notifications or processing data, allowing the application to return a response "
                           "immediately. You can add these tasks by declaring a BackgroundTasks parameter in your path "
                           "operation functions or dependencies and using the .add_task() method.",
        "relevant_chunks": [
            {
                "chunk_id": "95d17c47-03f0-445f-b626-ece1494ddafb",
                "document_id": "19020574-25a2-44d2-b5c0-1cbb3574d9df",
                "page_number": 1,
            },
            {
                "chunk_id": "c037c113-e551-4c09-bc80-619d2828f1f3",
                "document_id": "19020574-25a2-44d2-b5c0-1cbb3574d9df",
                "page_number": 1,
            },
            {
                "chunk_id": "8439c425-e5c3-41b4-b433-bc502e1de3b6",
                "document_id": "19020574-25a2-44d2-b5c0-1cbb3574d9df",
                "page_number": 1,
            },
        ],
        "question_type": "multi_chunk",
        "difficulty": "medium",
        "answerable": True,
    },
    {
        "id": "eval-022",
        "question": "What are the different employment categories at Aetheria Technologies, and how are exempt and non-exempt employees distinguished? Use only my stored documents to answer. Never search in "
                    "internet. Answer in 1-2 short sentences",
        "expected_answer": "Aetheria Technologies classifies employees as regular full-time, regular part-time, "
                           "temporary, seasonal, or remote. Exempt employees are salaried staff ineligible for "
                           "overtime, while non-exempt employees are eligible for overtime pay and must "
                           "log all hours worked.",
        "relevant_chunks": [
            {
                "chunk_id": "bfde8c1c-afdc-4198-8ecb-d9c299e40b09",
                "document_id": "0aa84078-f7b2-435f-8920-7da348507bd8",
                "page_number": 1,
            },
            {
                "chunk_id": "1e592599-cead-4f39-8141-18bcbcd866a8",
                "document_id": "0aa84078-f7b2-435f-8920-7da348507bd8",
                "page_number": 1,
            }
        ],
        "question_type": "multi_chunk",
        "difficulty": "medium",
        "answerable": True,
    },
    {
        "id": "eval-023",
        "question": "What are the company's policies regarding hybrid and remote work, including home office equipment "
                    "and ergonomic guidelines? Use only my stored documents to answer. Never search in internet. "
                    "Answer in 1-2 short sentences",
        "expected_answer": "Aetheria Technologies supports three work models—office-centric, hybrid, and fully "
                           "remote—requiring approved residential workspaces with high-speed internet and strict "
                           "security compliance. Employees receive standard hardware, a $1,000 one-time setup stipend "
                           "for ergonomic furniture, and a $75 monthly technology allowance.",
        "relevant_chunks": [
            {
                "chunk_id": "92f1c2b6-f4d6-4427-8c9b-d7d3dfdf7095",
                "document_id": "0aa84078-f7b2-435f-8920-7da348507bd8",
                "page_number": 1,
            },
            {
                "chunk_id": "9e6a4bd7-88ab-4afd-8877-fd0b8e61e48f",
                "document_id": "0aa84078-f7b2-435f-8920-7da348507bd8",
                "page_number": 1,
            },
            {
                "chunk_id": "e6a364c1-935b-4bb8-8a8e-8028f3a78ff2",
                "document_id": "0aa84078-f7b2-435f-8920-7da348507bd8",
                "page_number": 1,
            }
        ],
        "question_type": "multi_chunk",
        "difficulty": "medium",
        "answerable": True,
    },
    {
        "id": "eval-024",
        "question": "What are the company's policies regarding hybrid and remote work, including home office equipment "
                    "and ergonomic guidelines? Use only my stored documents to answer. Never search in internet. "
                    "Answer in 1-2 short sentences",
        "expected_answer": "The employee handbook addresses overtime compensation for non-exempt employees "
                           "(1.5x to 2.0x base rate depending on thresholds), provides formulas for discretionary "
                           "performance-based bonuses, and governs stock option plans via the Aetheria Equity Incentive "
                           "Plan subject to Board approval. Detailed policies for these areas are outlined in "
                           "Chapter 4 of the manual.",
        "relevant_chunks": [
            {
                "chunk_id": "92f1c2b6-f4d6-4427-8c9b-d7d3dfdf7095",
                "document_id": "0aa84078-f7b2-435f-8920-7da348507bd8",
                "page_number": 1,
            },
            {
                "chunk_id": "34437af0-b02f-401a-bf03-c260a8a4bd16",
                "document_id": "0aa84078-f7b2-435f-8920-7da348507bd8",
                "page_number": 1,
            },
            {
                "chunk_id": "fd1344f6-580c-49b0-9df8-a54e8fe03f7c",
                "document_id": "0aa84078-f7b2-435f-8920-7da348507bd8",
                "page_number": 1,
            }
        ],
        "question_type": "multi_chunk",
        "difficulty": "medium",
        "answerable": True,
    },
    {
        "id": "eval-025",
        "question": "How does the company conduct performance reviews, use the OKR framework, and determine promotions "
                    "or merit increases? Use only my stored documents to answer. Never search in internet. "
                    "Answer in 1-2 short sentences",
        "expected_answer": "Aetheria utilizes a bi-annual performance enablement framework and quarterly OKR reviews to "
                           "align individual output with business goals, supported by ongoing 1-on-1 feedback. "
                           "Promotions and merit increases are determined based on performance ratings from the "
                           "End-of-Year review process, with merit pay tied to specific rating categories "
                           "and market dynamics",
        "relevant_chunks": [
            {
                "chunk_id": "0a1c21b0-8ec7-4ec0-bc9e-8b662c67af4e",
                "document_id": "0aa84078-f7b2-435f-8920-7da348507bd8",
                "page_number": 1,
            },
            {
                "chunk_id": "c55caf98-4bd0-4de6-b4bb-f55da7166fcd",
                "document_id": "0aa84078-f7b2-435f-8920-7da348507bd8",
                "page_number": 1,
            },
            {
                "chunk_id": "a257d3dc-6390-4d26-a5bb-78469027f69c",
                "document_id": "0aa84078-f7b2-435f-8920-7da348507bd8",
                "page_number": 1,
            }
        ],
        "question_type": "multi_chunk",
        "difficulty": "medium",
        "answerable": True,
    },
    {
        "id": "eval-026",
        "question": "What are the rules for PTO accrual, requesting vacation, carrying over unused days, and cashing "
                    "out accrued PTO? Use only my stored documents to answer. Never search in internet. "
                    "Answer in 1-2 short sentences",
        "expected_answer": "Employees accrue PTO bi-weekly based on tenure, with a maximum cap of 1.5x annual "
                           "entitlement and a carryover limit of 5 unused days. Vacation requests require two weeks' "
                           "notice for 3+ consecutive days, and unused PTO is only paid out upon separation "
                           "of employment.",
        "relevant_chunks": [
            {
                "chunk_id": "9db4bc9c-334e-4eca-810f-f5237461712d",
                "document_id": "0aa84078-f7b2-435f-8920-7da348507bd8",
                "page_number": 1,
            },
            {
                "chunk_id": "682cbe7c-b52b-42a4-beed-d8f4a3a89e00",
                "document_id": "0aa84078-f7b2-435f-8920-7da348507bd8",
                "page_number": 1,
            },
            {
                "chunk_id": "fb58146d-e0ca-4186-ae58-d86877936ec7",
                "document_id": "0aa84078-f7b2-435f-8920-7da348507bd8",
                "page_number": 1,
            },
            {
                "chunk_id": "b0d56c6a-0238-4f2d-8986-4dda1851261b",
                "document_id": "0aa84078-f7b2-435f-8920-7da348507bd8",
                "page_number": 1,
            }
        ],
        "question_type": "multi_chunk",
        "difficulty": "medium",
        "answerable": True,
    },
    # GenAI
    {
        "id": "eval-027",
        "question": "Inwiefern unterscheidet sich die Nutzung von generativer KI in alltäglichen kreativen Prozessen "
                    "von ihrer Rolle in professionellen Umfeldern, und welche konkreten Maßnahmen empfiehlt der Text "
                    "zur Steigerung des digitalen Bewusstseins? Use only my stored documents to answer. Never search "
                    "in internet. Answer in 1-2 short sentences",
        "expected_answer": "Der Text unterscheidet nicht explizit zwischen einer alltagsbezogenen und einer "
                           "professionellen Nutzung, sondern betrachtet generative KI als Werkzeug zur Förderung "
                           "kreativer Lösungen in beiden Bereichen. Zur Steigerung des digitalen Bewusstseins "
                           "empfiehlt er, die Kompetenz zu entwickeln, generative KI-Tools adäquat, sicher und "
                           "effektiv zu nutzen, sowie Chancen, Risiken und eine verantwortungsbewusste Anwendung "
                           "zu erkennen.",
        "relevant_chunks": [
            {
                "chunk_id": "1a31d01f-5c24-4a93-acf0-d70d1dd933f2",
                "document_id": "d9d79cec-ad3e-4a1c-a5c8-5e969dfca2ae",
                "page_number": 1,
            }
        ],
        "question_type": "multi_chunk",
        "difficulty": "medium",
        "answerable": True,
    },
    {
        "id": "eval-028",
        "question": "Welche Schritte durchläuft die Studie methodisch von der theoretischen Grundlage bis zum "
                    "praktischen Ergebnis, und welches Hauptziel wird mit dem entwickelten Leitfaden verfolgt? "
                    "Use only my stored documents to answer. Never search "
                    "in internet. Answer in 1-2 short sentences",
        "expected_answer": "Die Studie entwickelt auf theoretischer Grundlage – definiert durch das digitale "
                           "Bewusstsein im Kontext von Kreativität und generativer KI – mittels einer "
                           "Fragebogenuntersuchung und anschließender quantitativer sowie qualitativer Analyse einen "
                           "praxisnahen Leitfaden. Das Hauptziel dieses Leitfadens ist es, Einzelpersonen eine "
                           "Orientierungshilfe für den effektiven Einsatz generativer KI in der Textkreation zu "
                           "bieten und als Basis für weiterführende Schulungsformate zur Kompetenzvermittlung zu dienen.",
        "relevant_chunks": [
            {
                "chunk_id": None,
                "document_id": "d9d79cec-ad3e-4a1c-a5c8-5e969dfca2ae",
                "page_number": 1,
            }
        ],
        "question_type": "multi_chunk",
        "difficulty": "medium",
        "answerable": True,
    },
    {
        "id": "eval-029",
        "question": "Welche spezifische Funktion erfüllt generative KI im Gegensatz zu allgemeinen KI-Systemen, und "
                    "wie unterstützt sie den menschlichen Kreativitätsprozess gemäß dem Text"
                    "Use only my stored documents to answer. Never search "
                    "in internet. Answer in 1-2 short sentences",
        "expected_answer": "Generative KI erfüllt im Gegensatz zu allgemeinen Systemen die spezifische Funktion, "
                           "neue Inhalte wie Texte, Bilder oder Musik zu kreieren. Sie unterstützt den menschlichen "
                           "Kreativitätsprozess, indem sie als Werkzeug in allen Phasen der Entstehung – von der "
                           "Ideenfindung über die Formulierung von Hypothesen bis hin zur Verfeinerung – fördernd zur "
                           "Seite steht.",
        "relevant_chunks": [
            {
                "chunk_id": None,
                "document_id": "d9d79cec-ad3e-4a1c-a5c8-5e969dfca2ae",
                "page_number": None,
            },
            {
                "chunk_id": None,
                "document_id": "d9d79cec-ad3e-4a1c-a5c8-5e969dfca2ae",
                "page_number": None,
            }
        ],
        "question_type": "multi_chunk",
        "difficulty": "medium",
        "answerable": True,
    },
    {
        "id": "eval-030",
        "question": "Warum ist die frühzeitige Einbindung von Mitarbeitenden in technologische Veränderungsprozesse "
                    "für Unternehmen laut dem Text so entscheidend, und wie tragen kostenlose Schulungsangebote dazu bei?"
                    "Use only my stored documents to answer. Never search "
                    "in internet. Answer in 1-2 short sentences",
        "expected_answer": "Die frühzeitige Einbindung von Mitarbeitenden in technologische Veränderungsprozesse ist "
                           "entscheidend, um Unsicherheiten abzubauen, Kreativität zu fördern und Hemmnisse bei der "
                           "Nutzung neuer Technologien zu vermeiden. Kostenlose Schulungsangebote tragen dazu bei, "
                           "indem sie einen niedrigschwelligen Zugang zu digitalen Kompetenzen ermöglichen, "
                           "Mitarbeitende motivieren und ihnen eine partizipative Teilhabe an diesen Prozessen erleichtern.",
        "relevant_chunks": [
            {
                "chunk_id": "612240b4-53e7-4b9a-999d-5c3f66b5fead",
                "document_id": "d9d79cec-ad3e-4a1c-a5c8-5e969dfca2ae",
                "page_number": 1,
            },
            {
                "chunk_id": "489c831c-d54a-4cef-9a94-bb02562d7776",
                "document_id": "d9d79cec-ad3e-4a1c-a5c8-5e969dfca2ae",
                "page_number": 1,
            }
        ],
        "question_type": "multi_chunk",
        "difficulty": "medium",
        "answerable": True,
    },
    {
        "id": "eval-031",
        "question": "Welche methodischen Einschränkungen nennt der Text hinsichtlich der Datenerhebung und "
                    "des Fragebogendesigns, und welche Empfehlungen werden für zukünftige Arbeiten gegeben, "
                    "um diesen Bias und Auswertungsproblemen entgegenzuwirken?"
                    "Use only my stored documents to answer. Never search "
                    "in internet. Answer in 1-2 short sentences",
        "expected_answer": "Die methodischen Einschränkungen umfassen die Verwendung nicht-etablierter Skalen, "
                           "eine mögliche Selektionsverzerrung durch die Rekrutierung über Social Media, kurz gefasste "
                           "qualitative Antworten sowie die fehlende Evaluierung des Leitfadens. Zukünftigen Studien "
                           "wird empfohlen, etablierte Skalen und umfassendere Analysen zu nutzen, eine präzisere "
                           "Definition der Begriffe vorzunehmen, diversifizierte Rekrutierungsstrategien anzuwenden "
                           "und auf qualitative Interviews oder optimierte Fragebogendesigns zu setzen.",
        "relevant_chunks": [
            {
                "chunk_id": "6433638d-8453-48df-8011-9e8c7271dcc8",
                "document_id": "d9d79cec-ad3e-4a1c-a5c8-5e969dfca2ae",
                "page_number": 1,
            },
            {
                "chunk_id": "7ec4f849-d047-4c55-8752-a1d2c36df767",
                "document_id": "d9d79cec-ad3e-4a1c-a5c8-5e969dfca2ae",
                "page_number": 1,
            }
        ],
        "question_type": "multi_chunk",
        "difficulty": "medium",
        "answerable": True,
    },
    {
        "id": "eval-032",
        "question": "What is machine learning?"
                    "Use only my stored documents to answer. Never search "
                    "in internet. Answer in 1-2 short sentences",
        "expected_answer": "Machine learning is characterized by the fact that classifications and recommendations "
                           "are not based solely on predefined rules, but are instead derived from existing data. "
                           "It provides universal methods for analyzing texts, images, or numbers.",
        "relevant_chunks": [
            {
                "chunk_id": "99a80ccf-e14e-4a39-a38c-d59fadbb48eb",
                "document_id": "b6838bac-c52e-4800-93ed-109aae8f2282",
                "page_number": 1,
            },
            {
                "chunk_id": "d261bd66-a6f7-49d5-b0b1-628be5256ab0",
                "document_id": "b6838bac-c52e-4800-93ed-109aae8f2282",
                "page_number": 1,
            }
        ],
        "question_type": "multi_chunk",
        "difficulty": "medium",
        "answerable": True,
    },
    {
        "id": "eval-033",
        "question": "Was ist der Unterschied zwischen Überwachtes und Unüberwachtes Lernen?"
                    "Use only my stored documents to answer. Never search "
                    "in internet. Answer in 1-2 short sentences",
        "expected_answer": "Beim überwachten Lernen sind für einen Teil der Daten die korrekten Antworten bereits "
                           "vorab bekannt, um daraus Vorhersagen für weitere Fälle zu treffen. Beim unüberwachten "
                           "Lernen hingegen ist das Ergebnis im Voraus unbekannt, und der Algorithmus sucht "
                           "selbstständig nach Mustern und Strukturen in den Daten, um diese zu gruppieren.",
        "relevant_chunks": [
            {
                "chunk_id": None,
                "document_id": "b6838bac-c52e-4800-93ed-109aae8f2282",
                "page_number": 1,
            },
            {
                "chunk_id": None,
                "document_id": "b6838bac-c52e-4800-93ed-109aae8f2282",
                "page_number": 1,
            }
        ],
        "question_type": "multi_chunk",
        "difficulty": "medium",
        "answerable": True,
    },
    {
        "id": "eval-034",
        "question": "Wie funktionieren Künstliche Neuronale Netze und wie werden sie modelliert?"
                    "Use only my stored documents to answer. Never search "
                    "in internet. Answer in 1-2 short sentences",
        "expected_answer": "Künstliche Neuronale Netze imitieren menschliches Denken, indem sie Input-Werte durch "
                           "gewichtete verdeckte Schichten in einen Output überführen. Modelliert werden sie dabei "
                           "durch Schichtstrukturen, deren Verbindungen und Gewichte mittels des "
                           "Backpropagation-Algorithmus während eines Trainingsprozesses optimiert werden.",
        "relevant_chunks": [
            {
                "chunk_id": "355d719e-dca9-4ae6-ac62-b9249411edd7",
                "document_id": "b6838bac-c52e-4800-93ed-109aae8f2282",
                "page_number": 1,
            },
            {
                "chunk_id": "19473a89-edf0-4675-aeca-03bbb66661e7",
                "document_id": "b6838bac-c52e-4800-93ed-109aae8f2282",
                "page_number": 1,
            },
            {
                "chunk_id": "9f686ec5-a258-4f92-a014-1c8191992a1e",
                "document_id": "b6838bac-c52e-4800-93ed-109aae8f2282",
                "page_number": 1,
            }
        ],
        "question_type": "multi_chunk",
        "difficulty": "medium",
        "answerable": True,
    },
    {
        "id": "eval-035",
        "question": "Wie wird GenAI-Weiterbildung in Deutschland gefördert?"
                    "Use only my stored documents to answer. Never search "
                    "in internet. Answer in 1-2 short sentences",
        "expected_answer": "Die Förderung von GenAI-Weiterbildung in Deutschland erfolgt unter anderem durch "
                           "kostenlose Schulungsangebote, die in Zusammenarbeit zwischen Wissenschaft und Praxis für "
                           "Mitarbeitende aus kleinen und mittleren Unternehmen sowie dem öffentlichen Sektor "
                           "bereitgestellt werden. Zudem wird Unternehmen nahegelegt, eigene Schulungsformate "
                           "anzubieten, um Mitarbeitende zu motivieren und eine faire Teilhabe an der digitalen "
                           "Welt zu ermöglichen.",
        "relevant_chunks": [
            {
                "chunk_id": "489c831c-d54a-4cef-9a94-bb02562d7776",
                "document_id": "d9d79cec-ad3e-4a1c-a5c8-5e969dfca2ae",
                "page_number": 1,
            },
            {
                "chunk_id": "fd59c9d3-74cb-425a-b70c-6a3efd54aaf2",
                "document_id": "d9d79cec-ad3e-4a1c-a5c8-5e969dfca2ae",
                "page_number": 1,
            }
        ],
        "question_type": "multi_chunk",
        "difficulty": "medium",
        "answerable": True,
    },
    {
        "id": "eval-036",
        "question": "Wie wird GenAI-Weiterbildung in Kamerun gefördert? Use only my stored documents to answer. "
                    "Never search in internet. Answer in 1-2 short sentences",
        "expected_answer": (
            "Ich konnte in Ihren gespeicherten Dokumenten keine Informationen darüber finden, "
            "wie GenAI-Weiterbildung in Kamerun gefördert wird."
        ),
        "relevant_chunks": [],
        "question_type": "unanswerable",
        "difficulty": "easy",
        "answerable": False,
    },
    {
        "id": "eval-037",
        "question": "Wer ist der Bundeskanzler? Use only my stored documents to answer. "
                    "Never search in internet. Answer in 1-2 short sentences",
        "expected_answer": (
            "Ich konnte in Ihren gespeicherten Dokumenten keine Informationen über den aktuellen Bundeskanzler finden."
        ),
        "relevant_chunks": [],
        "question_type": "unanswerable",
        "difficulty": "easy",
        "answerable": False,
    },
]
