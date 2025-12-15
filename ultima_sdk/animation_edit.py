"""
AnimationEdit module - Utilities for editing animations.
"""


from __future__ import annotations

from pathlib import Path
from typing import List

from .animations import AnimationData, AnimationFrame
from .exceptions import FileAccessException
from .rendering import image_from_pixels


class AnimationEdit:
    """Utility class for animation editing operations."""

    @classmethod
    def frame_to_image(cls, frame: AnimationFrame):
        """Convert an AnimationFrame to a Pillow image.

        Frames are decoded as 16-bit UO 5-5-5 pixel buffers.
        """
        return image_from_pixels(frame.width, frame.height, frame.pixels, format_hint="UO16")

    @classmethod
    def animation_to_images(cls, animation: AnimationData) -> List:
        """Convert an AnimationData to a list of Pillow images."""
        return [cls.frame_to_image(frame) for frame in animation.frames]

    @classmethod
    def save_gif(
        cls,
        animation: AnimationData | None,
        path,
        *,
        duration_ms: int = 100,
        loop: int = 0,
    ) -> bool:
        """Save an animation as an animated GIF.

        This requires Pillow at runtime because `frame_to_image()` returns
        Pillow images.

        Args:
            animation: The decoded animation.
            path: Output file path (str or Path-like).
            duration_ms: Frame duration in milliseconds.
            loop: GIF loop count; 0 means infinite.

        Returns:
            True if saved; False if animation is None or has no frames.
        """
        if animation is None or not getattr(animation, "frames", None):
            return False

        try:
            out_path = Path(path)
        except Exception as e:
            raise FileAccessException(f"Invalid output path: {e}")

        try:
            images = cls.animation_to_images(animation)
            if not images:
                return False
            first, rest = images[0], images[1:]

            # Pillow API: Image.save(..., save_all=True, append_images=[...])
            first.save(
                str(out_path),
                format="GIF",
                save_all=True,
                append_images=rest,
                duration=int(duration_ms),
                loop=int(loop),
            )
            return True
        except Exception as e:
            raise FileAccessException(f"Failed to save animation GIF: {e}")
