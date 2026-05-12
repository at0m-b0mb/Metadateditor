import os
import zipfile
import xml.etree.ElementTree as ET


class OfficeHandler:
    file_type = 'Office / Document'

    NS = {
        'cp':      'http://schemas.openxmlformats.org/package/2006/metadata/core-properties',
        'dc':      'http://purl.org/dc/elements/1.1/',
        'dcterms': 'http://purl.org/dc/terms/',
        'xsi':     'http://www.w3.org/2001/XMLSchema-instance',
    }

    APP_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/extended-properties'

    CORE_FIELDS = [
        ('dc:title',           'Title',             True),
        ('dc:subject',         'Subject',           True),
        ('dc:creator',         'Author',            True),
        ('cp:keywords',        'Keywords',          True),
        ('dc:description',     'Description',       True),
        ('cp:lastModifiedBy',  'Last Modified By',  True),
        ('dcterms:created',    'Created',           True),
        ('dcterms:modified',   'Modified',          True),
        ('cp:category',        'Category',          True),
        ('cp:version',         'Version',           True),
        ('cp:revision',        'Revision',          True),
    ]

    APP_FIELDS = [
        ('Application',  'Application',   True),
        ('AppVersion',   'App Version',   True),
        ('Company',      'Company',       True),
        ('Manager',      'Manager',       True),
        ('Template',     'Template',      True),
    ]

    EPUB_DC_FIELDS = [
        ('title',       'Title'),
        ('creator',     'Author'),
        ('subject',     'Subject'),
        ('description', 'Description'),
        ('publisher',   'Publisher'),
        ('contributor', 'Contributor'),
        ('date',        'Date'),
        ('type',        'Type'),
        ('format',      'Format'),
        ('identifier',  'Identifier'),
        ('source',      'Source'),
        ('language',    'Language'),
        ('rights',      'Rights'),
    ]

    def __init__(self, path):
        self.path = path
        self.ext = os.path.splitext(path)[1].lower()

    def _ns(self, tag):
        prefix, local = tag.split(':')
        return f'{{{self.NS[prefix]}}}{local}'

    # ── read ─────────────────────────────────────────────────────────────────

    def read(self):
        if self.ext == '.epub':
            return self._read_epub()
        return self._read_ooxml()

    def _read_ooxml(self):
        sections = []
        try:
            if not zipfile.is_zipfile(self.path):
                raise ValueError('Not a valid Office file (not a ZIP archive).')

            with zipfile.ZipFile(self.path, 'r') as z:
                names = z.namelist()

                if 'docProps/core.xml' in names:
                    root = ET.fromstring(z.read('docProps/core.xml'))
                    fields = []
                    for tag, label, editable in self.CORE_FIELDS:
                        elem = root.find(self._ns(tag))
                        val = (elem.text or '') if elem is not None else ''
                        fields.append({
                            'key': f'core_{tag.replace(":", "_")}',
                            'label': label,
                            'value': val,
                            'type': 'text',
                            'editable': editable,
                            '_core_tag': tag,
                        })
                    sections.append({'name': 'Document Properties', 'icon': 'file-text', 'fields': fields})

                if 'docProps/app.xml' in names:
                    root = ET.fromstring(z.read('docProps/app.xml'))
                    fields = []
                    for xml_tag, label, editable in self.APP_FIELDS:
                        elem = root.find(f'{{{self.APP_NS}}}{xml_tag}')
                        val = (elem.text or '') if elem is not None else ''
                        fields.append({
                            'key': f'app_{xml_tag.lower()}',
                            'label': label,
                            'value': val,
                            'type': 'text',
                            'editable': editable,
                            '_app_tag': xml_tag,
                        })
                    sections.append({'name': 'Application Properties', 'icon': 'monitor', 'fields': fields})

        except Exception as e:
            sections.append({'name': 'Error', 'icon': 'alert', 'fields': [
                {'key': 'err', 'label': 'Error', 'value': str(e), 'type': 'text', 'editable': False},
            ]})
        return sections

    def _read_epub(self):
        sections = []
        try:
            with zipfile.ZipFile(self.path, 'r') as z:
                container = ET.fromstring(z.read('META-INF/container.xml'))
                ns_c = {'n': 'urn:oasis:names:tc:opendocument:xmlns:container'}
                rf = container.find('.//n:rootfile', ns_c)
                opf_path = rf.get('full-path') if rf is not None else 'OEBPS/content.opf'

                opf = ET.fromstring(z.read(opf_path))
                dc_ns = 'http://purl.org/dc/elements/1.1/'
                opf_ns = 'http://www.idpf.org/2007/opf'
                meta_elem = opf.find(f'{{{opf_ns}}}metadata') or opf.find('metadata')

                fields = []
                for tag, label in self.EPUB_DC_FIELDS:
                    elem = meta_elem.find(f'{{{dc_ns}}}{tag}') if meta_elem is not None else None
                    val = (elem.text or '') if elem is not None else ''
                    fields.append({
                        'key': f'epub_{tag}',
                        'label': label,
                        'value': val,
                        'type': 'text',
                        'editable': True,
                        '_epub_tag': tag,
                    })
                sections.append({'name': 'Book Metadata', 'icon': 'book-open', 'fields': fields})

        except Exception as e:
            sections.append({'name': 'Error', 'icon': 'alert', 'fields': [
                {'key': 'err', 'label': 'Error', 'value': str(e), 'type': 'text', 'editable': False},
            ]})
        return sections

    # ── write ─────────────────────────────────────────────────────────────────

    def write(self, sections):
        if self.ext == '.epub':
            self._write_epub(sections)
        else:
            self._write_ooxml(sections)

    def _write_ooxml(self, sections):
        core_updates, app_updates, custom_updates = {}, {}, {}
        for section in sections:
            for field in section.get('fields', []):
                if not field.get('editable'):
                    continue
                if '_core_tag' in field:
                    core_updates[field['_core_tag']] = field.get('value', '')
                elif '_app_tag' in field:
                    app_updates[field['_app_tag']] = field.get('value', '')
                elif '_custom_name' in field:
                    custom_updates[field['_custom_name']] = field.get('value', '')

        tmp = self.path + '.tmp'
        with zipfile.ZipFile(self.path, 'r') as zin:
            with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    data = zin.read(item.filename)
                    if item.filename == 'docProps/core.xml' and core_updates:
                        data = self._patch_core(data, core_updates)
                    elif item.filename == 'docProps/app.xml' and app_updates:
                        data = self._patch_app(data, app_updates)
                    zout.writestr(item, data)
        os.replace(tmp, self.path)

    def _patch_core(self, data, updates):
        for prefix, uri in self.NS.items():
            ET.register_namespace(prefix, uri)
        root = ET.fromstring(data)
        for tag, value in updates.items():
            elem = root.find(self._ns(tag))
            if elem is None:
                elem = ET.SubElement(root, self._ns(tag))
            elem.text = value
        return ET.tostring(root, encoding='utf-8', xml_declaration=True)

    def _patch_app(self, data, updates):
        ET.register_namespace('', self.APP_NS)
        root = ET.fromstring(data)
        for xml_tag, value in updates.items():
            elem = root.find(f'{{{self.APP_NS}}}{xml_tag}')
            if elem is None:
                elem = ET.SubElement(root, f'{{{self.APP_NS}}}{xml_tag}')
            elem.text = value
        return ET.tostring(root, encoding='utf-8', xml_declaration=True)

    def _write_epub(self, sections):
        epub_updates = {}
        for section in sections:
            for field in section.get('fields', []):
                if field.get('editable') and '_epub_tag' in field:
                    epub_updates[field['_epub_tag']] = field.get('value', '')

        with zipfile.ZipFile(self.path, 'r') as z:
            container = ET.fromstring(z.read('META-INF/container.xml'))
            ns_c = {'n': 'urn:oasis:names:tc:opendocument:xmlns:container'}
            rf = container.find('.//n:rootfile', ns_c)
            opf_path = rf.get('full-path') if rf is not None else 'OEBPS/content.opf'

            tmp = self.path + '.tmp'
            with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
                for item in z.infolist():
                    data = z.read(item.filename)
                    if item.filename == opf_path and epub_updates:
                        data = self._patch_opf(data, epub_updates)
                    zout.writestr(item, data)
        os.replace(tmp, self.path)

    def _patch_opf(self, data, updates):
        dc_ns = 'http://purl.org/dc/elements/1.1/'
        opf_ns = 'http://www.idpf.org/2007/opf'
        ET.register_namespace('dc', dc_ns)
        ET.register_namespace('opf', opf_ns)

        root = ET.fromstring(data)
        meta = root.find(f'{{{opf_ns}}}metadata') or root.find('metadata')
        if meta is None:
            return data

        for tag, value in updates.items():
            elem = meta.find(f'{{{dc_ns}}}{tag}')
            if elem is None:
                elem = ET.SubElement(meta, f'{{{dc_ns}}}{tag}')
            elem.text = value
        return ET.tostring(root, encoding='utf-8', xml_declaration=True)

    def strip(self):
        """Reset all known metadata fields to empty values."""
        empty_sections = []
        if self.ext == '.epub':
            empty_sections.append({'fields': [
                {'editable': True, '_epub_tag': tag, 'value': ''}
                for tag, _ in self.EPUB_DC_FIELDS
            ]})
        else:
            empty_sections.append({'fields': [
                {'editable': True, '_core_tag': tag, 'value': ''}
                for tag, _, _ in self.CORE_FIELDS
            ]})
            empty_sections.append({'fields': [
                {'editable': True, '_app_tag': tag, 'value': ''}
                for tag, _, _ in self.APP_FIELDS
            ]})
        self.write(empty_sections)
