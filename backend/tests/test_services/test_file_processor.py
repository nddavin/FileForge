import pytest
import tempfile
import os
from file_processor.services.file_processor import FileProcessor


def test_file_processor_initialization():
    processor = FileProcessor()
    assert processor.supported_formats == {
        "pdf",
        "docx",
        "txt",
        "jpg",
        "png",
        "mp4",
        "mp3",
        "zip",
    }


def test_process_nonexistent_file():
    processor = FileProcessor()
    with pytest.raises(FileNotFoundError):
        processor.process_file("/nonexistent/file.txt")


def test_process_text_file():
    processor = FileProcessor()

    # Create a temporary text file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("This is a test document with some content.")
        temp_file = f.name

    try:
        result = processor.process_file(temp_file)

        assert result["filename"].endswith(".txt")
        assert result["extension"] == "txt"
        assert result["is_supported"] is True
        assert result["type"] == "document"
        assert "text_content" in result
    finally:
        os.unlink(temp_file)


def test_process_image_file():
    processor = FileProcessor()

    # Create a temporary file with image extension
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        f.write(b"fake image data")
        temp_file = f.name

    try:
        result = processor.process_file(temp_file)

        assert result["extension"] == "jpg"
        assert result["is_supported"] is True
        assert result["type"] == "image"
        assert "width" in result
        assert "height" in result
    finally:
        os.unlink(temp_file)


def test_process_unsupported_file():
    processor = FileProcessor()

    # Create a temporary file with unsupported extension
    with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
        f.write(b"unsupported file")
        temp_file = f.name

    try:
        result = processor.process_file(temp_file)

        assert result["extension"] == "xyz"
        assert result["is_supported"] is False
    finally:
        os.unlink(temp_file)
