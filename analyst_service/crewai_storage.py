"""Helpers to keep CrewAI SQLite storage inside the project workspace."""
from pathlib import Path


def configure_crewai_storage() -> str:
    """Redirect CrewAI storage to a writable workspace-local directory."""
    storage_dir = Path(__file__).resolve().parents[1] / ".crewai_storage"
    storage_dir.mkdir(parents=True, exist_ok=True)

    from crewai.utilities import paths as crew_paths
    from crewai.memory.storage import kickoff_task_outputs_storage as kickoff_storage
    from crewai.memory.storage import ltm_sqlite_storage as ltm_storage
    from crewai.memory.storage import rag_storage as rag_storage_module
    from crewai.knowledge.storage import knowledge_storage as knowledge_storage_module
    from crewai.flow.persistence import sqlite as flow_sqlite_module

    def _storage_path() -> str:
        return str(storage_dir)

    crew_paths.db_storage_path = _storage_path
    kickoff_storage.db_storage_path = _storage_path
    ltm_storage.db_storage_path = _storage_path
    rag_storage_module.db_storage_path = _storage_path
    knowledge_storage_module.db_storage_path = _storage_path
    flow_sqlite_module.db_storage_path = _storage_path
    return str(storage_dir)
