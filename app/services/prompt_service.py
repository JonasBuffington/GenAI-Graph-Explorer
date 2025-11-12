# app/services/prompt_service.py
import asyncio
import json
from pathlib import Path
from typing import Any
from app.core.prompts import DEFAULT_PROMPTS

class PromptService:
    def __init__(self, store_path: Path | None = None):
        base_dir = Path(__file__).resolve().parents[1]
        self.store_dir = store_path or base_dir / "data"
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()

    def _get_user_store_path(self, user_id: str) -> Path:
        # Sanitize user_id for filename safety, although UUIDs are generally safe.
        safe_filename = "".join(c for c in user_id if c.isalnum() or c in ('-', '_'))
        return self.store_dir / f"prompts_{safe_filename}.json"

    async def get_prompt(self, key: str, user_id: str) -> str:
        normalized_key = self._normalize_key(key)
        async with self._lock:
            data = await self._read_store(user_id)
        if normalized_key in data:
            return data[normalized_key]
        if normalized_key in DEFAULT_PROMPTS:
            return DEFAULT_PROMPTS[normalized_key]
        raise KeyError(f"Prompt '{key}' not found.")

    async def upsert_prompt(self, key: str, prompt_text: str, user_id: str) -> str:
        normalized_key = self._normalize_key(key)
        sanitized_prompt = prompt_text.strip()
        if not sanitized_prompt:
            raise ValueError("Prompt text cannot be empty.")
        async with self._lock:
            data = await self._read_store(user_id)
            if normalized_key not in DEFAULT_PROMPTS and normalized_key not in data:
                raise KeyError(f"Prompt '{key}' not found.")
            data[normalized_key] = sanitized_prompt
            await self._write_store(data, user_id)
        return sanitized_prompt

    async def reset_prompt(self, key: str, user_id: str) -> str:
        normalized_key = self._normalize_key(key)
        if normalized_key not in DEFAULT_PROMPTS:
            raise KeyError(f"Prompt '{key}' not found.")
        default_prompt = DEFAULT_PROMPTS[normalized_key]
        async with self._lock:
            data = await self._read_store(user_id)
            data[normalized_key] = default_prompt
            await self._write_store(data, user_id)
        return default_prompt

    async def _read_store(self, user_id: str) -> dict[str, str]:
        store_path = self._get_user_store_path(user_id)
        if not store_path.exists():
            return {}
        def _read() -> dict[str, Any]:
            with store_path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        return await asyncio.to_thread(_read)

    async def _write_store(self, data: dict[str, str], user_id: str) -> None:
        store_path = self._get_user_store_path(user_id)
        def _write() -> None:
            with store_path.open("w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2)
        await asyncio.to_thread(_write)

    def normalize_key(self, key: str) -> str:
        return self._normalize_key(key)

    @staticmethod
    def _normalize_key(key: str) -> str:
        return key.strip().lower().replace(" ", "-").replace("_", "-")