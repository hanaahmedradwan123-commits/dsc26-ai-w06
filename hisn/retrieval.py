
"""Offline TF-IDF search over Hisn's SOC runbooks."""

from __future__ import annotations

import re
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


RUNBOOK_DIR = Path(__file__).parent / "data" / "runbooks"


def load_runbooks() -> list[dict]:
    """Load runbooks and extract their front matter and Markdown body."""

    runbooks = []

    for path in sorted(RUNBOOK_DIR.glob("RB-*.md")):
        content = path.read_text(encoding="utf-8")

        # Separate YAML-style front matter from the Markdown body.
        parts = content.split("---", 2)

        if len(parts) != 3:
            continue

        metadata = {}

        for line in parts[1].splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                metadata[key.strip()] = value.strip()

        runbook_id = metadata.get("id", path.stem)
        title = metadata.get("title", runbook_id)
        body = parts[2].strip()

        runbooks.append({
            "id": runbook_id,
            "title": title,
            "body": body,
        })

    return runbooks


def search_runbooks(query: str, k: int = 3) -> list[dict]:
    """Search runbooks using TF-IDF and cosine similarity."""

    if not query or not query.strip():
        return []

    k = max(1, min(10, int(k)))

    runbooks = load_runbooks()

    if not runbooks:
        return []

    # Give the title extra importance during matching.
    documents = [
        f"{rb['title']} {rb['title']} {rb['body']}"
        for rb in runbooks
    ]

    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 2),
        sublinear_tf=True,
    )

    document_vectors = vectorizer.fit_transform(documents)
    query_vector = vectorizer.transform([query])

    scores = cosine_similarity(
        query_vector,
        document_vectors
    ).flatten()

    results = []

    for rb, score in zip(runbooks, scores):
        # Return a short excerpt of the runbook.
        snippet = re.sub(r"\s+", " ", rb["body"]).strip()[:240]

        results.append({
            "id": rb["id"],
            "title": rb["title"],
            "snippet": snippet,
            "score": float(score),
        })

    # Highest similarity first; ties broken by ID ascending.
    results.sort(key=lambda result: (
        -result["score"],
        result["id"]
    ))

    return results[:k]
