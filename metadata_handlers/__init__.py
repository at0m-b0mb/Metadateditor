from .image_handler   import ImageHandler
from .audio_handler   import AudioHandler
from .pdf_handler     import PdfHandler
from .office_handler  import OfficeHandler
from .general_handler import GeneralHandler

HANDLERS = {
    # ── Images ────────────────────────────────────────────────────────────
    ".jpg": ImageHandler, ".jpeg": ImageHandler, ".jpe": ImageHandler,
    ".tif": ImageHandler, ".tiff": ImageHandler,
    ".png": ImageHandler,
    ".webp": ImageHandler,
    ".heic": ImageHandler, ".heif": ImageHandler,

    # RAW camera formats (TIFF-based EXIF)
    ".dng": ImageHandler,                          # Adobe DNG
    ".cr2": ImageHandler, ".cr3": ImageHandler,    # Canon
    ".nef": ImageHandler, ".nrw": ImageHandler,    # Nikon
    ".arw": ImageHandler, ".sr2": ImageHandler,    # Sony
    ".rw2": ImageHandler,                          # Panasonic
    ".orf": ImageHandler,                          # Olympus
    ".raf": ImageHandler,                          # Fujifilm
    ".pef": ImageHandler,                          # Pentax
    ".x3f": ImageHandler,                          # Sigma
    ".3fr": ImageHandler,                          # Hasselblad

    # ── Audio ─────────────────────────────────────────────────────────────
    ".mp3":  AudioHandler,
    ".flac": AudioHandler,
    ".ogg":  AudioHandler, ".oga": AudioHandler,
    ".m4a":  AudioHandler, ".aac": AudioHandler,
    ".m4b":  AudioHandler,                         # Apple audiobook
    ".m4r":  AudioHandler,                         # iPhone ringtone
    ".wav":  AudioHandler,
    ".aiff": AudioHandler, ".aif": AudioHandler,
    ".wma":  AudioHandler,
    ".opus": AudioHandler,
    ".ape":  AudioHandler,                         # Monkey's Audio
    ".mpc":  AudioHandler,                         # Musepack
    ".wv":   AudioHandler,                         # WavPack
    ".mp2":  AudioHandler,
    ".spx":  AudioHandler,                         # Speex
    ".dsf":  AudioHandler,                         # DSD

    # ── Video ─────────────────────────────────────────────────────────────
    ".mp4":  AudioHandler, ".m4v": AudioHandler,
    ".mkv":  AudioHandler, ".mka": AudioHandler,
    ".mov":  AudioHandler,
    ".avi":  AudioHandler,
    ".wmv":  AudioHandler,
    ".webm": AudioHandler,
    ".3gp":  AudioHandler, ".3g2": AudioHandler,
    ".asf":  AudioHandler,
    ".ogv":  AudioHandler,
    ".flv":  AudioHandler,

    # ── PDF ───────────────────────────────────────────────────────────────
    ".pdf": PdfHandler,

    # ── Office / Documents ────────────────────────────────────────────────
    ".docx": OfficeHandler,
    ".xlsx": OfficeHandler,
    ".pptx": OfficeHandler,
    ".epub": OfficeHandler,
}


def get_handler(ext: str, path: str):
    """Return the best handler for this extension.
    Falls back to GeneralHandler (filesystem metadata) for unknown types.
    """
    cls = HANDLERS.get(ext.lower())
    return (cls or GeneralHandler)(path)
