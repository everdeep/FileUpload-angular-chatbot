#!/bin/bash
export FLASK_APP=./src/main.py
export FLASK_ENV=development
source $(pipenv --venv)/bin/activate

# Start postgres server instance through docker
docker run -p 5432:5432 -e POSTGRES_DB=chatbot -e POSTGRES_PASSWORD=chatbot-secret123 -d postgres

# start backend
flask run -h 0.0.0.0
