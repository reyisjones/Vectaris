from fastapi import APIRouter

from app.models.llm import LLMRuntimeReport
from app.services.llm_runtime_service import get_runtime_report

router = APIRouter()


@router.get("/runtime", response_model=LLMRuntimeReport)
async def llm_runtime() -> LLMRuntimeReport:
    """Live status + installed models for the configured LLM runtime (Ollama)."""
    return await get_runtime_report()
