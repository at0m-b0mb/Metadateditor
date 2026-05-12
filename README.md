<div align="center">

# ⚡ MetaEditor

### Universal Metadata Editor for Everything

*One desktop app to read, edit, strip, export and import metadata from
images, audio, video, PDFs, Office documents, e-books — and the
filesystem itself.*

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)](#)
[![Formats](https://img.shields.io/badge/Formats-50+-8b5cf6)](#-supported-formats)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux%20%7C%20Windows-10b981)](#)
[![License](https://img.shields.io/badge/License-MIT-blue)](#)

</div>

---

## ✨ Why MetaEditor?

Most metadata tools focus on a single format — one for EXIF, another for ID3,
another for PDF, and yet another for Office docs. **MetaEditor unifies them all
in a single dark/light themed desktop app**, with a consistent edit-and-save
workflow that works the same way regardless of what you open.

Beyond format metadata, MetaEditor also lets you edit data the OS normally
hides from you: file timestamps, permissions, and extended attributes — for
*any* file type.

---

## 🚀 Headline Features

|     | Feature | What it does |
| :-: | --- | --- |
| 🖼️ | **50+ formats** | JPEG · PNG · TIFF · WEBP · HEIC · RAW · MP3 · FLAC · WAV · OGG · MP4 · MKV · MOV · PDF · DOCX · XLSX · PPTX · EPUB · and more |
| 💾 | **Save in place or Save As** | Overwrite the original (with automatic timestamped backup), or save a clean copy elsewhere |
| 🗑 | **Strip All Metadata** | One click privacy — removes EXIF, ID3, PDF Info, Office props, and extended attributes |
| 📤 | **Export / Import JSON** | Copy metadata between files, version-control your tags, or back up before risky edits |
| 🔍 | **Live search** | Filter hundreds of fields instantly — search by name or value |
| ↶ ↷ | **Undo / Redo** | 100-step history per file, with full keyboard shortcuts |
| 📂 | **Drag & drop** | Drop a file onto the window to open it instantly *(via `tkinterdnd2`)* |
| 🕘 | **Recent files** | Quick re-open from a menu that remembers your last 10 files |
| 🌗 | **Dark / light theme** | Toggle with one click — preference is remembered between sessions |
| 🗺 | **GPS map link** | Open an image's GPS coordinates straight in OpenStreetMap |
| ⌨️ | **Full keyboard shortcuts** | ⌘O · ⌘S · ⌘⇧S · ⌘Z · ⌘⇧Z · ⌘F · ⌘R |
| 🖼️ | **Image preview** | Thumbnail of the loaded image right in the sidebar |
| 📅 | **Filesystem metadata for *every* file** | Edit modification time, access time, creation date (macOS), permissions, and xattrs — even on file types we don't otherwise understand |

---

## 📦 Installation

### Prerequisites

* **Python 3.9** or later
* **macOS** / **Linux** / **Windows**

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
│  └────────────┘  │ │ 🔍 Exposure & Lens   · 18 fields · 16 editable │   │
│  Tools           │ │   ...                                          │   │
│  📤 Export JSON  │ └────────────────────────────────────────────────┘   │
│  📥 Import JSON  │                                                      │
│  🗑 Strip Meta   │                                                      │
├──────────────────┴──────────────────────────────────────────────────────┤
│  ✓ Loaded sunset.jpg  •  47 editable fields                  v2.0  •  drag-drop on │   ← Status bar
└─────────────────────────────────────────────────────────────────────────┘
```

### Field Indicators

| Symbol | Meaning |
| :-: | --- |
| `●` (filled, normal color) | **Editable** — click to type a new value |
| `○` (hollow, dim) | **Read-only** — computed from the file (e.g. pixel dimensions) |
| `●  Label  ✎` | **Modified** — value differs from when the file was opened |
| Purple dot in sidebar stats | Live count of modified fields |

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

### Filesystem (every file)

* **Date Modified** — editable
* **Date Accessed** — editable
* **Date Created** — editable on macOS (uses `SetFile`)
* **Permissions** — editable on POSIX (`rwx` or octal form)
* **Owner** — read-only (requires `sudo`)
* **Extended attributes** (`xattr` on macOS, `getxattr` on Linux) — editable

</details>

---

## 🔧 Power-User Tools

### 🗑 Strip All Metadata

Removes every editable piece of metadata in one pass and writes the result to a
new file. Useful before:

* Posting photos online (strips GPS / camera serial / unique IDs)
* Sharing a document (clears Author / Company / Last-Modified-By)
* Distributing audio (wipes ID3 v1/v2 tags)

Filesystem **xattrs** are also cleared (this removes macOS's `com.apple.quarantine`
flag among others).

### 📤 Export Metadata as JSON

Dumps the entire field tree to a structured JSON file — perfect for:

* Backing up metadata before bulk edits
* Diffing the metadata of two files
* Version-controlling tag changes alongside the files themselves

```jsonc
{
  "source":      "sunset.jpg",
  "exported_at": "2026-05-11T14:32:10",
  "app":         "MetaEditor 2.0",
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
backup first** (`photo.jpg.20260511_143210.bak`). This means you can:

* Iterate on edits without producing dozens of `_edited` copies
* Roll back instantly by renaming the `.bak`

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
whatever its format provides.

---

## 🛠 Troubleshooting

<details>
<summary><b>I see "○" next to a field — why can't I edit it?</b></summary>

Hollow circles mark **read-only** fields. These are values that are computed
from the file's content rather than stored as metadata — pixel dimensions,
file size, duration, MD5, etc. Changing them in MetaEditor wouldn't make sense
because they'd be overwritten the next time the file is read.

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

The filesystem date editor accepts these formats:

* `YYYY-MM-DD HH:MM:SS`  *(preferred)*
* `YYYY-MM-DD`
* `YYYY/MM/DD HH:MM:SS`
* `MM/DD/YYYY HH:MM:SS`
* `DD-MM-YYYY HH:MM:SS`

The PDF / EXIF date editor accepts `YYYY-MM-DD HH:MM:SS` and converts to the
format the spec requires.

</details>

<details>
<summary><b>How do I edit creation date on Linux / Windows?</b></summary>

Creation time (`btime`) is only routinely settable on **macOS** (via the
`SetFile` Xcode command-line tool, included with macOS). Linux's
`statx(2)` exposes `btime` to *readers* but most filesystems don't allow
writers to set it; Windows has its own NTFS-specific APIs.

If you need to fake a creation time portably, the most reliable trick is
to set **mtime** (which MetaEditor edits on every platform).

</details>

---

## 🛡 Privacy & Safety

* **Original files are never modified directly.** Edits go to a working copy
  in a temp directory. Saving copies the working file to the destination.
* **Save in Place creates a `.bak`** before overwriting — so even there, you
  can always roll back.
* MetaEditor is **fully offline**. It does not phone home, doesn't collect
  telemetry, doesn't open network connections. The only outgoing link is the
  optional "🗺" button which opens OpenStreetMap in your browser.

---

## 🤝 Contributing

Pull requests welcome. The handler interface is intentionally tiny — adding a
new format usually means one new file in `metadata_handlers/` and one line in
`__init__.py`. If you can read it with a Python library, MetaEditor can edit
it.

---

## 📜 License

MIT
