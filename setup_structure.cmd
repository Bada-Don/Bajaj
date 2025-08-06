@echo off
REM Change to the root folder - assuming 'search-api' exists in current dir
cd search-api

REM Create subdirectories
mkdir services
mkdir models

REM Create empty files
type nul > app.py
type nul > config.py
type nul > requirements.txt
type nul > Dockerfile
type nul > .env.example

REM Create service files
cd services
type nul > __init__.py
type nul > document_processor.py
type nul > embedding_service.py
type nul > search_service.py
cd ..

REM Create model files
cd models
type nul > __init__.py
type nul > schemas.py
cd ..

echo Project structure created successfully in search-api\
