from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class HardwareReference:
    name: str
    model_path: Path
    source: str | None = None
    notes: str | None = None

    def exists(self) -> bool:
        return self.model_path.expanduser().exists()
