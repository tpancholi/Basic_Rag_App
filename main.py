import os
import streamlit as st
from dotenv import load_dotenv, find_dotenv

from utils.completion import generate_response
from utils.prompt import build_prompt
from utils.retrieval import load_faiss_index, retrieve_top_k

load_dotenv(find_dotenv())

api_key = os.getenv("EURI_API_KEY")

st.title("Basic RAG App")
st.write("Ask questions about Euron Founder Sudhanshu Kumar")

query = st.text_input("Enter your query here:")

if query:
	index, chunk_mapping = load_faiss_index(api_key=api_key)
	top_chunks = retrieve_top_k(query, index, chunk_mapping, k=3, api_key=api_key)
	prompt = build_prompt(top_chunks, query)
	answer = generate_response(prompt, api_key=api_key)

	st.subheader("Answer:")
	st.write(answer)

	with st.expander("See the context"):
		for chunk in top_chunks:
			st.markdown(f"- {chunk}")
