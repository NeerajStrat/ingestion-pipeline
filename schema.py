"""
Pydantic Schemas for the API
"""
from pydantic import BaseModel, Field, validator, root_validator, Extra
from enum import Enum
from typing import List, Optional, Dict, Union, Any
from uuid import UUID
from bson import ObjectId
from datetime import datetime
from llama_index.core.schema import BaseNode, NodeWithScore
from llama_index.core.callbacks.schema import EventPayload
from llama_index.core.query_engine.sub_question_query_engine import SubQuestionAnswerPair
from llama_index.core.callbacks.schema import CBEventType
from models.db import (
    MessageRoleEnum,
    MessageStatusEnum,
    MessageSubProcessSourceEnum,
    MessageSubProcessStatusEnum,
)
from constants import DB_DOC_ID_KEY
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)



def build_uuid_validator(*field_names: str):
    return validator(*field_names)(lambda x: str(x) if x else x)


# Custom ObjectId handling
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, info):
        if not ObjectId.is_valid(v):
            raise ValueError('Invalid objectid')
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, schema, handler):
        schema.update(type='string')
        return schema

# 1
class Base(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, description="Unique identifier", alias="_id") # change because mongodb does not use uuid
    created_at: Optional[datetime] = Field(default=None, description="Creation datetime")
    updated_at: Optional[datetime] = Field(default=None, description="Update datetime")

    class Config:
        from_attributes = True
        exclude_none = True
        populate_by_name = True
        arbitrary_types_allowed = True
        extra = Extra.ignore  # Ignore extra fields that are not defined
        json_encoders = {ObjectId: str}

    def __init__(self, **data):
        # Initialize using BaseModel's initialization
        super().__init__(**data)

        # Remove attributes that were not provided
        if not self.id:
            del self.__dict__['id']
        if not self.created_at:
            del self.__dict__['created_at']
        if not self.updated_at:
            del self.__dict__['updated_at']

# 2
class BaseMetadataObject(BaseModel):
    class Config:
        from_attributes = True
        populate_by_name = True
        arbitrary_types_allowed = True

# 3
class Citation(BaseMetadataObject):
    document_id: PyObjectId
    text: str
    page_number: int
    score: Optional[float]

    @validator("document_id")
    def validate_document_id(cls, value):
        if value:
            return str(value)
        return value

    @classmethod
    def from_node(cls, node_w_score: NodeWithScore) -> "Citation":
        node: BaseNode = node_w_score.node
        page_number = int(node.source_node.metadata["page_label"])
        document_id = node.source_node.metadata[DB_DOC_ID_KEY]
        return cls(
            document_id=document_id,
            text=node.get_content(),
            page_number=page_number,
            score=node_w_score.score,
        )

# 4
class QuestionAnswerPair(BaseMetadataObject):
    """
    A question-answer pair that is used to store the sub-questions and answers
    """

    question: str
    answer: Optional[str]
    citations: Optional[List[Citation]] = None

    @classmethod
    def from_sub_question_answer_pair(
        cls, sub_question_answer_pair: SubQuestionAnswerPair
    ):
        if sub_question_answer_pair.sources is None:
            citations = None
        else:
            citations = [
                Citation.from_node(node_w_score)
                for node_w_score in sub_question_answer_pair.sources
                if node_w_score.node.source_node is not None
                and DB_DOC_ID_KEY in node_w_score.node.source_node.metadata
            ]
        citations = citations or None
        return cls(
            question=sub_question_answer_pair.sub_q.sub_question,
            answer=sub_question_answer_pair.answer,
            citations=citations,
        )

# 5
# later will be Union[QuestionAnswerPair, more to add later... ]
class SubProcessMetadataKeysEnum(str, Enum):
    SUB_QUESTION = EventPayload.SUB_QUESTION.value

# 6
# keeping the typing pretty loose here, in case there are changes to the metadata data formats.
SubProcessMetadataMap = Dict[Union[SubProcessMetadataKeysEnum, str], Any]

# 7
class MessageSubProcess(Base):
    message_id: PyObjectId
    source: MessageSubProcessSourceEnum
    status: MessageSubProcessStatusEnum
    metadata_map: Optional[SubProcessMetadataMap]

# 8
class Message(Base):
    conversation_id: PyObjectId
    content: str
    role: MessageRoleEnum
    status: MessageStatusEnum
    sub_processes: List[MessageSubProcess]
    
    @root_validator(pre=True)
    def remove_none_fields(cls, values):
        # Remove fields if not provided
        # if '_id' not in values:
        #     values.pop('id', None)  # Remove id if _id is not present
        if 'created_at' not in values:
            values.pop('created_at', None)  # Remove created_at if not provided
        if 'updated_at' not in values:
            values.pop('updated_at', None)  # Remove updated_at if not provided
        return values


# 9
class UserMessageCreate(BaseModel):
    content: str

# 10
class DocumentMetadataKeysEnum(str, Enum):
    """
    Enum for the keys of the metadata map for a document
    """

    SEC_DOCUMENT = "sec_document"

# 11
class SecDocumentTypeEnum(str, Enum):
    """
    Enum for the type of sec document
    """

    TEN_K = "10-K"
    TEN_Q = "10-Q"
    ANNUAL_REPORT="Annual Report"

# 12
class SecDocumentMetadata(BaseModel):
    """
    Metadata for a document that is a sec document
    """

    company_name: str
    company_ticker: Optional[str] = None
    doc_type: SecDocumentTypeEnum
    year: int
    quarter: Optional[int] = None
    accession_number: Optional[str] = None
    cik: Optional[str] = None
    registration_number: Optional[str] = None
    isin: Optional[str] = None
    period_of_report_date: Optional[datetime] = None
    filed_as_of_date: Optional[datetime] = None
    date_as_of_change: Optional[datetime] = None
    
    @root_validator(pre=True)
    def remove_none_fields(cls, values):
        # Remove fields if not provided
        if 'quarter' not in values:
            values.pop('quarter', None)  # Remove id if _id is not present
        if 'accession_number' not in values:
            values.pop('accession_number', None)  # Remove id if _id is not present
        if 'cik' not in values:
            values.pop('cik', None)  # Remove id if _id is not present
        if 'registration_number' not in values:
            values.pop('registration_number', None)  # Remove id if _id is not present
        if 'cik' not in values:
            values.pop('cik', None)  # Remove id if _id is not present
        if 'period_of_report_date' not in values:
            values.pop('period_of_report_date', None)  # Remove id if _id is not present
        if 'filed_as_of_date' not in values:
            values.pop('filed_as_of_date', None)  # Remove created_at if not provided
        if 'date_as_of_change' not in values:
            values.pop('date_as_of_change', None)  # Remove updated_at if not provided
        return values

# 13
DocumentMetadataMap = Dict[Union[DocumentMetadataKeysEnum, str], Any]

# 14
class Document(Base):
    url: str
    metadata_map: Optional[DocumentMetadataMap] = None

    @root_validator(pre=True)
    def remove_none_fields(cls, values):
        # Remove fields if not provided
        if values is None:
            return values
        if '_id' not in values:
            values.pop('id', None)  # Remove id if _id is not present
        if 'created_at' not in values:
            values.pop('created_at', None)  # Remove created_at if not provided
        if 'updated_at' not in values:
            values.pop('updated_at', None)  # Remove updated_at if not provided
        return values

# 15

class Conversation(Base):
    messages: Optional[List[Message]] = None
    documents: Optional[List[Document]] = None

    class Config:
        json_encoders = {
            ObjectId: str
        }

    @root_validator(pre=True)
    def remove_none_fields(cls, values):
        if values is None:
            return values
        # logging.info("values %s",values)
        # Remove fields if not provided
        if '_id' not in values:
            values.pop('id', None)  # Remove id if _id is not present
        if 'created_at' not in values:
            values.pop('created_at', None)  # Remove created_at if not provided
        if 'updated_at' not in values:
            values.pop('updated_at', None)  # Remove updated_at if not provided
        return values


# 16
class ConversationCreate(BaseModel):
    document_ids: Optional[List[PyObjectId]] = None


if __name__ == "__main__":
    # print(Document(_id= ObjectId("66f77e3bbae8b95b9c053482"), url="http://www.google.com"))
    # print(SecDocumentMetadata())
    # print(UserMessageCreate(content = "hello"))
    print(
        Message( 
            id=ObjectId(),
            conversation_id = ObjectId(),
            role="assistant",
            status = "PENDING",
            content = "",
            sub_processes = []
        ))
