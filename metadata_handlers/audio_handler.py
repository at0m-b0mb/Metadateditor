import os
from mutagen import File

# Register 'lyrics' as an EasyID3 key so MP3 lyrics round-trip correctly
try:
    from mutagen.easyid3 import EasyID3
    from mutagen.id3 import USLT
    EasyID3.RegisterKey(
        'lyrics',
        getter=lambda id3, _: [str(v) for v in id3.getall('USLT')],
        setter=lambda id3, _, val: id3.setall('USLT', [USLT(encoding=3, lang='eng', desc='', text=v) for v in val]),
        deleter=lambda id3, _: id3.delall('USLT'),
    )
except Exception:
    pass


class AudioHandler:
    file_type = 'Audio / Video'

    EASY_TAGS = [
        ('title',        'Title'),
        ('artist',       'Artist'),
        ('albumartist',  'Album Artist'),
        ('album',        'Album'),
        ('date',         'Date / Year'),
        ('genre',        'Genre'),
        ('tracknumber',  'Track Number'),
        ('discnumber',   'Disc Number'),
        ('composer',     'Composer'),
        ('lyricist',     'Lyricist'),
        ('comment',      'Comment'),
        ('description',  'Description'),
        ('bpm',          'BPM'),
        ('language',     'Language'),
        ('copyright',    'Copyright'),
        ('encodedby',    'Encoded By'),
        ('organization', 'Label / Organization'),
        ('isrc',         'ISRC'),
        ('conductor',    'Conductor'),
        ('remixer',      'Remixer / Mix Artist'),
        ('compilation',  'Compilation (1=yes)'),
        ('grouping',     'Grouping / Content Group'),
        ('mood',         'Mood'),
        ('website',      'Website'),
        ('lyrics',       'Lyrics'),
    ]

    def __init__(self, path):
        self.path = path
        self.ext = os.path.splitext(path)[1].lower()

    def read(self):
        sections = []
        try:
            audio = File(self.path, easy=True)
            if audio is None:
                return [{'name': 'Error', 'icon': 'alert', 'fields': [
                    {'key': 'err', 'label': 'Error', 'value': 'Could not read file — unsupported format.', 'type': 'text', 'editable': False},
                ]}]

            info_fields = [
                {'key': '_fmt', 'label': 'Format', 'value': type(audio).__name__, 'type': 'text', 'editable': False},
                {'key': '_ext', 'label': 'Extension', 'value': self.ext.upper().lstrip('.'), 'type': 'text', 'editable': False},
            ]
            if hasattr(audio, 'info'):
                nfo = audio.info
                if hasattr(nfo, 'length') and nfo.length:
                    m, s = divmod(int(nfo.length), 60)
                    h, m = divmod(m, 60)
                    dur = f'{h}:{m:02d}:{s:02d}' if h else f'{m}:{s:02d}'
                    info_fields.append({'key': '_dur', 'label': 'Duration', 'value': dur, 'type': 'text', 'editable': False})
                if hasattr(nfo, 'bitrate') and nfo.bitrate:
                    info_fields.append({'key': '_br', 'label': 'Bitrate', 'value': f'{nfo.bitrate} kbps', 'type': 'text', 'editable': False})
                if hasattr(nfo, 'sample_rate') and nfo.sample_rate:
                    info_fields.append({'key': '_sr', 'label': 'Sample Rate', 'value': f'{nfo.sample_rate} Hz', 'type': 'text', 'editable': False})
                if hasattr(nfo, 'channels') and nfo.channels:
                    info_fields.append({'key': '_ch', 'label': 'Channels', 'value': str(nfo.channels), 'type': 'text', 'editable': False})

            sections.append({'name': 'File Information', 'icon': 'music', 'fields': info_fields})

            tag_fields = []
            for easy_key, label in self.EASY_TAGS:
                try:
                    raw = audio.get(easy_key)
                    val = str(raw[0]) if raw else ''
                except Exception:
                    val = ''
                tag_fields.append({
                    'key': f'tag_{easy_key}',
                    'label': label,
                    'value': val,
                    'type': 'text',
                    'editable': True,
                    '_tag_key': easy_key,
                })
            sections.append({'name': 'Tags', 'icon': 'tag', 'fields': tag_fields})

        except Exception as e:
            sections.append({'name': 'Error', 'icon': 'alert', 'fields': [
                {'key': 'err', 'label': 'Error', 'value': str(e), 'type': 'text', 'editable': False},
            ]})
        return sections

    def write(self, sections):
        audio = File(self.path, easy=True)
        if audio is None:
            raise Exception('Could not open file for writing.')

        for section in sections:
            for field in section.get('fields', []):
                if not field.get('editable'):
                    continue
                tag_key = field.get('_tag_key')
                if not tag_key:
                    continue
                val = (field.get('value') or '').strip()
                try:
                    if val:
                        audio[tag_key] = [val]
                    elif tag_key in audio:
                        del audio[tag_key]
                except Exception:
                    pass  # tag not supported by this format — skip silently

        audio.save()

    def strip(self):
        """Remove all editable tags from the file."""
        audio = File(self.path, easy=True)
        if audio is None:
            return
        try:
            audio.delete()
        except Exception:
            for key in list(audio.keys()):
                try:
                    del audio[key]
                except Exception:
                    pass
        try:
            audio.save()
        except Exception:
            pass
