import requests
import numpy as np
from typing import Optional, Union
from requests.exceptions import RequestException, HTTPError
import logging

logging.basicConfig(
	level=logging.INFO,
	format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)
# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
DEFAULT_EMBEDDING_URL = "https://api.euron.one/api/v1/euri/embeddings"


# --------------------------------------------------------------------------- #
# Helper
# --------------------------------------------------------------------------- #
def _ensure_api_key(api_key: Optional[str]) -> str:
	"""
	Validate that an API key is available.
	"""
	if not api_key:
		raise ValueError("An API key must be supplied via the `api_key` argument.")
	return api_key


def get_embedding(
	text: str,
	model: str = "text-embedding-3-small",
	api_key: Optional[str] = None,
	url: str = DEFAULT_EMBEDDING_URL,
	timeout: float = 10.0,
) -> Union[np.ndarray, None]:
	"""
	Retrieve a dense vector representation for *text*.
	Parameters
	----------
	text : str
	    The document or sentence to embed.
	model : str, default ``"text-embedding-3-small"``
	    The name of the embedding model requested from the API.
	api_key : str, optional
	    The bearer token used to authenticate with the embedding service.
	    If omitted, the function will raise ``ValueError``.
	url : str, optional
	    Full endpoint for the embedding API.  The default matches
	    the official Euron One endpoint.
	timeout : float, optional
	    Seconds to wait for a response before raising
	    :class:`requests.exceptions.Timeout`.

	Returns
	-------
	numpy.ndarray
	    A 1‑D array containing the embedding vector.

	Raises
	------
	ValueError
	    If *api_key* is not supplied.
	    If *text* is empty or not a string.
	    If the response JSON cannot be parsed.
	    If the response is not valid JSON.
	    If the response JSON does not contain the *data* keys.

	HTTPError
	    If the server returns a non‑200 status code.
	RequestException
	    For network‑level errors (connection, timeout, DNS, etc.).
	KeyError
	    If the response JSON does not contain the expected keys.

	Examples
	--------
	>>> embed = get_embedding("Hello world!", api_key="sk-…")
	>>> embed.shape
	(1536,)
	"""
	if not len(text) > 0 or not isinstance(text, str):
		raise ValueError("Text must be a non-empty string.")

	api_key = _ensure_api_key(api_key)
	headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
	payload = {"input": text, "model": model}

	try:
		response = requests.post(url, headers=headers, json=payload, timeout=timeout)
		response.raise_for_status()
	except HTTPError as err:
		status = getattr(err.response, "status_code", "unknown")
		raise HTTPError(
			f"Error while embedding API request with (status {status}): {err}"
		) from err
	except RequestException as err:
		raise RequestException(
			f"Network Error while connecting to embedding API: {err}"
		) from err
	try:
		data = response.json()
	except ValueError as err:
		raise ValueError(f"Failed to parse JSON response: {err}.") from err
	if not isinstance(data, dict):
		raise ValueError(f"Invalid JSON response object, got type: {type(data)}.")

	if (
		"data" not in data
		or not isinstance(data["data"], list)
		or len(data["data"]) == 0
	):
		raise ValueError("Response does not contain any data.")

	try:
		embedding = data["data"][0]["embedding"]
	except (KeyError, IndexError, TypeError) as err:
		raise KeyError(
			f"Error while parsing embedding API response: {err}. Response: {data}"
		) from err
	return np.asarray(embedding, dtype=np.float32)
