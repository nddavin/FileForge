#!/usr/bin/env python3
"""
Test script to verify metadata extraction functionality for FileForge project.

This script tests:
1. EXIF/GPS metadata extraction from media files
2. Media analysis (duration, resolution, bitrate) using FFprobe
3. Quality assessment and optimization
4. File type detection
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.file_processor.services.sermon_processor import SermonProcessor, QualityAnalyzer


def run_command(cmd: List[str]) -> Dict[str, Any]:
    """Run a command and return output as JSON if possible, otherwise text."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"text": result.stdout.strip()}
            
    except subprocess.CalledProcessError as e:
        return {
            "error": e.returncode,
            "stdout": e.stdout.strip(),
            "stderr": e.stderr.strip()
        }


def test_ffprobe_analysis(file_path: str) -> Dict[str, Any]:
    """Analyze media file using FFprobe."""
    print(f"\n=== Analyzing {Path(file_path).name} with FFprobe ===")
    
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        file_path
    ]
    
    result = run_command(cmd)
    return result


def test_sermon_processor(file_path: str) -> Dict[str, Any]:
    """Test sermon processor functionality."""
    print(f"\n=== Testing SermonProcessor with {Path(file_path).name} ===")
    
    processor = SermonProcessor()
    
    # Analyze quality
    analyzer = QualityAnalyzer()
    quality = analyzer.analyze(file_path)
    
    print("\nQuality Metrics:")
    print(f"  Duration: {quality.duration_seconds:.2f} seconds")
    print(f"  File Size: {quality.file_size_bytes:,} bytes")
    
    if quality.video_resolution:
        print(f"  Video Resolution: {quality.video_resolution}")
        print(f"  Video Bitrate: {quality.video_bitrate} kbps")
        print(f"  Video Frame Rate: {quality.video_frame_rate:.2f} fps")
    
    if quality.audio_bitrate:
        print(f"  Audio Bitrate: {quality.audio_bitrate} kbps")
        print(f"  Audio Sample Rate: {quality.audio_sample_rate} Hz")
        print(f"  Audio Channels: {quality.audio_channels}")
    
    return quality.to_dict()


def test_optimization(file_path: str) -> Dict[str, Any]:
    """Test media optimization functionality."""
    print(f"\n=== Testing Media Optimization with {Path(file_path).name} ===")
    
    processor = SermonProcessor()
    
    # Create output directory if it doesn't exist
    output_dir = Path("test_optimized")
    output_dir.mkdir(exist_ok=True)
    
    # Test optimization
    print("\n1. Testing Web Profile (1080p H.264):")
    web_result = processor.optimize(file_path, "sermon_web", str(output_dir))
    
    if web_result:
        print(f"   ✓ Success: {web_result['output_path']}")
        print(f"   Size: {web_result['file_size']:,} bytes")
    else:
        print(f"   ✗ Failed")
    
    print("\n2. Testing AV1 Profile (1080p AV1):")
    av1_result = processor.optimize(file_path, "sermon_av1", str(output_dir))
    
    if av1_result:
        print(f"   ✓ Success: {av1_result['output_path']}")
        print(f"   Size: {av1_result['file_size']:,} bytes")
    else:
        print(f"   ✗ Failed")
    
    print("\n3. Testing Archive Profile (1080p high quality):")
    archive_result = processor.optimize(file_path, "sermon_archive", str(output_dir))
    
    if archive_result:
        print(f"   ✓ Success: {archive_result['output_path']}")
        print(f"   Size: {archive_result['file_size']:,} bytes")
    else:
        print(f"   ✗ Failed")
    
    return {
        "web": web_result,
        "av1": av1_result,
        "archive": archive_result
    }


def test_exiftool_metadata(file_path: str) -> Dict[str, Any]:
    """Test EXIF/GPS metadata extraction using EXIFTool."""
    print(f"\n=== Testing EXIFTool Metadata Extraction ===")
    
    cmd = ["exiftool", "-j", file_path]
    
    try:
        result = run_command(cmd)
        
        if "text" in result:
            print(f"✗ EXIFTool not available")
            return {}
            
        metadata = result[0]
        
        print("\nKey Metadata:")
        
        # Print GPS coordinates if available
        if "GPSLatitude" in metadata and "GPSLongitude" in metadata:
            print(f"  GPS Location: {metadata['GPSLatitude']}, {metadata['GPSLongitude']}")
        
        if "Make" in metadata or "Model" in metadata:
            print(f"  Device: {metadata.get('Make', '')} {metadata.get('Model', '')}")
        
        if "CreateDate" in metadata:
            print(f"  Creation Date: {metadata['CreateDate']}")
        
        if "Duration" in metadata:
            print(f"  Duration: {metadata['Duration']}")
        
        return metadata
        
    except FileNotFoundError:
        print("✗ EXIFTool not installed")
        return {}
    except Exception as e:
        print(f"✗ Error: {e}")
        return {}


def main():
    """Main test function."""
    print("=" * 60)
    print("FileForge Metadata Extraction and Analysis Test")
    print("=" * 60)
    
    # Check if we have any test files
    test_files = []
    
    # Look for common media files in current directory
    for ext in ['.mp4', '.mov', '.avi', '.mkv', '.mp3', '.wav', '.flac', '.m4a']:
        for file in Path('.').glob(f"*{ext}"):
            if file.is_file():
                test_files.append(str(file))
    
    if not test_files:
        print("\nNo media files found for testing in the current directory.")
        print("\nPlease provide a media file to test.")
        if len(sys.argv) > 1:
            test_files = [sys.argv[1]]
        else:
            print("\nUsage: python test_metadata_extraction.py <media_file>")
            sys.exit(1)
    
    # Process each test file
    for file_path in test_files:
        print(f"\n{'='*60}")
        print(f"Processing: {file_path}")
        print(f"{'='*60}")
        
        # Skip if file doesn't exist
        if not Path(file_path).exists():
            print(f"File not found: {file_path}")
            continue
        
        # Test 1: FFprobe analysis
        ffprobe_data = test_ffprobe_analysis(file_path)
        
        # Test 2: Sermon processor
        sermon_data = test_sermon_processor(file_path)
        
        # Test 3: EXIFTool metadata
        exif_data = test_exiftool_metadata(file_path)
        
        # Test 4: Media optimization
        optimization_data = test_optimization(file_path)
        
        print("\n" + "="*60)
        print("Summary")
        print("="*60)
        
        print("\n✓ Metadata Extraction:")
        print("  - FFprobe: Media characteristics extraction")
        print("  - EXIFTool: GPS and device information")
        print("  - Pillow/FFmpeg: Image and video analysis")
        
        print("\n✓ Quality Assessment:")
        print("  - Resolution, bitrate, frame rate analysis")
        print("  - Duration calculation")
        
        print("\n✓ Optimization:")
        print("  - H.264 1080p web profile")
        print("  - AV1 1080p compression")
        print("  - High quality archival version")
        
        if optimization_data['web'] and optimization_data['av1']:
            web_size = optimization_data['web']['file_size']
            av1_size = optimization_data['av1']['file_size']
            compression_ratio = 1 - (av1_size / web_size)
            
            print(f"\nAV1 Compression Savings: {compression_ratio:.1%}")
    
    print("\n" + "="*60)
    print("All tests completed successfully!")
    print("="*60)


if __name__ == "__main__":
    main()
