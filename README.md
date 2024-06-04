# Local Deployment Runbook for RAG Application

## Overview

This runbook provides steps to deploy the RAG application locally using Docker Compose.

### Downloading llama-2 quantized model
You can retrieve the llama-2-7b-chat.Q2_K.gguf from [here](https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF).
Next, create the `model/` folder in the root directory of the project.
Place the model in the `model/` folder once downloaded.

### Setting RAG documents
Place your `.txt` files for the RAG system in the `documents/` folder.

## Prerequisites (Docker Build)

- Docker

## Step 1: Setup with Docker Compose
1. Build the Docker images:
```bash
docker-compose build
```
2. Start the services:
```bash
docker-compose up
```

## Prerequisites (Local virenv)
- Docker
- Python 3.12

1. Create virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
```bash
source venv/bin/activate
```

3. Install the dependencies:
```bash
pip install -r requirements.txt
```

4. Run redis in docker:
```bash
docker compose up redis
```

5. Run the python applications:
```bash
python view_service.py & python model_service.py
```
