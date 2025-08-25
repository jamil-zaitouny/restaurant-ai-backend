import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import csv
import logging
from io import StringIO
from typing import List, Optional

import tiktoken
from fastapi import APIRouter
from fastapi import Path
from fastapi import UploadFile, Form, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String
from sqlalchemy import ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from app.model.db.db_base import load_database
from app.model.db.tool.db_category_tool import insert_category_item, insert_chunk_item, get_all_menu_tools_for_tool
from app.model.db.tool.db_instance_tool import insert_or_update_instance_tool
from app.model.db.tool.db_location_tool import get_instance_id_from_location_tool
from app.model.db.wordpress.db_menu import insert_menu_tool
from app.model.db.wordpress.db_tool import insert_tool

logger = logging.getLogger(__name__)

tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")
Base = declarative_base()


class CategoryToolInput(BaseModel):
    id: Optional[int]
    category_name: Optional[str]
    agent_name: Optional[str]
    agent_description: Optional[str]
    filter_primer_before: Optional[str]
    filter_primer_after: Optional[str]
    response_primer_before: Optional[str]
    response_primer_after: Optional[str]
    file: Optional[bytes]


class CategoryToolOutput(BaseModel):
    category_name: Optional[str]
    agent_name: Optional[str]
    agent_description: Optional[str]
    filter_primer_before: Optional[str]
    filter_primer_after: Optional[str]
    response_primer_before: Optional[str]
    response_primer_after: Optional[str]


router = APIRouter()


class MenuTool(Base):
    __tablename__ = 'menu_tool'
    id = Column(Integer, primary_key=True)
    instance_tool_id = Column(Integer)
    response_primer_before = Column(String)
    response_primer_after = Column(String)
    filter_primer_before = Column(String)
    filter_primer_after = Column(String)
    category_name = Column(String)
    chunks = relationship("Chunk", back_populates="menu_tool")


class Chunk(Base):
    __tablename__ = 'chunk'
    id = Column(Integer, primary_key=True)
    menu_tool_id = Column(Integer, ForeignKey('menu_tool.id'))
    chunk_data = Column(String)
    menu_tool = relationship("MenuTool", back_populates="chunks")


def clean_page_content(page_content):
    print("Cleaning page content...")
    lines = page_content.split("\n")
    clean_lines = [line for line in lines if line.strip()]
    return ' '.join(clean_lines)


async def process_csv_file(file: UploadFile, menu_tool_id: int):
    print("Processing CSV file...")
    content = await file.read()
    content_str = content.decode('utf-8-sig')
    csv_reader = csv.DictReader(StringIO(content_str))
    inserted_ids = []  # A list to store all the inserted idsfor row in csv_reader:

    for row in csv_reader:
        if all(val in (None, '') for val in row.values()):
            continue
        inserted_id = insert_category_item(menu_tool_id, row)
        print(f"inserted_id: {inserted_id}")  # print inserted id for each row
        inserted_ids.append(inserted_id)

    return inserted_ids  # make sure to return inserted_ids


def count_tokens(text):
    print(f"Counting tokens for: {text}")
    return len(tokenizer.encode(text))


def custom_split_text(row, headers_included):
    formatted_items = []
    for key, value in row.items():
        if key != 'id':
            if value is None or value == '':
                formatted_items.append('')  # append empty string for blanks
            else:
                if not headers_included:
                    formatted_items.append(f'{key.replace("_", " ").title()}: {value}')
                else:
                    formatted_items.append(f'{value}')
    return ','.join(formatted_items)  # join items with commas


def process_documents(documents, max_chunk_tokens=3000):
    print("Processing documents...")
    current_chunk = []
    current_chunk_tokens = 0
    chunks = []
    headers_included = False

    for doc in documents:
        cleaned_text = clean_page_content(custom_split_text(doc, headers_included))
        text_tokens = count_tokens(cleaned_text)

        if not headers_included:
            # Calculate additional tokens only when headers are to be included
            additional_tokens = sum([count_tokens(key) + 1 for key in doc.keys() if key != 'id' and doc[key] is not None and doc[key] != ''])
            potential_chunk_tokens = current_chunk_tokens + text_tokens + additional_tokens
        else:
            potential_chunk_tokens = current_chunk_tokens + text_tokens

        if potential_chunk_tokens > max_chunk_tokens:
            chunks.append('\n'.join(current_chunk))  # join rows by newlines
            current_chunk = []
            current_chunk_tokens = 0
            headers_included = False  # reset headers_included for each new chunk

        if not headers_included:
            # Write headers to the chunk
            headers = [key.replace("_", " ").title() for key in doc.keys() if key != 'id']
            header_line = ','.join(headers)
            current_chunk.append(header_line)
            current_chunk_tokens += additional_tokens
            headers_included = True

        current_chunk.append(cleaned_text)
        current_chunk_tokens += text_tokens

    if current_chunk:
        chunks.append('\n'.join(current_chunk))  # join remaining rows by newlines

    return chunks


@router.post("/category_tool/")
async def post_category_tool(
        id: int = Form(...),
        category_name: Optional[str] = Form(None),
        agent_name: Optional[str] = Form(None),
        agent_description: Optional[str] = Form(None),
        filter_primer_before: Optional[str] = Form(None),
        filter_primer_after: Optional[str] = Form(None),
        response_primer_before: Optional[str] = Form(None),
        response_primer_after: Optional[str] = Form(None),
        llm_model: Optional[str] = Form(None),
        file: UploadFile = File(...),
):
    try:
        print("Starting post_category_tool...")

        # Removed insert_tool and get_instance_id_from_location_tool
        tool_id = 2  # static tool_id for this endpoint

        instance_tool_id, _ = insert_or_update_instance_tool(
            id,
            tool_id,
            agent_name,
            agent_description,
            True,
            "Initial state of instance tool is on",
            llm_model
        )
        print("Inserted instance_tool.")
        menu_tool_id = insert_menu_tool(
            tool_id,
            response_primer_before,
            response_primer_after,
            filter_primer_before,
            filter_primer_after,
            category_name,
            instance_tool_id  # instance_tool_id included as a new parameter
        )
        # print("Inserted menu_tool, got menu_tool_id.")
        inserted_ids = await process_csv_file(file, menu_tool_id)
        # print("Processed CSV file.")

        db = load_database()
        print("Loaded database.")
        cursor = db.cursor()

        documents = []
        for inserted_id in inserted_ids:
            print(f"inserted_id: {inserted_id}")
            cursor.execute("SELECT * FROM category_items WHERE id = %s", (inserted_id,))
            documents.extend(cursor.fetchall())
            print("Fetched all related documents from cursor.")

        # Convert tuples to dictionaries
        fieldnames = [desc[0] for desc in cursor.description]
        documents = [dict(zip(fieldnames, doc)) for doc in documents]
        # print("Converted tuples to dictionaries.")

        chunks = process_documents(documents, max_chunk_tokens=2500)
        # print("Processed documents.")

        for chunk in chunks:
            insert_chunk_item(menu_tool_id, str(chunk))
            print(f"Inserted chunk_item for chunk: {chunk}")
            db.commit()

        print("Committed changes to DB.")
        return JSONResponse(status_code=200, content={"message": "Successfully created category tool"})
    except Exception as exception:
        print(f"An error occurred: {str(exception)}")
        logger.error(f"An error occurred: {str(exception)}")
        raise HTTPException(status_code=500, detail="An error occurred while processing your request.")


@router.get("/category_tool/{instance_id}", response_model=List[CategoryToolOutput])
async def get_all_category_tools_endpoints(instance_id: int = Path(..., description="The ID of the instance of the tool")):
    print("Getting all category tools...")
    category_tools = get_all_menu_tools_for_tool(instance_id)

    # Convert tuples to LocationToolOutput objects
    category_tools = [
        CategoryToolOutput(
            response_primer_before=row[0],
            response_primer_after=row[1],
            filter_primer_before=row[2],
            filter_primer_after=row[3],
            category_name=row[4],
            agent_name=row[5],
            agent_description=row[6],
        ) for row in category_tools
    ]

    return category_tools


# Test endpoint
def test_post_category_tool():
    url = "http://localhost:8081/category_tool/"
    data = {
        "id": 1,
        "category_name": "Test Category",
        "agent_name": "Test Agent",
        "agent_description": "This is a test agent",
        "filter_primer_before": "Test filter primer before",
        "filter_primer_after": "Test filter primer after",
        "response_primer_before": "Test response primer before",
        "response_primer_after": "Test response primer after",
    }
    files = {'file': open("C:/Users/BDru/Downloads/cactus + headers.csv", 'rb')}
    response = requests.post(url, data=data, files=files)
    print(response.json())


if __name__ == "__main__":
    test_post_category_tool()
