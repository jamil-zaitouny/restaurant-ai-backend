# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements-2.txt

# Download NLTK data
RUN python -m nltk.downloader stopwords

# Make port 8214 available to the world outside this container
EXPOSE 8214


# Define environment variables
ENV NAME World
ENV OPENAI_API_KEY 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
ENV DB_HOST ownyourai.com
ENV DB_USER chatsys
ENV DB_PASSWORD pW6fWXSb^I1DCaZO1bQD%Vsx#I
ENV DB_DATABASE client_management
ENV DB_PORT 3306
ENV PINECONE_API_KEY e3b22e5c-352c-4e09-844e-52f952e49405
ENV PINECONE_INDEX_NAME ownyourai
ENV PINECONE_ENVIRONMENT us-east-1-aws
ENV DEEPGRAM_API_KEY ed4257320996d13bee1cbddf7be51de35cd07de2
ENV GROQ_API_KEY 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

# Run app.py when the container launches
CMD ["python", "-m", "gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8214", "--log-level=debug"]