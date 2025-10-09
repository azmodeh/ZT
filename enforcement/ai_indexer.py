from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parent.parent))

import httpx
import orjson

from enforcement.utils import (
    ProjectPaths,
    emit_ui_message,
    ensure_directory,
    get_logger,
    load_ai_model_config,
    load_contract_rules,
    load_project_paths,
)

LOGGER = get_logger("zero_tolerance.indexer")
CACHE_DIR = Path("data/cache/ai_index")


@dataclass
class Chunk:
    identifier: str
    path: Path
    start_line: int
    end_line: int
    content: str
    embedding: List[float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.identifier,
            "path": str(self.path),
            "start_line": self.start_line,
            "end_line": self.end_line,
            "content": self.content,
            "embedding": self.embedding,
        }


class EmbeddingService:
    def __init__(self, api_key: Optional[str], model_config: Dict[str, Any]) -> None:
        self.api_key = api_key
        self.model_config = model_config
        self.embedding_model = model_config.get("embedding_model", "text-embedding-3-large")
        self._client: Optional[httpx.Client] = None

    def embed(self, texts: Sequence[str]) -> List[List[float]]:
        if not texts:
            return []
        if not self.api_key:
            LOGGER.warning("No OPENROUTER_API_KEY found; using hash-based embeddings.")
            return [self._hash_embedding(text) for text in texts]
        try:
            response = self._client_instance().post(
                "https://openrouter.ai/api/v1/embeddings",
                json={"model": self.embedding_model, "input": list(texts)},
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30,
            )
            response.raise_for_status()
            payload = response.json()
            data = payload.get("data", [])
            embeddings = [item.get("embedding", []) for item in data]
            if not embeddings or any(not emb for emb in embeddings):
                raise ValueError("Embedding response missing vectors.")
            return embeddings
        except Exception as exc:
            LOGGER.error("Embedding request failed (%s). Falling back to hash vectors.", exc)
            return [self._hash_embedding(text) for text in texts]

    def _client_instance(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client()
        return self._client

    def _hash_embedding(self, text: str, dimensions: int = 64) -> List[float]:
        digest = hashlib.blake2b(text.encode("utf-8"), digest_size=dimensions).digest()
        return [round(byte / 255.0, 6) for byte in digest]


class ProjectIndexer:
    def __init__(self, project_paths: ProjectPaths, embed_service: EmbeddingService) -> None:
        self.project_paths = project_paths
        self.embed_service = embed_service
        self.chunk_size = 400  # characters

    def build(self) -> List[Chunk]:
        chunks: List[Tuple[Path, int, int, str]] = []
        for path in self._iter_files():
            file_chunks = self._chunk_file(path)
            chunks.extend(file_chunks)
        LOGGER.info("Prepared %s chunks for embedding.", len(chunks))
        embeddings = self.embed_service.embed([item[3] for item in chunks])
        packaged: List[Chunk] = []
        for index, (path, start, end, content) in enumerate(chunks):
            vector = embeddings[index] if index < len(embeddings) else []
            identifier = f"{path.stem}-{index}"
            packaged.append(Chunk(identifier=identifier, path=path, start_line=start, end_line=end, content=content, embedding=vector))
        return packaged

    def _iter_files(self) -> Iterable[Path]:
        yield from self.project_paths.iter_python_files()

    def _chunk_file(self, path: Path) -> List[Tuple[Path, int, int, str]]:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            LOGGER.error("Failed to read %s: %s", path, exc)
            return []
        lines = text.splitlines()
        chunks: List[Tuple[Path, int, int, str]] = []
        buffer: List[str] = []
        start_line = 1
        char_count = 0

        for idx, line in enumerate(lines, start=1):
            buffer.append(line)
            char_count += len(line)
            if char_count >= self.chunk_size:
                chunk_text = "\n".join(buffer)
                chunks.append((path, start_line, idx, chunk_text))
                buffer = []
                char_count = 0
                start_line = idx + 1

        if buffer:
            chunk_text = "\n".join(buffer)
            chunks.append((path, start_line, len(lines), chunk_text))
        return chunks


def persist_chunks(chunks: List[Chunk]) -> Path:
    ensure_directory(CACHE_DIR)
    payload = [chunk.to_dict() for chunk in chunks]
    destination = CACHE_DIR / "index.json"
    destination.write_bytes(orjson.dumps(payload, option=orjson.OPT_INDENT_2))
    LOGGER.info("Stored index with %s chunks at %s", len(chunks), destination)
    return destination


def main() -> None:
    rules = load_contract_rules()
    models = load_ai_model_config()
    project_paths = load_project_paths()
    service = EmbeddingService(api_key=None, model_config=models)
    from os import getenv

    api_key = getenv("OPENROUTER_API_KEY") or models.get("openrouter_api_key") or rules.get("openrouter_api_key")
    service.api_key = api_key

    indexer = ProjectIndexer(project_paths=project_paths, embed_service=service)
    chunks = indexer.build()
    persist_chunks(chunks)
    message = (
        "ایندکس پروژه ساخته شد.\n"
        f"تعداد فایل‌های پردازش شده: {len({chunk.path for chunk in chunks})}\n"
        f"تعداد قطعه‌های ایجاد شده: {len(chunks)}"
    )
    emit_ui_message(message)


if __name__ == "__main__":
    main()
