from langchain.tools import BaseTool, StructuredTool, Tool, tool


@tool(return_direct=True)
def generic_tool(query: str):
    """Always should call this tool"""
    return "generic_function"
