"""Light/Dark theme palettes and Qt stylesheet (shadcn-style tokens)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    name: str

    background: str
    foreground: str

    card: str
    card_foreground: str

    popover: str
    popover_foreground: str

    primary: str
    primary_foreground: str

    secondary: str
    secondary_foreground: str

    muted: str
    muted_foreground: str

    accent: str
    accent_foreground: str

    destructive: str
    destructive_foreground: str

    border: str
    input: str
    ring: str

    sidebar: str
    sidebar_border: str

    success: str
    warning: str

    # ParrotSub brand accent (teal/parrot-feather), used for the brand
    # icon, the "Start recording" CTA and the active StatusPill state.
    brand: str
    brand_foreground: str
    brand_soft: str  # tinted background for the active sidebar slot

    radius: str = "8px"


# Light palette built from shadcn-style HSL tokens.
LIGHT = Palette(
    name="light",
    background="#ffffff",
    foreground="#0f172a",
    card="#ffffff",
    card_foreground="#0f172a",
    popover="#ffffff",
    popover_foreground="#0f172a",
    # ParrotSub: teal-600 primary so the brand colour leads the page.
    primary="#0d9488",
    primary_foreground="#ffffff",
    secondary="#f1f5f9",
    secondary_foreground="#0f172a",
    muted="#f1f5f9",
    muted_foreground="#64748b",
    accent="#f1f5f9",
    accent_foreground="#0f172a",
    destructive="#ef4444",
    destructive_foreground="#f8fafc",
    border="#e2e8f0",
    input="#e2e8f0",
    ring="#0d9488",
    sidebar="#fafafa",
    sidebar_border="#e5e7eb",
    success="#16a34a",
    warning="#f59e0b",
    brand="#0d9488",            # teal-600
    brand_foreground="#ffffff",
    brand_soft="#ccfbf1",       # teal-100
)

DARK = Palette(
    name="dark",
    background="#0b1220",
    foreground="#f8fafc",
    card="#0f172a",
    card_foreground="#f8fafc",
    popover="#0f172a",
    popover_foreground="#f8fafc",
    # ParrotSub: teal-500 primary keeps the brand colour readable on dark.
    primary="#14b8a6",
    primary_foreground="#04211e",
    secondary="#1e293b",
    secondary_foreground="#f8fafc",
    muted="#1e293b",
    muted_foreground="#94a3b8",
    accent="#1e293b",
    accent_foreground="#f8fafc",
    destructive="#7f1d1d",
    destructive_foreground="#f8fafc",
    border="#1e293b",
    input="#1e293b",
    ring="#14b8a6",
    sidebar="#0a1020",
    sidebar_border="#1e293b",
    success="#22c55e",
    warning="#facc15",
    brand="#14b8a6",            # teal-500
    brand_foreground="#04211e",
    brand_soft="#134e4a",       # teal-900
)


def stylesheet(p: Palette) -> str:
    """Return the full Qt stylesheet for the given palette."""
    return f"""
    /* ============================================================
       Base
       ============================================================ */
    QWidget {{
        background-color: {p.background};
        color: {p.foreground};
        font-family: -apple-system, "SF Pro Text", "Helvetica Neue", "PingFang SC",
            "Microsoft YaHei", sans-serif;
        font-size: 13px;
    }}

    QMainWindow, QDialog {{
        background-color: {p.background};
    }}

    QToolTip {{
        background-color: {p.popover};
        color: {p.popover_foreground};
        border: 1px solid {p.border};
        padding: 6px 10px;
        border-radius: 6px;
        font-size: 12px;
    }}

    /* ============================================================
       App shell pieces (objectName-scoped)
       ============================================================ */
    QFrame#Sidebar {{
        background-color: {p.sidebar};
        border: none;
        border-right: 1px solid {p.sidebar_border};
    }}

    QFrame#Header {{
        background-color: {p.background};
        border: none;
        border-bottom: 1px solid {p.border};
    }}

    QLabel#HeaderTitle {{
        font-size: 15px;
        font-weight: 600;
        color: {p.foreground};
    }}

    QLabel#HeaderVersion {{
        color: {p.muted_foreground};
        font-size: 11px;
    }}

    QFrame#StatusPill {{
        background-color: {p.muted};
        border: 1px solid {p.border};
        border-radius: 999px;
    }}

    QFrame#StatusPill[state="active"] {{
        background-color: {p.brand_soft};
        border-color: {p.brand};
    }}

    QFrame#StatusPill[state="warn"] {{
        background-color: rgba(245, 158, 11, 0.15);
        border-color: {p.warning};
    }}

    QLabel#StatusPillText {{
        color: {p.muted_foreground};
        font-size: 11px;
        font-weight: 500;
    }}

    QFrame#StatusPill[state="active"] QLabel#StatusPillText {{
        color: {p.brand};
    }}

    QFrame#StatusPill[state="warn"] QLabel#StatusPillText {{
        color: {p.warning};
    }}

    QFrame#StatusDot {{
        background-color: {p.muted_foreground};
        border-radius: 4px;
        min-width: 8px; max-width: 8px;
        min-height: 8px; max-height: 8px;
    }}

    QFrame#StatusPill[state="active"] QFrame#StatusDot {{
        background-color: {p.brand};
    }}

    QFrame#StatusPill[state="warn"] QFrame#StatusDot {{
        background-color: {p.warning};
    }}

    /* ============================================================
       Cards
       ============================================================ */
    QFrame#Card {{
        background-color: {p.card};
        border: 1px solid {p.border};
        border-radius: {p.radius};
    }}

    QLabel#CardTitle {{
        font-size: 14px;
        font-weight: 600;
        color: {p.card_foreground};
    }}

    QLabel#CardDescription {{
        font-size: 12px;
        color: {p.muted_foreground};
    }}

    QFrame#CardSeparator {{
        background-color: {p.border};
        max-height: 1px; min-height: 1px;
        border: none;
    }}

    /* ============================================================
       Buttons (shadcn-like)
       ============================================================ */
    QPushButton {{
        background-color: {p.primary};
        color: {p.primary_foreground};
        border: 1px solid {p.primary};
        border-radius: {p.radius};
        padding: 7px 14px;
        font-size: 13px;
        font-weight: 500;
        min-height: 18px;
    }}

    QPushButton:hover {{
        background-color: {_alpha_mix(p.primary, p.background, 0.9)};
    }}

    QPushButton:pressed {{
        background-color: {_alpha_mix(p.primary, p.background, 0.8)};
    }}

    QPushButton:disabled {{
        background-color: {p.muted};
        color: {p.muted_foreground};
        border-color: {p.border};
    }}

    QPushButton[variant="secondary"] {{
        background-color: {p.secondary};
        color: {p.secondary_foreground};
        border: 1px solid {p.border};
    }}
    QPushButton[variant="secondary"]:hover {{
        background-color: {p.muted};
    }}

    QPushButton[variant="outline"] {{
        background-color: transparent;
        color: {p.foreground};
        border: 1px solid {p.border};
    }}
    QPushButton[variant="outline"]:hover {{
        background-color: {p.muted};
    }}

    QPushButton[variant="ghost"] {{
        background-color: transparent;
        color: {p.foreground};
        border: 1px solid transparent;
    }}
    QPushButton[variant="ghost"]:hover {{
        background-color: {p.muted};
    }}

    QPushButton[variant="destructive"] {{
        background-color: {p.destructive};
        color: {p.destructive_foreground};
        border-color: {p.destructive};
    }}
    QPushButton[variant="destructive"]:hover {{
        background-color: {_alpha_mix(p.destructive, p.background, 0.9)};
    }}

    QPushButton[variant="success"] {{
        background-color: {p.success};
        color: #ffffff;
        border-color: {p.success};
    }}

    /* ============================================================
       Sidebar nav buttons (icon-only, 40x40, rounded)
       ============================================================ */
    QPushButton#NavButton {{
        background-color: transparent;
        border: 1px solid transparent;
        border-radius: {p.radius};
        padding: 0;
        min-width: 40px; max-width: 40px;
        min-height: 40px; max-height: 40px;
    }}
    QPushButton#NavButton:hover {{
        background-color: {p.muted};
    }}
    QPushButton#NavButton[active="true"] {{
        background-color: {p.brand_soft};
        border-color: {p.brand};
    }}

    /* ParrotSub brand button at the top of the sidebar uses the teal accent. */
    QPushButton#SidebarBrand {{
        background-color: {p.brand};
        border: 1px solid {p.brand};
        border-radius: 12px;
        padding: 0;
        min-width: 40px; max-width: 40px;
        min-height: 40px; max-height: 40px;
    }}
    QPushButton#SidebarBrand:hover {{
        background-color: {_alpha_mix(p.brand, p.background, 0.85)};
        border-color: {_alpha_mix(p.brand, p.background, 0.85)};
    }}

    /* ============================================================
       Inputs
       ============================================================ */
    QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QAbstractSpinBox {{
        background-color: {p.background};
        color: {p.foreground};
        border: 1px solid {p.input};
        border-radius: {p.radius};
        padding: 6px 10px;
        selection-background-color: {p.primary};
        selection-color: {p.primary_foreground};
    }}
    QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus,
    QSpinBox:focus, QDoubleSpinBox:focus {{
        border-color: {p.ring};
    }}

    /* shared subtitle viewer style */
    QTextEdit#SubtitleView {{
        background-color: {p.background};
        border: 1px solid {p.border};
        border-radius: {p.radius};
        padding: 12px 14px;
        font-size: 14px;
        line-height: 1.6;
    }}

    /* ============================================================
       ComboBox
       ============================================================ */
    QComboBox {{
        background-color: {p.background};
        color: {p.foreground};
        border: 1px solid {p.input};
        border-radius: {p.radius};
        padding: 6px 32px 6px 10px;
        min-height: 18px;
    }}
    QComboBox:hover {{ border-color: {p.muted_foreground}; }}
    QComboBox:focus {{ border-color: {p.ring}; }}

    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 28px;
        border: none;
    }}
    QComboBox::down-arrow {{
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid {p.muted_foreground};
        margin-right: 10px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {p.popover};
        color: {p.popover_foreground};
        border: 1px solid {p.border};
        border-radius: {p.radius};
        padding: 4px;
        outline: 0;
        selection-background-color: {p.muted};
        selection-color: {p.foreground};
    }}

    /* ============================================================
       Switch (a styled QCheckBox)
       ============================================================ */
    QCheckBox#Switch {{
        spacing: 10px;
        color: {p.foreground};
    }}
    QCheckBox#Switch::indicator {{
        width: 36px;
        height: 20px;
        border-radius: 10px;
        background-color: {p.muted};
        border: 1px solid {p.border};
    }}
    QCheckBox#Switch::indicator:checked {{
        background-color: {p.primary};
        border-color: {p.primary};
    }}
    QCheckBox#Switch::indicator:hover {{
        border-color: {p.muted_foreground};
    }}

    /* ============================================================
       Plain checkbox
       ============================================================ */
    QCheckBox {{
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 16px; height: 16px;
        border: 1px solid {p.input};
        border-radius: 4px;
        background-color: {p.background};
    }}
    QCheckBox::indicator:checked {{
        background-color: {p.primary};
        border-color: {p.primary};
    }}

    /* ============================================================
       Labels (form labels)
       ============================================================ */
    QLabel {{
        color: {p.foreground};
        background: transparent;
    }}

    QLabel[muted="true"] {{
        color: {p.muted_foreground};
    }}

    QLabel#FieldLabel {{
        color: {p.foreground};
        font-size: 12px;
        font-weight: 500;
    }}

    QLabel#FieldHint {{
        color: {p.muted_foreground};
        font-size: 11px;
    }}

    /* ============================================================
       Scroll area / scrollbar
       ============================================================ */
    QScrollArea {{
        background-color: transparent;
        border: none;
    }}
    QScrollArea > QWidget > QWidget {{
        background-color: transparent;
    }}

    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 4px 2px 4px 0;
    }}
    QScrollBar::handle:vertical {{
        background: {p.border};
        border-radius: 4px;
        min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {p.muted_foreground}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

    QScrollBar:horizontal {{
        background: transparent;
        height: 10px;
        margin: 0 4px 2px 4px;
    }}
    QScrollBar::handle:horizontal {{
        background: {p.border};
        border-radius: 4px;
        min-width: 24px;
    }}
    QScrollBar::handle:horizontal:hover {{ background: {p.muted_foreground}; }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

    /* ============================================================
       List views (Exports page, etc.)
       ============================================================ */
    QListWidget {{
        background-color: transparent;
        border: 1px solid {p.border};
        border-radius: {p.radius};
        padding: 4px;
        outline: 0;
    }}
    QListWidget::item {{
        padding: 10px 12px;
        border-radius: 6px;
        color: {p.foreground};
    }}
    QListWidget::item:selected {{
        background-color: {p.muted};
        color: {p.foreground};
    }}
    QListWidget::item:hover {{
        background-color: {p.muted};
    }}

    /* ============================================================
       Floating window
       ============================================================ */
    QFrame#FloatingRoot {{
        background-color: rgba(0, 0, 0, 160);
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 25);
    }}
    """


def _alpha_mix(fg_hex: str, bg_hex: str, fg_weight: float) -> str:
    """Mix two #rrggbb colors. Returns a #rrggbb string (no alpha).

    Used to fake hover/pressed states because Qt stylesheets do not
    support color-mix().
    """
    fr, fg, fb = _hex_to_rgb(fg_hex)
    br, bg, bb = _hex_to_rgb(bg_hex)
    w = max(0.0, min(1.0, fg_weight))
    r = int(fr * w + br * (1 - w))
    g = int(fg * w + bg * (1 - w))
    b = int(fb * w + bb * (1 - w))
    return f"#{r:02x}{g:02x}{b:02x}"


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    s = value.lstrip("#")
    if len(s) == 3:
        s = "".join(ch * 2 for ch in s)
    return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
