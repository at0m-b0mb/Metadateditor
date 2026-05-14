#!/usr/bin/env python3
"""MetaEditor — Universal Metadata Editor

A modern desktop app for reading, editing, and stripping metadata across
images, audio, video, PDFs, Office documents, e-books, and the filesystem.
"""

import copy
import json
import os
import platform
import shutil
import tempfile
import threading
import webbrowser
from collections import deque
from datetime import datetime

import customtkinter as ctk
from tkinter import filedialog, messagebox

from metadata_handlers import get_handler
from metadata_handlers.general_handler import GeneralHandler

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    _DND_AVAILABLE = True
except Exception:
    _DND_AVAILABLE = False

try:
    from PIL import Image as PILImage
    _PIL_AVAILABLE = True
except Exception:
    _PIL_AVAILABLE = False


# ══════════════════════════════════════════════════════════════════════════
# DESIGN SYSTEM
# ══════════════════════════════════════════════════════════════════════════

APP_VERSION = "2.0"
APP_DIR     = os.path.join(os.path.expanduser("~"), ".metaeditor")
SETTINGS    = os.path.join(APP_DIR, "settings.json")
MAX_RECENT  = 10
UNDO_LIMIT  = 100

# ── Spacing scale ──────────────────────────────────────────────────────────
SP_XS, SP_SM, SP_MD, SP_LG, SP_XL = 4, 8, 14, 22, 32

# ── Radius scale ───────────────────────────────────────────────────────────
R_SM, R_MD, R_LG, R_XL = 6, 10, 14, 18

# ── Colors (light, dark) tuples ────────────────────────────────────────────
# Inspired by Tailwind zinc + indigo, refined for a "premium" feel.

# Surface levels (lowest → highest elevation)
BG_ROOT      = ("#f5f5f7", "#09090f")        # outer window
BG_PANEL     = ("#ffffff", "#13131c")        # sidebar / status / header
BG_CARD      = ("#ffffff", "#1a1a26")        # main content surface
BG_CARD_2    = ("#f4f4f6", "#22222f")        # card-inside surfaces
BG_INPUT     = ("#f8f8fa", "#0f0f17")        # form inputs
BG_INPUT_RO  = ("#f0f0f3", "#171724")        # read-only inputs

# Borders (very subtle)
BORDER_HAIR  = ("#e5e5e8", "#2a2a3a")
BORDER_FOCUS = ("#a5b4fc", "#6366f1")

# Text
TX_PRIMARY   = ("#0f0f14", "#fafafa")
TX_SECONDARY = ("#52525b", "#a1a1aa")
TX_TERTIARY  = ("#71717a", "#71717a")
TX_DISABLED  = ("#a1a1aa", "#52525b")

# Accent (Indigo)
ACCENT       = "#6366f1"
ACCENT_HVR   = "#4f46e5"
ACCENT_SOFT  = ("#eef2ff", "#1e1b4b")
ACCENT_TEXT  = ("#4338ca", "#a5b4fc")

# Semantic colors
SUCCESS      = "#10b981"
SUCCESS_HVR  = "#059669"
SUCCESS_SOFT = ("#d1fae5", "#022c22")

WARN         = "#f59e0b"
WARN_HVR     = "#d97706"
WARN_SOFT    = ("#fef3c7", "#1c1607")

DANGER       = "#ef4444"
DANGER_HVR   = "#dc2626"
DANGER_SOFT  = ("#fee2e2", "#1f0808")

# Fonts
def font(size=12, weight="normal", mono=False):
    family = "SF Mono" if mono and platform.system() == "Darwin" else \
             "Menlo" if mono and platform.system() == "Darwin" else \
             "Consolas" if mono else \
             "Inter" if platform.system() != "Darwin" else None
    # CTk falls back gracefully if the font name isn't available
    return ctk.CTkFont(family=family, size=size, weight=weight) if family \
        else ctk.CTkFont(size=size, weight=weight)


# ── Section accent palette (each section type has its own vibe) ────────────
SECTION_ACCENTS = {
    "camera":    ("#3b82f6", "#dbeafe", "#1e3a8a"),   # blue
    "aperture":  ("#f59e0b", "#fef3c7", "#451a03"),   # amber
    "map-pin":   ("#ef4444", "#fee2e2", "#450a0a"),   # red
    "tag":       ("#8b5cf6", "#ede9fe", "#2e1065"),   # violet
    "music":     ("#10b981", "#d1fae5", "#022c22"),   # emerald
    "file":      ("#64748b", "#f1f5f9", "#0f172a"),   # slate
    "file-text": ("#0ea5e9", "#e0f2fe", "#082f49"),   # sky
    "monitor":   ("#06b6d4", "#cffafe", "#083344"),   # cyan
    "book-open": ("#ea580c", "#ffedd5", "#431407"),   # orange
    "alert":     ("#dc2626", "#fee2e2", "#450a0a"),   # red (urgent)
}

SECTION_ICONS = {
    "camera": "📷", "aperture": "🔍", "map-pin": "📍",
    "tag": "🏷",  "music":    "🎵", "file":    "📁",
    "file-text": "📄", "monitor": "🖥", "book-open": "📚",
    "alert": "⚠",
}

FILE_TYPE_BADGE = {
    "Image":             ("#3b82f6", "🖼"),
    "Audio / Video":     ("#10b981", "🎵"),
    "PDF Document":      ("#ef4444", "📄"),
    "Office / Document": ("#0ea5e9", "📝"),
    "General File":      ("#64748b", "📁"),
}

SUPPORTED_TYPES = [
    ("All Supported Files",
     "*.jpg *.jpeg *.jpe *.png *.tif *.tiff *.webp *.heic *.heif "
     "*.dng *.cr2 *.cr3 *.nef *.nrw *.arw *.sr2 *.rw2 *.orf *.raf *.pef "
     "*.mp3 *.flac *.ogg *.oga *.m4a *.m4b *.m4r *.aac *.wav *.aiff *.aif "
     "*.wma *.opus *.ape *.mpc *.wv *.mp2 *.dsf "
     "*.mp4 *.m4v *.mkv *.mka *.mov *.avi *.wmv *.webm *.3gp *.asf *.ogv "
     "*.pdf *.docx *.xlsx *.pptx *.epub"),
    ("Images",       "*.jpg *.jpeg *.png *.tif *.tiff *.webp *.heic *.heif"),
    ("RAW Images",   "*.dng *.cr2 *.cr3 *.nef *.arw *.rw2 *.orf *.raf *.pef"),
    ("Audio",        "*.mp3 *.flac *.ogg *.m4a *.wav *.aiff *.wma *.opus *.ape"),
    ("Video",        "*.mp4 *.mkv *.mov *.avi *.wmv *.webm"),
    ("Documents",    "*.pdf *.docx *.xlsx *.pptx *.epub"),
    ("All Files",    "*.*"),
]

PREVIEW_EXTS = {".jpg", ".jpeg", ".jpe", ".png", ".tif", ".tiff", ".webp",
                ".heic", ".heif", ".bmp", ".gif"}


# ══════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════

def fmt_size(b: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.1f} {unit}" if unit != "B" else f"{b} {unit}"
        b /= 1024
    return f"{b:.2f} TB"


def ext_upper(filename: str) -> str:
    parts = filename.rsplit(".", 1)
    return parts[-1].upper() if len(parts) > 1 else "?"


def load_settings() -> dict:
    try:
        os.makedirs(APP_DIR, exist_ok=True)
        with open(SETTINGS, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_settings(data: dict) -> None:
    try:
        os.makedirs(APP_DIR, exist_ok=True)
        with open(SETTINGS, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def mod_key():
    return "Command" if platform.system() == "Darwin" else "Control"


def mod_label():
    return "⌘" if platform.system() == "Darwin" else "Ctrl"


# ══════════════════════════════════════════════════════════════════════════
# TOAST NOTIFICATION
# ══════════════════════════════════════════════════════════════════════════

class Toast:
    """Floating notification at the bottom of the window."""

    def __init__(self, parent):
        self.parent = parent
        self._frame = None
        self._after = None

    def show(self, message, kind="info", duration=3200):
        self.dismiss()

        if kind == "success":
            accent, icon = SUCCESS, "✓"
            soft = SUCCESS_SOFT
        elif kind == "warn":
            accent, icon = WARN, "⚠"
            soft = WARN_SOFT
        elif kind == "error":
            accent, icon = DANGER, "✕"
            soft = DANGER_SOFT
        else:
            accent, icon = ACCENT, "ⓘ"
            soft = ACCENT_SOFT

        self._frame = ctk.CTkFrame(
            self.parent, fg_color=BG_PANEL,
            corner_radius=R_LG, border_width=1,
            border_color=BORDER_HAIR,
        )
        inner = ctk.CTkFrame(self._frame, fg_color="transparent")
        inner.pack(padx=SP_MD, pady=SP_MD)

        icon_lbl = ctk.CTkLabel(
            inner, text=icon,
            fg_color=soft, text_color=accent,
            corner_radius=R_SM, width=28, height=28,
            font=font(13, "bold"),
        )
        icon_lbl.pack(side="left", padx=(0, SP_MD))

        ctk.CTkLabel(
            inner, text=message,
            font=font(12, "normal"),
            text_color=TX_PRIMARY, anchor="w",
        ).pack(side="left", padx=(0, SP_SM))

        self._frame.place(relx=0.5, rely=1.0, anchor="s", y=-30)
        self._after = self.parent.after(duration, self.dismiss)

    def dismiss(self):
        if self._after:
            try:
                self.parent.after_cancel(self._after)
            except Exception:
                pass
            self._after = None
        if self._frame:
            try:
                self._frame.destroy()
            except Exception:
                pass
            self._frame = None


# Optional drag-and-drop base
if _DND_AVAILABLE:
    class _Base(ctk.CTk, TkinterDnD.DnDWrapper):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            self.TkdndVersion = TkinterDnD._require(self)
else:
    _Base = ctk.CTk


# ══════════════════════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════════════════════

class MetaEditorApp(_Base):

    def __init__(self):
        super().__init__()
        self.title(f"MetaEditor")
        self.geometry("1360x900")
        self.minsize(1080, 720)
        self.configure(fg_color=BG_ROOT)

        # ── Settings ──
        self._settings = load_settings()
        ctk.set_appearance_mode(self._settings.get("theme", "dark"))

        # ── State ──
        self._src_path  = None
        self._work_dir  = tempfile.mkdtemp(prefix="metaedit_")
        self._work_path = None
        self._handler   = None
        self._sections  = []
        self._originals = []

        # Widget maps
        self._vars:    dict = {}
        self._labels:  dict = {}
        self._mod_marks: dict = {}
        self._widgets: dict = {}
        self._rows:    dict = {}
        self._bodies:    dict = {}
        self._collapsed: dict = {}
        self._stat: dict = {}

        # Undo / Redo
        self._undo: deque = deque(maxlen=UNDO_LIMIT)
        self._redo: deque = deque(maxlen=UNDO_LIMIT)
        self._suppress_undo = False

        # Status / preview
        self._status_var = ctk.StringVar(value="Ready")
        self._preview_img_ref = None
        self._toast = Toast(self)

        # Filter mode: "all" | "editable" | "modified"
        self._filter_mode = "all"
        self._filter_btns: dict = {}
        self._empty_state = None

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_layout()
        self._bind_shortcuts()
        if _DND_AVAILABLE:
            self.drop_target_register(DND_FILES)
            self.dnd_bind("<<Drop>>", self._on_drop)

    # ── Lifecycle ──────────────────────────────────────────────────────────

    def _on_close(self):
        shutil.rmtree(self._work_dir, ignore_errors=True)
        save_settings(self._settings)
        self.destroy()

    # ── Keyboard shortcuts ─────────────────────────────────────────────────

    def _bind_shortcuts(self):
        m = mod_key()
        self.bind_all(f"<{m}-o>",       lambda e: self._pick_file())
        self.bind_all(f"<{m}-s>",       lambda e: self._save_in_place())
        self.bind_all(f"<{m}-Shift-S>", lambda e: self._save_file())
        self.bind_all(f"<{m}-z>",       lambda e: self._undo_action())
        self.bind_all(f"<{m}-y>",       lambda e: self._redo_action())
        self.bind_all(f"<{m}-Shift-Z>", lambda e: self._redo_action())
        self.bind_all(f"<{m}-f>",       lambda e: self._focus_search())
        self.bind_all(f"<{m}-r>",       lambda e: self._reset_changes())

    def _focus_search(self):
        if hasattr(self, "_search_entry"):
            try:
                self._search_entry.focus_set()
            except Exception:
                pass

    # ──────────────────────────────────────────────────────────────────────
    # LAYOUT
    # ──────────────────────────────────────────────────────────────────────

    def _build_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_header()
        self._build_sidebar()
        self._build_content()
        self._build_statusbar()

    # ── Header ─────────────────────────────────────────────────────────────

    def _build_header(self):
        hdr = ctk.CTkFrame(self, height=72, corner_radius=0, fg_color=BG_PANEL)
        hdr.grid(row=0, column=0, columnspan=2, sticky="ew")
        hdr.grid_propagate(False)
        hdr.grid_columnconfigure(2, weight=1)

        # Subtle bottom border via thin frame
        sep = ctk.CTkFrame(self, height=1, corner_radius=0, fg_color=BORDER_HAIR)
        sep.grid(row=0, column=0, columnspan=2, sticky="sew")

        # ── Brand ──
        brand = ctk.CTkFrame(hdr, fg_color="transparent")
        brand.grid(row=0, column=0, padx=(SP_LG, SP_LG), pady=SP_MD)

        # Gradient-feel logo badge
        logo = ctk.CTkLabel(
            brand, text="⚡",
            fg_color=ACCENT, text_color="#ffffff",
            corner_radius=R_MD, width=42, height=42,
            font=font(18, "bold"),
        )
        logo.grid(row=0, column=0, rowspan=2, padx=(0, SP_MD))

        ctk.CTkLabel(brand, text="MetaEditor",
                     font=font(20, "bold"), text_color=TX_PRIMARY,
                     ).grid(row=0, column=1, sticky="sw")
        ctk.CTkLabel(brand, text=f"v{APP_VERSION}  ·  Universal Metadata Editor",
                     font=font(11), text_color=TX_TERTIARY,
                     ).grid(row=1, column=1, sticky="nw")

        # ── File type badge (gridded after load) ──
        self._badge_wrap = ctk.CTkFrame(hdr, fg_color="transparent")
        self._badge_icon = ctk.CTkLabel(
            self._badge_wrap, text="", text_color="#ffffff",
            corner_radius=R_SM, width=24, height=24,
            font=font(12, "bold"),
        )
        self._badge_label = ctk.CTkLabel(
            self._badge_wrap, text="", text_color=TX_PRIMARY,
            font=font(12, "bold"),
        )

        # ── Right-aligned action row ──
        btns = ctk.CTkFrame(hdr, fg_color="transparent")
        btns.grid(row=0, column=3, padx=SP_LG, pady=SP_MD)

        self._recent_btn = self._mk_btn(
            btns, text="Recent  ▾", command=self._show_recent_menu,
            variant="ghost", width=92,
        )
        self._recent_btn.pack(side="left", padx=(0, SP_SM))

        self._btn_open = self._mk_btn(
            btns, text="Open File", command=self._pick_file,
            variant="ghost", width=104, icon="📂",
        )
        self._btn_open.pack(side="left", padx=(0, SP_SM))

        self._btn_save_inplace = self._mk_btn(
            btns, text="Save", command=self._save_in_place,
            variant="success", width=92, icon="💾",
            state="disabled",
        )
        self._btn_save_inplace.pack(side="left", padx=(0, SP_SM))

        self._btn_save = self._mk_btn(
            btns, text="Save As…", command=self._save_file,
            variant="primary", width=110,
            state="disabled",
        )
        self._btn_save.pack(side="left", padx=(0, SP_SM))

        self._btn_theme = self._mk_btn(
            btns, text=self._theme_icon(), command=self._toggle_theme,
            variant="ghost", width=44,
        )
        self._btn_theme.pack(side="left")

    def _theme_icon(self):
        return "☀" if ctk.get_appearance_mode() == "Dark" else "☾"

    def _toggle_theme(self):
        new = "light" if ctk.get_appearance_mode() == "Dark" else "dark"
        ctk.set_appearance_mode(new)
        self._settings["theme"] = new
        save_settings(self._settings)
        self._btn_theme.configure(text=self._theme_icon())
        self._toast.show(f"Switched to {new} mode", kind="info", duration=2000)

    # ── Button factory ─────────────────────────────────────────────────────

    def _mk_btn(self, parent, text, command, variant="ghost",
                width=None, icon=None, state="normal", height=38):
        if icon:
            text = f"{icon}  {text}"

        if variant == "primary":
            fg, hvr, txt = ACCENT, ACCENT_HVR, "#ffffff"
        elif variant == "success":
            fg, hvr, txt = SUCCESS, SUCCESS_HVR, "#ffffff"
        elif variant == "danger":
            fg, hvr, txt = DANGER, DANGER_HVR, "#ffffff"
        else:  # ghost
            fg, hvr, txt = BG_CARD_2, BORDER_HAIR, TX_PRIMARY

        return ctk.CTkButton(
            parent, text=text, command=command,
            fg_color=fg, hover_color=hvr, text_color=txt,
            width=width or 100, height=height, corner_radius=R_MD,
            font=font(12, "bold"),
            state=state,
        )

    # ── Recent menu ────────────────────────────────────────────────────────

    def _show_recent_menu(self):
        recents = self._settings.get("recent", [])
        if not recents:
            self._toast.show("No recent files yet — open one first", kind="warn")
            return

        menu = ctk.CTkToplevel(self)
        menu.title("Recent Files")
        menu.geometry("560x420")
        menu.transient(self)
        menu.configure(fg_color=BG_ROOT)

        hdr = ctk.CTkFrame(menu, fg_color="transparent")
        hdr.pack(fill="x", padx=SP_LG, pady=(SP_LG, SP_SM))

        ctk.CTkLabel(hdr, text="Recent Files", anchor="w",
                     font=font(16, "bold"), text_color=TX_PRIMARY,
                     ).pack(side="left")
        ctk.CTkLabel(hdr, text=f"{len(recents)} file{'s' if len(recents)!=1 else ''}",
                     anchor="e", font=font(11), text_color=TX_TERTIARY,
                     ).pack(side="right")

        scr = ctk.CTkScrollableFrame(
            menu, fg_color=BG_PANEL, corner_radius=R_LG,
        )
        scr.pack(fill="both", expand=True, padx=SP_LG, pady=(SP_SM, SP_SM))

        for path in recents:
            exists = os.path.exists(path)
            name = os.path.basename(path)
            ext  = os.path.splitext(path)[1].upper().lstrip(".") or "FILE"

            row = ctk.CTkFrame(scr, fg_color=BG_CARD_2, corner_radius=R_MD)
            row.pack(fill="x", padx=SP_SM, pady=4)
            row.grid_columnconfigure(1, weight=1)

            tag = ctk.CTkLabel(
                row, text=ext, fg_color=ACCENT_SOFT,
                text_color=ACCENT_TEXT, corner_radius=R_SM,
                width=46, height=26, font=font(10, "bold"),
            )
            tag.grid(row=0, column=0, rowspan=2, padx=(SP_MD, SP_MD), pady=SP_SM)

            ctk.CTkLabel(
                row, text=name, anchor="w",
                font=font(12, "bold"),
                text_color=TX_PRIMARY if exists else TX_DISABLED,
            ).grid(row=0, column=1, sticky="ew", pady=(SP_SM, 0))

            sub = path if exists else "⚠ file no longer exists"
            ctk.CTkLabel(
                row, text=sub, anchor="w",
                font=font(10), text_color=TX_TERTIARY,
            ).grid(row=1, column=1, sticky="ew", pady=(0, SP_SM))

            if exists:
                self._mk_btn(
                    row, text="Open", variant="ghost", width=72, height=28,
                    command=lambda p=path, m=menu: (m.destroy(), self._load_path(p)),
                ).grid(row=0, column=2, rowspan=2, padx=SP_MD)

        # Footer
        ftr = ctk.CTkFrame(menu, fg_color="transparent")
        ftr.pack(fill="x", padx=SP_LG, pady=(0, SP_LG))

        self._mk_btn(
            ftr, text="Clear Recent Files", variant="danger", width=180,
            command=lambda: (self._settings.update({"recent": []}),
                             save_settings(self._settings), menu.destroy(),
                             self._toast.show("Cleared recent files", kind="info")),
        ).pack(side="right")

    def _push_recent(self, path):
        recents = self._settings.get("recent", [])
        if path in recents:
            recents.remove(path)
        recents.insert(0, path)
        self._settings["recent"] = recents[:MAX_RECENT]
        save_settings(self._settings)

    # ── Sidebar ────────────────────────────────────────────────────────────

    def _build_sidebar(self):
        # The sidebar is a panel surface, with cards arranged inside
        self._sidebar = ctk.CTkFrame(self, width=316, corner_radius=0,
                                     fg_color=BG_PANEL)
        self._sidebar.grid(row=1, column=0, sticky="nsew")
        self._sidebar.grid_propagate(False)
        self._sidebar.grid_columnconfigure(0, weight=1)
        self._sidebar.grid_rowconfigure(1, weight=1)

        # Vertical separator
        sep = ctk.CTkFrame(self, width=1, fg_color=BORDER_HAIR, corner_radius=0)
        sep.grid(row=1, column=0, sticky="nse")

        # ── Welcome card (visible until a file is loaded) ──
        self._welcome_side = ctk.CTkFrame(self._sidebar, fg_color="transparent")
        self._welcome_side.grid(row=0, column=0, padx=SP_LG, pady=(SP_LG, SP_SM), sticky="ew")

        wcard = ctk.CTkFrame(
            self._welcome_side, fg_color=BG_CARD,
            corner_radius=R_LG, border_width=1, border_color=BORDER_HAIR,
        )
        wcard.pack(fill="x")

        ctk.CTkLabel(wcard, text="📂",
                     font=font(46), text_color=TX_PRIMARY,
                     ).pack(pady=(SP_LG, SP_SM))
        ctk.CTkLabel(wcard, text="No file open",
                     font=font(14, "bold"), text_color=TX_PRIMARY,
                     ).pack()
        msg = "Choose a file to view\nand edit its metadata"
        if _DND_AVAILABLE:
            msg += "\n\nor drop one onto the window"
        ctk.CTkLabel(wcard, text=msg, justify="center",
                     font=font(11), text_color=TX_TERTIARY,
                     ).pack(pady=(SP_SM, SP_LG))

        self._mk_btn(
            wcard, text="Browse Files…", command=self._pick_file,
            variant="primary", width=200, icon="📁",
        ).pack(padx=SP_LG, pady=(0, SP_LG))

        # ── File-info side (filled when a file loads) ──
        self._file_side = ctk.CTkFrame(self._sidebar, fg_color="transparent")
        self._stats_panel  = ctk.CTkFrame(self._sidebar, fg_color="transparent")
        self._action_panel = ctk.CTkFrame(self._sidebar, fg_color="transparent")

    def _refresh_sidebar(self, filename, file_type, file_size, fmt):
        for w in self._file_side.winfo_children():
            w.destroy()

        # ── File card: preview / icon + name + meta ──
        card = ctk.CTkFrame(
            self._file_side, fg_color=BG_CARD,
            corner_radius=R_LG, border_width=1, border_color=BORDER_HAIR,
        )
        card.pack(fill="x")

        # Image preview, or large icon fallback
        ext = os.path.splitext(self._src_path)[1].lower()
        preview_drawn = False
        if _PIL_AVAILABLE and ext in PREVIEW_EXTS:
            try:
                pil = PILImage.open(self._src_path)
                pil.thumbnail((260, 220), PILImage.LANCZOS)
                self._preview_img_ref = ctk.CTkImage(
                    light_image=pil, dark_image=pil,
                    size=(pil.width, pil.height),
                )
                preview_holder = ctk.CTkFrame(
                    card, fg_color=BG_CARD_2, corner_radius=R_MD,
                )
                preview_holder.pack(fill="x", padx=SP_MD, pady=(SP_MD, SP_SM))
                ctk.CTkLabel(preview_holder, image=self._preview_img_ref, text="",
                             ).pack(pady=SP_SM)
                preview_drawn = True
            except Exception:
                preview_drawn = False

        if not preview_drawn:
            color, icon = FILE_TYPE_BADGE.get(file_type, (ACCENT, "📁"))
            icon_holder = ctk.CTkFrame(
                card, fg_color=color, corner_radius=R_MD,
                width=72, height=72,
            )
            icon_holder.pack(pady=(SP_LG, SP_SM))
            icon_holder.pack_propagate(False)
            ctk.CTkLabel(icon_holder, text=icon, text_color="#ffffff",
                         font=font(32),
                         ).place(relx=0.5, rely=0.5, anchor="center")

        # Filename
        ctk.CTkLabel(
            card, text=filename, wraplength=260, justify="center",
            font=font(13, "bold"), text_color=TX_PRIMARY,
        ).pack(padx=SP_MD, pady=(SP_SM, SP_MD))

        # Meta rows
        meta = ctk.CTkFrame(card, fg_color="transparent")
        meta.pack(fill="x", padx=SP_MD, pady=(0, SP_MD))
        meta.grid_columnconfigure(1, weight=1)

        rows = [("Type", file_type), ("Size", fmt_size(file_size)), ("Format", fmt)]
        for i, (lbl, val) in enumerate(rows):
            ctk.CTkLabel(meta, text=lbl.upper(), anchor="w",
                         font=font(9, "bold"), text_color=TX_TERTIARY,
                         ).grid(row=i, column=0, padx=SP_SM, pady=3, sticky="w")
            ctk.CTkLabel(meta, text=val, anchor="e",
                         font=font(11, "bold"), text_color=TX_PRIMARY,
                         ).grid(row=i, column=1, padx=SP_SM, pady=3, sticky="e")

        # Open different file
        self._mk_btn(
            card, text="Open Different File", command=self._pick_file,
            variant="ghost", width=240, height=34,
        ).pack(padx=SP_MD, pady=(SP_SM, SP_MD), fill="x")

        # ── Stats card ──
        for w in self._stats_panel.winfo_children():
            w.destroy()
        stats_card = ctk.CTkFrame(
            self._stats_panel, fg_color=BG_CARD,
            corner_radius=R_LG, border_width=1, border_color=BORDER_HAIR,
        )
        stats_card.pack(fill="x")

        ctk.CTkLabel(stats_card, text="OVERVIEW",
                     font=font(9, "bold"), text_color=TX_TERTIARY, anchor="w",
                     ).pack(fill="x", padx=SP_MD, pady=(SP_MD, 2))

        stats_inner = ctk.CTkFrame(stats_card, fg_color="transparent")
        stats_inner.pack(fill="x", padx=SP_SM, pady=(SP_SM, SP_MD))
        stats_inner.grid_columnconfigure((0, 1, 2), weight=1)

        self._stat = {k: ctk.StringVar(value="0")
                      for k in ("total", "editable", "changed")}
        stat_meta = [
            ("total",    "Fields",   TX_PRIMARY),
            ("editable", "Editable", ACCENT_TEXT),
            ("changed",  "Modified", ("#0891b2", "#34d399")),
        ]
        for i, (key, lbl, color) in enumerate(stat_meta):
            cell = ctk.CTkFrame(stats_inner, fg_color=BG_CARD_2,
                                corner_radius=R_MD)
            cell.grid(row=0, column=i, padx=3, pady=2, sticky="ew")
            ctk.CTkLabel(cell, textvariable=self._stat[key],
                         font=font(20, "bold"), text_color=color,
                         ).pack(pady=(SP_SM, 0))
            ctk.CTkLabel(cell, text=lbl,
                         font=font(9, "bold"), text_color=TX_TERTIARY,
                         ).pack(pady=(0, SP_SM))

        # ── Tools card ──
        for w in self._action_panel.winfo_children():
            w.destroy()
        tools_card = ctk.CTkFrame(
            self._action_panel, fg_color=BG_CARD,
            corner_radius=R_LG, border_width=1, border_color=BORDER_HAIR,
        )
        tools_card.pack(fill="x")

        ctk.CTkLabel(tools_card, text="TOOLS",
                     font=font(9, "bold"), text_color=TX_TERTIARY, anchor="w",
                     ).pack(fill="x", padx=SP_MD, pady=(SP_MD, SP_SM))

        for txt, cmd, icon, variant in [
            ("Export Metadata as JSON", self._export_json, "📤", "ghost"),
            ("Import Metadata from JSON", self._import_json, "📥", "ghost"),
            ("Strip All Metadata",      self._strip_all,   "🗑", "danger"),
        ]:
            self._mk_btn(
                tools_card, text=txt, command=cmd, variant=variant,
                icon=icon, height=32,
            ).pack(fill="x", padx=SP_MD, pady=2)

        ctk.CTkFrame(tools_card, fg_color="transparent", height=SP_SM
                     ).pack()

        # Show file side, hide welcome
        self._welcome_side.grid_remove()
        self._file_side.grid(row=0, column=0, padx=SP_LG, pady=(SP_LG, SP_SM), sticky="ew")
        self._stats_panel.grid(row=2, column=0, padx=SP_LG, pady=(0, SP_SM), sticky="ew")
        self._action_panel.grid(row=3, column=0, padx=SP_LG, pady=(0, SP_LG), sticky="ew")

    # ── Content ────────────────────────────────────────────────────────────

    def _build_content(self):
        self._content = ctk.CTkFrame(self, corner_radius=0, fg_color=BG_ROOT)
        self._content.grid(row=1, column=1, sticky="nsew")
        self._content.grid_columnconfigure(0, weight=1)
        self._content.grid_rowconfigure(1, weight=1)

        # Welcome splash
        self._welcome_main = ctk.CTkFrame(self._content, fg_color="transparent")
        self._welcome_main.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self._content.grid_rowconfigure(0, weight=1)
        self._build_welcome_splash(self._welcome_main)

        # Toolbar
        self._toolbar = ctk.CTkFrame(self._content, height=60, corner_radius=0,
                                     fg_color=BG_ROOT)
        self._search_var = ctk.StringVar()
        self._search_var.trace("w", self._on_search)

        # Search with prefix icon hack: place a label on top of the entry
        search_wrap = ctk.CTkFrame(self._toolbar, fg_color="transparent")
        self._search_wrap = search_wrap
        self._search_entry = ctk.CTkEntry(
            search_wrap, textvariable=self._search_var,
            placeholder_text="    Search fields by name or value…",
            width=340, height=38, corner_radius=R_MD,
            fg_color=BG_PANEL, border_color=BORDER_HAIR,
            text_color=TX_PRIMARY,
            font=font(12),
        )
        self._search_entry.pack(side="left")
        ctk.CTkLabel(self._search_entry, text="🔍",
                     fg_color="transparent", text_color=TX_TERTIARY,
                     font=font(12),
                     ).place(x=10, y=10)

        # Filter pills — quick way to focus on Editable / Modified fields only
        self._filter_wrap = ctk.CTkFrame(self._toolbar, fg_color=BG_CARD,
                                         corner_radius=R_MD, border_width=1,
                                         border_color=BORDER_HAIR)
        for key, label in (("all", "All"), ("editable", "Editable"), ("modified", "Modified")):
            btn = ctk.CTkButton(
                self._filter_wrap, text=label,
                command=lambda k=key: self._set_filter_mode(k),
                fg_color="transparent", text_color=TX_SECONDARY,
                hover_color=BG_CARD_2,
                width=82, height=30, corner_radius=R_SM,
                font=font(11, "bold"),
            )
            btn.pack(side="left", padx=2, pady=2)
            self._filter_btns[key] = btn

        self._btn_expand   = self._mk_btn(self._toolbar, text="Expand All",   command=self._expand_all,   variant="ghost", width=104, height=38)
        self._btn_collapse = self._mk_btn(self._toolbar, text="Collapse All", command=self._collapse_all, variant="ghost", width=110, height=38)
        self._btn_reset    = self._mk_btn(self._toolbar, text="Reset",        command=self._reset_changes, variant="ghost", width=80,  height=38, icon="↺")
        self._btn_undo     = self._mk_btn(self._toolbar, text="Undo",         command=self._undo_action,   variant="ghost", width=80,  height=38, icon="↶")
        self._btn_redo     = self._mk_btn(self._toolbar, text="Redo",         command=self._redo_action,   variant="ghost", width=80,  height=38, icon="↷")

        # Scrollable card stack
        self._scroll = ctk.CTkScrollableFrame(
            self._content, fg_color="transparent", corner_radius=0,
        )

    def _build_welcome_splash(self, parent):
        # Use a scrollable container so the splash never gets cut off on smaller windows
        outer = ctk.CTkScrollableFrame(parent, fg_color="transparent",
                                       corner_radius=0)
        outer.pack(fill="both", expand=True)

        inner = ctk.CTkFrame(outer, fg_color="transparent")
        inner.pack(pady=(SP_XL, SP_XL))

        # Hero
        ctk.CTkLabel(
            inner, text="⚡",
            fg_color=ACCENT, text_color="#ffffff",
            corner_radius=R_XL, width=88, height=88,
            font=font(40, "bold"),
        ).pack(pady=(0, SP_MD))

        ctk.CTkLabel(
            inner, text="MetaEditor",
            font=font(34, "bold"), text_color=TX_PRIMARY,
        ).pack()
        ctk.CTkLabel(
            inner, text="One desktop app for every kind of file metadata.",
            font=font(13), text_color=TX_SECONDARY,
        ).pack(pady=(2, SP_LG))

        # CTA
        cta_row = ctk.CTkFrame(inner, fg_color="transparent")
        cta_row.pack(pady=(0, SP_LG))
        self._mk_btn(
            cta_row, text="Open File", icon="📂",
            command=self._pick_file, variant="primary",
            width=170, height=44,
        ).pack(side="left", padx=SP_SM)
        if self._settings.get("recent"):
            self._mk_btn(
                cta_row, text="Show All Recent", command=self._show_recent_menu,
                variant="ghost", width=160, height=44,
            ).pack(side="left", padx=SP_SM)

        # ── Recents inline (top 4) ──
        recents = (self._settings.get("recent") or [])[:4]
        if recents:
            rec_label = ctk.CTkLabel(
                inner, text="RECENT FILES",
                font=font(9, "bold"), text_color=TX_TERTIARY,
            )
            rec_label.pack(pady=(SP_MD, SP_SM))

            rec_grid = ctk.CTkFrame(inner, fg_color="transparent")
            rec_grid.pack(pady=(0, SP_LG))

            for i, path in enumerate(recents):
                exists = os.path.exists(path)
                name = os.path.basename(path)
                ext  = os.path.splitext(path)[1].upper().lstrip(".") or "FILE"
                dirname = os.path.dirname(path) or "/"
                if len(dirname) > 36:
                    dirname = "…" + dirname[-34:]

                card = ctk.CTkFrame(
                    rec_grid, fg_color=BG_CARD,
                    corner_radius=R_MD, border_width=1, border_color=BORDER_HAIR,
                )
                card.grid(row=i // 2, column=i % 2, padx=SP_SM, pady=SP_SM, sticky="ew")
                card.configure(width=260, height=66)
                card.grid_propagate(False)

                tag = ctk.CTkLabel(
                    card, text=ext, fg_color=ACCENT_SOFT,
                    text_color=ACCENT_TEXT, corner_radius=R_SM,
                    width=44, height=24, font=font(9, "bold"),
                )
                tag.place(x=12, y=12)

                ctk.CTkLabel(card, text=name, anchor="w",
                             font=font(12, "bold"),
                             text_color=TX_PRIMARY if exists else TX_DISABLED,
                             ).place(x=64, y=8)
                sub = dirname if exists else "⚠ file no longer exists"
                ctk.CTkLabel(card, text=sub, anchor="w",
                             font=font(10), text_color=TX_TERTIARY,
                             ).place(x=64, y=30)

                # Make the card clickable
                if exists:
                    def _open(p=path):
                        self._load_path(p)

                    for w in (card, tag):
                        w.bind("<Button-1>", lambda _e, fn=_open: fn())
                    card.configure(cursor="hand2")

        # Feature grid
        grid = ctk.CTkFrame(inner, fg_color="transparent")
        grid.pack()
        features = [
            ("🖼", "50+ formats",
             "Images, RAW, audio, video,\nPDF, Office, EPUB"),
            ("💾", "Safe saves",
             "Save As, Save In Place with\nautomatic .bak backup"),
            ("🗑", "Privacy first",
             "Strip EXIF, ID3, xattrs &\nOffice props in one click"),
            ("📤", "JSON I/O",
             "Export, import, and template\nmetadata between files"),
        ]
        for i, (ico, title, desc) in enumerate(features):
            card = ctk.CTkFrame(
                grid, fg_color=BG_CARD,
                corner_radius=R_LG, border_width=1, border_color=BORDER_HAIR,
            )
            card.grid(row=i // 2, column=i % 2, padx=SP_SM, pady=SP_SM, sticky="ew")
            card.configure(width=260, height=110)
            card.grid_propagate(False)

            ctk.CTkLabel(card, text=ico,
                         fg_color=ACCENT_SOFT, text_color=ACCENT_TEXT,
                         corner_radius=R_SM, width=32, height=32,
                         font=font(15, "bold"),
                         ).place(x=14, y=14)
            ctk.CTkLabel(card, text=title, anchor="w",
                         font=font(13, "bold"), text_color=TX_PRIMARY,
                         ).place(x=58, y=14)
            ctk.CTkLabel(card, text=desc, anchor="nw", justify="left",
                         font=font(11), text_color=TX_TERTIARY,
                         ).place(x=14, y=52)

        # Shortcuts strip
        m = mod_label()
        shortcuts = (
            f"{m}+O  Open    "
            f"{m}+S  Save    "
            f"{m}+⇧+S  Save As    "
            f"{m}+Z  Undo    "
            f"{m}+F  Search"
        )
        ctk.CTkLabel(
            inner, text=shortcuts,
            font=font(11), text_color=TX_TERTIARY,
        ).pack(pady=(SP_LG, 0))

    def _show_toolbar_and_scroll(self):
        self._welcome_main.grid_remove()
        self._content.grid_rowconfigure(0, weight=0)
        self._content.grid_rowconfigure(1, weight=1)

        self._toolbar.grid(row=0, column=0, sticky="ew", padx=SP_LG, pady=(SP_LG, SP_SM))
        self._search_wrap.pack(side="left", padx=(0, SP_MD), pady=SP_SM)
        self._filter_wrap.pack(side="left", padx=(0, SP_MD), pady=SP_SM)
        self._btn_expand.pack(side="left",   padx=SP_XS, pady=SP_SM)
        self._btn_collapse.pack(side="left", padx=SP_XS, pady=SP_SM)
        self._btn_reset.pack(side="left",    padx=SP_XS, pady=SP_SM)
        self._btn_redo.pack(side="right", padx=(SP_XS, 0), pady=SP_SM)
        self._btn_undo.pack(side="right", padx=SP_XS, pady=SP_SM)

        self._scroll.grid(row=1, column=0, sticky="nsew", padx=SP_LG, pady=(SP_SM, SP_LG))
        self._set_filter_mode("all")  # initialize chip styles

    # ── Status bar ─────────────────────────────────────────────────────────

    def _build_statusbar(self):
        sep = ctk.CTkFrame(self, height=1, corner_radius=0, fg_color=BORDER_HAIR)
        sep.grid(row=2, column=0, columnspan=2, sticky="new")

        bar = ctk.CTkFrame(self, height=28, corner_radius=0, fg_color=BG_PANEL)
        bar.grid(row=3, column=0, columnspan=2, sticky="ew")
        bar.grid_propagate(False)
        bar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(bar, textvariable=self._status_var,
                     anchor="w", font=font(11),
                     text_color=TX_SECONDARY,
                     ).grid(row=0, column=0, padx=SP_LG, sticky="w")

        version_bits = [f"v{APP_VERSION}"]
        if _DND_AVAILABLE:
            version_bits.append("drag-drop")
        if _PIL_AVAILABLE:
            version_bits.append("image preview")
        ctk.CTkLabel(bar, text="  ·  ".join(version_bits),
                     anchor="e", font=font(10), text_color=TX_TERTIARY,
                     ).grid(row=0, column=2, padx=SP_LG, sticky="e")

    def _set_status(self, text):
        self._status_var.set(text)
        self.after(5000, lambda t=text: (self._status_var.set("Ready")
                                         if self._status_var.get() == t else None))

    # ──────────────────────────────────────────────────────────────────────
    # FILE OPERATIONS
    # ──────────────────────────────────────────────────────────────────────

    def _pick_file(self):
        path = filedialog.askopenfilename(
            title="Open File — MetaEditor",
            filetypes=SUPPORTED_TYPES,
        )
        if path:
            self._load_path(path)

    def _load_path(self, path):
        if not os.path.exists(path):
            messagebox.showerror("File not found", f"Cannot find:\n{path}", parent=self)
            return

        ext = os.path.splitext(path)[1].lower()
        work = os.path.join(self._work_dir, "working" + ext)
        try:
            shutil.copy2(path, work)
        except Exception as e:
            messagebox.showerror("Cannot copy", str(e), parent=self)
            return

        self._src_path  = path
        self._work_path = work

        self._btn_open.configure(state="disabled", text="Loading…")
        self._set_status(f"Loading {os.path.basename(path)}…")
        threading.Thread(target=self._load_thread, daemon=True).start()

    def _on_drop(self, event):
        raw = event.data.strip()
        if not raw:
            return
        if raw.startswith("{"):
            end = raw.find("}")
            path = raw[1:end] if end > 0 else raw[1:]
        else:
            path = raw.split()[0]
        self._load_path(path)

    def _load_thread(self):
        try:
            ext     = os.path.splitext(self._work_path)[1].lower()
            handler = get_handler(ext, self._work_path)
            load_warning = None

            if isinstance(handler, GeneralHandler):
                # Unsupported format — show only the source file's filesystem
                # properties (NOT the temp copy's, which would show a fresh
                # birthtime instead of the original).
                handler  = GeneralHandler(self._src_path)
                sections = handler.read()
            else:
                try:
                    sections = handler.read()
                except Exception as inner:
                    # Format-specific handler crashed (corrupt header, missing
                    # codec, etc.). Fall back so the user can still edit dates
                    # and other filesystem properties.
                    label = (ext or "file").lstrip(".").upper() or "file"
                    load_warning = (
                        f"Couldn't parse {label} metadata "
                        f"({inner.__class__.__name__}). "
                        "Filesystem properties are still editable."
                    )
                    handler  = GeneralHandler(self._src_path)
                    sections = []

                # Always append filesystem properties of the original file.
                if not any(s.get("_general") for s in sections):
                    sections += GeneralHandler(self._src_path).read()

            self._handler      = handler
            self._sections     = sections
            self._originals    = copy.deepcopy(sections)
            self._load_warning = load_warning

            size     = os.path.getsize(self._src_path)
            filename = os.path.basename(self._src_path)
            fmt      = ext_upper(self._src_path)
            ftype    = handler.file_type

            self.after(0, lambda: self._on_loaded(filename, ftype, size, fmt))
        except Exception as exc:
            self.after(0, lambda: self._load_error(str(exc)))

    def _on_loaded(self, filename, file_type, file_size, fmt):
        self._btn_open.configure(state="normal", text="📂  Open File")
        self._refresh_sidebar(filename, file_type, file_size, fmt)
        self._show_toolbar_and_scroll()
        self._undo.clear()
        self._redo.clear()
        self._render_sections()
        self._btn_save.configure(state="normal")
        self._btn_save_inplace.configure(state="normal")

        # Update top badge
        color, icon = FILE_TYPE_BADGE.get(file_type, (ACCENT, "📄"))
        self._badge_wrap.grid(row=0, column=1, padx=SP_MD)
        self._badge_icon.configure(text=icon, fg_color=color)
        self._badge_icon.pack(side="left", padx=(0, SP_SM))
        self._badge_label.configure(text=filename)
        self._badge_label.pack(side="left")

        self._update_stats()
        self._push_recent(self._src_path)
        editable_count = sum(1 for s in self._sections
                             for f in s.get("fields", []) if f.get("editable"))
        self._set_status(f"Loaded {filename}  •  {editable_count} editable fields")
        warning = getattr(self, "_load_warning", None)
        if warning:
            self._toast.show(warning, kind="warning", duration=6000)
            self._load_warning = None
        else:
            self._toast.show(f"Opened {filename}", kind="success")

    def _load_error(self, msg):
        self._btn_open.configure(state="normal", text="📂  Open File")
        self._set_status("Failed to load file")
        self._toast.show("Failed to load file", kind="error")
        messagebox.showerror("Cannot open file", msg, parent=self)

    def _save_file(self):
        if not self._handler or not self._src_path:
            return
        ext  = os.path.splitext(self._src_path)[1].lower()
        stem = os.path.splitext(os.path.basename(self._src_path))[0]
        dest = filedialog.asksaveasfilename(
            title="Save As — MetaEditor",
            initialfile=f"{stem}_edited{ext}",
            initialdir=os.path.dirname(self._src_path),
            defaultextension=ext,
            filetypes=[(f"{ext.upper()} file", f"*{ext}"), ("All files", "*.*")],
        )
        if dest:
            self._do_save_to(dest, in_place=False)

    def _save_in_place(self):
        if not self._handler or not self._src_path:
            return
        if not messagebox.askyesno(
            "Save in place",
            f"Overwrite the original file?\n\n{self._src_path}\n\n"
            "A timestamped .bak file will be created alongside it.",
            parent=self):
            return
        try:
            backup = self._src_path + datetime.now().strftime(".%Y%m%d_%H%M%S.bak")
            shutil.copy2(self._src_path, backup)
        except Exception as e:
            messagebox.showerror("Backup failed",
                                 f"Couldn't create backup, save aborted:\n{e}",
                                 parent=self)
            return
        self._do_save_to(self._src_path, in_place=True)

    def _do_save_to(self, dest, *, in_place):
        try:
            ext = os.path.splitext(self._src_path)[1].lower()
            shutil.copy2(self._src_path, self._work_path)

            fresh = get_handler(ext, self._work_path)

            specific = [s for s in self._sections if not s.get("_general")]
            general  = [s for s in self._sections if s.get("_general")]

            # Format-specific edits rewrite file content/headers — do them
            # on the temp copy first.
            if not isinstance(fresh, GeneralHandler):
                fresh.write(specific)

            shutil.copy2(self._work_path, dest)

            # Filesystem-level edits (mtime/atime/btime, perms, xattrs) MUST
            # be applied to the actual destination. shutil.copy2 propagates
            # mtime/atime, but birthtime and macOS xattrs do not transfer
            # from the work copy.
            if general:
                GeneralHandler(dest).write(general)

            self._originals = copy.deepcopy(self._sections)
            # Refresh modified marks
            for (si, fi), mark in self._mod_marks.items():
                mark.configure(text="")
            self._update_stats()

            if in_place:
                self._set_status(f"Saved in place: {os.path.basename(dest)}")
                self._toast.show(f"Saved {os.path.basename(dest)}", kind="success")
            else:
                self._set_status(f"Saved: {os.path.basename(dest)}")
                self._toast.show(f"Saved to {os.path.basename(dest)}", kind="success")
        except Exception as exc:
            self._set_status("Save failed")
            messagebox.showerror("Save failed", str(exc), parent=self)

    # ── Strip / Export / Import ────────────────────────────────────────────

    def _strip_all(self):
        if not self._handler or not self._src_path:
            return
        if not messagebox.askyesno(
            "Strip all metadata",
            "This will remove EXIF / tag / xattr metadata from a saved copy "
            "of the file. The original file is not touched here — you will be "
            "prompted to choose a destination.\n\nContinue?",
            parent=self):
            return

        ext  = os.path.splitext(self._src_path)[1].lower()
        stem = os.path.splitext(os.path.basename(self._src_path))[0]
        dest = filedialog.asksaveasfilename(
            title="Save Stripped Copy As… — MetaEditor",
            initialfile=f"{stem}_stripped{ext}",
            initialdir=os.path.dirname(self._src_path),
            defaultextension=ext,
            filetypes=[(f"{ext.upper()} file", f"*{ext}"), ("All files", "*.*")],
        )
        if not dest:
            return

        try:
            shutil.copy2(self._src_path, self._work_path)
            fresh = get_handler(ext, self._work_path)
            if hasattr(fresh, "strip"):
                fresh.strip()
            shutil.copy2(self._work_path, dest)
            # macOS xattrs don't ride along with shutil.copy2 — strip on the
            # destination too so an existing-file overwrite is fully clean.
            GeneralHandler(dest).strip()
            self._set_status(f"Stripped → {os.path.basename(dest)}")
            self._toast.show("Metadata stripped from copy", kind="success")
        except Exception as e:
            self._set_status("Strip failed")
            messagebox.showerror("Strip failed", str(e), parent=self)

    def _export_json(self):
        if not self._sections or not self._src_path:
            return
        stem = os.path.splitext(os.path.basename(self._src_path))[0]
        dest = filedialog.asksaveasfilename(
            title="Export Metadata as JSON",
            initialfile=f"{stem}_metadata.json",
            initialdir=os.path.dirname(self._src_path),
            defaultextension=".json",
            filetypes=[("JSON file", "*.json"), ("All files", "*.*")],
        )
        if not dest:
            return
        try:
            payload = {
                "source": os.path.basename(self._src_path),
                "exported_at": datetime.now().isoformat(timespec="seconds"),
                "app": f"MetaEditor {APP_VERSION}",
                "sections": [
                    {
                        "name": sec.get("name"),
                        "icon": sec.get("icon"),
                        "fields": [
                            {"label": f.get("label"),
                             "key":   f.get("key"),
                             "value": f.get("value"),
                             "editable": f.get("editable", False)}
                            for f in sec.get("fields", [])
                        ],
                    }
                    for sec in self._sections
                ],
            }
            with open(dest, "w") as f:
                json.dump(payload, f, indent=2)
            self._set_status(f"Exported → {os.path.basename(dest)}")
            self._toast.show("Exported metadata to JSON", kind="success")
        except Exception as e:
            self._set_status("Export failed")
            messagebox.showerror("Export failed", str(e), parent=self)

    def _import_json(self):
        if not self._sections:
            return
        src = filedialog.askopenfilename(
            title="Import Metadata from JSON",
            filetypes=[("JSON file", "*.json"), ("All files", "*.*")],
        )
        if not src:
            return
        try:
            with open(src) as f:
                payload = json.load(f)
            incoming = {}
            for sec in payload.get("sections", []):
                for fld in sec.get("fields", []):
                    if fld.get("key") and fld.get("editable"):
                        incoming[fld["key"]] = fld.get("value", "")

            applied = 0
            for si, sec in enumerate(self._sections):
                for fi, fld in enumerate(sec.get("fields", [])):
                    key = fld.get("key")
                    if key in incoming and fld.get("editable"):
                        new_val = incoming[key]
                        fld["value"] = new_val
                        var = self._vars.get((si, fi))
                        if var is not None:
                            var.set(new_val)
                        applied += 1

            self._update_stats()
            self._set_status(f"Imported {applied} fields")
            self._toast.show(f"Applied {applied} fields  •  remember to save",
                             kind="success")
        except Exception as e:
            self._set_status("Import failed")
            messagebox.showerror("Import failed", str(e), parent=self)

    # ──────────────────────────────────────────────────────────────────────
    # RENDERING (the redesigned section card + field row)
    # ──────────────────────────────────────────────────────────────────────

    def _render_sections(self):
        for w in self._scroll.winfo_children():
            w.destroy()
        self._vars.clear()
        self._labels.clear()
        self._mod_marks.clear()
        self._widgets.clear()
        self._rows.clear()
        self._bodies.clear()
        self._collapsed.clear()

        for si, section in enumerate(self._sections):
            self._build_section_card(si, section)

    def _build_section_card(self, si, section):
        icon_key = section.get("icon", "file")
        icon = SECTION_ICONS.get(icon_key, "▸")
        accent_dark, soft_light, soft_dark = SECTION_ACCENTS.get(
            icon_key, (ACCENT, "#eef2ff", "#1e1b4b"))
        soft_color = (soft_light, soft_dark)

        name   = section.get("name", f"Section {si}")
        fields = section.get("fields", [])
        editable_count = sum(1 for f in fields if f.get("editable"))

        # Outer container with subtle border + larger radius
        card = ctk.CTkFrame(
            self._scroll, fg_color=BG_CARD,
            corner_radius=R_LG, border_width=1, border_color=BORDER_HAIR,
        )
        card.pack(fill="x", padx=SP_XS, pady=SP_SM)
        card.grid_columnconfigure(1, weight=1)

        # Left accent stripe — gives each section card a colored "spine"
        stripe = ctk.CTkFrame(card, width=4, corner_radius=0,
                              fg_color=accent_dark)
        stripe.grid(row=0, column=0, rowspan=2, sticky="nsw")

        # Header row: icon badge + name + counts + chevron toggle button
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.grid(row=0, column=1, sticky="ew", padx=(SP_MD, SP_XS), pady=(SP_MD, SP_SM))
        hdr.grid_columnconfigure(1, weight=1)

        icon_badge = ctk.CTkLabel(
            hdr, text=icon, fg_color=soft_color,
            text_color=accent_dark,
            corner_radius=R_SM, width=34, height=34,
            font=font(15, "bold"),
        )
        icon_badge.grid(row=0, column=0, rowspan=2, padx=(0, SP_MD))

        ctk.CTkLabel(hdr, text=name, anchor="w",
                     font=font(14, "bold"), text_color=TX_PRIMARY,
                     ).grid(row=0, column=1, sticky="sw")

        sub = f"{len(fields)} fields  ·  {editable_count} editable"
        ctk.CTkLabel(hdr, text=sub, anchor="w",
                     font=font(11), text_color=TX_TERTIARY,
                     ).grid(row=1, column=1, sticky="nw")

        toggle = ctk.CTkButton(
            hdr, text="▾",
            command=lambda s=si: self._toggle_section(s),
            fg_color="transparent", text_color=TX_SECONDARY,
            hover_color=BG_CARD_2,
            width=36, height=36, corner_radius=R_SM,
            font=font(13, "bold"),
        )
        toggle.grid(row=0, column=2, rowspan=2, padx=SP_SM)
        self._collapsed[si] = False

        # Body
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.grid(row=1, column=1, sticky="ew", padx=(SP_MD, SP_LG), pady=(0, SP_MD))
        body.grid_columnconfigure(0, weight=1)
        body._toggle = toggle  # so we can update the chevron later

        self._bodies[si] = body
        self._rows[si]   = []

        for fi, field in enumerate(fields):
            row = self._build_field_row(body, si, fi, field, accent_dark, soft_color)
            row.grid(row=fi, column=0, sticky="ew", pady=2)
            self._rows[si].append(row)

    def _build_field_row(self, parent, si, fi, field, accent_color, soft_color):
        label_text = field.get("label", "")
        value      = field.get("value") or ""
        editable   = field.get("editable", False)
        is_select  = field.get("type") == "select" and field.get("options") and editable
        orig_val   = value

        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.grid_columnconfigure(1, weight=1)
        row._search_label = label_text.lower()
        row._search_value = str(value).lower()

        # Indicator dot — fills with section accent for editable, hollow grey for RO
        dot = ctk.CTkLabel(
            row, text="●" if editable else "○",
            font=font(10), text_color=accent_color if editable else TX_DISABLED,
            width=16, anchor="w",
        )
        dot.grid(row=0, column=0, padx=(0, SP_SM), pady=2, sticky="w")

        lbl = ctk.CTkLabel(
            row, text=label_text, anchor="w",
            font=font(12, "bold" if editable else "normal"),
            text_color=TX_PRIMARY if editable else TX_TERTIARY,
            width=210,
        )
        lbl.grid(row=0, column=1, padx=(0, SP_MD), pady=2, sticky="w")
        self._labels[(si, fi)] = lbl

        var = ctk.StringVar(value=value)
        self._vars[(si, fi)] = var

        # Input area
        input_holder = ctk.CTkFrame(row, fg_color="transparent")
        input_holder.grid(row=0, column=2, sticky="ew", pady=2)
        input_holder.grid_columnconfigure(0, weight=1)
        row.grid_columnconfigure(2, weight=1)

        if is_select:
            opts = [""] + [o["label"] for o in field["options"]]
            widget = ctk.CTkOptionMenu(
                input_holder, variable=var, values=opts,
                fg_color=BG_INPUT, button_color=accent_color,
                button_hover_color=ACCENT_HVR,
                dropdown_fg_color=BG_PANEL,
                text_color=TX_PRIMARY,
                font=font(11, mono=True),
                height=32, corner_radius=R_SM, dynamic_resizing=False,
            )
            widget.set(value)

            def _on_select(val, s=si, f=fi, orig=orig_val):
                prev = self._sections[s]["fields"][f].get("value", "")
                if val != prev:
                    self._record_undo(s, f, prev, val)
                    self._sections[s]["fields"][f]["value"] = val
                    self._flag_modified(s, f, val != orig)
            widget.configure(command=_on_select)

        elif editable:
            widget = ctk.CTkEntry(
                input_holder, textvariable=var,
                font=font(11, mono=True),
                fg_color=BG_INPUT, border_color=BORDER_HAIR,
                text_color=TX_PRIMARY,
                height=32, corner_radius=R_SM,
                border_width=1,
            )

            def _on_type(*_, s=si, f=fi, v=var, orig=orig_val):
                val = v.get()
                prev = self._sections[s]["fields"][f].get("value", "")
                if val != prev:
                    self._record_undo(s, f, prev, val)
                    self._sections[s]["fields"][f]["value"] = val
                    self._flag_modified(s, f, val != orig)

            var.trace("w", _on_type)

            # Focus state — border lights up to the section accent when the
            # input has the keyboard focus, giving a clear visual cue.
            def _on_focus_in(_e, w=widget, c=accent_color):
                w.configure(border_color=c, border_width=2)

            def _on_focus_out(_e, w=widget):
                w.configure(border_color=BORDER_HAIR, border_width=1)

            widget.bind("<FocusIn>",  _on_focus_in)
            widget.bind("<FocusOut>", _on_focus_out)
        else:
            widget = ctk.CTkEntry(
                input_holder, textvariable=var,
                font=font(11, mono=True),
                fg_color=BG_INPUT_RO, border_color=BORDER_HAIR,
                text_color=TX_DISABLED,
                height=32, corner_radius=R_SM,
                state="disabled",
            )

        widget.grid(row=0, column=0, sticky="ew")
        self._widgets[(si, fi)] = widget

        # Modified indicator (pill) — placed to the right of the input
        mod_mark = ctk.CTkLabel(
            row, text="",
            font=font(9, "bold"),
            text_color=("#0891b2", "#34d399"),
            width=24,
        )
        mod_mark.grid(row=0, column=3, padx=(SP_SM, SP_XS), pady=2)
        self._mod_marks[(si, fi)] = mod_mark

        # GPS map button if relevant
        etype = field.get("_exif_type", "")
        if etype in ("gps_lat", "gps_lon"):
            map_btn = ctk.CTkButton(
                row, text="🗺",
                command=self._open_map,
                fg_color=BG_CARD_2, hover_color=BORDER_HAIR,
                text_color=TX_PRIMARY,
                width=32, height=32, corner_radius=R_SM,
                font=font(13),
            )
            map_btn.grid(row=0, column=4, padx=(0, SP_XS), pady=2)

        return row

    # ──────────────────────────────────────────────────────────────────────
    # UNDO / REDO
    # ──────────────────────────────────────────────────────────────────────

    def _record_undo(self, si, fi, prev_val, new_val):
        if self._suppress_undo or prev_val == new_val:
            return
        self._undo.append((si, fi, prev_val, new_val))
        self._redo.clear()

    def _undo_action(self):
        if not self._undo:
            self._toast.show("Nothing to undo", kind="warn", duration=1500)
            return
        si, fi, prev_val, new_val = self._undo.pop()
        self._redo.append((si, fi, prev_val, new_val))
        self._apply_value(si, fi, prev_val)
        self._set_status("Undid last change")

    def _redo_action(self):
        if not self._redo:
            self._toast.show("Nothing to redo", kind="warn", duration=1500)
            return
        si, fi, prev_val, new_val = self._redo.pop()
        self._undo.append((si, fi, prev_val, new_val))
        self._apply_value(si, fi, new_val)
        self._set_status("Redid change")

    def _apply_value(self, si, fi, value):
        if si >= len(self._sections):
            return
        fields = self._sections[si].get("fields", [])
        if fi >= len(fields):
            return
        self._suppress_undo = True
        try:
            fields[fi]["value"] = value
            var = self._vars.get((si, fi))
            if var is not None:
                var.set(value)
            orig = ""
            if si < len(self._originals) and fi < len(self._originals[si].get("fields", [])):
                orig = self._originals[si]["fields"][fi].get("value") or ""
            self._flag_modified(si, fi, value != orig)
        finally:
            self._suppress_undo = False

    # ── Modified indicator ─────────────────────────────────────────────────

    def _flag_modified(self, si, fi, is_modified):
        mark = self._mod_marks.get((si, fi))
        if mark is not None:
            mark.configure(text="● modified" if is_modified else "")
        self._update_stats()

    def _update_stats(self):
        if not self._stat:
            return
        total    = sum(len(s.get("fields", [])) for s in self._sections)
        editable = sum(1 for s in self._sections
                       for f in s.get("fields", []) if f.get("editable"))
        changed  = 0
        for si, sec in enumerate(self._sections):
            for fi, fld in enumerate(sec.get("fields", [])):
                orig = ""
                if si < len(self._originals) and fi < len(self._originals[si].get("fields", [])):
                    orig = self._originals[si]["fields"][fi].get("value") or ""
                if (fld.get("value") or "") != orig:
                    changed += 1
        self._stat["total"].set(str(total))
        self._stat["editable"].set(str(editable))
        self._stat["changed"].set(str(changed))

    # ── Section collapse ───────────────────────────────────────────────────

    def _toggle_section(self, si):
        body = self._bodies.get(si)
        if body is None:
            return
        if self._collapsed[si]:
            body.grid()
            self._collapsed[si] = False
            try:
                body._toggle.configure(text="▾")
            except Exception:
                pass
        else:
            body.grid_remove()
            self._collapsed[si] = True
            try:
                body._toggle.configure(text="▸")
            except Exception:
                pass

    def _expand_all(self):
        for si, body in self._bodies.items():
            body.grid()
            self._collapsed[si] = False
            try:
                body._toggle.configure(text="▾")
            except Exception:
                pass

    def _collapse_all(self):
        for si, body in self._bodies.items():
            body.grid_remove()
            self._collapsed[si] = True
            try:
                body._toggle.configure(text="▸")
            except Exception:
                pass

    # ── Search & filter ────────────────────────────────────────────────────

    def _set_filter_mode(self, mode):
        self._filter_mode = mode
        # Update chip styles
        for key, btn in self._filter_btns.items():
            if key == mode:
                btn.configure(fg_color=ACCENT, text_color="#ffffff")
            else:
                btn.configure(fg_color="transparent", text_color=TX_SECONDARY)
        self._on_search()

    def _row_matches_filter(self, si, fi):
        if self._filter_mode == "all":
            return True
        try:
            fld = self._sections[si]["fields"][fi]
        except (IndexError, KeyError):
            return True
        if self._filter_mode == "editable":
            return bool(fld.get("editable"))
        if self._filter_mode == "modified":
            orig = ""
            if si < len(self._originals) and fi < len(self._originals[si].get("fields", [])):
                orig = self._originals[si]["fields"][fi].get("value") or ""
            return (fld.get("value") or "") != orig
        return True

    def _on_search(self, *_):
        q = self._search_var.get().lower().strip()
        any_visible = False
        section_visible: dict = {}

        for si, row_list in self._rows.items():
            section_visible[si] = False
            for fi, row in enumerate(row_list):
                # Filter mode check
                if not self._row_matches_filter(si, fi):
                    row.grid_remove()
                    continue
                # Search-query check
                if q:
                    cur_val = (self._vars.get((si, fi)) or ctk.StringVar()).get().lower()
                    matched = (q in row._search_label) or (q in row._search_value) or (q in cur_val)
                    if not matched:
                        row.grid_remove()
                        continue
                row.grid()
                section_visible[si] = True
                any_visible = True

        # Hide entire section card when nothing inside it is visible
        for si, body in self._bodies.items():
            card = body.master  # body's parent is the section card
            if section_visible.get(si):
                if hasattr(card, "winfo_manager") and card.winfo_manager() == "":
                    card.pack(fill="x", padx=SP_XS, pady=SP_SM)
                else:
                    try:
                        card.pack(fill="x", padx=SP_XS, pady=SP_SM)
                    except Exception:
                        pass
            else:
                try:
                    card.pack_forget()
                except Exception:
                    pass

        self._update_empty_state(any_visible, q)

    def _update_empty_state(self, any_visible, query):
        # Tear down old empty state
        if self._empty_state is not None:
            try:
                self._empty_state.destroy()
            except Exception:
                pass
            self._empty_state = None

        if any_visible or not self._sections:
            return

        # Build a friendly "no results" card
        wrap = ctk.CTkFrame(self._scroll, fg_color="transparent")
        wrap.pack(fill="x", expand=True, pady=(SP_XL, SP_XL))

        card = ctk.CTkFrame(
            wrap, fg_color=BG_CARD,
            corner_radius=R_LG, border_width=1, border_color=BORDER_HAIR,
        )
        card.pack(padx=SP_LG)

        ctk.CTkLabel(card, text="🔎", font=font(36),
                     ).pack(padx=SP_XL, pady=(SP_LG, SP_SM))
        ctk.CTkLabel(card, text="No matching fields",
                     font=font(15, "bold"), text_color=TX_PRIMARY,
                     ).pack(padx=SP_XL)

        if query and self._filter_mode != "all":
            sub = f"No “{query}” in filter “{self._filter_mode}”"
        elif query:
            sub = f"No fields match “{query}”"
        else:
            sub = f"No “{self._filter_mode}” fields in this file"
        ctk.CTkLabel(card, text=sub, font=font(11),
                     text_color=TX_TERTIARY,
                     ).pack(padx=SP_XL, pady=(SP_XS, SP_SM))

        clear_btn = self._mk_btn(
            card, text="Clear filters", variant="ghost",
            command=self._clear_filters, width=160, height=32,
        )
        clear_btn.pack(padx=SP_LG, pady=(SP_SM, SP_LG))

        self._empty_state = wrap

    def _clear_filters(self):
        self._search_var.set("")
        self._set_filter_mode("all")

    # ── Reset ──────────────────────────────────────────────────────────────

    def _reset_changes(self):
        if not self._sections:
            return
        if not messagebox.askyesno("Reset changes",
                                   "Restore all fields to their original values?",
                                   parent=self):
            return
        self._suppress_undo = True
        try:
            self._sections = copy.deepcopy(self._originals)
            for (si, fi), var in self._vars.items():
                val = ""
                if si < len(self._sections) and fi < len(self._sections[si].get("fields", [])):
                    val = self._sections[si]["fields"][fi].get("value") or ""
                var.set(val)
                mark = self._mod_marks.get((si, fi))
                if mark is not None:
                    mark.configure(text="")
            self._undo.clear()
            self._redo.clear()
        finally:
            self._suppress_undo = False
        self._update_stats()
        self._set_status("Reset all changes")
        self._toast.show("All changes reverted", kind="info")

    # ── GPS map link ───────────────────────────────────────────────────────

    def _open_map(self):
        lat = lon = ""
        for sec in self._sections:
            for fld in sec.get("fields", []):
                if fld.get("_exif_type") == "gps_lat":
                    lat = fld.get("value", "")
                elif fld.get("_exif_type") == "gps_lon":
                    lon = fld.get("value", "")
        if lat and lon:
            webbrowser.open(
                f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}&zoom=14"
            )
        else:
            self._toast.show("Enter both Latitude and Longitude first", kind="warn")


# ── Entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = MetaEditorApp()
    app.mainloop()
