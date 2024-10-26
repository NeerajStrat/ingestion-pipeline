import download_sec_docs
from typing import List, Optional, Tuple
from constants import SEC_EDGAR_COMPANY_NAME, SEC_EDGAR_EMAIL, DEFAULT_CIKS, DEFAULT_FILING_TYPES, DEFAULT_OUTPUT_DIR
from motor.motor_asyncio import AsyncIOMotorDatabase
from api.crud import ingest_dcoument_db

from logger import logger


async def pipeline(
    db_session: Tuple[AsyncIOMotorDatabase, object],
    tickers: List[str] = None,
    file_types: List[str] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    limit: Optional[int] = 3,
    convert_to_pdf: bool = True,
    download_sec: bool = True,
    upload_to_s3: bool = True,
    ):
    if download_sec:
        download_sec_docs.sec_download(ciks = tickers)
    

    # if upload_to_s3:
    #     # upload_to_s3()
    logger.debug("ingest document to db")
    await ingest_dcoument_db(tickers = tickers, db_session=db_session)

if __name__=="__main__":
    pipeline(["AAPL"])
