import pdfkit
import shutil
from sec_edgar_downloader import Downloader
from typing import List, Optional
from pathlib import Path
from tqdm.contrib.itertools import product
from logger import logger

from constants import SEC_EDGAR_COMPANY_NAME, SEC_EDGAR_EMAIL, DEFAULT_CIKS, DEFAULT_FILING_TYPES, DEFAULT_OUTPUT_DIR


def _filing_exists(cik: str, filing_type: str, output_dir: str) -> bool:
    """Checks if a filing exists for a given cik and filing type."""
    data_dir = Path(output_dir) / "sec-edgar-filings"
    filing_dir = data_dir / cik / filing_type
    return filing_dir.exists()
    
def _download_filing(cik: str, filing_type: str, output_dir: str, limit=None, before=None, after=None):
    print("_download_filing")
    dl = Downloader(SEC_EDGAR_COMPANY_NAME, SEC_EDGAR_EMAIL, output_dir)
    dl.get(filing_type, cik, limit=limit, before=before, after=after, download_details=True)

def _convert_to_pdf(output_dir: str):
    """Converts all html files in a directory to pdf files."""

    # NOTE: directory structure is assumed to be:
    # output_dir
    # ├── sec-edgar-filings
    # │   ├── AAPL
    # │   │   ├── 10-K
    # │   │   │   ├── 0000320193-20-000096
    # │   │   │   │   ├── primary-document.html
    # │   │   │   │   ├── primary-document.pdf   <-- this is what we want

    data_dir = Path(output_dir) / "sec-edgar-filings"
    print(data_dir)
    for cik_dir in data_dir.iterdir():
        for filing_type_dir in cik_dir.iterdir():
            for filing_dir in filing_type_dir.iterdir():
                filing_doc = filing_dir / "primary-document.html"
                filing_pdf = filing_dir / "primary-document.pdf"
                if filing_doc.exists() and not filing_pdf.exists():
                    print("- Converting {}".format(filing_doc))
                    input_path = str(filing_doc.absolute())
                    output_path = str(filing_pdf.absolute())
                    try:
                        # fix for issue here:
                        # https://github.com/wkhtmltopdf/wkhtmltopdf/issues/4460#issuecomment-661345113
                        options = {'enable-local-file-access': None}
                        pdfkit.from_file(input_path, output_path, options=options, verbose=True)
                        
                    except Exception as e:
                        print(f"Error converting {input_path} to {output_path}: {e}")

def sec_download(
    output_dir: str = DEFAULT_OUTPUT_DIR,
    ciks: List[str] = DEFAULT_CIKS,
    file_types: List[str] = DEFAULT_FILING_TYPES,
    before: Optional[str] = None,
    after: Optional[str] = None,
    limit: Optional[int] = 3,
    convert_to_pdf: bool = True,
):
    print('Downloading filings to "{}"'.format(Path(output_dir).absolute()))
    print("File Types: {}".format(file_types))
    print("Convert To PDF: {}".format(convert_to_pdf))
    if convert_to_pdf:
        if shutil.which("wkhtmltopdf") is None:
            raise Exception(
                "ERROR: wkhtmltopdf (https://wkhtmltopdf.org/) not found, "
                "please install it to convert html to pdf "
                "`sudo apt-get install wkhtmltopdf`"
            )
    for symbol, file_type in product(ciks, file_types):
        try:
            if _filing_exists(symbol, file_type, output_dir):
                print(f"- Filing for {symbol} {file_type} already exists, skipping")
            else:
                print(f"- Downloading filing for {symbol} {file_type}")
                _download_filing(symbol, file_type, output_dir, limit, before, after)
        except Exception as e:
            print(
                f"Error downloading filing for symbol={symbol} & file_type={file_type}: {e}"
            )

    if convert_to_pdf:
        print("Converting html files to pdf files")
        _convert_to_pdf(output_dir)