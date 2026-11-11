"""Versioned policy retrieval with an offline lexical default."""

import hashlib
import json
import logging
import math
import re
from collections import Counter
from pathlib import Path

from app.api.schemas import Source

POLICY_PATH = Path(__file__).resolve().parents[2] / "policies/support.json"
STOP_WORDS = {
    "the",
    "and",
    "for",
    "this",
    "that",
    "with",
    "have",
    "was",
    "are",
    "you",
    "your",
    "from",
    "not",
    "but",
    "can",
    "has",
    "had",
    "our",
    "my",
    "to",
    "it",
    "is",
    "of",
    "in",
    "an",
    "on",
    "a",
    "i",
}


def tokenize(text):
    """Normalize policy and query terms for lexical retrieval."""
    return [
        word
        for word in re.findall(r"[a-z]+", text.lower())
        if word not in STOP_WORDS
    ]


class CompanyKnowledgeBase:
    """Reload changed policies and return versioned evidence snapshots."""

    def __init__(self, path=POLICY_PATH, backend="lexical"):
        self.path = Path(path)
        self.backend = backend
        self.version = ""
        self.documents = []
        self.collection = None

    def load_guidelines(self):
        """Rebuild the index when policy content changes."""
        raw = self.path.read_bytes()
        version = hashlib.sha256(raw).hexdigest()[:12]
        if version == self.version:
            return
        documents = json.loads(raw)
        if not documents or len({d["id"] for d in documents}) != len(
            documents
        ):
            raise ValueError("Policies must have unique IDs and contain text")
        for document in documents:
            if not all(document.get(key) for key in ("id", "title", "text")):
                raise ValueError("A policy is missing required fields")
        self.documents = documents
        self.version = version
        if self.backend == "chroma":
            import chromadb

            path = self.path.parent / ".chroma"
            client = chromadb.PersistentClient(path=str(path))
            self.collection = client.get_or_create_collection(
                name=f"policies-{version}"
            )
            if self.collection.count() != len(documents):
                self.collection.upsert(
                    ids=[d["id"] for d in documents],
                    documents=[d["text"] for d in documents],
                )

        logging.getLogger(__name__).info(
            "RAG ready: %s policy chunks loaded (%s index, version %s)",
            len(self.documents),
            self.backend,
            self.version,
        )

    def search(self, query, n_results=3):
        """Return relevant policy text, stable IDs, and a content version."""
        self.load_guidelines()
        if self.backend == "chroma":
            result = self.collection.query(
                query_texts=[query],
                n_results=min(n_results, len(self.documents)),
            )
            ids = result["ids"][0]
            scores = {
                key: 1 / (1 + distance)
                for key, distance in zip(ids, result["distances"][0])
            }
            ranked = sorted(
                self.documents,
                key=lambda d: scores.get(d["id"], 0),
                reverse=True,
            )[:n_results]
        else:
            query_terms = set(tokenize(query))
            counts = [
                Counter(
                    tokenize(
                        d["title"] + " " + d["category"] + " " + d["text"]
                    )
                )
                for d in self.documents
            ]
            scores = {}
            for document, terms in zip(self.documents, counts):
                score = 0.0
                for term in query_terms:
                    frequency = sum(term in count for count in counts)
                    weight = math.log(1 + len(counts) / (1 + frequency))
                    score += min(terms[term], 2) * weight
                scores[document["id"]] = score / math.sqrt(sum(terms.values()))
            ranked = sorted(
                self.documents, key=lambda d: scores[d["id"]], reverse=True
            )[:n_results]
        return [
            Source(
                id=d["id"],
                title=d["title"],
                text=d["text"],
                version=self.version,
                score=round(scores[d["id"]], 4),
            )
            for d in ranked
            if scores[d["id"]] > 0
        ]
