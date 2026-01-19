"""Token counting utilities for Factory Droid hooks.

Provides tiktoken-based token counting with fallback for when tiktoken
is not available.
"""

from __future__ import annotations

from typing import Callable

# ============================================================================
# Tiktoken Initialization (lazy loading)
# ============================================================================

_encoder: Callable[[str], list[int]] | None = None
_tiktoken_available: bool | None = None


def _init_tiktoken() -> bool:
    """Initialize tiktoken encoder (called once on first use)."""
    global _encoder, _tiktoken_available

    if _tiktoken_available is not None:
        return _tiktoken_available

    try:
        import tiktoken

        enc = tiktoken.get_encoding("o200k_base")
        _encoder = enc.encode_ordinary
        _tiktoken_available = True
    except ImportError:
        _tiktoken_available = False

    return _tiktoken_available


# ============================================================================
# Token Counting Functions
# ============================================================================

def count_tokens(text: str) -> int:
    """Count tokens in text using tiktoken o200k_base encoding.

    Falls back to character-based estimation (len/4) if tiktoken is unavailable.

    Args:
        text: Text to count tokens for

    Returns:
        Estimated token count
    """
    if _init_tiktoken() and _encoder is not None:
        return len(_encoder(text))
    # Fallback: rough estimate of ~4 chars per token
    return len(text) >> 2


def count_tokens_exact(text: str) -> int | None:
    """Count tokens using tiktoken, returning None if unavailable.

    Use this when you need to know if the count is exact or estimated.

    Args:
        text: Text to count tokens for

    Returns:
        Exact token count, or None if tiktoken unavailable
    """
    if _init_tiktoken() and _encoder is not None:
        return len(_encoder(text))
    return None


def is_tiktoken_available() -> bool:
    """Check if tiktoken is available for exact token counting.

    Returns:
        True if tiktoken is installed and working
    """
    return _init_tiktoken()


def estimate_tokens(text: str) -> int:
    """Estimate tokens using character-based heuristic.

    This is faster than tiktoken but less accurate. Use when approximate
    counts are acceptable.

    Args:
        text: Text to estimate tokens for

    Returns:
        Estimated token count (len/4)
    """
    return len(text) >> 2


def exceeds_threshold(text: str, threshold: int) -> bool:
    """Check if text exceeds a token threshold.

    For performance, uses character-based estimation first for early exit.

    Args:
        text: Text to check
        threshold: Token threshold

    Returns:
        True if text exceeds threshold
    """
    # Quick check using character estimate (assuming ~4 chars/token)
    char_estimate = len(text) >> 2
    if char_estimate < threshold * 0.8:
        # Definitely under threshold
        return False
    if char_estimate > threshold * 1.5:
        # Definitely over threshold
        return True
    # Close to threshold - use exact count if available
    return count_tokens(text) > threshold
