"""SanityLang file handle — wraps Python file objects with SP-aware operations.

File handles are Personality instances with Moods, Traits, Trust, and
their own SP. Extension-based starting state per §30.
"""
from __future__ import annotations
import os
import math
import random
from typing import Optional

from .variables import Mood, Trait


# Extension → (starting Mood, starting Trust, optional extra Traits)
_EXTENSION_MAP: dict[str, tuple[Mood, int, list[Trait]]] = {
    ".san":  (Mood.HAPPY,   70, []),
    ".txt":  (Mood.NEUTRAL, 70, []),
    ".json": (Mood.NEUTRAL, 70, [Trait.PARANOID]),   # "Paranoid" — strict format
    ".csv":  (Mood.SAD,     70, []),
    ".log":  (Mood.NEUTRAL, 70, [Trait.TIRED]),       # "Tired" — it's seen things
    ".md":   (Mood.HAPPY,   70, []),
    ".yaml": (Mood.AFRAID,  70, []),
    ".yml":  (Mood.AFRAID,  70, []),
    ".xml":  (Mood.ANGRY,   70, []),
    ".env":  (Mood.NEUTRAL, 40, [Trait.PARANOID]),    # Contains secrets, Trust 40
}

# Default for unknown extension
_DEFAULT_EXT = (Mood.AFRAID, 70, [])
# No extension at all
_NO_EXT = (Mood.NEUTRAL, 70, [])


class SanFileHandle:
    """A file handle in SanityLang.

    Tracks open state, access mode, bytes written/read, mood, trust,
    and traits. SP costs scale with file size per the spec.
    """

    def __init__(self, path: str, handle_name: str):
        self.path = path
        self.handle_name = handle_name
        self._file: Optional[object] = None
        self.is_open = False
        self.bytes_read: int = 0
        self.bytes_written: int = 0
        self.observed: bool = False

        # Derive extension-based starting state
        _, ext = os.path.splitext(path)
        ext = ext.lower()
        if ext == "":
            mood, trust, traits = _NO_EXT
        elif ext in _EXTENSION_MAP:
            mood, trust, traits = _EXTENSION_MAP[ext]
        else:
            mood, trust, traits = _DEFAULT_EXT

        self.mood: Mood = mood
        self.trust: int = trust
        self.traits: set[Trait] = set(traits)
        self.sp: int = 100  # File handle's own SP

    def open(self) -> None:
        """Open the file for reading and writing (creates if missing)."""
        parent = os.path.dirname(self.path)
        if parent:
            os.makedirs(parent, exist_ok=True)

        if not os.path.exists(self.path):
            with open(self.path, "w") as f:
                pass

        self._file = open(self.path, "r+")
        self.is_open = True

    def read(self) -> str:
        """Read the entire file contents.

        The returned content inherits the file handle's Trust and Mood.
        Reading makes the handle Observed.
        """
        if not self.is_open or self._file is None:
            raise RuntimeError(f"File handle '{self.handle_name}' is not open")
        self._file.seek(0)  # type: ignore
        content = self._file.read()  # type: ignore
        self.bytes_read += len(content)
        self.observed = True

        # Files > 1MB become Tired
        if len(content) > 1024 * 1024:
            self.mood = Mood.NEUTRAL  # Tired mapped as neutral variant
            self.traits.add(Trait.TIRED)

        return content

    def write(self, content: str) -> None:
        """Overwrite the file with content.

        Handles Mood effects:
        - Angry → fail silently (returns without writing)
        - Tired → 5% chance of truncating last 10% of content
        """
        if not self.is_open or self._file is None:
            raise RuntimeError(f"File handle '{self.handle_name}' is not open")

        # Angry handle: silent fail
        if self.mood == Mood.ANGRY:
            self.trust = max(0, self.trust - 10)
            return

        # Tired: 5% chance of truncation
        if Trait.TIRED in self.traits and random.random() < 0.05:
            cut = max(1, len(content) * 9 // 10)
            content = content[:cut]

        self._file.seek(0)  # type: ignore
        self._file.truncate()  # type: ignore
        self._file.write(content)  # type: ignore
        self._file.flush()  # type: ignore
        self.bytes_written += len(content)

    def append(self, content: str) -> None:
        """Append content to the file."""
        if not self.is_open or self._file is None:
            raise RuntimeError(f"File handle '{self.handle_name}' is not open")

        # Angry handle: silent fail
        if self.mood == Mood.ANGRY:
            self.trust = max(0, self.trust - 10)
            return

        # Tired: 5% chance of truncation
        if Trait.TIRED in self.traits and random.random() < 0.05:
            cut = max(1, len(content) * 9 // 10)
            content = content[:cut]

        self._file.seek(0, 2)  # Seek to end  # type: ignore
        self._file.write(content)  # type: ignore
        self._file.flush()  # type: ignore
        self.bytes_written += len(content)

    def lines(self) -> list[str]:
        """Read file as a list of lines.

        List Mood depends on line count:
        - < 100 → Happy
        - 100-1000 → Neutral
        - 1000-10000 → Tired (adds TIRED trait)
        - > 10000 → Overwhelmed
        """
        content = self.read()
        result = content.splitlines()
        # Mood based on line count would be set on the returned SanValue
        # by the runtime, not here. We just return the raw lines.
        return result

    def close(self) -> None:
        """Close the file handle."""
        if self._file is not None:
            self._file.close()  # type: ignore
        self.is_open = False
        self._file = None

    def sp_cost_for_size(self, base_cost: int = 3) -> int:
        """Calculate SP cost based on file size.

        Per spec: SP cost scales with file size.
        Base cost + log2(size_in_kb + 1) rounded up.
        """
        try:
            size_bytes = os.path.getsize(self.path)
        except OSError:
            size_bytes = 0
        size_kb = size_bytes / 1024.0
        scaling = math.ceil(math.log2(size_kb + 1))
        return base_cost + scaling

    def file_size_bytes(self) -> int:
        """Get the file size in bytes."""
        try:
            return os.path.getsize(self.path)
        except OSError:
            return 0

    def __repr__(self) -> str:
        status = "open" if self.is_open else "closed"
        return (
            f"SanFileHandle({self.handle_name!r}, path={self.path!r}, "
            f"{status}, mood={self.mood.value}, trust={self.trust})"
        )
