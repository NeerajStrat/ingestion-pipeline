from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum
from typing import List, Optional, Dict, Any
from llama_index.core.callbacks.schema import CBEventType
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

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

class Base(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True
        from_attributes = True
        json_encoders = {
            ObjectId: str,
            Enum: lambda x: x.value  # Convert enums to string
        }

    def dict(self, *args, **kwargs):
        # Call the original dict method
        original_dict = super().dict(*args, **kwargs)
        # Convert nested enums to their string representations
        return self.serialize_enums(original_dict)

    def serialize_enums(self, data):
        if isinstance(data, list):
            return [self.serialize_enums(item) for item in data]
        elif isinstance(data, dict):
            return {key: self.serialize_enums(value) for key, value in data.items()}
        elif isinstance(data, Enum):
            return data.value  # Convert enum to its value
        return data  # Return other data as is

# Message Roles
class MessageRoleEnum(str, Enum):
    user = "user"
    assistant = "assistant"

# Message Status
class MessageStatusEnum(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"

# Message SubProcess Status
class MessageSubProcessStatusEnum(str, Enum):
    PENDING = "PENDING"
    FINISHED = "FINISHED"

# Extend Enums
additional_message_subprocess_fields = {
    "CONSTRUCTED_QUERY_ENGINE": "constructed_query_engine",
    "SUB_QUESTIONS": "sub_questions",
}

MessageSubProcessSourceEnum = Enum(
    "MessageSubProcessSourceEnum",
    [(event_type.name, event_type.value) for event_type in CBEventType] + list(additional_message_subprocess_fields.items()),
)

class ConversationDocument(Base):
    conversation_id: PyObjectId
    document_id: PyObjectId

class MessageSubProcess(Base):
    message_id: PyObjectId
    source: MessageSubProcessSourceEnum
    status: MessageSubProcessStatusEnum = MessageSubProcessStatusEnum.FINISHED
    metadata_map: Optional[Dict[str, Any]] = Field(default=None)

class Message(Base):
    conversation_id: PyObjectId
    content: str
    role: MessageRoleEnum
    status: MessageStatusEnum
    sub_processes: Optional[List[MessageSubProcess]] = []

class Conversation(Base):
    messages: Optional[List[Message]] = Field(default=None)
    conversation_documents: Optional[List[ConversationDocument]] = Field(default=None)

class Document(Base):
    url: HttpUrl
    metadata_map: Optional[Dict[str, Any]] = Field(default=None)
    conversations: Optional[List[Conversation]] = Field(default=None)

# Additional logging for debugging purposes
logger.info("Pydantic models are defined successfully.")

if __name__=="__main__":
    Message()
