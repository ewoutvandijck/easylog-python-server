from anthropic.types.citations_delta import Citation


def format_academic_citation(citation: Citation) -> str | None:
    """
    Formats a citation location object into a formal academic-style citation.

    Args:
        citation: A CitationCharLocation, CitationPageLocation, or CitationContentBlockLocation object

    Returns:
        str: A formatted academic-style citation string
    """
    # If no document title is provided, use a generic reference
    doc_reference = citation.document_title if citation.document_title else f"Document {citation.document_index}"

    if citation.type == "page_location":
        # Page-based citation (similar to academic page citations)
        if citation.start_page_number == citation.end_page_number:
            location = f"p. {citation.start_page_number}"
        else:
            location = f"pp. {citation.start_page_number}-{citation.end_page_number}"
        return f"{doc_reference}, {location}."

    elif citation.type == "char_location":
        # Character-based citation (less common in academic writing)
        return f"{doc_reference}, char. {citation.start_char_index}-{citation.end_char_index}."

    elif citation.type == "content_block_location":
        # Block-based citation (similar to paragraph or section citations)
        if citation.start_block_index == citation.end_block_index:
            location = f"block {citation.start_block_index}"
        else:
            location = f"blocks {citation.start_block_index}-{citation.end_block_index}"
        return f"{doc_reference}, {location}."


def format_inline_citation(citation: Citation) -> str:
    """
    Formats a citation for inline use with quoted text.
    """
    base_citation = format_academic_citation(citation)
    if base_citation is None:
        return ""

    base_citation = base_citation.rstrip(".")  # Remove trailing period
    return f'"{citation.cited_text}" ({base_citation})'
