from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from src.utils.download_tool import get_cached_path


class Tool(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def version(self) -> 'ToolVersion': ...

    @property
    def jar_path(self):
        return get_cached_path(f"{self.name}-{self.version.name}.jar")


@dataclass
class ToolVersion:
    name: str
    download_url: Optional[str] = None
