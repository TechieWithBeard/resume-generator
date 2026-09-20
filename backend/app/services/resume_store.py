"""
Base Resume Store & Persistence Manager.
Manages candidate base profile as Ground Truth. Decoupled from core distributable engine.
"""

import json
import os
from pathlib import Path
from typing import Optional
from backend.app.models.resume import ResumeData

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DEFAULT_BASE_PATH = DATA_DIR / "default_base_resume.json"
SAMPLE_RESUME_PATH = DATA_DIR / "sample_resume.json"
USER_PERSISTED_PATH = DATA_DIR / "my_resume.json"


class ResumeStore:
    def __init__(self):
        self._cached_resume: Optional[ResumeData] = None

    def get_base_resume(self) -> ResumeData:
        """
        Retrieves the base resume (Ground Truth).
        Order of resolution:
        1. Custom path via RESUME_DATA_PATH environment variable
        2. User edited persistence: data/my_resume.json
        3. Local default: data/default_base_resume.json (if present)
        4. Generic sample: data/sample_resume.json
        """
        if self._cached_resume:
            return self._cached_resume

        custom_env_path = os.getenv("RESUME_DATA_PATH")
        candidates = []
        if custom_env_path:
            candidates.append(Path(custom_env_path))
        candidates.extend([USER_PERSISTED_PATH, DEFAULT_BASE_PATH, SAMPLE_RESUME_PATH])

        for path in candidates:
            if path.is_file():
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self._cached_resume = ResumeData.model_validate(data)
                    return self._cached_resume
                except Exception as e:
                    print(f"Warning: Failed to load resume from {path}: {e}")

        # Fallback empty resume if no file exists
        fallback = self.get_sample_resume()
        self._cached_resume = fallback
        return fallback

    def save_base_resume(self, resume: ResumeData) -> ResumeData:
        """Persists the user's updated base resume to data/my_resume.json."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(USER_PERSISTED_PATH, "w", encoding="utf-8") as f:
            json.dump(resume.model_dump(), f, indent=2)
        self._cached_resume = resume
        return resume

    def reset_to_default(self) -> ResumeData:
        """Resets cached resume to original default or sample."""
        if USER_PERSISTED_PATH.exists():
            try:
                USER_PERSISTED_PATH.unlink()
            except Exception:
                pass
        self._cached_resume = None
        return self.get_base_resume()

    def get_sample_resume(self) -> ResumeData:
        """Returns the generic sample resume."""
        if SAMPLE_RESUME_PATH.is_file():
            with open(SAMPLE_RESUME_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return ResumeData.model_validate(data)
        
        # Absolute minimal fallback
        return ResumeData(
            name="Sample Candidate",
            title="Senior Software Engineer",
            summary="Experienced engineer with background in distributed web systems.",
            experience=[],
            education=[],
            skills={"core": ["Python", "TypeScript", "Angular"]}
        )


resume_store = ResumeStore()
