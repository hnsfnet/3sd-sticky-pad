import uuid
import time
from dataclasses import dataclass, field, asdict
from typing import List, Optional

import config


@dataclass
class Note:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    x: Optional[int] = None
    y: Optional[int] = None
    width: int = config.DEFAULT_WIDTH
    height: int = config.DEFAULT_HEIGHT
    content: str = ""
    color: str = config.DEFAULT_COLOR
    tag: str = ""
    pinned: bool = False
    bold_ranges: List[List[str]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def validate(self):
        if self.color not in config.COLORS:
            self.color = config.DEFAULT_COLOR
        self.width = max(config.MIN_WIDTH, int(self.width))
        self.height = max(config.MIN_HEIGHT, int(self.height))
        self.tag = self.tag or ""
        self.pinned = bool(self.pinned)
        if not isinstance(self.bold_ranges, list):
            self.bold_ranges = []

    def touch(self):
        self.updated_at = time.time()

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        note = cls(
            id=data.get("id") or str(uuid.uuid4()),
            x=data.get("x"),
            y=data.get("y"),
            width=data.get("width", config.DEFAULT_WIDTH),
            height=data.get("height", config.DEFAULT_HEIGHT),
            content=data.get("content", ""),
            color=data.get("color", config.DEFAULT_COLOR),
            tag=data.get("tag", ""),
            pinned=data.get("pinned", False),
            bold_ranges=data.get("bold_ranges", []),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
        )
        note.validate()
        return note
