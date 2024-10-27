import os
import schema
import constants
from tqdm import tqdm
from pymongo import MongoClient, ASCENDING
from ingestion.stock_utils import get_stocks_by_symbol, Stock
from ingestion.file_utils import get_available_filings, Filing, load_pdf 
from pytickersymbols import PyTickerSymbols
from fastapi.encoders import jsonable_encoder
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Dict, List, Optional, Tuple
from logger import logger
from pymongo.errors import DuplicateKeyError
from llama_index.storage.index_store.mongodb import MongoIndexStore
from llama_index.storage.docstore.mongodb import MongoDocumentStore
from llama_index.vector_stores.mongodb import MongoDBAtlasVectorSearch
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext
from llama_index.core import load_indices_from_storage, load_index_from_storage
from llm import LLM


async def upsert_document_by_url(
    collection, document: schema.Document
) -> schema.Document:
    """
    Upsert a document
    """
    logger.debug({
        **document.dict(),
        "url": str(document.url)
    })
    insert_result = await collection.insert_one({
        **document.dict(),
        "url": str(document.url)
    })
    document.id = insert_result.inserted_id
    logger.debug(document)
    return document 
    
    
async def upsert_document(stock: Stock, filing: Filing, url_base: str, collection):
    # construct a string for just the document's sub-path after the doc_dir
    # e.g. "sec-edgar-filings/AAPL/10-K/0000320193-20-000096/primary-document.pdf"
    logger.info("upsert_document")
    doc_path = Path(filing.file_path).relative_to(constants.DEFAULT_OUTPUT_DIR)
    url_path = url_base.rstrip("/") + "/" + str(doc_path).lstrip("/")
    doc_type = (
        schema.SecDocumentTypeEnum.TEN_K
        if filing.filing_type == "10-K"
        else schema.SecDocumentTypeEnum.TEN_Q
    )
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
    metadata_map: schema.DocumentMetadataMap = {
        schema.DocumentMetadataKeysEnum.SEC_DOCUMENT: jsonable_encoder(
            sec_doc_metadata.dict(exclude_none=True)
        )
    }
    doc = schema.Document(url=str(url_path), metadata_map=metadata_map)
    logger.debug("doc {}".format(doc))
    try:
        doc = await upsert_document_by_url(collection, doc)
        build_doc_id_to_index_map([doc])
    except DuplicateKeyError:
        logger.info(f"Duplicate key error: Document with URL {doc.url} already exists.")
    except Exception as e:
        logger.exception("An error occurred while inserting the document.")
        raise e  # Re-raise any other exception
    # pdf = await load_pdf(doc)
    


async def async_upsert_documents_from_filings(tickers, collection):
    """
    Upserts SEC documents into the database based on what has been downloaded to the filesystem.
    """
    logger.info("async_upsert_documents_from_filings")

    url_base = "https://{}.s3.amazonaws.com".format(constants.BUCKET_NAME)
    filings = get_available_filings(tickers)
    stocks_data = PyTickerSymbols()
    stocks_dict = get_stocks_by_symbol(stocks_data.get_all_indices())
    
    # print("Step 1",filings)
    for filing in tqdm(filings, desc="Upserting docs from filings"):
        if filing.symbol not in stocks_dict:
            print(f"Symbol {filing.symbol} not found in stocks_dict. Skipping.")
            continue
        stock = stocks_dict[filing.symbol]
        await upsert_document(stock, filing, url_base, collection)
        
        

async def ingest_dcoument_db(
        db_session: Tuple[AsyncIOMotorDatabase, object],
        tickers = List[str],
    ):

    # db, session = db_session
    async with db_session as (db, session): 

        collection = db.get_collection(constants.COLLECTION_NAME)
        await collection.create_index([("url", ASCENDING)], unique=True)
        await async_upsert_documents_from_filings(tickers, collection)


def build_doc_id_to_index_map(
    # llm,
    documents: List[schema.Document],
) -> Dict[str, VectorStoreIndex]:

    docstore=MongoDocumentStore.from_uri(uri=os.environ["MONGODB_URI"], db_name=constants.DB_NAME, namespace=constants.DOCSTORE_NAMESPACE)
    vector_store=MongoDBAtlasVectorSearch(
        # MongoClient(os.environ["MONGODB_URI"]), it will take from MONGODB_URI
        db_name=constants.DB_NAME, 
        collection_name = constants.VECTOR_COLLECTION_NAME,
        vector_index_name = constants.VECTOR_INDEX_NAME,
        relevance_score_fn="cosine"
    )
    index_store=MongoIndexStore.from_uri(uri=os.environ["MONGODB_URI"], db_name=constants.DB_NAME, namespace=constants.INDEX_NAMESPACE)
    
    # try:
    storage_context = StorageContext.from_defaults(
        docstore = docstore,
        vector_store = vector_store,
        index_store = index_store
    )

    try:
        # Now you can access the id attribute safely
        index_ids = [str(doc.id) for doc in documents]
        print(index_ids)  # This will print the list of ids
    
        indices = load_indices_from_storage(
            storage_context,
            index_ids=index_ids,
        )
        
        doc_id_to_index = dict(zip(index_ids, indices))
        
    except ValueError:
        print(
            "Failed to load indices from storage. Creating new indices. "
            "If you're running the seed_db script, this is normal and expected."
        )
        doc_id_to_index = {}
        
        for doc in documents:
            llama_index_docs = load_pdf(doc)
            storage_context.docstore.add_documents(llama_index_docs)
            index = VectorStoreIndex.from_documents(
                llama_index_docs,
                storage_context=storage_context,
                embed_model = LLM.embedding_model, # that's why they were passing service context here
                # transformation = node_parser
            )
            index.set_index_id(str(doc.id))
            doc_id_to_index[str(doc.id)] = index


    return doc_id_to_index

async def fetch_documents(
        db_session: Tuple[AsyncIOMotorDatabase, object]
    ) -> List[schema.Document]:

    async with db_session as (db, session): 

        collection = db.get_collection(constants.COLLECTION_NAME)
        return list(collection.find({}))
