import json
import logging
from pathlib import Path
from typing import Tuple, List

import faiss

from utils.embedding import get_embedding
from utils.chunking import chunk_text
import numpy as np

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

BASE_DIR = Path(__file__).parent.parent
INDEX_DIR = BASE_DIR / "faiss_store"
INDEX_FILE = INDEX_DIR / "index.faiss"
MAPPING_FILE = INDEX_DIR / "chunk_mapping.json"
DATA_FILE = BASE_DIR / "data" / "founder_story.txt"
EMBEDDING_DIM = 1536
INDEX_TYPE = "FlatL2"

logging.basicConfig(
	level=logging.INFO,
	format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Helper
# --------------------------------------------------------------------------- #

Chunk = str


def _ensure_dir(path: Path) -> None:
	"""Create a directory if it doesn't exist."""
	path.mkdir(exist_ok=True, parents=True)


def _create_index(embeddings: np.ndarray) -> faiss.Index:
	"""Create the FAISS index based on the configured type."""
	if INDEX_TYPE == "FlatL2":
		index = faiss.IndexFlatL2(EMBEDDING_DIM)
	else:
		raise ValueError(f"Invalid index type: {INDEX_TYPE}")
	index.add(embeddings.astype("float32"))  # type: ignore
	return index


def load_faiss_index(api_key: str | None = None) -> Tuple[faiss.Index, List[Chunk]]:
	"""
	    Load or create FAISS index and chunk mapping.
	Parameters
	----------
	api_key : str
	    The api key for the embedding provider.

	Returns
	-------
	index : faiss.Index
	    Index for the FAISS search.
	mapping : list[Chunks]
		mapping of chunks to their index in the FAISS index.

	Raises
	------
	ValueError
	    If *chunks* do not match the number of embeddings.
	    If no chunks are found in the data file.
	    If chunk embedding dimensions don't match with index embedding dimensions.
	FileNotFoundError
		If the data file does not exist.
	"""
	try:
		if INDEX_FILE.exists() and MAPPING_FILE.exists():
			logger.info("Loading existing FAISS index.")
			index = faiss.read_index(str(INDEX_FILE))
			with open(MAPPING_FILE, "r", encoding="utf-8") as f:
				mapping: List[Chunk] = json.load(f)
			if len(mapping) != index.ntotal:
				raise ValueError(
					"Number of chunks in the mapping does not match the number of chunks in the index."
				)
			return index, mapping

		if not DATA_FILE.exists():
			raise FileNotFoundError(f"Data file {DATA_FILE} does not exist.")

		logger.info("Creating new FAISS index.")
		text = DATA_FILE.read_text(encoding="utf-8")
		chunks = chunk_text(text)
		if not chunks:
			raise ValueError("No chunks found in the data file.")

		mapping: List[Chunk] = []
		embeddings: List[np.ndarray] = []

		for chunk in chunks:
			emb = get_embedding(chunk, api_key=api_key)
			emb_arr = np.array(emb, dtype="float32")
			if emb_arr.shape[0] != EMBEDDING_DIM:
				raise ValueError(
					f"Embedding dimension mismatch for chunk '{chunk}'. "
					f"Expected {EMBEDDING_DIM} dimensions, got {emb_arr.shape[0]}."
				)
			embeddings.append(emb_arr)
			mapping.append(chunk)
		mat = np.vstack(embeddings)
		index = _create_index(mat)

		_ensure_dir(INDEX_DIR)
		faiss.write_index(index, str(INDEX_FILE))
		with open(MAPPING_FILE, "w", encoding="utf-8") as f:
			json.dump(mapping, f, indent=2, ensure_ascii=False)
		return index, mapping
	except Exception as e:
		logger.error(f"Error loading FAISS index: {e}")
		raise


def retrieve_top_k(
	query: str,
	index: faiss.Index,
	mapping: List[Chunk],
	k: int = 3,
	api_key: str | None = None,
) -> List[Chunk]:
	"""
	Retrieve top-k chunks for a given query.
	Parameters
	----------
	query : str
	    The user question or prompt.
	index : faiss.Index
	    Pre‑built FAISS index.
	mapping : list[str]
	    Parallel list of chunks that were indexed.
	k : int, default=3
	    Number of results to return.
	api_key : str | None, default=None
	    Optional key for the embedding provider.

	Returns
	-------
	list[str]
	    The `k` most relevant chunks (ordered by similarity).

	Raises
	------
	ValueError
	    If *query* is empty or not a string.
	    If *k* is less than 1.
	    If query embedding dimensions don't match with index embedding dimensions.
	"""
	if not query or not isinstance(query, str):
		raise ValueError("Query must be a non-empty string.")
	if k <= 0:
		raise ValueError("k must be a positive integer.")
	k = min(k, len(mapping))

	query_embedding = np.asarray(get_embedding(query, api_key=api_key), dtype="float32")
	if query_embedding.shape[0] != EMBEDDING_DIM:
		raise ValueError(
			f"Embedding dimension mismatch for query '{query}'. "
			f"Expected {EMBEDDING_DIM} dimensions, got {query_embedding.shape[0]}."
		)
	distance, indices = index.search(np.expand_dims(query_embedding, axis=0), k=k)  # type: ignore
	valid_indices = [i for i in indices[0] if i >= 0]
	return [mapping[i] for i in valid_indices]
