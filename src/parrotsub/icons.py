"""Lucide-inspired SVG icons rendered to QIcon with theme-aware color."""

from __future__ import annotations

from typing import Dict, Optional

from PyQt6.QtCore import QByteArray, QSize, Qt
from PyQt6.QtGui import QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer


# All paths use stroke="currentColor"; we substitute the color at render time.
_LUCIDE: Dict[str, str] = {
    # Sidebar / brand
    "monitor-play": (
        '<rect width="20" height="14" x="2" y="3" rx="2"/>'
        '<path d="M12 17v4"/><path d="M8 21h8"/>'
        '<path d="m10 8 5 3-5 3Z" fill="currentColor"/>'
    ),
    # ParrotSub mascot/brand icon: stylised closed-caption box.
    "captions": (
        '<rect width="18" height="14" x="3" y="5" rx="3" ry="3"/>'
        '<path d="M7 15h4"/>'
        '<path d="M15 15h2"/>'
        '<path d="M7 11h2"/>'
        '<path d="M13 11h4"/>'
    ),
    "settings": (
        '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0'
        ' 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2'
        ' 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2'
        ' 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0'
        ' 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2'
        ' 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0'
        ' 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0'
        ' 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0'
        ' 0-2-2z"/>'
        '<circle cx="12" cy="12" r="3"/>'
    ),
    "download": (
        '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>'
        '<polyline points="7 10 12 15 17 10"/>'
        '<line x1="12" y1="15" x2="12" y2="3"/>'
    ),
    "github": (
        '<path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14'
        '-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S'
        '18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07'
        ' 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37'
        ' 0 0 0 9 18.13V22"/>'
    ),
    # Theme toggle
    "sun": (
        '<circle cx="12" cy="12" r="4"/>'
        '<path d="M12 2v2"/><path d="M12 20v2"/>'
        '<path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/>'
        '<path d="M2 12h2"/><path d="M20 12h2"/>'
        '<path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/>'
    ),
    "moon": (
        '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>'
    ),
    # Home actions
    "play": ('<polygon points="6 3 20 12 6 21 6 3"/>'),
    "square": ('<rect width="14" height="14" x="5" y="5" rx="2"/>'),
    "save": (
        '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>'
        '<polyline points="17 21 17 13 7 13 7 21"/>'
        '<polyline points="7 3 7 8 15 8"/>'
    ),
    "eye": (
        '<path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/>'
        '<circle cx="12" cy="12" r="3"/>'
    ),
    "eye-off": (
        '<path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/>'
        '<path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0'
        ' 0 1-1.67 2.68"/>'
        '<path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0'
        ' 5.39-1.61"/>'
        '<line x1="2" x2="22" y1="2" y2="22"/>'
    ),
    "languages": (
        '<path d="m5 8 6 6"/><path d="m4 14 6-6 2-3"/>'
        '<path d="M2 5h12"/><path d="M7 2h1"/><path d="m22 22-5-10-5 10"/>'
        '<path d="M14 18h6"/>'
    ),
    "rocket": (
        '<path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a'
        '2.18 2.18 0 0 0-2.91-.09z"/>'
        '<path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78'
        ' 7.5-6 11a22.35 22.35 0 0 1-4 2z"/>'
        '<path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/>'
        '<path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/>'
    ),
    "folder": (
        '<path d="M20 19a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82'
        '-1.2A2 2 0 0 0 7.93 2H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>'
    ),
    "refresh-cw": (
        '<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>'
        '<path d="M21 3v5h-5"/>'
        '<path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>'
        '<path d="M8 16H3v5"/>'
    ),
    "mic": (
        '<path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/>'
        '<path d="M19 10v2a7 7 0 0 1-14 0v-2"/>'
        '<line x1="12" x2="12" y1="19" y2="22"/>'
    ),
}


def lucide_svg(name: str, color: str = "#0f172a", size: int = 24, stroke: float = 2.0) -> bytes:
    """Return the SVG bytes for a named icon, recolored to ``color``."""
    body = _LUCIDE[name]
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        f'width="{size}" height="{size}" fill="none" stroke="{color}" '
        f'stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round">'
        f'{body}</svg>'
    )
    # Some inner paths use fill="currentColor"; substitute it too.
    svg = svg.replace("currentColor", color)
    return svg.encode("utf-8")


def make_icon(
    name: str,
    color: str = "#0f172a",
    size: int = 20,
    *,
    pixmap_size: Optional[int] = None,
) -> QIcon:
    """Render a Lucide icon to a crisp QIcon at the requested logical size."""
    pixmap_size = pixmap_size or (size * 2)
    svg_bytes = lucide_svg(name, color=color, size=size, stroke=1.8)
    renderer = QSvgRenderer(QByteArray(svg_bytes))
    pm = QPixmap(QSize(pixmap_size, pixmap_size))
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    renderer.render(painter)
    painter.end()
    icon = QIcon(pm)
    return icon
