FROM python:3.11-slim-bookworm

WORKDIR /app

# Install Node.js and npm for running MCP agents that might require them
RUN apt-get update &&     apt-get install -y ca-certificates curl &&     curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&     apt-get install -y nodejs

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
