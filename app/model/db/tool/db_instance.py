from langchain.schema import SystemMessage

from app.model.db.db_base import fetch_sql_query


def get_instance_primers(instance_id):
    query = "SELECT agent_primer_before, agent_primer_after, llm_model  FROM instance WHERE id = %s"
    params = (instance_id,)

    result = fetch_sql_query(query, params)

    # If there's no result, return None
    if not result:
        return None

    # If there are results, return the first one (there should only be one since id is unique)
    agent_primer_before, agent_primer_after, llm_model = result[0]

    return SystemMessage(content=agent_primer_before), SystemMessage(content=agent_primer_after), llm_model


if __name__ == "__main__":
    print(get_instance_primers("20"))
