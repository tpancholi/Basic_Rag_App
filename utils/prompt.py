from typing import Iterable

Chunk = str


def build_prompt(context_chunks: Iterable[Chunk], query: str) -> str:
	"""
	Prompt creation based on context chunks and query.
	Parameters
	----------
	context_chunks : Iterable[str]
	    One or more pieces of context that will be concatenated
	    with a blank line between them.
	query : str
	    The question to answer.

	Returns
	-------
	str
	    A prompt that can be fed to a language model.

	Raises
	------
	ValueError
	    If *context_chunks* is empty or *query* is an empty string.
	"""
	if not context_chunks:
		raise ValueError("Context chunks cannot be empty.")
	if not query.strip() or not isinstance(query, str):
		raise ValueError("Query must be a non-empty string.")
	context = "\n\n".join(ch.strip() for ch in context_chunks if ch.strip())
	if not context:
		raise ValueError("All context chunks are empty.")
	prompt = f"""Given the following context, answer the question below.
	Context:
	{context}
	Question:
	{query}"""
	return prompt.strip()
