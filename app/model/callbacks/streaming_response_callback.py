# app/model/callbacks/streaming_response_callback.py

"""Callback Handler streams to stdout on new llm token."""
from datetime import datetime
from typing import Any, Dict, List, Union
import logging
import traceback
from queue import Queue

from langchain.llms.openai import OpenAI
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import AgentAction, AgentFinish, LLMResult

from app.model.db.frontend.db_logging import log_token_usage, get_client_id_from_instance
from app.utilities.usage_billings_helper import log_inbound_message, log_outbound_message, log_gpt_usages

logger = logging.getLogger(__name__)


class StreamingResponseCallback(BaseCallbackHandler):
    """Callback handler for streaming. Only works with LLMs that support streaming."""

    def __init__(self, queue: Queue, credit_transaction_id: int, model_type: str, 
                 message_id: str, conversation_id: str, tool_type_id: int,
                 tool_type_table: str, name: str, instance_id: str):
        self.initial_query = None
        self.start = None
        self.end = None
        self.queue = queue
        self.content_sent = ""
        self.credit_transaction_id = credit_transaction_id
        self.llm = OpenAI()
        self.tokens_prompt = 0
        self.tokens_completion = 0
        self.tool_type_id = tool_type_id
        self.tool_type_table = tool_type_table
        self.message_id = message_id
        self.conversation_id = conversation_id
        self.model_type = model_type
        self.name = name
        self.instance_id = instance_id
        logger.debug(f"Initialized StreamingResponseCallback with model_type: {model_type}")

    def on_llm_start(
            self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Run when LLM starts running."""
        try:
            self.initial_query = str(prompts)
            self.tokens_prompt += self.llm.get_num_tokens("".join(prompts))
            self.start = datetime.now()
            logger.debug(f"LLM Start - Initial tokens: {self.tokens_prompt}")
        except Exception as e:
            logger.error(f"Error in on_llm_start: {str(e)}")
            traceback.print_exc()

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Run on new LLM token. Only available when streaming is enabled."""
        try:
            self.content_sent += token
            self.queue.put(token)
            self.tokens_completion += self.llm.get_num_tokens(token)
            logger.debug(f"New token received, total completion tokens: {self.tokens_completion}")
        except Exception as e:
            logger.error(f"Error in on_llm_new_token: {str(e)}")
            traceback.print_exc()

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Run when LLM ends running."""
        try:
            self.queue.put("end_message_id:front_end")
            self.queue.put("end_message_id:back_end")
            self.end = datetime.now()

            logger.debug(f"LLM End - Final tokens - Prompt: {self.tokens_prompt}, Completion: {self.tokens_completion}")

            usage_id = log_token_usage(
                self.content_sent,
                self.initial_query,
                self.tokens_prompt,
                self.tokens_completion,
                self.start,
                self.end,
                "streaming response",
                self.tool_type_id,
                self.tool_type_table,
                self.message_id,
                self.conversation_id
            )

            client_id = get_client_id_from_instance(self.instance_id)
            log_inbound_message(usage_id, self.credit_transaction_id, client_id)
            log_outbound_message(usage_id, self.credit_transaction_id, self.model_type, client_id)
            log_gpt_usages(
                usage_id,
                self.credit_transaction_id,
                self.model_type,
                self.tokens_completion,
                self.tokens_prompt,
                self.name,
                client_id
            )

            logger.debug(f"Successfully logged all usage data. Usage ID: {usage_id}")

        except Exception as e:
            logger.error(f"Error in on_llm_end: {str(e)}")
            traceback.print_exc()

    def on_llm_error(
            self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        """Run when LLM errors."""
        logger.error(f"LLM Error: {str(error)}")
        traceback.print_exc()

    def on_chain_start(
            self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> None:
        """Run when chain starts running."""
        print(f"Chain Start - Inputs: {str(inputs)[:100]}...")  # Log first 100 chars of inputs

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Run when chain ends running."""
        print(f"Chain End - Outputs: {str(outputs)[:100]}...")  # Log first 100 chars of outputs

    def on_chain_error(
            self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        """Run when chain errors."""
        print(f"Chain Error: {str(error)}")

    def on_tool_start(
            self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        """Run when tool starts running."""
        print(f"Tool Start - Input: {input_str[:100]}...")  # Log first 100 chars of input

    def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any:
        """Run on agent action."""
        print(f"Agent Action: {str(action)}")

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Run when tool ends running."""
        print(f"Tool End - Output: {output[:100]}...")  # Log first 100 chars of output

    def on_tool_error(
            self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        """Run when tool errors."""
        print(f"Tool Error: {str(error)}")

    def on_text(self, text: str, **kwargs: Any) -> None:
        """Run on arbitrary text."""
        print(f"Text: {text[:100]}...")  # Log first 100 chars of text

    def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> None:
        """Run on agent end."""
        print(f"Agent Finish: {str(finish)}")