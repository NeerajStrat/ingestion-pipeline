DEFAULT_OUTPUT_DIR = "/app/data/"
DEFAULT_CIKS = [
        "AAPL",
        "TSLA",
        "MSFT",
]
DEFAULT_FILING_TYPES = [
    "10-K",
    "10-Q",
]

SEC_EDGAR_COMPANY_NAME="MyCompanyName"
SEC_EDGAR_EMAIL="my.email@domain.com"
BUCKET_NAME="finaillm"

# Database
DB_NAME="finaillm-sec-documents"
COLLECTION_NAME = "sec-documents"
CONVERSATION_COLLECTION_NAME="conversations"
MESSAGES_COLLECTION_NAME="messages"
VECTOR_COLLECTION_NAME = "{}-vectors".format(COLLECTION_NAME)
INDEX_NAMESPACE ="{}-index".format(COLLECTION_NAME)
DOCSTORE_NAMESPACE = "{}-docs".format(COLLECTION_NAME)
VECTOR_INDEX_NAME = "{}-vector-index".format(COLLECTION_NAME)
DB_DOC_ID_KEY = "db_document_id"

#LLM
NODE_PARSER_CHUNK_SIZE = 512
NODE_PARSER_CHUNK_OVERLAP = 10
OPENAI_TOOL_LLM_NAME = "gpt-3.5-turbo"
