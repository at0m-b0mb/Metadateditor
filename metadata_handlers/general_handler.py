"""
GeneralHandler — filesystem dates, permissions, and extended attributes.
Works on every file regardless of format.  Sections are tagged with
_general=True so the save logic knows to route them here, not to the
format-specific handler.
"""

import os
import stat
import platform
import re
import shutil
import subprocess
from datetime import datetime


# ── helpers ────────────────────────────────────────────────────────────────

def _ts(ts: float) -> str:
    try:
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ""


def _parse(s: str) -> float:
    s = s.strip()
    for fmt in (
        "%Y-%m-%d %H:%M:%S", "%Y-%m-%d",
        "%Y/%m/%d %H:%M:%S", "%Y/%m/%d",
        "%m/%d/%Y %H:%M:%S", "%m/%d/%Y",
        "%d-%m-%Y %H:%M:%S", "%d-%m-%Y",
        "%d/%m/%Y %H:%M:%S", "%d/%m/%Y",
    ):
        try:
            return datetime.strptime(s, fmt).timestamp()
        except ValueError:
            pass
    raise ValueError(f"Cannot parse date: '{s}'  — use YYYY-MM-DD HH:MM:SS")


def _field(key, label, value, editable=False, **extra):
    f = {"key": key, "label": label, "value": value,
         "type": "text", "editable": editable, "_general": True}
    f.update(extra)
    return f


# ══════════════════════════════════════════════════════════════════════════
class GeneralHandler:
# ══════════════════════════════════════════════════════════════════════════

    file_type = "General File"

    def __init__(self, path: str):
        self.path = path

    # ── read ───────────────────────────────────────────────────────────────

    def read(self) -> list:
        sections = []

        # ── Filesystem section ──────────────────────────────────────────
        try:
            s = os.stat(self.path)
            fields = []

            # Modification time — writable via os.utime
            fields.append(_field(
                "fs_mtime", "Date Modified", _ts(s.st_mtime),
                editable=True, _fs="mtime",
            ))

            # Access time — writable via os.utime
            fields.append(_field(
                "fs_atime", "Date Accessed", _ts(s.st_atime),
                editable=True, _fs="atime",
            ))

            # Creation / birth time — editable on macOS via SetFile
            if hasattr(s, "st_birthtime"):
                birth_editable = platform.system() == "Darwin" and \
                    shutil.which("SetFile") is not None
                fields.append(_field(
                    "fs_btime", "Date Created", _ts(s.st_birthtime),
                    editable=birth_editable, _fs="birthtime",
                ))

            # ctime — metadata change time, not directly editable
            fields.append(_field(
                "fs_ctime", "Date Metadata Changed", _ts(s.st_ctime),
                editable=False, _fs="ctime",
            ))

            # Size (calculated, read-only)
            fields.append(_field(
                "fs_size", "File Size", f"{s.st_size:,} bytes",
            ))

            # Permissions — editable via chmod on POSIX
            perms_editable = platform.system() != "Windows"
            fields.append(_field(
                "fs_perms", "Permissions", stat.filemode(s.st_mode),
                editable=perms_editable, _fs="perms",
            ))

            # Permissions in octal — also editable as an alternate input
            fields.append(_field(
                "fs_perms_octal", "Permissions (Octal)",
                oct(stat.S_IMODE(s.st_mode))[2:].zfill(3),
                editable=perms_editable, _fs="perms_octal",
            ))

            # Owner (read-only — requires root to change)
            try:
                import pwd
                owner = pwd.getpwuid(s.st_uid).pw_name
            except Exception:
                owner = str(s.st_uid)
            fields.append(_field("fs_owner", "Owner", owner))

            # File path information
            fields.append(_field(
                "fs_path", "Full Path", os.path.abspath(self.path),
            ))

            sections.append({
                "name": "File System",
                "icon": "file",
                "_general": True,
                "fields": fields,
            })

        except Exception as exc:
            sections.append({
                "name": "File System", "icon": "alert", "_general": True,
                "fields": [_field("fs_err", "Error", str(exc))],
            })

        # ── Extended-attributes section ─────────────────────────────────
        xattr_fields = self._read_xattrs()
        if xattr_fields:
            sections.append({
                "name": "Extended Attributes (xattr)",
                "icon": "tag",
                "_general": True,
                "fields": xattr_fields,
            })

        return sections

    # ── xattr reading ───────────────────────────────────────────────────

    def _read_xattrs(self) -> list:
        sys = platform.system()
        if sys == "Darwin":
            return self._xattrs_darwin()
        if sys == "Linux":
            return self._xattrs_linux()
        return []

    def _xattrs_darwin(self) -> list:
        try:
            r = subprocess.run(
                ["xattr", self.path],
                capture_output=True, text=True, timeout=5,
            )
            names = [n.strip() for n in r.stdout.strip().splitlines() if n.strip()]
        except Exception:
            return []

        fields = []
        for name in names:
            try:
                r2 = subprocess.run(
                    ["xattr", "-p", name, self.path],
                    capture_output=True, timeout=5,
                )
                try:
                    val = r2.stdout.decode("utf-8").rstrip("\n")
                    stripped = val.replace(" ", "").replace("\n", "")
                    is_binary = len(stripped) > 16 and all(
                        c in "0123456789abcdefABCDEF" for c in stripped
                    )
                    if is_binary or "\x00" in val:
                        val = "[binary data]"
                        editable = False
                    else:
                        editable = True
                except UnicodeDecodeError:
                    val = "[binary data]"
                    editable = False

                fields.append(_field(
                    f"xattr_{name.replace('.','_').replace(':','_')}",
                    name, val,
                    editable=editable, _xattr=name,
                ))
            except Exception:
                pass

        return fields

    def _xattrs_linux(self) -> list:
        try:
            names = os.listxattr(self.path)
        except Exception:
            return []

        fields = []
        for name in names:
            try:
                raw = os.getxattr(self.path, name)
                try:
                    val = raw.decode("utf-8").strip("\x00")
                    editable = True
                except UnicodeDecodeError:
                    val = "[binary data]"
                    editable = False
                fields.append(_field(
                    f"xattr_{name.replace('.','_')}",
                    name, val,
                    editable=editable, _xattr=name,
                ))
            except Exception:
                pass

        return fields

    # ── write ──────────────────────────────────────────────────────────────

    @staticmethod
    def _filemode_to_octal(mode_str: str):
        """Convert rwx-style ('-rwxr-xr--') back to an octal int."""
        s = mode_str.strip()
        if len(s) == 10:
            s = s[1:]  # drop file-type marker
        if len(s) != 9:
            return None
        result = 0
        for i, group in enumerate((s[0:3], s[3:6], s[6:9])):
            v = 0
            if group[0] == 'r':
                v |= 4
            if group[1] == 'w':
                v |= 2
            if group[2] in ('x', 's', 't', 'S', 'T'):
                v |= 1
            result = (result << 3) | v
        return result

    def write(self, sections: list):
        new_atime = new_mtime = new_btime = None
        new_perms = None
        xattr_updates: dict = {}

        for section in sections:
            for field in section.get("fields", []):
                if not field.get("editable"):
                    continue
                val   = (field.get("value") or "").strip()
                fs    = field.get("_fs")
                xattr = field.get("_xattr")

                if fs == "mtime" and val:
                    try:
                        new_mtime = _parse(val)
                    except Exception:
                        pass
                elif fs == "atime" and val:
                    try:
                        new_atime = _parse(val)
                    except Exception:
                        pass
                elif fs == "birthtime" and val:
                    try:
                        new_btime = _parse(val)
                    except Exception:
                        pass
                elif fs == "perms" and val:
                    octal = self._filemode_to_octal(val)
                    if octal is not None:
                        new_perms = octal
                elif fs == "perms_octal" and val:
                    if re.fullmatch(r'[0-7]{3,4}', val):
                        try:
                            new_perms = int(val, 8)
                        except Exception:
                            pass
                elif xattr:
                    xattr_updates[xattr] = val

        # Apply timestamp changes
        if new_mtime is not None or new_atime is not None:
            s = os.stat(self.path)
            atime = new_atime if new_atime is not None else s.st_atime
            mtime = new_mtime if new_mtime is not None else s.st_mtime
            os.utime(self.path, (atime, mtime))

        # macOS creation time via SetFile
        if new_btime is not None and platform.system() == "Darwin":
            try:
                dt = datetime.fromtimestamp(new_btime)
                stamp = dt.strftime("%m/%d/%Y %H:%M:%S")
                subprocess.run(
                    ["SetFile", "-d", stamp, self.path],
                    capture_output=True, timeout=5,
                )
            except Exception:
                pass

        # Permission changes
        if new_perms is not None:
            try:
                os.chmod(self.path, new_perms)
            except Exception:
                pass

        # Apply xattr changes
        sys = platform.system()
        for key, val in xattr_updates.items():
            if val and val != "[binary data]":
                try:
                    if sys == "Darwin":
                        subprocess.run(
                            ["xattr", "-w", key, val, self.path], timeout=5)
                    elif sys == "Linux":
                        os.setxattr(self.path, key, val.encode("utf-8"))
                except Exception:
                    pass
            else:
                try:
                    if sys == "Darwin":
                        subprocess.run(
                            ["xattr", "-d", key, self.path], timeout=5)
                    elif sys == "Linux":
                        os.removexattr(self.path, key)
                except Exception:
                    pass

    def strip(self):
        """Remove all extended attributes from the file."""
        sys = platform.system()
        if sys == "Darwin":
            try:
                subprocess.run(["xattr", "-c", self.path], timeout=5)
            except Exception:
                pass
        elif sys == "Linux":
            try:
                for name in os.listxattr(self.path):
                    try:
                        os.removexattr(self.path, name)
                    except Exception:
                        pass
            except Exception:
                pass
