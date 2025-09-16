import re


def chunk_text(text, max_words=100) -> list[str]:
	"""
	Split text into chunks of approximately max_words each.

	Parameters
	----------
	text : str
	    The input text to be chunked.
	max_words : int, default 100
	    Maximum number of words per chunk. Must be at least 1.

	Returns
	-------
	List[str]
	    List of text chunks, each containing up to max_words words.

	Raises
	------
	ValueError
	    If max_words is less than 1 or text is empty/None.
	TypeError
	    If text is not a string.

	Examples
	--------
	>>> chunk_text("Hello world", max_words=1)
	['Hello', 'world']

	>>> chunk_text("A short text", max_words=5)
	['A short text']
	"""
	if not isinstance(text, str):
		raise TypeError(f"text must be a string, got {type(text).__name__}")
	stripped_text = text.strip()
	if not stripped_text:
		raise ValueError("text cannot be empty or whitespace-only")

	if max_words < 1:
		raise ValueError("max_words must be at least 1")

	words = re.split(r"\s+", stripped_text)
	if len(words) <= max_words:
		return [stripped_text]

	return [" ".join(words[i : i + max_words]) for i in range(0, len(words), max_words)]
