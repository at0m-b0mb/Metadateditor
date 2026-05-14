<div align="center">

# ⚡ MetaEditor

### Universal Metadata Editor for Everything

*One desktop app to read, edit, strip, export and import metadata from
images, audio, video, PDFs, Office documents, e-books — and the
filesystem itself, for **any** file on disk.*

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)](#)
[![Formats](https://img.shields.io/badge/Formats-50+-8b5cf6)](#-supported-formats)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux%20%7C%20Windows-10b981)](#)
[![License](https://img.shields.io/badge/License-MIT-blue)](#)

</div>

---

## 📑 Table of Contents

1. [Why MetaEditor?](#-why-metaeditor)
2. [What's New in v2.1](#-whats-new-in-v21)
3. [Headline Features](#-headline-features)
4. [Installation](#-installation)
5. [Quick Start](#-quick-start)
6. [Keyboard Shortcuts](#%EF%B8%8F-keyboard-shortcuts)
7. [The Interface, Annotated](#-the-interface-annotated)
8. [Supported Formats](#-supported-formats)
9. [Editing Any File — Filesystem Mode](#-editing-any-file--filesystem-mode)
10. [Power-User Tools](#-power-user-tools)
11. [How Saving Works (the Pipeline)](#-how-saving-works-the-pipeline)
12. [Architecture](#-architecture)
13. [Troubleshooting](#-troubleshooting)
14. [Privacy & Safety](#-privacy--safety)
15. [Contributing](#-contributing)
16. [License](#-license)

---

## ✨ Why MetaEditor?

Most metadata tools focus on one format — one for EXIF, another for ID3,
another for PDF, and yet another for Office docs. **MetaEditor unifies them all
in a single dark/light themed desktop app**, with a consistent edit-and-save
workflow that works the same way no matter what you open.

Beyond format-specific metadata, MetaEditor also lets you edit the data the OS
normally hides from you: file timestamps, permissions, and extended
attributes — for **any** file type. Plain `.txt`? Random `.exe`? An archive
with no known format? You can still rewrite its **Date Created**, **Date
Modified**, and **Date Accessed** through the same UI.

---

## 🆕 What's New in v2.1

> A focused release that fixes the most-reported bug: filesystem edits
> (especially **Date Created** and macOS xattrs) silently being dropped on
> save, and "Date Created" showing the wrong baseline value.

| 🩹 Fix | What was wrong | What now happens |
| --- | --- | --- |
| **"Date Created" / xattr edits actually persist on save** | Edits were applied to the temp working copy, then `shutil.copy2` propagated to the destination — but `copy2` does **not** carry over birthtime or macOS xattrs. They were silently lost. | Filesystem edits are now applied directly to the **final destination file** after the copy, so they survive both Save-in-Place and Save As. |
| **"Date Created" shows the real value** | The filesystem section was being read from the temp `working` copy, whose birthtime was the moment of opening — so every file looked freshly created today. | Filesystem properties are now read from the **original source file**, so what you see matches what `stat` reports. |
| **Broken / unknown formats no longer block editing** | If a format-specific parser crashed on a corrupt file, you got a hard error and couldn't edit anything — not even dates. | MetaEditor now falls back to filesystem-only mode with a clear warning toast, so you can still edit timestamps, permissions, and xattrs. |
| **Strip-All cleans the destination too** | `xattr -c` was applied only to the work copy, so an overwritten existing destination could retain its original xattrs. | Stripping now also runs on the destination file after the copy. |

See [How Saving Works](#-how-saving-works-the-pipeline) for the full data flow.

---

## 🚀 Headline Features

|     | Feature | What it does |
| :-: | --- | --- |
| 🖼️ | **50+ formats** | JPEG · PNG · TIFF · WEBP · HEIC · RAW · MP3 · FLAC · WAV · OGG · MP4 · MKV · MOV · PDF · DOCX · XLSX · PPTX · EPUB · and more |
| 📅 | **Filesystem metadata for *every* file** | Edit modification time, access time, **creation date** (macOS), permissions, and xattrs — even on file types we don't otherwise understand |
| 💾 | **Save in place or Save As** | Overwrite the original (with automatic timestamped `.bak` backup), or save a clean copy elsewhere |
| 🗑 | **Strip All Metadata** | One click privacy — removes EXIF, ID3, PDF Info, Office props, and extended attributes |
| 📤 | **Export / Import JSON** | Copy metadata between files, version-control your tags, or back up before risky edits |
| 🔍 | **Live search** | Filter hundreds of fields instantly — search by name or value |
| ↶ ↷ | **Undo / Redo** | 100-step history per file, with full keyboard shortcuts |
| 📂 | **Drag & drop** | Drop *any* file onto the window to open it *(via `tkinterdnd2`)* |
| 🕘 | **Recent files** | Quick re-open from a menu that remembers your last 10 files |
| 🌗 | **Dark / light theme** | Toggle with one click — preference is remembered between sessions |
| 🗺 | **GPS map link** | Open an image's GPS coordinates straight in OpenStreetMap |
| ⌨️ | **Full keyboard shortcuts** | ⌘O · ⌘S · ⌘⇧S · ⌘Z · ⌘⇧Z · ⌘F · ⌘R |
| 🖼️ | **Image preview** | Thumbnail of the loaded image right in the sidebar |
| 🛟 | **Graceful fallback** | A corrupt or exotic file still opens — you get filesystem-only edits and a clear warning |

---

## 📦 Installation

### Prerequisites

* **Python 3.9** or later
* **macOS** / **Linux** / **Windows**
* *(macOS only, optional but recommended)* **Xcode Command-Line Tools**, which
  ship with the `SetFile` binary used to edit **Date Created**. Install with:
  ```bash
  xcode-select --install
  ```
  Without it, MetaEditor will still open files and edit every other field —
  the "Date Created" row just becomes read-only.

### Install

```bash
git clone <your-repo-url> Metadateditor
cd Metadateditor

# (recommended) create a virtual environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# install dependencies
pip install -r requirements.txt
```

### Run

```bash
python3 main.py
```

---

## 🏁 Quick Start

1. **Launch the app** — `python3 main.py`.
2. **Open a file** — click **Open File**, hit ⌘O, or **drag-and-drop** any
   file onto the window. To open file types not in MetaEditor's format list
   (`.txt`, `.exe`, `.zip`, no extension at all, …), pick **"All Files"** in
   the file dialog or just drag the file in.
3. **Edit fields** — the form shows every editable piece of metadata. Type
   into a field, pick from a dropdown, or paste a value. Modified fields
   show **● modified** next to the label.
4. **Save** —
   * **⌘S** (Save in place) overwrites the original *and* writes a
     `.YYYYMMDD_HHMMSS.bak` next to it.
   * **⌘⇧S** (Save As…) writes to a new path of your choice.

> 💡 **Tip:** For a `.txt`, `.exe`, or any "boring" file, only the **File
> System** section appears — and that's exactly the point. You can rewrite
> its Date Created / Modified / Accessed / Permissions / xattrs from there.

---

## ⌨️ Keyboard Shortcuts

| Shortcut (macOS) | Shortcut (Linux/Win) | Action |
| --- | --- | --- |
| `⌘O` | `Ctrl+O` | Open a file |
| `⌘S` | `Ctrl+S` | **Save in place** (creates `.bak` backup first) |
| `⌘⇧S` | `Ctrl+Shift+S` | **Save As** (write to a new path) |
| `⌘Z` | `Ctrl+Z` | Undo last field edit |
| `⌘⇧Z` / `⌘Y` | `Ctrl+Shift+Z` / `Ctrl+Y` | Redo |
| `⌘F` | `Ctrl+F` | Focus the search box |
| `⌘R` | `Ctrl+R` | Reset all changes |

---

## 🧭 The Interface, Annotated

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ⚡ MetaEditor              [Image]           Recent▾  Open  Save  ☀️  │   ← Top bar: file-type badge & actions
├──────────────────┬──────────────────────────────────────────────────────┤
│  📂 sunset.jpg   │  🔍 Search…   Expand   Collapse   Reset   ↶  ↷       │   ← Toolbar: filter + view + history
│  [thumbnail]     │ ┌────────────────────────────────────────────────┐   │
│                  │ │ 📷 Camera & Image    · 9 fields · 8 editable   │   │   ← Section card (click header to collapse)
│  Type: Image     │ │   ●  Camera Make        Sony                    │   │
│  Size: 4.2 MB    │ │   ●  Camera Model       ILCE-7M3                │   │
│  Format: JPEG    │ │   ●  Orientation        [Normal           ▾]   │   │   ← Dropdowns for enum fields
│                  │ │   ●  Software           Lightroom 13     ✎     │   │   ← ✎ = modified
│  ┌────────────┐  │ │   ○  Pixel Width        6000 px                │   │   ← ○ = read-only
│  │  Stats     │  │ └────────────────────────────────────────────────┘   │
│  │  127  64  3│  │ ┌────────────────────────────────────────────────┐   │
│  └────────────┘  │ │ 📁 File System       · 8 fields · 5 editable   │   │
│  Tools           │ │   ●  Date Modified      2024-08-12 14:30:00    │   │
│  📤 Export JSON  │ │   ●  Date Accessed      2026-05-14 09:11:02    │   │
│  📥 Import JSON  │ │   ●  Date Created       2020-01-01 10:00:00    │   │   ← Editable on macOS (SetFile)
│  🗑 Strip Meta   │ │   ●  Permissions        -rw-r--r--             │   │
├──────────────────┴──────────────────────────────────────────────────────┤
│  ✓ Loaded sunset.jpg  •  47 editable fields                  v2.1  •  drag-drop on │   ← Status bar
└─────────────────────────────────────────────────────────────────────────┘
```

### Field Indicators

| Symbol | Meaning |
| :-: | --- |
| `●` (filled, normal color) | **Editable** — click to type a new value |
| `○` (hollow, dim) | **Read-only** — computed from the file (e.g. pixel dimensions, size) |
| `●  Label  ✎` | **Modified** — value differs from when the file was opened |
| Purple dot in sidebar stats | Live count of modified fields |
| ⚠️ warning toast on open | A format parser failed; you're in filesystem-only fallback mode |

---

## 🗂 Supported Formats

<details>
<summary><b>Click to expand the full list</b></summary>

### Images

`.jpg` · `.jpeg` · `.jpe` · `.png` · `.tif` · `.tiff` · `.webp` · `.heic` · `.heif`

**Editable:** Camera Make/Model, Orientation, X/Y Resolution, Resolution Unit,
Software, Date/Time Modified/Original/Digitized, Artist, Copyright, Exposure
Time, F-Number, Exposure Program, ISO Speed, Shutter/Aperture/Brightness/
Exposure-bias APEX values, Subject Distance, Metering Mode, Light Source,
Flash, Focal Length, Color Space, Exposure Mode, White Balance, Digital Zoom,
35mm Equivalent Focal Length, Scene Capture Type, Sharpness, Image Unique ID,
Camera Owner/Serial, Lens Make/Model/Serial, GPS Latitude/Longitude/Altitude/
Date.

PNG also exposes Title, Author, Description, Copyright, Software, Comment.

### RAW Camera Formats

`.dng` · `.cr2` · `.cr3` · `.nef` · `.nrw` · `.arw` · `.sr2` · `.rw2` ·
`.orf` · `.raf` · `.pef` · `.x3f` · `.3fr`

All TIFF-based EXIF tags listed above.

### Audio

`.mp3` · `.flac` · `.ogg` · `.oga` · `.m4a` · `.aac` · `.m4b` · `.m4r` ·
`.wav` · `.aiff` · `.aif` · `.wma` · `.opus` · `.ape` · `.mpc` · `.wv` ·
`.mp2` · `.spx` · `.dsf`

**Editable:** Title, Artist, Album Artist, Album, Date/Year, Genre, Track #,
Disc #, Composer, Lyricist, Comment, Description, BPM, Language, Copyright,
Encoded By, Label/Organization, ISRC, Conductor, Remixer, Compilation,
Grouping, Mood, Website, Lyrics.

### Video

`.mp4` · `.m4v` · `.mkv` · `.mka` · `.mov` · `.avi` · `.wmv` · `.webm` ·
`.3gp` · `.3g2` · `.asf` · `.ogv` · `.flv`

Container-level tags (handled by Mutagen).

### PDF

`.pdf`

**Editable:** Title, Author, Subject, Keywords, Creator Application,
Producer, Creation Date, Modification Date, Trapped, plus any custom
metadata keys already present in the file.

### Office / Documents

`.docx` · `.xlsx` · `.pptx`

**Editable (core):** Title, Subject, Author, Keywords, Description, Last
Modified By, Created, Modified, Category, Version, Revision.

**Editable (app):** Application, App Version, Company, Manager, Template.

### E-books

`.epub`

**Editable (Dublin Core):** Title, Author, Subject, Description, Publisher,
Contributor, Date, Type, Format, Identifier, Source, Language, Rights.

### Filesystem (every file — including formats not listed above)

* **Date Modified** (`mtime`) — editable on all platforms via `os.utime`
* **Date Accessed** (`atime`) — editable on all platforms via `os.utime`
* **Date Created** (`btime`) — editable on macOS via `SetFile -d`
* **Permissions** — editable on POSIX via `chmod` (both `rwx` and octal accepted)
* **Owner** — read-only (changing it requires `sudo`)
* **Extended attributes** (`xattr` on macOS, `getxattr` on Linux) — editable

</details>

---

## 📂 Editing Any File — Filesystem Mode

MetaEditor recognizes 50+ formats out of the box. For anything else — a plain
`.txt`, a binary `.exe`, an archive, a file with no extension — it falls back
to **filesystem mode**, where you can still edit:

| Property | macOS | Linux | Windows |
| --- | :-: | :-: | :-: |
| Date Modified | ✅ | ✅ | ✅ |
| Date Accessed | ✅ | ✅ | ✅ |
| **Date Created** | ✅ *(SetFile)* | ⚠️ read-only | ⚠️ read-only |
| Permissions (chmod) | ✅ | ✅ | — |
| Owner | read-only | read-only | read-only |
| Extended attributes (xattr) | ✅ | ✅ | — |

### Opening unsupported files

The Open dialog filter defaults to **"All Supported Files"**. To open any
other file:

* In the Open dialog, switch the filter dropdown to **"All Files"**, **or**
* Just **drag and drop** the file onto the window.

In filesystem mode the form shrinks to a single **📁 File System** section
plus an **🏷 Extended Attributes** section (when xattrs are present). Edit
the values, hit Save, and the changes are applied directly to the
destination file.

### Accepted date formats

The filesystem date editor accepts any of these, and converts internally:

```
YYYY-MM-DD HH:MM:SS    ← preferred
YYYY-MM-DD
YYYY/MM/DD HH:MM:SS
MM/DD/YYYY HH:MM:SS
DD-MM-YYYY HH:MM:SS
DD/MM/YYYY HH:MM:SS
```

### A worked example

```text
Original file:   /Users/me/notes.txt
                 Modified:  2026-05-14 09:00:00
                 Created:   2026-05-14 09:00:00     ← created today

Open in MetaEditor, change:
  Date Created  →  2018-03-21 11:42:17
  Date Modified →  2018-03-21 12:00:00

⌘S  (Save in place — creates notes.txt.20260514_091223.bak)

After save:
                 Modified:  2018-03-21 12:00:00
                 Created:   2018-03-21 11:42:17     ✅ persists
                 Backup:    notes.txt.20260514_091223.bak  (untouched copy)
```

---

## 🔧 Power-User Tools

### 🗑 Strip All Metadata

Removes every editable piece of metadata in one pass and writes the result to
a new file. Useful before:

* Posting photos online (strips GPS / camera serial / unique IDs)
* Sharing a document (clears Author / Company / Last-Modified-By)
* Distributing audio (wipes ID3 v1/v2 tags)

Filesystem **xattrs** are also cleared — this removes macOS's
`com.apple.quarantine` flag among others.

### 📤 Export Metadata as JSON

Dumps the entire field tree to a structured JSON file — perfect for:

* Backing up metadata before bulk edits
* Diffing the metadata of two files
* Version-controlling tag changes alongside the files themselves

```jsonc
{
  "source":      "sunset.jpg",
  "exported_at": "2026-05-14T14:32:10",
  "app":         "MetaEditor 2.1",
  "sections": [
    {
      "name": "Camera & Image",
      "icon": "camera",
      "fields": [
        { "label": "Camera Make",  "key": "ifd0_271", "value": "Sony",     "editable": true },
        { "label": "Camera Model", "key": "ifd0_272", "value": "ILCE-7M3", "editable": true }
      ]
    }
  ]
}
```

### 📥 Import Metadata from JSON

The inverse: load a JSON exported by MetaEditor and apply every matching
editable field to the file currently open. Fields are matched by **key**, so
the templates work even when the source and destination files are different.

A typical workflow:

1. Open `photo-1.jpg`, set Artist / Copyright / Software exactly how you want
   them.
2. Export to `my-defaults.json`.
3. Open `photo-2.jpg` → Import `my-defaults.json` → Save.
4. Repeat for the rest of the shoot.

### 💾 Save in Place

Overwrites the original file directly **but always creates a timestamped
backup first** (`photo.jpg.20260514_143210.bak`). This means you can:

* Iterate on edits without producing dozens of `_edited` copies
* Roll back instantly by renaming the `.bak`

---

## 🔁 How Saving Works (the Pipeline)

Understanding the save pipeline is the easiest way to understand why
MetaEditor is safe and why filesystem edits now stick:

```
                    ┌────────────────────────┐
                    │     SOURCE FILE        │
                    │  /path/to/photo.jpg    │
                    └───────────┬────────────┘
                                │ shutil.copy2 (preserves mtime/atime/mode)
                                ▼
                    ┌────────────────────────┐
                    │     WORK COPY          │
                    │  ~/tmpXXX/working.jpg  │
                    └───────────┬────────────┘
                                │ format-specific handler writes
                                │   EXIF / ID3 / PDF / OOXML / …
                                ▼
                    ┌────────────────────────┐
                    │   WORK COPY (edited)   │
                    └───────────┬────────────┘
                                │ shutil.copy2 → DEST
                                ▼
                    ┌────────────────────────┐
                    │   DESTINATION FILE     │
                    │  (src for Save-In-Place│
                    │   or new path for      │
                    │   Save As)             │
                    └───────────┬────────────┘
                                │ GeneralHandler(DEST).write(general)
                                │   • os.utime  → mtime / atime
                                │   • SetFile -d → btime  (macOS)
                                │   • chmod     → permissions
                                │   • xattr -w  → extended attributes
                                ▼
                    ┌────────────────────────┐
                    │   FINAL FILE           │
                    │   (your edits live)    │
                    └────────────────────────┘
```

The **key insight** — and the bug fixed in v2.1 — is that `shutil.copy2`
preserves *some* filesystem properties (mtime, atime, mode) but **not all**:
birthtime and macOS xattrs do not ride along with `copy2`. Applying those
edits to the work copy and then copying to destination silently dropped them.
The fix is to apply filesystem-level edits directly to the destination,
after the copy.

For Save-in-Place specifically, a `.bak` snapshot of the original is taken
**before** any of this runs — so you can always roll back by renaming the
backup.

---

## 🏗 Architecture

```
Metadateditor/
├── main.py                          # Tkinter (CTk) GUI, undo/redo, JSON I/O, status bar
├── requirements.txt
└── metadata_handlers/
    ├── __init__.py                  # Routes file extensions → handlers
    ├── image_handler.py             # JPEG / PNG / TIFF / RAW (via Pillow + piexif)
    ├── audio_handler.py             # All formats Mutagen understands (audio + video tags)
    ├── pdf_handler.py               # PDF Info dictionary (via pypdf)
    ├── office_handler.py            # OOXML core + app props, EPUB metadata
    └── general_handler.py           # Filesystem dates, permissions, xattrs (every file)
```

### Handler contract

Every handler in `metadata_handlers/` implements three methods:

```python
class FooHandler:
    file_type = "Foo"                # human-readable string for the badge

    def read(self) -> list[dict]:    # returns a list of "sections"
        ...

    def write(self, sections):       # accepts the same shape back
        ...

    def strip(self):                 # one-shot: erase all editable metadata
        ...
```

A **section** is a `dict` with `name`, `icon`, and a list of `fields`. A
**field** is a `dict` with at minimum `key`, `label`, `value`, `type`,
`editable`. Format-specific fields carry extra `_xxx` keys that the matching
handler uses on write.

`GeneralHandler` is always appended after the format-specific handler's
sections, so every loaded file gets filesystem and xattr editors on top of
whatever its format provides. Filesystem sections are flagged with
`_general=True`, so the save logic knows to route them through
`GeneralHandler(dest)` after the format-specific write completes.

### Adding a new format

1. Create `metadata_handlers/myformat_handler.py` with the three methods
   above.
2. Register the extension(s) in `metadata_handlers/__init__.py`:
   ```python
   from .myformat_handler import MyFormatHandler
   HANDLERS[".myext"] = MyFormatHandler
   ```
3. (Optional) Add a `file_type` entry to `FILE_TYPE_BADGE` in `main.py` for
   a coloured badge.

If a `.myext` is opened *before* you write a handler, MetaEditor falls back
to `GeneralHandler` — so the user always gets at least filesystem edits.

---

## 🛠 Troubleshooting

<details>
<summary><b>I see "○" next to a field — why can't I edit it?</b></summary>

Hollow circles mark **read-only** fields. These are values computed from the
file's content rather than stored as metadata — pixel dimensions, file size,
duration, MD5, etc. Changing them in MetaEditor wouldn't make sense because
they'd be overwritten the next time the file is read.

</details>

<details>
<summary><b>"Date Created" is read-only on macOS</b></summary>

MetaEditor uses `SetFile -d` to change birthtime, and `SetFile` is part of the
Xcode Command-Line Tools. Install with:

```bash
xcode-select --install
```

After installing, reopen MetaEditor. The field will become editable.

</details>

<details>
<summary><b>My "Date Created" edit didn't stick (pre-v2.1)</b></summary>

This was the bug fixed in v2.1. The edit was being applied to the temp
working copy, but `shutil.copy2` doesn't preserve birthtime on macOS, so the
change never reached the destination. Pull the latest code and the edit
will now apply directly to the saved file.

</details>

<details>
<summary><b>Drag-and-drop doesn't work</b></summary>

Drag-and-drop requires the optional **`tkinterdnd2`** package. Install it with:

```bash
pip install tkinterdnd2
```

The status bar will show `drag-drop on` when it's available.

</details>

<details>
<summary><b>HEIC files won't open on Linux</b></summary>

Pillow's HEIC support needs the `pillow-heif` plugin on some platforms:

```bash
pip install pillow-heif
```

</details>

<details>
<summary><b>"Cannot parse date" when saving</b></summary>

The filesystem date editor accepts:

* `YYYY-MM-DD HH:MM:SS`  *(preferred)*
* `YYYY-MM-DD`
* `YYYY/MM/DD HH:MM:SS`
* `MM/DD/YYYY HH:MM:SS`
* `DD-MM-YYYY HH:MM:SS`
* `DD/MM/YYYY HH:MM:SS`

The PDF / EXIF date editor accepts `YYYY-MM-DD HH:MM:SS` and converts to the
format the spec requires.

</details>

<details>
<summary><b>How do I edit creation date on Linux / Windows?</b></summary>

Creation time (`btime`) is only routinely settable on **macOS** (via the
`SetFile` Xcode command-line tool). Linux's `statx(2)` exposes `btime` to
*readers* but most filesystems don't allow writers to set it; Windows has
its own NTFS-specific APIs that MetaEditor doesn't currently wrap.

If you need to fake a creation time portably, the most reliable trick is
to set **mtime** (which MetaEditor edits on every platform).

</details>

<details>
<summary><b>I opened a corrupt file and got a warning toast — what happened?</b></summary>

The format-specific parser for that file (Mutagen, Pillow, pypdf, etc.) threw
while reading. Rather than blocking you out entirely, MetaEditor falls back
to **filesystem-only mode** — you can still edit timestamps, permissions,
and xattrs. The toast tells you the format wasn't parsed.

</details>

<details>
<summary><b>Can I batch-edit multiple files?</b></summary>

Not in the GUI today. The supported workflow is:

1. Export the metadata you want as JSON from a "template" file.
2. Open each target file, **Import JSON**, **Save**.

A real batch mode is on the wishlist — PRs welcome.

</details>

---

## 🛡 Privacy & Safety

* **Original files are never modified mid-edit.** All edits go to a working
  copy in a temp directory. Saving copies the working file to the destination
  and then applies filesystem-level edits directly to that destination.
* **Save in Place creates a `.bak`** before overwriting — so even there, you
  can always roll back by renaming the backup.
* MetaEditor is **fully offline**. It does not phone home, doesn't collect
  telemetry, doesn't open network connections. The only outgoing link is the
  optional "🗺" button which opens OpenStreetMap in your browser for GPS.
* No file is ever written to outside of:
  * The temp working directory (cleaned up on exit)
  * The destination you explicitly chose
  * The `.bak` next to the original (Save-in-Place only)
  * `~/.metaeditor/settings.json` (your theme and recent-files list)

---

## 🤝 Contributing

Pull requests welcome. The handler interface is intentionally tiny — adding a
new format usually means one new file in `metadata_handlers/` and one line
in `__init__.py`. If you can read it with a Python library, MetaEditor can
edit it.

Ideas on the wishlist:

* Batch mode (apply a JSON template to a folder of files)
* Windows-native creation-date editing
* A CLI front-end that reuses the handlers
* Sidecar-file support (`.xmp`)

---

## 📜 License

MIT
