import os
from fractions import Fraction
from PIL import Image
import piexif


class ImageHandler:
    file_type = 'Image'

    IFD0_TAGS = {
        0x010E: ('Image Description', 'text'),
        0x010F: ('Camera Make', 'text'),
        0x0110: ('Camera Model', 'text'),
        0x0112: ('Orientation', 'select', {
            1: 'Normal', 2: 'Mirrored Horizontal', 3: 'Rotated 180°',
            4: 'Mirrored Vertical', 5: 'Mirrored + Rotated 90° CW',
            6: 'Rotated 90° CW', 7: 'Mirrored + Rotated 90° CCW',
            8: 'Rotated 90° CCW',
        }),
        0x011A: ('X Resolution', 'rational'),
        0x011B: ('Y Resolution', 'rational'),
        0x0128: ('Resolution Unit', 'select', {
            1: 'No Unit', 2: 'Inches', 3: 'Centimeters',
        }),
        0x0131: ('Software', 'text'),
        0x0132: ('Date/Time Modified', 'datetime'),
        0x013B: ('Artist', 'text'),
        0x013E: ('White Point', 'text'),
        0x8298: ('Copyright', 'text'),
    }

    EXIF_TAGS = {
        0x829A: ('Exposure Time', 'rational'),
        0x829D: ('F-Number', 'rational'),
        0x8822: ('Exposure Program', 'select', {
            0: 'Not Defined', 1: 'Manual', 2: 'Normal Program',
            3: 'Aperture Priority', 4: 'Shutter Priority', 5: 'Creative Program',
            6: 'Action Program', 7: 'Portrait Mode', 8: 'Landscape Mode',
        }),
        0x8827: ('ISO Speed', 'int'),
        0x9003: ('Date/Time Original', 'datetime'),
        0x9004: ('Date/Time Digitized', 'datetime'),
        0x9201: ('Shutter Speed (APEX)', 'srational'),
        0x9202: ('Aperture (APEX)', 'rational'),
        0x9203: ('Brightness (APEX)', 'srational'),
        0x9204: ('Exposure Bias', 'srational'),
        0x9205: ('Max Aperture (APEX)', 'rational'),
        0x9206: ('Subject Distance (m)', 'rational'),
        0x9207: ('Metering Mode', 'select', {
            0: 'Unknown', 1: 'Average', 2: 'Center Weighted Average',
            3: 'Spot', 4: 'Multi-Spot', 5: 'Pattern', 6: 'Partial',
        }),
        0x9208: ('Light Source', 'select', {
            0: 'Unknown', 1: 'Daylight', 2: 'Fluorescent', 3: 'Tungsten',
            4: 'Flash', 9: 'Fine Weather', 10: 'Cloudy Weather', 11: 'Shade',
            17: 'Standard Light A', 18: 'Standard Light B', 19: 'Standard Light C',
        }),
        0x9209: ('Flash', 'select', {
            0: 'No Flash', 1: 'Flash Fired', 5: 'Flash Fired (No Return)',
            7: 'Flash Fired (Return Detected)', 9: 'Flash On (Fired)',
            16: 'Flash Off', 24: 'Auto (No Flash)', 25: 'Auto (Flash Fired)',
        }),
        0x920A: ('Focal Length (mm)', 'rational'),
        0xA001: ('Color Space', 'select', {1: 'sRGB', 65535: 'Uncalibrated'}),
        0xA002: ('Pixel Width', 'int_ro'),
        0xA003: ('Pixel Height', 'int_ro'),
        0xA402: ('Exposure Mode', 'select', {
            0: 'Auto', 1: 'Manual', 2: 'Auto Bracket',
        }),
        0xA403: ('White Balance', 'select', {
            0: 'Auto', 1: 'Manual',
        }),
        0xA404: ('Digital Zoom Ratio', 'rational'),
        0xA405: ('Focal Length 35mm (mm)', 'int'),
        0xA406: ('Scene Capture Type', 'select', {
            0: 'Standard', 1: 'Landscape', 2: 'Portrait', 3: 'Night Scene',
        }),
        0xA40A: ('Sharpness', 'select', {
            0: 'Normal', 1: 'Soft', 2: 'Hard',
        }),
        0xA420: ('Image Unique ID', 'text'),
        0xA430: ('Camera Owner', 'text'),
        0xA431: ('Camera Serial Number', 'text'),
        0xA433: ('Lens Make', 'text'),
        0xA434: ('Lens Model', 'text'),
        0xA435: ('Lens Serial Number', 'text'),
    }

    def __init__(self, path):
        self.path = path
        self.ext = os.path.splitext(path)[1].lower()

    # ── helpers ──────────────────────────────────────────────────────────────

    def _b2s(self, val):
        if isinstance(val, bytes):
            try:
                return val.decode('utf-8').rstrip('\x00')
            except Exception:
                try:
                    return val.decode('latin-1').rstrip('\x00')
                except Exception:
                    return val.hex()
        return val

    def _rational_display(self, val):
        if isinstance(val, tuple):
            if val[1] == 0:
                return '0'
            result = val[0] / val[1]
            if result == int(result):
                return str(int(result))
            return f'{result:.6f}'.rstrip('0').rstrip('.')
        return str(val)

    def _str_to_rational(self, s):
        s = str(s).strip()
        if '/' in s:
            n, d = s.split('/', 1)
            return (int(n), int(d))
        try:
            frac = Fraction(float(s)).limit_denominator(100000)
            return (frac.numerator, frac.denominator)
        except Exception:
            return (0, 1)

    def _gps_to_decimal(self, coords, ref):
        try:
            d = coords[0][0] / coords[0][1]
            m = coords[1][0] / coords[1][1]
            s = coords[2][0] / coords[2][1]
            dec = d + m / 60 + s / 3600
            if ref in ('S', 'W'):
                dec = -dec
            return dec
        except Exception:
            return None

    def _decimal_to_gps(self, decimal):
        decimal = abs(decimal)
        d = int(decimal)
        m = int((decimal - d) * 60)
        s_num = int(round(((decimal - d) * 60 - m) * 3600 * 100))
        return ((d, 1), (m, 1), (s_num, 100))

    def _format_val(self, val, ftype, info):
        if ftype in ('text', 'datetime'):
            return self._b2s(val)
        if ftype in ('int', 'int_ro'):
            return str(val)
        if ftype == 'rational':
            return self._rational_display(val)
        if ftype == 'srational':
            return self._rational_display(val)
        if ftype == 'select' and len(info) > 2:
            return str(info[2].get(val, val))
        return str(val)

    def _make_field(self, key, label, ftype, val_raw, val_display, info, ifd=None, tag=None):
        editable = not ftype.endswith('_ro')
        ftype_ui = 'select' if ftype == 'select' else 'text'
        field = {
            'key': key,
            'label': label,
            'value': val_display,
            'type': ftype_ui,
            'editable': editable,
        }
        if ifd is not None:
            field['_exif_ifd'] = ifd
            field['_exif_tag'] = tag
            field['_exif_type'] = ftype
        if ftype == 'select' and len(info) > 2:
            field['options'] = [{'value': str(k), 'label': v} for k, v in info[2].items()]
        return field

    # ── read ─────────────────────────────────────────────────────────────────

    def read(self):
        sections = []
        try:
            img = Image.open(self.path)
            sections.append({'name': 'File Information', 'icon': 'file', 'fields': [
                {'key': '_w', 'label': 'Width', 'value': f'{img.width} px', 'type': 'text', 'editable': False},
                {'key': '_h', 'label': 'Height', 'value': f'{img.height} px', 'type': 'text', 'editable': False},
                {'key': '_mode', 'label': 'Color Mode', 'value': img.mode, 'type': 'text', 'editable': False},
                {'key': '_fmt', 'label': 'Format', 'value': img.format or self.ext.upper().lstrip('.'), 'type': 'text', 'editable': False},
            ]})

            if self.ext in ('.jpg', '.jpeg', '.jpe', '.tif', '.tiff', '.webp'):
                self._read_exif(sections)

            if self.ext == '.png':
                self._read_png(sections, img)

        except Exception as e:
            sections.append({'name': 'Error', 'icon': 'alert', 'fields': [
                {'key': 'err', 'label': 'Error', 'value': str(e), 'type': 'text', 'editable': False},
            ]})
        return sections

    def _read_exif(self, sections):
        try:
            exif = piexif.load(self.path)
        except Exception:
            exif = {'0th': {}, 'Exif': {}, 'GPS': {}}

        ifd0_fields = []
        for tag, info in self.IFD0_TAGS.items():
            label, ftype = info[0], info[1]
            raw = exif.get('0th', {}).get(tag)
            display = self._format_val(raw, ftype, info) if raw is not None else ''
            ifd0_fields.append(self._make_field(f'ifd0_{tag}', label, ftype, raw, display, info, '0th', tag))
        sections.append({'name': 'Camera & Image', 'icon': 'camera', 'fields': ifd0_fields})

        exif_fields = []
        for tag, info in self.EXIF_TAGS.items():
            label, ftype = info[0], info[1]
            raw = exif.get('Exif', {}).get(tag)
            display = self._format_val(raw, ftype, info) if raw is not None else ''
            exif_fields.append(self._make_field(f'exif_{tag}', label, ftype, raw, display, info, 'Exif', tag))
        sections.append({'name': 'Exposure & Lens', 'icon': 'aperture', 'fields': exif_fields})

        gps = exif.get('GPS', {})
        gps_fields = []

        lat_raw, lat_ref_raw = gps.get(2), gps.get(1)
        lat_ref = self._b2s(lat_ref_raw) if lat_ref_raw else 'N'
        lat_dec = self._gps_to_decimal(lat_raw, lat_ref) if lat_raw else None
        gps_fields.append({'key': 'gps_lat', 'label': 'Latitude (decimal)', 'value': f'{lat_dec:.7f}' if lat_dec is not None else '', 'type': 'text', 'editable': True, '_exif_type': 'gps_lat'})

        lon_raw, lon_ref_raw = gps.get(4), gps.get(3)
        lon_ref = self._b2s(lon_ref_raw) if lon_ref_raw else 'E'
        lon_dec = self._gps_to_decimal(lon_raw, lon_ref) if lon_raw else None
        gps_fields.append({'key': 'gps_lon', 'label': 'Longitude (decimal)', 'value': f'{lon_dec:.7f}' if lon_dec is not None else '', 'type': 'text', 'editable': True, '_exif_type': 'gps_lon'})

        alt_raw = gps.get(6)
        alt_val = (alt_raw[0] / alt_raw[1]) if alt_raw and alt_raw[1] != 0 else None
        gps_fields.append({'key': 'gps_alt', 'label': 'Altitude (m)', 'value': f'{alt_val:.1f}' if alt_val is not None else '', 'type': 'text', 'editable': True, '_exif_type': 'gps_alt'})

        date_raw = gps.get(29)
        gps_fields.append({'key': 'gps_date', 'label': 'GPS Date', 'value': self._b2s(date_raw) if date_raw else '', 'type': 'text', 'editable': True, '_exif_type': 'gps_date'})

        sections.append({'name': 'GPS Location', 'icon': 'map-pin', 'fields': gps_fields})

    def _read_png(self, sections, img):
        known = {'Title', 'Author', 'Description', 'Copyright', 'Creation Time', 'Software', 'Disclaimer', 'Warning', 'Source', 'Comment'}
        fields = []
        existing = set()
        for k, v in img.info.items():
            if isinstance(v, str):
                existing.add(k)
                fields.append({'key': f'png_{k}', 'label': k, 'value': v, 'type': 'text', 'editable': k in known or True, '_png_key': k})
        for k in ['Title', 'Author', 'Description', 'Copyright', 'Software', 'Comment']:
            if k not in existing:
                fields.append({'key': f'png_{k}', 'label': k, 'value': '', 'type': 'text', 'editable': True, '_png_key': k})
        if fields:
            sections.append({'name': 'PNG Text Metadata', 'icon': 'tag', 'fields': fields})

    # ── write ─────────────────────────────────────────────────────────────────

    # EXIF-capable formats (TIFF-based RAWs share the same EXIF structure)
    _EXIF_EXTS = {
        '.jpg', '.jpeg', '.jpe',
        '.tif', '.tiff',
        '.webp',
        '.dng', '.cr2', '.cr3',
        '.nef', '.nrw',
        '.arw', '.sr2',
        '.rw2', '.orf', '.raf',
        '.pef', '.x3f', '.3fr',
        '.heic', '.heif',
    }

    def write(self, sections):
        if self.ext in self._EXIF_EXTS:
            self._write_exif(sections)
        elif self.ext == '.png':
            self._write_png(sections)

    def _write_exif(self, sections):
        try:
            exif = piexif.load(self.path)
        except Exception:
            exif = {'0th': {}, 'Exif': {}, 'GPS': {}, '1st': {}, 'thumbnail': None}

        for section in sections:
            for field in section.get('fields', []):
                if not field.get('editable'):
                    continue
                val = field.get('value', '')
                ifd = field.get('_exif_ifd')
                tag = field.get('_exif_tag')
                etype = field.get('_exif_type', 'text')

                if ifd and tag is not None:
                    if val == '' or val is None:
                        exif.get(ifd, {}).pop(tag, None)
                        continue

                    if etype == 'select':
                        # val is a human label ("Normal") — reverse-map to its number
                        options = field.get('options', [])
                        numeric = None
                        for opt in options:
                            if opt['label'] == val or str(opt['value']) == str(val):
                                numeric = int(opt['value'])
                                break
                        if numeric is None:
                            try:
                                numeric = int(val)
                            except (ValueError, TypeError):
                                continue
                        exif[ifd][tag] = numeric
                    else:
                        converted = self._to_exif(val, etype)
                        if converted is not None:
                            exif[ifd][tag] = converted

                if etype == 'gps_lat' and val:
                    try:
                        dec = float(val)
                        exif['GPS'][1] = b'N' if dec >= 0 else b'S'
                        exif['GPS'][2] = self._decimal_to_gps(dec)
                    except Exception:
                        pass
                elif etype == 'gps_lon' and val:
                    try:
                        dec = float(val)
                        exif['GPS'][3] = b'E' if dec >= 0 else b'W'
                        exif['GPS'][4] = self._decimal_to_gps(dec)
                    except Exception:
                        pass
                elif etype == 'gps_alt' and val:
                    try:
                        alt = float(val)
                        exif['GPS'][6] = (int(alt * 100), 100)
                    except Exception:
                        pass
                elif etype == 'gps_date' and val:
                    exif['GPS'][29] = val.encode()

        exif_bytes = piexif.dump(exif)
        piexif.insert(exif_bytes, self.path)

    def _to_exif(self, val, etype):
        try:
            if etype == 'datetime':
                s = val.strip() if isinstance(val, str) else str(val)
                # Accept YYYY-MM-DD (common) → normalise to EXIF YYYY:MM:DD
                if len(s) >= 10 and s[4] == '-':
                    s = s[:4] + ':' + s[5:7] + ':' + s[8:]
                return s.encode('utf-8')
            if etype == 'text':
                return val.encode('utf-8') if isinstance(val, str) else val
            if etype == 'int':
                return int(str(val).strip())
            if etype in ('rational', 'srational'):
                return self._str_to_rational(val)
            # 'select' is handled inline in _write_exif — should not reach here
        except Exception:
            pass
        return None

    def _write_png(self, sections):
        from PIL import PngImagePlugin
        img = Image.open(self.path)
        meta = {k: v for k, v in img.info.items() if isinstance(v, str)}

        for section in sections:
            for field in section.get('fields', []):
                if not field.get('editable'):
                    continue
                key = field.get('_png_key')
                if key:
                    val = field.get('value', '')
                    if val:
                        meta[key] = val
                    else:
                        meta.pop(key, None)

        pnginfo = PngImagePlugin.PngInfo()
        for k, v in meta.items():
            pnginfo.add_text(k, v)
        img.save(self.path, pnginfo=pnginfo)

    def strip(self):
        """Remove all EXIF / PNG text metadata from the image."""
        if self.ext in self._EXIF_EXTS:
            try:
                piexif.remove(self.path)
            except Exception:
                # piexif.remove only handles JPEG / TIFF. For other EXIF-capable
                # formats, fall through to a generic re-save with no exif.
                img = Image.open(self.path)
                img.save(self.path)
        elif self.ext == '.png':
            from PIL import PngImagePlugin
            img = Image.open(self.path)
            img.save(self.path, pnginfo=PngImagePlugin.PngInfo())
