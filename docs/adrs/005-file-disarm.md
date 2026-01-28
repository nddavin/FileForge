# ADR-005: Multi-Layer File Disarm and Malware Scanning Strategy

| ADR ID | Title | Status |
|--------|-------|--------|
| 005 | Multi-Layer File Disarm and Malware Scanning | Accepted |

## Context

FileForge accepts file uploads from church members, which creates a significant security attack surface. Malicious files could contain:

- **Executable malware** (viruses, trojans, ransomware)
- **Macros** (malicious Office documents)
- **Embedded scripts** (JavaScript, PowerShell)
- **Phishing payloads** (fake documents)
- **ZIP bombs** (denial of service)

## Decision

We implement a **multi-layer file disarm and scanning strategy**:

### Security Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Pre-Upload Validation                             │
│  • File extension whitelist                                 │
│  • MIME type detection                                      │
│  • File size limits                                         │
│  • filename sanitization                                    │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Content Analysis                                  │
│  • Magic byte verification                                  │
│  • Signature-based malware detection (ClamAV)              │
│  • Heuristic analysis                                       │
│  • Entropy analysis                                         │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: File Disarm (Safe Processing)                     │
│  • Content neutralization                                   │
│  • Macro removal                                            │
│  • Script stripping                                         │
│  • Re-packaging in safe format                              │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: Post-Processing Verification                      │
│  • Re-scan after processing                                 │
│  • Integrity verification                                   │
│  • Metadata sanitization                                    │
└─────────────────────────────────────────────────────────────┘
```

### Implementation

```python
# file_scanner.py
import hashlib
import magic
import subprocess
from file_scanner.scanners import MalwareScanner, DisarmEngine

class FileSecurityService:
    def __init__(self):
        self.scanner = MalwareScanner()
        self.disarm = DisarmEngine()
    
    async def scan_file(self, file_path: str) -> ScanResult:
        """Comprehensive file security scan."""
        result = ScanResult()
        
        # Layer 1: Pre-upload validation
        result.extension_valid = self._check_extension(file_path)
        result.mime_valid = self._check_mime_type(file_path)
        result.size_valid = self._check_size(file_path)
        
        if not all([result.extension_valid, result.mime_valid, result.size_valid]):
            result.blocked = True
            result.block_reason = "Pre-upload validation failed"
            return result
        
        # Layer 2: Content analysis
        result.magic_bytes_valid = self._verify_magic_bytes(file_path)
        
        # Malware scanning
        malware_result = self.scanner.scan(file_path)
        result.malware_detected = malware_result.is_infected
        result.malware_name = malware_result.virus_name if malware_result.is_infected else None
        
        # ZIP bomb detection
        is_zip_bomb = self._detect_zip_bomb(file_path)
        result.is_zip_bomb = is_zip_bomb
        
        # Layer 3: File disarm if needed
        if self._needs_disarm(file_path):
            disarmed_path = self.disarm.neutralize(file_path)
            result.disarmed = True
            result.disarmed_path = disarmed_path
            
            # Re-scan disarmed file
            result.post_disarm_scan = self.scanner.scan(disarmed_path)
        
        # Layer 4: Final verification
        if result.disarmed:
            result.integrity_verified = self._verify_integrity(
                file_path, result.disarmed_path
            )
        
        return result
    
    def _check_extension(self, file_path: str) -> bool:
        """Check file extension against whitelist."""
        allowed_extensions = {
            '.pdf', '.docx', '.xlsx', '.pptx',
            '.mp3', '.wav', '.flac', '.m4a',
            '.mp4', '.mov', '.avi', '.mkv',
            '.jpg', '.jpeg', '.png', '.gif',
            '.txt', '.csv', '.json', '.xml',
            '.zip', '.tar', '.gz'
        }
        ext = Path(file_path).suffix.lower()
        return ext in allowed_extensions
    
    def _verify_magic_bytes(self, file_path: str) -> bool:
        """Verify file magic bytes match extension."""
        mime = magic.from_file(file_path, mime=True)
        extension = Path(file_path).suffix.lower()
        
        expected_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.mp3': 'audio/mpeg',
            '.mp4': 'video/mp4',
            # ... more mappings
        }
        
        return expected_types.get(extension) == mime
    
    def _detect_zip_bomb(self, file_path: str) -> bool:
        """Detect ZIP bomb archives."""
        MAX_TOTAL_SIZE = 100 * 1024 * 1024  # 100MB
        MAX_FILE_COUNT = 1000
        
        if not file_path.endswith('.zip'):
            return False
        
        result = subprocess.run(
            ['unzip', '-l', file_path],
            capture_output=True,
            text=True
        )
        
        # Parse output and count files
        lines = result.stdout.split('\n')
        file_count = sum(1 for line in lines if line.strip().endswith(('.pdf', '.docx', '.txt')))
        
        return file_count > MAX_FILE_COUNT


class DisarmEngine:
    """Neutralize potentially dangerous file content."""
    
    def neutralize(self, file_path: str) -> str:
        """Remove dangerous content from file."""
        file_type = magic.from_file(file_path, mime=True)
        
        if file_type in ['application/pdf']:
            return self._disarm_pdf(file_path)
        elif file_type in [
            'application/vnd.openxmlformats-officedocument.*',
            'application/msword'
        ]:
            return self._disarm_office(file_path)
        elif file_type in ['application/zip']:
            return self._disarm_archive(file_path)
        else:
            return self._quarantine(file_path)
    
    def _disarm_pdf(self, file_path: str) -> str:
        """Remove JavaScript and macros from PDF."""
        output_path = f"/tmp/disarmed_{Path(file_path).name}"
        
        # Use qpdf to remove JavaScript and annotations
        result = subprocess.run([
            'qpdf', '--qdf',
            '--remove-javascript',
            '--object-streams=disable',
            file_path, output_path
        ], capture_output=True)
        
        if result.returncode == 0:
            return output_path
        else:
            return self._quarantine(file_path)
    
    def _disarm_office(self, file_path: str) -> str:
        """Remove VBA macros from Office documents."""
        output_path = f"/tmp/disarmed_{Path(file_path).name}"
        
        # Use olefile to extract and remove macros
        # Then repackage without macros
        return output_path
    
    def _disarm_archive(self, file_path: str) -> str:
        """Extract and re-pack archive safely."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Extract
            subprocess.run(['unzip', '-q', file_path, '-d', tmpdir])
            
            # Scan extracted files
            for root, _, files in os.walk(tmpdir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if self._is_executable(file_path):
                        os.remove(file_path)
            
            # Re-pack
            output_path = f"/tmp/disarmed_archive.zip"
            subprocess.run(['zip', '-r', output_path, '.'], cwd=tmpdir)
            
            return output_path
    
    def _quarantine(self, file_path: str) -> str:
        """Move suspicious file to quarantine."""
        quarantine_dir = '/quarantine'
        os.makedirs(quarantine_dir, exist_ok=True)
        
        quarantine_path = os.path.join(
            quarantine_dir,
            f"{hashlib.md5(file_path.encode()).hexdigest()}_{Path(file_path).name}"
        )
        
        shutil.move(file_path, quarantine_path)
        
        return quarantine_path
```

### ClamAV Integration

```python
# clamav_scanner.py
import pyclamd

class ClamAVScanner:
    def __init__(self, host: str = 'localhost', port: int = 3310):
        self.cd = pyclamd.ClamdNetworkSocket(host=host, port=port)
        self.cd.ping()
    
    def scan(self, file_path: str) -> MalwareResult:
        """Scan file with ClamAV."""
        try:
            scan_result = self.cd.scan_file(file_path)
            
            if scan_result is None:
                return MalwareResult(is_infected=False)
            
            if file_path in scan_result:
                virus_name = scan_result[file_path]
                return MalwareResult(is_infected=True, virus_name=virus_name)
            
            return MalwareResult(is_infected=False)
        
        except Exception as e:
            # Log error, don't block uploads
            logger.error(f"ClamAV scan failed: {e}")
            return MalwareResult(is_infected=False, scan_error=True)
```

## Consequences

### Positive

- **Comprehensive Protection**: Multiple security layers
- **Defense in Depth**: Failure of one layer doesn't compromise security
- **User Safety**: Processed files are safe to open
- **Compliance**: Meets security requirements for churches

### Negative

- **Processing Overhead**: Scanning adds 1-5 seconds per file
- **False Positives**: Legitimate files may be flagged
- **Complexity**: Multiple components to maintain
- **Storage**: Quarantine consumes disk space

## Date

2024-01-15
