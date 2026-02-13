"""SanCanvas — SanityLang graphics canvas with headless mode support.

Canvas is a Personality instance with its own SP, Mood, Trust, Traits.
All drawing operations are recorded for headless testing.
Full Pygame rendering is deferred — this provides the complete API surface
with headless buffering so the rest of the interpreter works.
"""
from __future__ import annotations
import random
from typing import Optional

from .variables import Mood, Trait


class SanCanvas:
    """A graphics canvas that acts as a Personality instance.

    In headless mode (default), all draw calls are recorded but
    no window is created. In windowed mode, Pygame would be used.
    """

    def __init__(self, title: str, width: int, height: int, headless: bool = True):
        self.title = title
        self.width = width
        self.height = height
        self.headless = headless

        # Personality state
        self.mood: Mood = Mood.HAPPY      # Fresh blank canvas
        self.trust: int = 100
        self.sp: int = 100                 # Canvas's own SP
        self.traits: set[Trait] = {Trait.CREATIVE}

        # Drawing state
        self._buffer: list[dict] = []      # Recorded draw ops
        self._frame_count: int = 0
        self._is_open: bool = True
        self._visual_insanity: bool = False

        # Event handlers
        self._on_click: Optional[object] = None
        self._on_key: Optional[object] = None
        self._on_mouse_move: Optional[object] = None
        self._every_callback: Optional[object] = None
        self._every_ms: int = 0

    @property
    def is_open(self) -> bool:
        return self._is_open

    # ── SP management ──

    def _canvas_sp_cost(self, amount: int, op: str) -> None:
        """Deduct from canvas SP. Triggers Visual Insanity at ≤ 0."""
        self.sp -= amount
        if self.sp <= 0 and not self._visual_insanity:
            self._visual_insanity = True

    def _apply_visual_insanity(self, params: dict) -> dict:
        """Corrupt drawing parameters when in Visual Insanity Mode."""
        if not self._visual_insanity:
            return params
        result = dict(params)
        # Hue shift on colors
        if 'color' in result and isinstance(result['color'], str):
            shifts = ['red', 'blue', 'green', 'yellow', 'purple', 'cyan', 'orange']
            result['color'] = random.choice(shifts)
        # Wobble on coordinates
        for key in ('x', 'y', 'x1', 'y1', 'x2', 'y2'):
            if key in result and isinstance(result[key], (int, float)):
                result[key] = result[key] + random.randint(-3, 3)
        # Random size variation on text
        if 'font_size' in result:
            var = int(result['font_size'] * 0.3)
            result['font_size'] += random.randint(-var, var)
        return result

    # ── Drawing primitives ──

    def pixel(self, x: int, y: int, color: str) -> None:
        """Draw a single pixel. Cost: 0 canvas SP."""
        op = {'type': 'pixel', 'x': x, 'y': y, 'color': color}
        self._buffer.append(self._apply_visual_insanity(op))

    def line(self, x1: int, y1: int, x2: int, y2: int, color: str) -> None:
        """Draw a line. Cost: -1 canvas SP."""
        self._canvas_sp_cost(1, 'line')
        op = {'type': 'line', 'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'color': color}
        self._buffer.append(self._apply_visual_insanity(op))

    def rect(self, x: int, y: int, w: int, h: int, color: str, filled: bool = True) -> None:
        """Draw a rectangle. Cost: -2 canvas SP."""
        self._canvas_sp_cost(2, 'rect')
        op = {'type': 'rect', 'x': x, 'y': y, 'w': w, 'h': h,
              'color': color, 'filled': filled}
        self._buffer.append(self._apply_visual_insanity(op))

    def circle(self, x: int, y: int, radius: int, color: str) -> None:
        """Draw a circle. Cost: -3 canvas SP."""
        self._canvas_sp_cost(3, 'circle')
        op = {'type': 'circle', 'x': x, 'y': y, 'radius': radius, 'color': color}
        self._buffer.append(self._apply_visual_insanity(op))

    def text(self, x: int, y: int, content: str, font_size: int = 16) -> None:
        """Draw text. Cost: -5 canvas SP."""
        self._canvas_sp_cost(5, 'text')
        op = {'type': 'text', 'x': x, 'y': y, 'content': content, 'font_size': font_size}
        self._buffer.append(self._apply_visual_insanity(op))

    def clear(self) -> None:
        """Clear the canvas. Cost: -1 canvas SP."""
        self._canvas_sp_cost(1, 'clear')
        self._buffer.clear()

    # ── Display ──

    def show(self) -> None:
        """Flip the double buffer. Canvas SP +1 (recovery).

        In headless mode, this is a no-op for rendering but still
        increments the frame count and recovers SP.
        """
        self._frame_count += 1
        self.sp += 1  # Canvas rests between frames
        # In non-headless mode, this would call pygame.display.flip()

    # ── Event handlers ──

    def on_click(self, callback: object) -> None:
        """Register click handler."""
        self._on_click = callback

    def on_key(self, callback: object) -> None:
        """Register key handler."""
        self._on_key = callback

    def on_mouse_move(self, callback: object) -> None:
        """Register mouse move handler."""
        self._on_mouse_move = callback

    def every(self, ms: int, callback: object) -> None:
        """Register a recurring callback (game loop)."""
        self._every_ms = ms
        self._every_callback = callback

    # ── State ──

    def save(self, path: str) -> None:
        """Save canvas state (screenshot stub)."""
        pass  # In full implementation, would save buffer as image

    @property
    def fps(self) -> int:
        """Return current FPS (0 in headless mode)."""
        return 0

    @property
    def frame_count(self) -> int:
        return self._frame_count

    @property
    def buffer(self) -> list[dict]:
        """Return the current draw buffer (for testing)."""
        return list(self._buffer)

    def close(self) -> None:
        """Close the canvas."""
        self._is_open = False

    def __repr__(self) -> str:
        return (f"SanCanvas('{self.title}', {self.width}x{self.height}, "
                f"mood={self.mood.name}, sp={self.sp}, "
                f"frames={self._frame_count}, "
                f"{'headless' if self.headless else 'windowed'})")
