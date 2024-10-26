import os
from llama_index.llms.openai import OpenAI
import constants 
# from llama_index.question_gen.guidance import GuidanceQuestionGenerator
from llama_index.core.node_parser import SentenceSplitter
from guidance.models import OpenAI as GuidanceOpenAI
from llama_index.embeddings.openai import (
    OpenAIEmbedding,
    OpenAIEmbeddingMode,
    OpenAIEmbeddingModelType
)
# question_gen = GuidanceQuestionGenerator.from_defaults(
#     guidance_llm=GuidanceOpenAI("text-davinci-003"), verbose=False
# )

class LLM:
    guidanceLLM = GuidanceOpenAI("gpt-4")

    llm = OpenAI(
        temperature=0,
        model=constants.OPENAI_TOOL_LLM_NAME,
        streaming=False,
        api_key=os.environ["OPENAI_API_KEY"],
    )
    chat_llm = OpenAI(
        temperature=0,
        model=constants.OPENAI_TOOL_LLM_NAME,
        streaming=True,
        api_key=os.environ["OPENAI_API_KEY"],
    )

    embedding_model = OpenAIEmbedding(
        mode=OpenAIEmbeddingMode.SIMILARITY_MODE,
        model_type=OpenAIEmbeddingModelType.TEXT_EMBED_ADA_002,
        api_key=os.environ["OPENAI_API_KEY"],
    )
    # Use a smaller chunk size to retrieve more granular results
    node_parser = SentenceSplitter.from_defaults(
        chunk_size=constants.NODE_PARSER_CHUNK_SIZE,
        chunk_overlap=constants.NODE_PARSER_CHUNK_OVERLAP,
        # callback_manager=callback_manager,
    )
