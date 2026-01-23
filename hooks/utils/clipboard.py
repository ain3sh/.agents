"""Cross-platform clipboard utilities for Factory Droid hooks.

Provides clipboard operations that work on macOS, Windows, WSL, and Linux.
"""

from __future__ import annotations

import os
import subprocess
import sys

# ============================================================================
# Platform Detection (cached at module load)
# ============================================================================

_PLATFORM = sys.platform
_IS_WSL = "microsoft" in os.uname().release.lower() if hasattr(os, "uname") else False


def is_wsl() -> bool:
    """Check if running under Windows Subsystem for Linux."""
    return _IS_WSL


def is_macos() -> bool:
    """Check if running on macOS."""
    return _PLATFORM == "darwin"


def is_windows() -> bool:
    """Check if running on Windows."""
    return _PLATFORM == "win32"


def is_linux() -> bool:
    """Check if running on Linux (non-WSL)."""
    return _PLATFORM.startswith("linux") and not _IS_WSL


# ============================================================================
# Clipboard Operations
# ============================================================================

def copy_to_clipboard(text: str) -> bool:
    """Copy text to system clipboard.

    Supports:
    - macOS: pbcopy
    - Windows: clip.exe
    - WSL: clip.exe
    - Linux: xclip or xsel

    Args:
        text: Text to copy to clipboard

    Returns:
        True if successful, False otherwise
    """
    text_bytes = text.encode("utf-8")
    devnull = subprocess.DEVNULL

    try:
        if _PLATFORM == "darwin":
            subprocess.run(
                ["pbcopy"],
                input=text_bytes,
                check=True,
                stdout=devnull,
                stderr=devnull,
            )
            return True

        if _PLATFORM == "win32" or _IS_WSL:
            subprocess.run(
                ["clip.exe"],
                input=text_bytes,
                check=True,
                stdout=devnull,
                stderr=devnull,
            )
            return True

        # Linux: try xclip, then xsel
        for cmd in (
            ["xclip", "-selection", "clipboard"],
            ["xsel", "--clipboard", "--input"],
        ):
            try:
                subprocess.run(
                    cmd,
                    input=text_bytes,
                    check=True,
                    stdout=devnull,
                    stderr=devnull,
                )
                return True
            except (FileNotFoundError, subprocess.CalledProcessError):
                continue

        return False

    except Exception:
        return False


def get_from_clipboard() -> str | None:
    """Get text from system clipboard.

    Supports:
    - macOS: pbpaste
    - Windows: PowerShell Get-Clipboard
    - WSL: PowerShell Get-Clipboard
    - Linux: xclip or xsel

    Returns:
        Clipboard contents, or None if failed
    """
    try:
        if _PLATFORM == "darwin":
            result = subprocess.run(
                ["pbpaste"],
                capture_output=True,
                check=True,
            )
            return result.stdout.decode("utf-8")

        if _PLATFORM == "win32" or _IS_WSL:
            result = subprocess.run(
                ["powershell.exe", "-Command", "Get-Clipboard"],
                capture_output=True,
                check=True,
            )
            return result.stdout.decode("utf-8").rstrip("\r\n")

        # Linux: try xclip, then xsel
        for cmd in (
            ["xclip", "-selection", "clipboard", "-o"],
            ["xsel", "--clipboard", "--output"],
        ):
            try:
                result = subprocess.run(cmd, capture_output=True, check=True)
                return result.stdout.decode("utf-8")
            except (FileNotFoundError, subprocess.CalledProcessError):
                continue

        return None

    except Exception:
        return None


def is_clipboard_available() -> bool:
    """Check if clipboard operations are available.

    Returns:
        True if clipboard commands are available
    """
    try:
        if _PLATFORM == "darwin":
            subprocess.run(
                ["which", "pbcopy"],
                check=True,
                capture_output=True,
            )
            return True

        if _PLATFORM == "win32" or _IS_WSL:
            subprocess.run(
                ["which", "clip.exe"],
                check=True,
                capture_output=True,
            )
            return True

        # Linux: check for xclip or xsel
        for cmd in ["xclip", "xsel"]:
            try:
                subprocess.run(["which", cmd], check=True, capture_output=True)
                return True
            except subprocess.CalledProcessError:
                continue

        return False

    except Exception:
        return False
