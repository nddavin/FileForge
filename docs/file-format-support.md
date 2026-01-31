# File Format Support Matrix

This document provides comprehensive documentation of supported file formats, metadata extraction methods, processing capabilities, and limitations for the FileForge file processing system.

## 📊 Overview

The FileForge system supports **50+ file types** across multiple categories, each with specialized processing capabilities:

| Category | Format Count | Priority | Processing Mode |
|----------|-------------|----------|-----------------|
| Documents | 15 | High | Synchronous/Async |
| Images | 15 | Medium | Async (batch) |
| Videos | 12 | High | Async (long-running) |
| Audio | 12 | Medium | Async (batch) |
| Archives | 12 | Low | Synchronous |
| Business Files | 8 | High | Synchronous/Async |
| CAD/Engineering | 5 | High | Async |
| Medical/Compliance | 5 | Critical | Async (with PHI) |
| Geospatial | 7 | High | Async |
| E-books | 6 | Medium | Synchronous |
| Email Files | 4 | Medium | Async (batch) |
| Disk Images | 6 | Low | Async |
| Code/Scripts | 35 | Medium | Synchronous |
| Log Files | 10 | Low | Async (batch) |

---

## 📄 Documents

### Supported Formats

| Extension | MIME Type | Size Limit | Priority | Processing |
|-----------|-----------|------------|----------|------------|
| `.pdf` | `application/pdf` | 100MB | High | Text extraction, metadata, OCR |
| `.doc` | `application/msword` | 50MB | High | Metadata extraction |
| `.docx` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | 50MB | High | Full text, metadata, styling |
| `.xls` | `application/vnd.ms-excel` | 50MB | High | Sheet analysis, formulas |
| `.xlsx` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | 50MB | High | Full content extraction |
| `.ppt` | `application/vnd.ms-powerpoint` | 50MB | Medium | Slide extraction |
| `.pptx` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` | 50MB | Medium | Full content extraction |
| `.txt` | `text/plain` | 10MB | Medium | Encoding detection, indexing |
| `.rtf` | `application/rtf` | 50MB | Medium | Rich text extraction |
| `.odt` | `application/vnd.oasis.opendocument.text` | 50MB | Medium | Full content extraction |
| `.ods` | `application/vnd.oasis.opendocument.spreadsheet` | 50MB | Medium | Sheet analysis |
| `.odp` | `application/vnd.oasis.opendocument.presentation` | 50MB | Medium | Slide extraction |
| `.csv` | `text/csv` | 100MB | High | Data analysis, validation |
| `.tsv` | `text/tab-separated-values` | 100MB | High | Data analysis, validation |
| `.xml` | `application/xml` | 50MB | Medium | Schema validation, parsing |

### Metadata Extraction

| Field | Extraction Method | Notes |
|-------|------------------|-------|
| Author | python-docx, PyPDF2 | Document properties |
| Title | python-docx, PyPDF2 | Document properties |
| Creation Date | python-docx, PyPDF2 | File system or metadata |
| Modification Date | python-docx, PyPDF2 | File system or metadata |
| Page Count | PyPDF2 | PDF only |
| Word Count | python-docx | Word docs only |
| Language Detection | langdetect | Text content analysis |
| Keywords | python-docx | Document properties |

### Limitations

- Encrypted PDFs require password
- Scanned PDFs need OCR (Tesseract)
- Complex formulas in spreadsheets may not render correctly
- Password-protected documents cannot be processed

---

## 🖼️ Images

### Supported Formats

| Extension | MIME Type | Size Limit | Priority | Processing |
|-----------|-----------|------------|----------|------------|
| `.jpg` / `.jpeg` | `image/jpeg` | 100MB | High | EXIF, dimensions, colors |
| `.png` | `image/png` | 100MB | High | Transparency, dimensions |
| `.gif` | `image/gif` | 50MB | Medium | Frame extraction, animation |
| `.bmp` | `image/bmp` | 100MB | Low | Basic processing |
| `.tiff` / `.tif` | `image/tiff` | 200MB | High | Multi-page support |
| `.webp` | `image/webp` | 100MB | Medium | Lossless/lossy analysis |
| `.svg` | `image/svg+xml` | 10MB | Medium | Vector analysis |
| `.ico` | `image/x-icon` | 5MB | Low | Icon metadata |
| `.raw` | `image/x-raw` | 500MB | Medium | Camera RAW formats |
| `.cr2` | `image/x-canon-raw` | 500MB | Medium | Canon RAW |
| `.nef` | `image/x-nikon-raw` | 500MB | Medium | Nikon RAW |
| `.arw` | `image/x-sony-raw` | 500MB | Medium | Sony RAW |
| `.heic` | `image/heic` | 100MB | Medium | Apple format support |
| `.heif` | `image/heif` | 100MB | Medium | HEIF container |

### Metadata Extraction

| Field | Extraction Method | Notes |
|-------|------------------|-------|
| Dimensions (Width × Height) | Pillow, OpenCV | Pixels |
| Resolution (DPI) | Pillow | Dots per inch |
| Color Depth | Pillow | Bits per channel |
| EXIF Data | piexif, Pillow | Camera info, GPS |
| GPS Coordinates | piexif | Decimal degrees |
| Camera Model | piexif | Make, model |
| ISO | piexif | Camera settings |
| Aperture | piexif | f-number |
| Shutter Speed | piexif | Seconds notation |
| Focal Length | piexif | mm |
| Date Taken | piexif | Datetime original |
| Color Profile | Pillow | ICC profiles |

### Processing Capabilities

| Capability | Tools | Notes |
|------------|-------|-------|
| OCR | Tesseract | Text extraction from images |
| Thumbnail Generation | Pillow | Configurable sizes |
| Format Conversion | Pillow, ImageMagick | JPEG, PNG, WebP |
| Resize/Crop | Pillow | Aspect ratio preservation |
| Color Analysis | OpenCV | Dominant colors |
| Face Detection | OpenCV, dlib | Optional dependency |

### Limitations

- RAW files require additional libraries
- Very large images (>1GB) may timeout
- HEIC support depends on system libraries
- Encrypted images not supported

---

## 🎥 Videos

### Supported Formats

| Extension | MIME Type | Size Limit | Priority | Processing |
|-----------|-----------|------------|----------|------------|
| `.mp4` | `video/mp4` | 2GB | High | Full analysis |
| `.avi` | `video/avi` | 2GB | High | Codec detection |
| `.mov` | `video/quicktime` | 2GB | High | Apple formats |
| `.mkv` | `video/x-matroska` | 2GB | Medium | Multiple tracks |
| `.wmv` | `video/x-ms-wmv` | 1GB | Medium | Windows formats |
| `.flv` | `video/x-flv` | 1GB | Low | Flash video |
| `.webm` | `video/webm` | 1GB | Medium | Web formats |
| `.m4v` | `video/x-m4v` | 2GB | Medium | Apple video |
| `.3gp` | `video/3gpp` | 500MB | Low | Mobile formats |
| `.mpg` / `.mpeg` | `video/mpeg` | 1GB | Medium | Standard formats |
| `.ts` | `video/mp2t` | 2GB | Medium | Transport stream |
| `.mts` | `video/mp2t` | 2GB | Medium | AVCHD format |

### Metadata Extraction

| Field | Extraction Method | Notes |
|-------|------------------|-------|
| Duration | FFprobe | Seconds |
| Dimensions | FFprobe | Width × Height |
| Frame Rate | FFprobe | fps |
| Bitrate | FFprobe | kbps |
| Codec | FFprobe | Video/audio codecs |
| Audio Channels | FFprobe | Count |
| Audio Sample Rate | FFprobe | Hz |
| Aspect Ratio | FFprobe | Calculated |
| Container Format | FFprobe | File format |

### Processing Capabilities

| Capability | Tools | Notes |
|------------|-------|-------|
| Transcoding | FFmpeg | Format conversion |
| Thumbnail Extraction | FFmpeg | Configurable time |
| Audio Extraction | FFmpeg | MP3, WAV output |
| Resolution Change | FFmpeg | Scale filtering |
| Container Conversion | FFmpeg | Remuxing |
| Video Analysis | OpenCV | Scene detection |

### Limitations

- Processing requires FFmpeg installed
- Very long videos (>1hr) use extended timeout
- DRM-protected content cannot be processed
- Hardware acceleration depends on system

---

## 🎵 Audio

### Supported Formats

| Extension | MIME Type | Size Limit | Priority | Processing |
|-----------|-----------|------------|----------|------------|
| `.mp3` | `audio/mpeg` | 100MB | High | ID3 tags, analysis |
| `.wav` | `audio/wav` | 200MB | High | PCM analysis |
| `.flac` | `audio/flac` | 200MB | High | Full metadata |
| `.aac` | `audio/aac` | 100MB | Medium | M4A support |
| `.ogg` | `audio/ogg` | 100MB | Medium | Vorbis/Opus |
| `.wma` | `audio/x-ms-wma` | 100MB | Low | Windows formats |
| `.m4a` | `audio/mp4` | 100MB | Medium | Apple audio |
| `.aiff` | `audio/aiff` | 200MB | Medium | AIFF support |
| `.au` | `audio/basic` | 50MB | Low | Sun audio |
| `.ra` | `audio/x-pn-realaudio` | 50MB | Low | RealAudio |
| `.ape` | `audio/x-ape` | 200MB | Low | Monkey's Audio |
| `.opus` | `audio/opus` | 100MB | Medium | Opus format |

### Metadata Extraction

| Field | Extraction Method | Notes |
|-------|------------------|-------|
| Duration | mutagen, FFprobe | Seconds |
| Bitrate | mutagen | kbps |
| Sample Rate | mutagen | Hz |
| Channels | mutagen | Count |
| Artist | mutagen (ID3) | ID3v1/v2 tags |
| Album | mutagen (ID3) | ID3v1/v2 tags |
| Title | mutagen (ID3) | ID3v1/v2 tags |
| Genre | mutagen (ID3) | ID3v1/v2 tags |
| Year | mutagen (ID3) | ID3v1/v2 tags |
| Track Number | mutagen (ID3) | ID3v1/v2 tags |
| Album Art | mutagen | Cover images |

### Processing Capabilities

| Capability | Tools | Notes |
|------------|-------|-------|
| Format Conversion | FFmpeg | Cross-platform |
| Audio Normalization | FFmpeg | LUFS standard |
| Silence Removal | FFmpeg | Audio processing |
| Waveform Generation | librosa | Visualization |
| Speech Recognition | Whisper | Optional |

### Limitations

- DRM-protected audio not supported
- Lossless formats require more memory
- Very long audio (>2hr) may timeout

---

## 📦 Archives

### Supported Formats

| Extension | MIME Type | Size Limit | Priority | Processing |
|-----------|-----------|------------|----------|------------|
| `.zip` | `application/zip` | 2GB | High | Contents listing |
| `.rar` | `application/x-rar-compressed` | 2GB | Medium | UnRAR required |
| `.7z` | `application/x-7z-compressed` | 2GB | Medium | 7-Zip required |
| `.tar` | `application/x-tar` | 2GB | Medium | Contents listing |
| `.gz` | `application/gzip` | 1GB | Medium | Single file |
| `.bz2` | `application/x-bzip2` | 1GB | Medium | Single file |
| `.xz` | `application/x-xz` | 1GB | Medium | Single file |
| `.tgz` | `application/gzip` | 1GB | Medium | tar+gzip |
| `.tbz2` | `application/x-bzip2` | 1GB | Medium | tar+bzip2 |
| `.txz` | `application/x-xz` | 1GB | Medium | tar+xz |
| `.cab` | `application/vnd.ms-cab-compressed` | 500MB | Low | Windows CAB |
| `.iso` | `application/x-iso9660-image` | 5GB | Medium | Disk image |

### Metadata Extraction

| Field | Extraction Method | Notes |
|-------|------------------|-------|
| Contents Count | Archive library | Files + folders |
| Compression Ratio | Calculated | Original/compressed |
| Archive Type | Detection | Format identifier |
| Total Size | Archive library | Uncompressed |
| Nested Archives | Recursive scan | Supported |

### Security Limits

| Limit | Value | Description |
|-------|-------|-------------|
| Max Files | 10,000 | Per archive |
| Max Folder Depth | 50 | Nesting level |
| Max Single File | 2GB | Within archive |
| Max Total Size | 10GB | Uncompressed total |

### Limitations

- Encrypted archives require password
- Some proprietary formats may fail
- Nested archives have extended processing time

---

## 💼 Business Files

### Supported Formats

| Extension | MIME Type | Size Limit | Priority | Processing |
|-----------|-----------|------------|----------|------------|
| `.xlsx` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | 50MB | High | Full analysis |
| `.xls` | `application/vnd.ms-excel` | 50MB | High | Sheet analysis |
| `.csv` | `text/csv` | 100MB | High | Data validation |
| `.pdf` | `application/pdf` | 100MB | High | Invoice processing |
| `.xml` | `application/xml` | 50MB | Medium | Schema validation |
| `.json` | `application/json` | 50MB | Medium | Structure analysis |
| `.txt` | `text/plain` | 10MB | Medium | Text analysis |
| `.rtf` | `application/rtf` | 50MB | Medium | Rich text |

### Business-Specific Metadata

| Field | Extraction Method | Notes |
|-------|------------------|-------|
| Document Type | Content analysis | Invoice, PO, Report |
| Date Range | Regex + analysis | Multiple formats |
| Amount | Regex patterns | Currency detection |
| Reference Number | Regex patterns | Invoice #, PO # |
| Department | Keyword analysis | Configurable |
| Project | Keyword analysis | Configurable |
| Status | Content analysis | Draft, Final, Approved |
| Priority | Keyword analysis | Configurable |

### Business Processing Capabilities

| Capability | Description | Supported Types |
|------------|-------------|-----------------|
| Invoice Processing | Extract line items, totals | PDF, XLSX, CSV |
| Purchase Order | Parse PO fields | PDF, XLSX |
| Financial Reports | Summarize data | XLSX, CSV |
| Contract Analysis | Extract key terms | PDF, DOCX |
| Receipt Processing | OCR + extraction | Images, PDF |

### Limitations

- Complex layouts may require manual review
- Handwritten text needs OCR
- Non-standard formats may fail

---

## 🏗️ CAD/Engineering Files

### Supported Formats

| Extension | MIME Type | Size Limit | Priority | Processing |
|-----------|-----------|------------|----------|------------|
| `.dwg` | `application/acad` | 500MB | High | Entity extraction |
| `.dxf` | `application/dxf` | 500MB | High | Full parsing |
| `.step` | `application/step` | 200MB | High | 3D geometry |
| `.stp` | `application/step` | 200MB | High | STEP format |
| `.iges` | `application/iges` | 200MB | High | IGES format |

### Metadata Extraction

| Field | Extraction Method | Notes |
|-------|------------------|-------|
| Entities Count | CAD library | Lines, circles, etc. |
| Layers Count | CAD library | Layer information |
| DXF Version | File header | Version detection |
| Schema | STEP parser | AP schema |
| Bounding Box | Calculated | Min/max coordinates |
| Units | Metadata | Unit detection |

### CAD Processing Capabilities

| Capability | Tools | Notes |
|------------|-------|-------|
| BOM Extraction | ezdxf | Bill of Materials |
| Dimension Extraction | ezdxf | Measurement data |
| Layer Analysis | ezdxf | Layer mapping |
| 3D Volume | OCC | Optional dependency |

### Limitations

- Complex 3D models may timeout
- Proprietary formats not supported
- Encrypted CAD files require password

---

## 🏥 Medical/Compliance Files

### Supported Formats

| Extension | MIME Type | Size Limit | Priority | Processing |
|-----------|-----------|------------|----------|------------|
| `.dcm` / `.dicom` | `application/dicom` | 500MB | Critical | Full DICOM support |
| `.hl7` | `application/hl7-v2` | 10MB | Critical | HL7 v2 parsing |
| `.xhl7` | `application/hl7-v2+xml` | 10MB | Critical | HL7 XML format |
| `.pdfa` | `application/pdfa` | 100MB | High | Archival PDF |
| `.pdf` | `application/pdf` | 100MB | High | Standard PDF |

### Medical-Specific Metadata

| Field | Extraction Method | Notes |
|-------|------------------|-------|
| Patient ID | DICOM tag | (0010,0020) |
| Study Date | DICOM tag | (0008,0020) |
| Modality | DICOM tag | (0008,0060) |
| Study Description | DICOM tag | (0008,1030) |
| PHI Detected | Pattern matching | Auto-flagging |
| HIPAA Compliant | Validation | Configurable rules |

### Medical Processing Capabilities

| Capability | Tools | Compliance |
|------------|-------|------------|
| DICOM Analysis | pydicom | HIPAA |
| HL7 Parsing | hl7 | HIPAA |
| PHI Detection | regex + NLP | HIPAA |
| PHI Redaction | OCR + masking | HIPAA |
| Audit Trail | Built-in | HIPAA |
| Access Controls | RBAC | HIPAA |

### Security for Medical Files

| Measure | Implementation |
|---------|----------------|
| PHI Detection | Automatic flagging |
| PHI Redaction | Optional masking |
| Access Logging | Full audit trail |
| Encryption | AES-256 at rest |
| Retention | Configurable (7+ years) |
| Data Residency | EU/US options |

### Limitations

- Encrypted DICOM requires password
- Complex HL7 messages may need custom parsing
- Very large DICOM series extended timeout

---

## 🌍 Geospatial Files

### Supported Formats

| Extension | MIME Type | Size Limit | Priority | Processing |
|-----------|-----------|------------|----------|------------|
| `.shp` | `application/shapefile` | 200MB | High | ESRI Shapefile |
| `.geojson` | `application/geo+json` | 100MB | High | GeoJSON format |
| `.kml` | `application/vnd.google-earth.kml+xml` | 50MB | Medium | Google Earth |
| `.kmz` | `application/vnd.google-earth.kmz` | 50MB | Medium | Compressed KML |
| `.gpx` | `application/gpx+xml` | 50MB | Medium | GPS data |
| `.gml` | `application/gml+xml` | 100MB | Medium | Geography markup |
| `.svg` | `image/svg+xml` | 10MB | Medium | Vector graphics |

### Geospatial Metadata

| Field | Extraction Method | Notes |
|-------|------------------|-------|
| Features Count | Geopandas/ogr | Number of features |
| Projection | ogr | CRS information |
| Bounds | ogr | Bounding box |
| Layers Count | ogr | Layer information |
| Geometry Type | ogr | Point/Line/Polygon |

### Geospatial Processing

| Capability | Tools | Notes |
|------------|-------|-------|
| Reprojection | pyproj | CRS transformation |
| Geometry Analysis | shapely | Spatial operations |
| Attribute Extraction | geopandas | Data columns |
| Export Formats | ogr | Multiple outputs |

### Limitations

- Large shapefiles may timeout
- Complex projections may fail
- Encrypted files not supported

---

## 📱 Email Files

### Supported Formats

| Extension | MIME Type | Size Limit | Priority | Processing |
|-----------|-----------|------------|----------|------------|
| `.eml` | `message/rfc822` | 50MB | Medium | Email export |
| `.msg` | `application/vnd.ms-outlook` | 50MB | Medium | Outlook format |
| `.pst` | `application/msoutlook-data` | 10GB | Medium | Outlook archive |
| `.mbox` | `application/mbox` | 10GB | Medium | Unix mailbox |

### Email Metadata

| Field | Extraction Method | Notes |
|-------|------------------|-------|
| Sender | Email parser | From address |
| Recipient | Email parser | To, CC fields |
| Date | Email parser | Sent date |
| Attachments Count | Email parser | Count + list |
| Message Count | Mail library | PST/MBOX only |

### Email Processing

| Capability | Tools | Notes |
|------------|-------|-------|
| Attachment Extraction | email library | Save to storage |
| Body Extraction | email library | HTML/Text |
| Contact Mining | NLP | Optional |

### Limitations

- Large PST files require extended timeout
- Encrypted emails need keys
- Proprietary formats limited

---

## 💻 Code & Scripts

### Supported Formats (35+ Languages)

| Category | Extensions | Processing |
|----------|------------|------------|
| Python | `.py`, `.pyw`, `.pyi` | Syntax analysis |
| JavaScript | `.js`, `.jsx`, `.mjs`, `.cjs` | Syntax analysis |
| TypeScript | `.ts`, `.tsx` | Syntax analysis |
| Java | `.java` | Syntax analysis |
| C/C++ | `.c`, `.cpp`, `.cc`, `.cxx`, `.h`, `.hpp` | Syntax analysis |
| C# | `.cs` | Syntax analysis |
| PHP | `.php` | Syntax analysis |
| Ruby | `.rb`, `.erb` | Syntax analysis |
| Go | `.go` | Syntax analysis |
| Rust | `.rs` | Syntax analysis |
| Swift | `.swift` | Syntax analysis |
| Kotlin | `.kt`, `.kts` | Syntax analysis |
| Scala | `.sc`, `.scala` | Syntax analysis |
| Shell | `.sh`, `.bash`, `.zsh`, `.ps1` | Syntax analysis |
| SQL | `.sql` | Syntax analysis |
| HTML | `.html`, `.htm` | Structure analysis |
| CSS | `.css`, `.scss`, `.sass` | Structure analysis |
| XML | `.xml`, `.xsl`, `.xslt` | Schema validation |
| JSON | `.json` | Schema validation |
| YAML | `.yaml`, `.yml` | Schema validation |
| Markdown | `.md`, `.markdown` | Text analysis |
| Config | `.ini`, `.cfg`, `.conf`, `.toml` | Structure analysis |

### Code Metadata

| Field | Extraction Method | Notes |
|-------|------------------|-------|
| Language | Extension + content | Auto-detection |
| Line Count | File reading | Total lines |
| Function Count | AST parsing | Language dependent |
| Class Count | AST parsing | Language dependent |
| Imports | AST parsing | Dependencies |
| Complexity | AST parsing | McCabe cyclomatic |

### Code Processing

| Capability | Tools | Notes |
|------------|-------|-------|
| Syntax Validation | Language parsers | Linting-ready |
| Language Detection | Extension + content | 99% accuracy |
| Dependency Analysis | AST parsing | Import extraction |
| Code Complexity | radon | Optional |

---

## 📋 Log Files

### Supported Formats

| Extension | MIME Type | Size Limit | Processing |
|-----------|-----------|------------|------------|
| `.log` | `text/plain` | 100MB | Pattern analysis |
| `.txt` | `text/plain` | 100MB | Text analysis |
| `.out` | `text/plain` | 100MB | Output parsing |
| `.err` | `text/plain` | 100MB | Error analysis |
| `.debug` | `text/plain` | 100MB | Debug parsing |
| `.trace` | `text/plain` | 100MB | Trace analysis |
| `.access` | `text/plain` | 100MB | Apache/Nginx logs |
| `.error` | `text/plain` | 100MB | Error logs |
| `.syslog` | `text/plain` | 100MB | System logs |
| `.journal` | `binary` | 100MB | Journalctl format |

### Log Metadata

| Field | Extraction Method | Notes |
|-------|------------------|-------|
| Timestamp Range | Regex parsing | First/last entry |
| Severity Levels | Pattern matching | Count by level |
| Error Count | Pattern matching | Total errors |
| Source | Pattern analysis | Application name |
| Entries Count | Line counting | Total entries |

### Log Processing

| Capability | Tools | Notes |
|------------|-------|-------|
| Pattern Matching | regex | Error detection |
| Severity Classification | regex + rules | Auto-classification |
| Time Series Analysis | pandas | Trend analysis |
| Anomaly Detection | Optional ML | Outlier detection |

---

## 🔧 Processing Capabilities Summary

### By Technology

| Capability | Tool/Technology | File Types |
|------------|-----------------|------------|
| OCR | Tesseract | Images, PDFs (scanned) |
| Text Extraction | PyPDF2, python-docx | Documents |
| Metadata Extraction | piexif, mutagen, pydicom | All types |
| Video Analysis | FFmpeg, OpenCV | Videos |
| Audio Analysis | FFmpeg, librosa | Audio |
| Code Analysis | AST parsing, radon | Code files |
| Geospatial | geopandas, ogr | Geo files |
| Medical | pydicom, hl7 | Medical files |
| Compression | zipfile, py7z-rar | Archives |

### Performance Characteristics

| Category | Typical Processing Time | Max Concurrent |
|----------|------------------------|----------------|
| Documents | < 5 seconds | 100 |
| Images | < 10 seconds | 50 |
| Videos | 10s - 5min | 10 |
| Audio | < 10 seconds | 50 |
| Archives | < 30 seconds | 20 |
| Business | < 5 seconds | 100 |
| CAD | 10s - 2min | 10 |
| Medical | 10s - 2min | 10 |
| Geospatial | < 30 seconds | 20 |
| Code | < 2 seconds | 200 |
| Logs | < 10 seconds | 50 |

---

## ⚠️ Limitations and Restrictions

### General Limitations

| Limitation | Description | Workaround |
|------------|-------------|------------|
| File Size | Default 100MB | Increase `max_file_size` |
| Processing Time | Default 5 min | Increase timeout |
| Concurrent Files | Rate limited | Queue processing |
| Encrypted Files | Need password | Manual decryption |
| DRM Content | Not supported | Remove DRM first |

### Format-Specific Limitations

| Format | Limitation | Impact |
|--------|------------|--------|
| PDF (scanned) | No text layer | Requires OCR |
| DOCX (protected) | Cannot open | Need password |
| DICOM (encrypted) | Cannot decode | Need key |
| RAW images | Library dependent | Convert first |
| HEIC | System library | Limited support |
| CAD (proprietary) | Limited parsing | Export to DXF |

### Deprecated Formats

The following formats are deprecated and may be removed:

| Extension | Status | Alternative |
|-----------|--------|-------------|
| `.doc` | Deprecated | `.docx` |
| `.xls` | Deprecated | `.xlsx` |
| `.ppt` | Deprecated | `.pptx` |
| `.wma` | Deprecated | `.mp3`/`.aac` |
| `.avi` | Legacy | `.mp4` |

---

## 📚 References

- [Developer Guide](developer-guide.md)
- [Security Guide](security-guide.md)
- [User Guide](user-guide.md)
- [API Documentation](/docs)
