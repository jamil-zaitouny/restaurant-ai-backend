import time
import asyncio
from typing import List, Dict

from app.api_helpers.customer_response_helpers import generate_tool_response
from app.model.db.indexing.db_search import search_database
from app.model.generators import search_terms_generator
from app.model.db.indexing import vector_db_search
from app.utilities.openai_helper import get_openai_api_key, get_pinecone_api_key, get_pinecone_environment

openai_api_key = get_openai_api_key()
pinecone_api_key = get_pinecone_api_key()


class ApiHelpers:

    @staticmethod
    async def search_index_and_database(
            index_name: str, account: str, table_name: str, search_terms: List[str]
    ):
        environment = get_pinecone_environment()
        index = vector_db_search.initialize_pinecone(
            pinecone_api_key, environment, index_name
        )

        async def get_vector_results():
            start_time = time.time()
            results = vector_db_search.main(
                pinecone_api_key, openai_api_key, environment, search_terms, index_name
            )
            print(f"Retrieved vector results: {time.time() - start_time:.2f} seconds")
            print(results)
            return results

        async def get_db_results():
            start_time = time.time()
            results = search_database(account, search_terms)
            print(f"Retrieved database results: {time.time() - start_time:.2f} seconds")
            print(results)
            return results

        vector_results, db_results = await asyncio.gather(
            get_vector_results(), get_db_results()
        )

        return vector_results, db_results

    @staticmethod
    def generate_response(
            query,
            history,
            credit_transaction_id,
            context,
            type,
            model_type,
            type_tool_id,
            instance_id,
            message_id,
            conversation_id,
    ):
        response = generate_tool_response(query, history, context, type, model_type, type_tool_id, instance_id, message_id, conversation_id)
        return response
