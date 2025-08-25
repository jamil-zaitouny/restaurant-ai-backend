from datetime import datetime
import traceback
from typing import Any, Dict, List, Union, Optional
from uuid import UUID

from langchain.llms.openai import OpenAI
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import LLMResult
from app.model.db.frontend.db_logging import log_token_usage, get_client_id_from_instance
from app.utilities.usage_billings_helper import log_inbound_message, log_outbound_message, log_gpt_usages


class TokenLoggingCallback(BaseCallbackHandler):
    def __init__(self, credit_transaction_id, type, model_type, message_id, conversation_id, tool_type_id,
                 tool_type_table, name, instance_id):
        self.start = None
        self.end = None
        self.credit_transaction_id = credit_transaction_id
        self.llm = OpenAI()
        self.tokens_completion = ""
        self.type = type
        self.user_query = ""
        self.model_type = model_type
        self.message_id = message_id
        self.conversation_id = conversation_id
        self.tool_type_id = tool_type_id
        self.tool_type_table = tool_type_table
        self.name = name
        self.instance_id = instance_id
        print(f"Initialized TokenLoggingCallback with model_type: {model_type}")


    def on_llm_start(
            self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Run when LLM starts running."""
        self.start = datetime.now()
        self.user_query = str(prompts)
        print(f"onllmstart serialized:{serialized} & prompts:{prompts}")

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Run on new LLM token. Only available when streaming is enabled."""

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        self.end = datetime.now()
        
        # Add defensive programming
        try:
            if not response or not response.llm_output or 'token_usage' not in response.llm_output:
                print(f"Warning: Missing token usage data in response: {response}")
                prompt_tokens = 0
                completion_tokens = 0
            else:
                prompt_tokens = response.llm_output["token_usage"].get('prompt_tokens', 0)
                completion_tokens = response.llm_output["token_usage"].get("completion_tokens", 0)

            generations_str = str(response.generations) if response and response.generations else "No generations"
            
            usage_id = log_token_usage(
                generations_str,
                self.user_query,
                prompt_tokens,
                completion_tokens,
                self.start,
                self.end,
                self.type,
                self.tool_type_id,
                self.tool_type_table,
                self.message_id,
                self.conversation_id
            )

            print(f"Logged token usage - Usage ID: {usage_id}, Prompt Tokens: {prompt_tokens}, Completion Tokens: {completion_tokens}")

            log_gpt_usages(
                usage_id,
                self.credit_transaction_id,
                self.model_type,
                completion_tokens,
                prompt_tokens,
                self.name,
                get_client_id_from_instance(self.instance_id)
            )

        except Exception as e:
            print(f"Error in TokenLoggingCallback.on_llm_end: {str(e)}")
            traceback.print_exc()

    def on_llm_error(
            self,
            error: Union[Exception, KeyboardInterrupt],
            *,
            run_id: UUID,
            parent_run_id: Optional[UUID] = None,
            **kwargs: Any,
    ) -> Any:
        print(error)
