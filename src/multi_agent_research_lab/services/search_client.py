"""Search client with a deterministic offline-corpus implementation."""

import json
import re
from pathlib import Path

from multi_agent_research_lab.core.schemas import SourceDocument


class SearchClient:
    """Search the corpus shipped with the lab using a small lexical ranker."""

    def __init__(self, corpus_root: Path | None = None) -> None:
        self.corpus_root = corpus_root or Path("ai_agent_offline_research_corpus_v2/topics")

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Return the most relevant local documents, ordered by token overlap."""

        if max_results < 1:
            return []
        query_tokens = self._tokens(query)
        ranked: list[tuple[int, str, SourceDocument]] = []
        for path in sorted(self.corpus_root.glob("*.json")):
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            topic = raw.get("topic")
            topic_data = topic if isinstance(topic, dict) else {}
            title = str(raw.get("title") or topic_data.get("name") or path.stem.replace("_", " "))
            text = self._flatten(raw)
            score = len(query_tokens & self._tokens(f"{title} {text}"))
            thesis = str(topic_data.get("working_thesis_for_evaluation") or "")
            question = str(topic_data.get("research_question") or "")
            snippet = re.sub(r"\s+", " ", f"{question} {thesis}").strip()[:700]
            document = SourceDocument(
                title=title,
                url=path.resolve().as_uri(),
                snippet=snippet or "No summary available.",
                metadata={"source": "offline_corpus", "path": str(path), "score": score},
            )
            ranked.append((score, title.lower(), document))
        ranked.sort(key=lambda item: (-item[0], item[1]))
        return [item[2] for item in ranked[:max_results]]

    @staticmethod
    def _tokens(value: str) -> set[str]:
        return {token for token in re.findall(r"[a-z0-9]+", value.lower()) if len(token) > 2}

    @classmethod
    def _flatten(cls, value: object) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            return " ".join(cls._flatten(item) for item in value.values())
        if isinstance(value, list):
            return " ".join(cls._flatten(item) for item in value)
        return ""
