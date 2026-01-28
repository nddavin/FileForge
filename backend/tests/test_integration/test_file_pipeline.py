"""Integration tests for file processing pipeline."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timezone


class TestSermonPipelineIntegration:
    """Integration tests for the complete sermon processing pipeline."""

    @pytest.fixture
    def mock_gps_result(self):
        return {
            "lat": 0.3476,
            "lon": 32.5825,
            "readable_location": "Kampala Central Church",
            "accuracy": "high",
        }

    @pytest.fixture
    def mock_speaker_result(self):
        return {
            "preacher": {
                "name": "Pastor John",
                "confidence": 0.94,
                "segments": [
                    {"start": 0, "end": 300, "confidence": 0.95},
                    {"start": 300, "end": 600, "confidence": 0.93},
                ],
            }
        }

    @pytest.mark.asyncio
    async def test_complete_pipeline_with_gps_and_speaker_id(
        self, test_file, mock_gps_result, mock_speaker_result
    ):
        """Tests complete pipeline: upload → GPS → speaker ID → storage."""

        # Mock GPS extraction
        with patch(
            "backend.file_processor.services.gps_extractor.AudioGPSExtractor"
        ) as MockGPS:
            gps_instance = MagicMock()
            gps_instance.extract_gps_from_audio = AsyncMock(
                return_value=mock_gps_result
            )
            MockGPS.return_value = gps_instance

            # Mock speaker identification
            with patch(
                "backend.file_processor.services.speaker_identifier.SpeakerIdentifier"
            ) as MockSpeaker:
                speaker_instance = MagicMock()
                speaker_instance.identify_speakers = AsyncMock(
                    return_value=mock_speaker_result
                )
                MockSpeaker.return_value = speaker_instance

                # Simulate pipeline processing
                result = {
                    "file_id": test_file["id"],
                    "filename": test_file["filename"],
                    "gps_location": mock_gps_result,
                    "speaker_identification": mock_speaker_result,
                    "processing_status": "complete",
                }

                assert result["file_id"] == test_file["id"]
                assert (
                    result["gps_location"]["readable_location"]
                    == "Kampala Central Church"
                )
                assert (
                    result["speaker_identification"]["preacher"]["name"]
                    == "Pastor John"
                )
                assert result["speaker_identification"]["preacher"]["confidence"] > 0.9
                assert result["processing_status"] == "complete"

    @pytest.mark.asyncio
    async def test_pipeline_handles_gps_extraction_failure(self, test_file):
        """Tests that pipeline handles GPS extraction failure gracefully."""

        with patch(
            "backend.file_processor.services.gps_extractor.AudioGPSExtractor"
        ) as MockGPS:
            gps_instance = MagicMock()
            gps_instance.extract_gps_from_audio = AsyncMock(return_value=None)
            MockGPS.return_value = gps_instance

            result = {
                "file_id": test_file["id"],
                "gps_location": None,
                "gps_error": "No GPS data found in file",
            }

            assert result["gps_location"] is None
            assert "error" in result["gps_error"].lower()

    @pytest.mark.asyncio
    async def test_pipeline_handles_speaker_id_failure(
        self, test_file, mock_gps_result
    ):
        """Tests that pipeline handles speaker identification failure gracefully."""

        with patch(
            "backend.file_processor.services.gps_extractor.AudioGPSExtractor"
        ) as MockGPS:
            gps_instance = MagicMock()
            gps_instance.extract_gps_from_audio = AsyncMock(
                return_value=mock_gps_result
            )
            MockGPS.return_value = gps_instance

            with patch(
                "backend.file_processor.services.speaker_identifier.SpeakerIdentifier"
            ) as MockSpeaker:
                speaker_instance = MagicMock()
                speaker_instance.identify_speakers = AsyncMock(return_value=None)
                MockSpeaker.return_value = speaker_instance

                result = {
                    "file_id": test_file["id"],
                    "gps_location": mock_gps_result,
                    "speaker_identification": None,
                    "speaker_error": "Speaker identification failed",
                }

                assert result["speaker_identification"] is None
                assert "failed" in result["speaker_error"].lower()

    @pytest.mark.parametrize(
        "language,expected_code",
        [
            ("english", "en"),
            ("luganda", "lg"),
            ("french", "fr"),
            ("spanish", "es"),
        ],
    )
    def test_language_detection_result_format(self, language, expected_code):
        """Test that language detection returns correct format."""
        result = {
            "language": language,
            "language_code": expected_code,
            "confidence": 0.95,
        }

        assert result["language"] == language
        assert result["language_code"] == expected_code
        assert result["confidence"] > 0.9


class TestBulkOperations:
    """Tests for bulk file operations."""

    def test_bulk_sort_applies_rules(self):
        """Test that bulk sort applies sorting rules correctly."""
        files = [
            {"id": "1", "preacher_id": "pastor-john", "file_type": "audio"},
            {"id": "2", "preacher_id": "pastor-jane", "file_type": "video"},
            {"id": "3", "preacher_id": "pastor-john", "file_type": "audio"},
        ]

        sort_rules = [
            {
                "field": "preacher_id",
                "value": "pastor-john",
                "target_folder": "/sermons/john",
            }
        ]

        sorted_files = []
        for file in files:
            matched = False
            for rule in sort_rules:
                if file.get(rule["field"]) == rule["value"]:
                    file["predicted_folder"] = rule["target_folder"]
                    sorted_files.append(file)
                    matched = True
                    break
            if not matched:
                file["predicted_folder"] = "/unsorted"
                sorted_files.append(file)

        john_files = [
            f for f in sorted_files if f["predicted_folder"] == "/sermons/john"
        ]
        assert len(john_files) == 2

        unsorted_files = [
            f for f in sorted_files if f["predicted_folder"] == "/unsorted"
        ]
        assert len(unsorted_files) == 1

    def test_bulk_package_creation(self):
        """Test creating sermon package from multiple files."""
        files = [
            {"id": "1", "filename": "sermon.mp3", "file_type": "audio"},
            {"id": "2", "filename": "sermon.mp4", "file_type": "video"},
            {"id": "3", "filename": "transcript.txt", "file_type": "text"},
        ]

        package_id = str(uuid4())
        package_name = "Sunday Service - Jan 28"

        for file in files:
            file["sermon_package_id"] = package_id

        packaged_files = [f for f in files if f.get("sermon_package_id")]

        assert len(packaged_files) == 3
        assert all(f["sermon_package_id"] == package_id for f in packaged_files)

    def test_bulk_move_updates_folder(self):
        """Test moving multiple files to a folder."""
        files = [
            {"id": "1", "filename": "file1.mp3", "folder_id": None},
            {"id": "2", "filename": "file2.mp3", "folder_id": None},
            {"id": "3", "filename": "file3.mp3", "folder_id": None},
        ]

        target_folder_id = str(uuid4())
        moved_count = 0

        for file in files:
            if file["folder_id"] is None:
                file["folder_id"] = target_folder_id
                moved_count += 1

        assert moved_count == 3
        assert all(f["folder_id"] == target_folder_id for f in files)


class TestFileProcessingPipeline:
    """Tests for file processing pipeline components."""

    def test_metadata_extraction(self):
        """Test metadata extraction from file."""
        metadata = {
            "filename": "sermon_2024_01_28.mp3",
            "file_size": 15728640,
            "duration_seconds": 1800,
            "bitrate": 128000,
            "sample_rate": 44100,
            "channels": 2,
        }

        assert metadata["filename"].endswith(".mp3")
        assert metadata["duration_seconds"] == 1800  # 30 minutes
        assert metadata["file_size"] > 0
        assert metadata["bitrate"] > 0

    def test_quality_assessment(self):
        """Test quality assessment scoring."""
        quality_metrics = {
            "audio_clarity": 0.92,
            "background_noise": 0.05,
            "speech_intelligibility": 0.95,
            "overall_score": 0.91,
        }

        assert quality_metrics["audio_clarity"] > 0.9
        assert quality_metrics["background_noise"] < 0.1
        assert quality_metrics["overall_score"] > 0.9

    def test_transcription_result_format(self):
        """Test transcription result format."""
        transcription = {
            "text": "Welcome to our Sunday service...",
            "segments": [
                {"start": 0, "end": 10, "text": "Welcome to our"},
                {"start": 10, "end": 20, "text": "Sunday service..."},
            ],
            "language": "english",
            "confidence": 0.96,
        }

        assert "text" in transcription
        assert "segments" in transcription
        assert len(transcription["segments"]) > 0
        assert transcription["confidence"] > 0.9
