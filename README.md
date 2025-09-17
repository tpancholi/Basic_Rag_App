# Basic Rag App
This app is created without use of any llm framework.

## Library / Packages used
- Numpy (for vector operations)
- FAISS-CPU (as vector search engine)
- typing (for type hinting)
- python-dotenv (for loading environment variables)

## How to install
- run command `pip install -r requirements.txt` or `uv venv && uv sync`
- rename `env.sample` file in root directory to `.env`
- update `.env` file with your own api key values
- run command `uv run streamlit run app.py`
- open url in browser `http://localhost:8501`