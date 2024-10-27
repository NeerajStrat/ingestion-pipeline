import os
import asyncio
import constants
import schema
from tqdm.asyncio import tqdm
from pymongo import ASCENDING
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Dict, List, Optional, Tuple
from fastapi.encoders import jsonable_encoder
from pathlib import Path
# from sse_starlette.sse import EventSourceResponse
from ingestion.stock_utils import get_stocks_by_symbol, Stock
from ingestion.file_utils import get_available_filings, Filing, load_pdf
from pytickersymbols import PyTickerSymbols
from pymongo.errors import DuplicateKeyError
from llama_index.storage.index_store.mongodb import MongoIndexStore
from llama_index.storage.docstore.mongodb import MongoDocumentStore
from llama_index.vector_stores.mongodb import MongoDBAtlasVectorSearch
from llama_index.core import StorageContext, VectorStoreIndex, load_indices_from_storage
from llm import LLM
from logger import logger


async def upsert_document_by_url(collection, document: schema.Document) -> schema.Document:
    """
    Upsert a document by URL.
    """
    logger.debug({"url": str(document.url), **document.dict()})
    insert_result = await collection.insert_one({"url": str(document.url), **document.dict()})
    document.id = insert_result.inserted_id
    logger.debug(document)
    return document


async def upsert_document(stock: Stock, filing: Filing, url_base: str, collection):
    """
    Upserts an SEC document with metadata into the MongoDB collection.
    """
    logger.info("Upserting document")
    doc_path = Path(filing.file_path).relative_to(constants.DEFAULT_OUTPUT_DIR)
    url_path = f"{url_base.rstrip('/')}/{str(doc_path).lstrip('/')}"
    doc_type = schema.SecDocumentTypeEnum.TEN_K if filing.filing_type == "10-K" else schema.SecDocumentTypeEnum.TEN_Q

    sec_doc_metadata = schema.SecDocumentMetadata(
        company_name=stock.name,
        company_ticker=stock.symbol,
        doc_type=doc_type,
        year=filing.year,
        quarter=filing.quarter,
        accession_number=filing.accession_number,
        cik=filing.cik,
        period_of_report_date=filing.period_of_report_date,
        filed_as_of_date=filing.filed_as_of_date,
        date_as_of_change=filing.date_as_of_change,
    )

    metadata_map = {
        schema.DocumentMetadataKeysEnum.SEC_DOCUMENT: jsonable_encoder(sec_doc_metadata.dict(exclude_none=True))
    }
    doc = schema.Document(url=str(url_path), metadata_map=metadata_map)
    logger.debug(f"Document to insert: {doc}")

    try:
        doc = await upsert_document_by_url(collection, doc)
        build_doc_id_to_index_map([doc])
        yield {"event": "vector", "data": f"Stored in Vector DB {doc.url}."}
    except DuplicateKeyError:
        logger.info(f"Duplicate key error: Document with URL {doc.url} already exists.")
        yield {"event": "duplicate", "data": f"Duplicate record found for {doc.url}."}
    except Exception as e:
        logger.exception("An error occurred while inserting the document.")
        raise e
    else:
        yield {"event": "upsert", "data": f"Upserted document for {filing.symbol}, filing type {filing.filing_type}, quarter {filing.quarter}"}


async def async_upsert_documents_from_filings(tickers, collection):
    """
    Streams filings upserts and event publishing as SSE.
    """
    url_base = f"https://{constants.BUCKET_NAME}.s3.amazonaws.com"
    filings = get_available_filings(tickers)
    stocks_data = PyTickerSymbols()
    stocks_dict = get_stocks_by_symbol(stocks_data.get_all_indices())

    for filing in tqdm(filings, desc="Upserting documents from filings"):
        if filing.symbol not in stocks_dict:
            yield {"event": "error", "data": f"Symbol {filing.symbol} not found in stocks_dict. Skipping."}
            continue

        stock = stocks_dict[filing.symbol]

        async for event in upsert_document(stock, filing, url_base, collection):
            yield event

    yield {"event": "done", "data": "Completed processing all filings."}


# async def ingest_document_db(db_session: Tuple[AsyncIOMotorDatabase, object], tickers: List[str]):
    # """
    # Initiates the document ingestion process and returns SSE for each filing.
    # """
    # async with db_session as (db, session):
    #     collection = db.get_collection(constants.COLLECTION_NAME)
    #     await collection.create_index([("url", ASCENDING)], unique=True)
    #     return await async_upsert_documents_from_filings(tickers, collection)


def build_doc_id_to_index_map(documents: List[schema.Document]) -> Dict[str, VectorStoreIndex]:
    """
    Builds a mapping of document IDs to index objects.
    """
    docstore = MongoDocumentStore.from_uri(uri=os.environ["MONGODB_URI"], db_name=constants.DB_NAME, namespace=constants.DOCSTORE_NAMESPACE)
    vector_store = MongoDBAtlasVectorSearch(
        db_name=constants.DB_NAME,
        collection_name=constants.VECTOR_COLLECTION_NAME,
        vector_index_name=constants.VECTOR_INDEX_NAME,
        relevance_score_fn="cosine"
    )
    index_store = MongoIndexStore.from_uri(uri=os.environ["MONGODB_URI"], db_name=constants.DB_NAME, namespace=constants.INDEX_NAMESPACE)

    storage_context = StorageContext.from_defaults(docstore=docstore, vector_store=vector_store, index_store=index_store)

    try:
        index_ids = [str(doc.id) for doc in documents]
        indices = load_indices_from_storage(storage_context, index_ids=index_ids)
        doc_id_to_index = dict(zip(index_ids, indices))
    except ValueError:
        doc_id_to_index = {}
        for doc in documents:
            llama_index_docs = load_pdf(doc)
            storage_context.docstore.add_documents(llama_index_docs)
            index = VectorStoreIndex.from_documents(
                llama_index_docs,
                storage_context=storage_context,
                embed_model=LLM.embedding_model
            )
            index.set_index_id(str(doc.id))
            doc_id_to_index[str(doc.id)] = index

    return doc_id_to_index


async def fetch_documents(db_session: Tuple[AsyncIOMotorDatabase, object]) -> List[schema.Document]:
    """
    Fetches documents from the MongoDB collection.
    """
    async with db_session as (db, session):
        collection = db.get_collection(constants.COLLECTION_NAME)
        documents = await collection.find({}).to_list(length=None)
        return documents
