import os
from datetime import datetime
from pypdf import PdfReader, PdfWriter


class PdfHandler:
    file_type = 'PDF Document'

    FIELDS = [
        ('/Title',        'Title',                   True),
        ('/Author',       'Author',                  True),
        ('/Subject',      'Subject',                 True),
        ('/Keywords',     'Keywords',                True),
        ('/Creator',      'Creator Application',     True),
        ('/Producer',     'Producer',                True),
        ('/CreationDate', 'Creation Date',           True),
        ('/ModDate',      'Modification Date',       True),
        ('/Trapped',      'Trapped',                 True),
    ]

    def __init__(self, path):
        self.path = path

    @staticmethod
    def _format_pdf_date(raw):
        """PDF dates are stored as D:YYYYMMDDHHmmSSOHH'mm. Convert to a friendly form."""
        if not raw:
            return ''
        s = str(raw)
        if s.startswith('D:'):
            s = s[2:]
        try:
            year   = s[0:4]
            month  = s[4:6] if len(s) >= 6 else '01'
            day    = s[6:8] if len(s) >= 8 else '01'
            hour   = s[8:10] if len(s) >= 10 else '00'
            minute = s[10:12] if len(s) >= 12 else '00'
            second = s[12:14] if len(s) >= 14 else '00'
            return f'{year}-{month}-{day} {hour}:{minute}:{second}'
        except Exception:
            return s

    @staticmethod
    def _parse_pdf_date(val):
        """Accept friendly date strings and convert to PDF date format."""
        if not val:
            return ''
        val = val.strip()
        # Already in PDF format
        if val.startswith('D:'):
            return val
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y/%m/%d %H:%M:%S', '%Y/%m/%d'):
            try:
                dt = datetime.strptime(val, fmt)
                return f"D:{dt.strftime('%Y%m%d%H%M%S')}"
            except ValueError:
                pass
        # Last-resort: pass through verbatim
        return val

    def read(self):
        sections = []
        try:
            reader = PdfReader(self.path)
            sections.append({'name': 'File Information', 'icon': 'file-text', 'fields': [
                {'key': '_pages', 'label': 'Page Count', 'value': str(len(reader.pages)), 'type': 'text', 'editable': False},
                {'key': '_enc', 'label': 'Encrypted', 'value': 'Yes' if reader.is_encrypted else 'No', 'type': 'text', 'editable': False},
                {'key': '_ver', 'label': 'PDF Version', 'value': str(getattr(reader, 'pdf_header', '') or '%PDF-?').lstrip('%PDF-'), 'type': 'text', 'editable': False},
            ]})

            meta = reader.metadata or {}
            doc_fields = []
            for key, label, editable in self.FIELDS:
                raw = meta.get(key, '')
                if key in ('/CreationDate', '/ModDate'):
                    val = self._format_pdf_date(raw)
                else:
                    val = str(raw) if raw else ''
                doc_fields.append({
                    'key': f'pdf_{key[1:].lower()}',
                    'label': label,
                    'value': val,
                    'type': 'text',
                    'editable': editable,
                    '_pdf_key': key,
                })
            # Custom metadata fields beyond the standard set
            standard_keys = {k for k, _, _ in self.FIELDS}
            for key, raw in meta.items():
                if key in standard_keys:
                    continue
                doc_fields.append({
                    'key': f'pdf_custom_{key[1:].lower()}',
                    'label': key.lstrip('/'),
                    'value': str(raw) if raw else '',
                    'type': 'text',
                    'editable': True,
                    '_pdf_key': key,
                })
            sections.append({'name': 'Document Properties', 'icon': 'file-text', 'fields': doc_fields})

        except Exception as e:
            sections.append({'name': 'Error', 'icon': 'alert', 'fields': [
                {'key': 'err', 'label': 'Error', 'value': str(e), 'type': 'text', 'editable': False},
            ]})
        return sections

    def write(self, sections):
        reader = PdfReader(self.path)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        new_meta = {}
        for section in sections:
            for field in section.get('fields', []):
                if not field.get('editable'):
                    continue
                key = field.get('_pdf_key')
                val = (field.get('value') or '').strip()
                if not key:
                    continue
                if key in ('/CreationDate', '/ModDate') and val:
                    val = self._parse_pdf_date(val)
                if val:
                    new_meta[key] = val

        writer.add_metadata(new_meta)

        tmp = self.path + '.tmp'
        with open(tmp, 'wb') as f:
            writer.write(f)
        os.replace(tmp, self.path)

    def strip(self):
        """Remove the PDF's Info dictionary entirely."""
        reader = PdfReader(self.path)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        # Add a single placeholder so the Info dict is empty but valid
        writer.add_metadata({})
        tmp = self.path + '.tmp'
        with open(tmp, 'wb') as f:
            writer.write(f)
        os.replace(tmp, self.path)
