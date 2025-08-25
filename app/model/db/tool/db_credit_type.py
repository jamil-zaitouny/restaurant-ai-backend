# app/model/db/tool/db_credit_type.py

from app.model.db.db_base import fetch_sql_query
import logging

logger = logging.getLogger(__name__)

def get_credit_type_by_search(search_criteria):
    """
    Get credit type based on search criteria with better error handling
    """
    try:
        # Initialize query and parameters
        base_query = "SELECT * FROM credit_type WHERE"
        params = []

        # Add each search criteria to the query
        for field, value in search_criteria.items():
            base_query += f" {field} = %s AND"
            params.append(value)

        # Remove the trailing 'AND'
        base_query = base_query.rstrip(' AND')
        
        logger.debug(f"Executing credit type query: {base_query} with params: {params}")
        
        # Execute the query and fetch the results
        results = fetch_sql_query(base_query, params)
        
        if not results:
            logger.warning(f"No credit type found for criteria: {search_criteria}")
            # Return default credit type or raise specific exception
            default_credit_type = get_default_credit_type()
            if default_credit_type:
                return [default_credit_type]
            raise ValueError(f"No credit type found for criteria: {search_criteria}")
            
        logger.debug(f"Found credit type results: {results}")
        return results

    except Exception as e:
        logger.error(f"Error in get_credit_type_by_search: {str(e)}")
        raise

def get_default_credit_type():
    """Get default credit type when specific type not found"""
    query = "SELECT * FROM credit_type WHERE name = 'default' LIMIT 1"
    results = fetch_sql_query(query)
    return results[0] if results else None