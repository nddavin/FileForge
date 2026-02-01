"""Sermon Processing Pipeline - Metadata Extraction, AI Analysis, and Optimization"""

import json
import logging
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from enum import Enum

import httpx
from pydantic import Field

logger = logging.getLogger(__name__)


class MediaType(Enum):
    """Types of media components"""

    VIDEO = "video"
    AUDIO = "audio"
    TRANSCRIPT = "transcript"
    ARTWORK = "artwork"


@dataclass
class SermonMetadata:
    """Sermon-specific metadata"""

    recording_location: Optional[str] = None
    has_video: bool = False
    has_audio: bool = False
    has_transcript: bool = False
    has_artwork: bool = False
    series_title: Optional[str] = None
    sermon_title: Optional[str] = None
    theme_scripture: Optional[str] = None
    assigned_team: Dict[str, str] = field(default_factory=dict)
    duration_seconds: int = 0
    quality_metrics: Dict[str, Any] = field(default_factory=dict)
    transcript_text: Optional[str] = None
    analysis_complete: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recording_location": self.recording_location,
            "has_video": self.has_video,
            "has_audio": self.has_audio,
            "has_transcript": self.has_transcript,
            "has_artwork": self.has_artwork,
            "series_title": self.series_title,
            "sermon_title": self.sermon_title,
            "theme_scripture": self.theme_scripture,
            "assigned_team": self.assigned_team,
            "duration_seconds": self.duration_seconds,
            "quality_metrics": self.quality_metrics,
            "analysis_complete": self.analysis_complete,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SermonMetadata":
        return cls(
            recording_location=data.get("recording_location"),
            has_video=data.get("has_video", False),
            has_audio=data.get("has_audio", False),
            has_transcript=data.get("has_transcript", False),
            has_artwork=data.get("has_artwork", False),
            series_title=data.get("series_title"),
            sermon_title=data.get("sermon_title"),
            theme_scripture=data.get("theme_scripture"),
            assigned_team=data.get("assigned_team", {}),
            duration_seconds=data.get("duration_seconds", 0),
            quality_metrics=data.get("quality_metrics", {}),
            analysis_complete=data.get("analysis_complete", False),
        )


@dataclass
class QualityMetrics:
    """Media quality metrics"""

    video_resolution: Optional[str] = None
    video_bitrate: Optional[int] = None
    video_frame_rate: Optional[float] = None
    audio_bitrate: Optional[int] = None
    audio_sample_rate: Optional[int] = None
    audio_channels: Optional[int] = None
    file_size_bytes: int = 0
    duration_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "video_resolution": self.video_resolution,
            "video_bitrate": self.video_bitrate,
            "video_frame_rate": self.video_frame_rate,
            "audio_bitrate": self.audio_bitrate,
            "audio_sample_rate": self.audio_sample_rate,
            "audio_channels": self.audio_channels,
            "file_size_bytes": self.file_size_bytes,
            "duration_seconds": self.duration_seconds,
        }


@dataclass
class OptimizationProfile:
    """Optimization profile configuration"""

    name: str
    description: str
    video_settings: Dict[str, Any] = field(default_factory=dict)
    audio_settings: Dict[str, Any] = field(default_factory=dict)
    output_extension: str = "mp4"

    def apply(self, input_path: str, output_path: str) -> bool:
        """Apply optimization to a file"""
        try:
            cmd = self._build_ffmpeg_cmd(input_path, output_path)
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            return False

    def _build_ffmpeg_cmd(self, input_path: str, output_path: str) -> List[str]:
        """Build FFmpeg command for optimization"""
        cmd = ["ffmpeg", "-y", "-i", input_path]

        # Video filters
        video_filters = []
        if "scale" in self.video_settings:
            video_filters.append(f"scale={self.video_settings['scale']}")
        if "crf" in self.video_settings:
            video_filters.append(f"crf={self.video_settings['crf']}")

        if video_filters:
            cmd.extend(["-vf", ",".join(video_filters)])

        # Video codec settings
        cmd.extend(["-c:v", self.video_settings.get("codec", "libx264")])
        if "preset" in self.video_settings:
            cmd.extend(["-preset", self.video_settings["preset"]])
        if "bitrate" in self.video_settings:
            cmd.extend(["-b:v", self.video_settings["bitrate"]])

        # Audio settings
        cmd.extend(["-c:a", self.audio_settings.get("codec", "aac")])
        if "bitrate" in self.audio_settings:
            cmd.extend(["-b:a", f"{self.audio_settings['bitrate']}k"])

        cmd.append(output_path)
        return cmd


# Standard optimization profiles
OPTIMIZATION_PROFILES = {
    "sermon_web": OptimizationProfile(
        name="sermon_web",
        description="Web optimized video for streaming (1080p H.264)",
        video_settings={
            "codec": "libx264",
            "scale": "1920:1080",
            "crf": 23,
            "preset": "medium",
            "bitrate": "4000k",  # Balanced bitrate for 1080p
        },
        audio_settings={"codec": "aac", "bitrate": 192},  # Stereo AAC 192kbps
        output_extension="mp4",
    ),
    "sermon_podcast": OptimizationProfile(
        name="sermon_podcast",
        description="Audio only for podcast distribution",
        video_settings={},
        audio_settings={"codec": "aac", "bitrate": 128},  # AAC 128kbps stereo
        output_extension="m4a",
    ),
    "sermon_archive": OptimizationProfile(
        name="sermon_archive",
        description="High quality archival version (1080p H.264)",
        video_settings={"codec": "libx264", "scale": "1920:1080", "crf": 18, "preset": "slow"},
        audio_settings={"codec": "aac", "bitrate": 256},  # AAC 256kbps stereo
        output_extension="mp4",
    ),
    "sermon_av1": OptimizationProfile(
        name="sermon_av1",
        description="AV1 codec for better compression at 1080p",
        video_settings={
            "codec": "libaom-av1",
            "scale": "1920:1080",
            "crf": 30,
            "preset": "6",  # Speed preset (0=slowest, 8=fastest)
            "bitrate": "2500k",
        },
        audio_settings={"codec": "aac", "bitrate": 192},
        output_extension="mp4",
    ),
}


class LocationDetector:
    """Detects recording location from audio metadata"""

    def __init__(self, geocoder_provider: str = "nominatim"):
        self.geocoder_provider = geocoder_provider
        self._geolocator = None

    async def extract_location(self, file_path: str) -> Optional[str]:
        """Extract and reverse geocode location from audio file"""
        try:
            # Try to read GPS coordinates from file metadata
            coordinates = self._extract_gps_from_file(file_path)

            if coordinates:
                return await self._reverse_geocode(
                    coordinates["lat"], coordinates["lon"]
                )

            return None
        except Exception as e:
            logger.error(f"Location extraction failed: {e}")
            return None

    def _extract_gps_from_file(self, file_path: str) -> Optional[Dict[str, float]]:
        """Extract GPS coordinates from file metadata"""
        try:
            # Use ffprobe to get metadata
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "quiet",
                    "-print_format",
                    "json",
                    "-show_format",
                    "-show_streams",
                    file_path,
                ],
                capture_output=True,
                text=True,
            )

            data = json.loads(result.stdout)

            # Look for GPS tags
            for stream in data.get("streams", []):
                tags = stream.get("tags", {})
                location = tags.get("location")
                if location:
                    # Parse "lat/lon" format
                    lat, lon = location.split("/")
                    return {
                        "lat": float(lat.replace("+", "")),
                        "lon": float(lon.replace("+", "")),
                    }

            # Try format-level tags
            format_tags = data.get("format", {}).get("tags", {})
            location = format_tags.get("location")
            if location:
                lat, lon = location.split("/")
                return {
                    "lat": float(lat.replace("+", "")),
                    "lon": float(lon.replace("+", "")),
                }

            return None
        except Exception as e:
            logger.debug(f"GPS extraction failed: {e}")
            return None

    async def _reverse_geocode(self, lat: float, lon: float) -> Optional[str]:
        """Reverse geocode coordinates to address"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://nominatim.openstreetmap.org/reverse",
                    params={"lat": lat, "lon": lon, "format": "json"},
                    headers={"User-Agent": "FileForge/1.0"},
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("display_name")

            return None
        except Exception as e:
            logger.error(f"Reverse geocoding failed: {e}")
            return None


class MultiModalDetector:
    """Detects sermon components (video, audio, transcript)"""

    VIDEO_FORMATS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
    AUDIO_FORMATS = {".mp3", ".wav", ".flac", ".m4a", ".aac"}
    TRANSCRIPT_FORMATS = {".txt", ".srt", ".vtt", ".json", ".docx"}
    ARTWORK_FORMATS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

    def detect_components(self, file_paths: List[str]) -> Dict[str, bool]:
        """Detect which sermon components are present"""
        return {
            "has_video": any(
                Path(f).suffix.lower() in self.VIDEO_FORMATS for f in file_paths
            ),
            "has_audio": any(
                Path(f).suffix.lower() in self.AUDIO_FORMATS for f in file_paths
            ),
            "has_transcript": any(
                Path(f).suffix.lower() in self.TRANSCRIPT_FORMATS for f in file_paths
            ),
            "has_artwork": any(
                Path(f).suffix.lower() in self.ARTWORK_FORMATS for f in file_paths
            ),
        }

    def get_duration(self, file_path: str) -> int:
        """Get duration of media file in seconds"""
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "quiet",
                    "-print_format",
                    "json",
                    "-show_format",
                    file_path,
                ],
                capture_output=True,
                text=True,
            )

            data = json.loads(result.stdout)
            duration = float(data.get("format", {}).get("duration", 0))
            return int(duration)
        except Exception as e:
            logger.error(f"Duration extraction failed: {e}")
            return 0


class AISermonAnalyzer:
    """AI-powered sermon analysis for metadata extraction"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._client = None

    @property
    def client(self):
        """Lazy initialization of OpenAI client"""
        if self._client is None and self.api_key:
            try:
                from openai import AsyncOpenAI

                self._client = AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                logger.warning("OpenAI client not available")
        return self._client

    async def analyze_transcript(
        self, transcript_path: str, model: str = "gpt-4o-mini"
    ) -> Dict[str, Optional[str]]:
        """Analyze transcript to extract sermon metadata"""
        if not self.client:
            logger.warning("OpenAI client not configured, skipping analysis")
            return {}

        try:
            with open(transcript_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Truncate to token limit
            max_chars = 8000
            content = content[:max_chars]

            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a helpful assistant that analyzes sermon transcripts.
Extract the following information as JSON:
- series_title: The sermon series this belongs to (if mentioned)
- sermon_title: The main title or topic of the sermon
- theme_scripture: Main Bible verses or books referenced
- key_themes: 3-5 main themes discussed
Return ONLY valid JSON, no other text.""",
                    },
                    {
                        "role": "user",
                        "content": f"Analyze this sermon transcript:\n\n{content}",
                    },
                ],
                response_format={"type": "json_object"},
            )

            result = json.loads(response.choices[0].message.content)
            return {
                "series_title": result.get("series_title"),
                "sermon_title": result.get("sermon_title"),
                "theme_scripture": result.get("theme_scripture"),
            }
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return {}


class TeamAssignmentService:
    """Assigns sermon processing tasks to team members"""

    def __init__(self, supabase_client=None):
        self.supabase = supabase_client

    async def assign_team(
        self, sermon_id: str, church_id: str, roles: List[str] = None
    ) -> Dict[str, str]:
        """Assign team members to sermon tasks"""
        if roles is None:
            roles = ["video_editor", "audio_engineer", "transcriber"]

        team = {}

        if self.supabase:
            try:
                result = await self.supabase.db.select(
                    "profiles", {"filters": {"church_id": church_id}, "limit": 10}
                )

                staff_by_role = {}
                for member in result.get("data", []):
                    role = member.get("role")
                    if role in roles:
                        if role not in staff_by_role:
                            staff_by_role[role] = []
                        staff_by_role[role].append(member)

                # Assign first available person for each role
                for role in roles:
                    if role in staff_by_role and staff_by_role[role]:
                        team[role] = staff_by_role[role][0]["email"]
            except Exception as e:
                logger.error(f"Team assignment failed: {e}")

        return team


class QualityAnalyzer:
    """Analyzes media file quality"""

    def analyze(self, file_path: str) -> QualityMetrics:
        """Analyze media file and return quality metrics"""
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "quiet",
                    "-print_format",
                    "json",
                    "-show_format",
                    "-show_streams",
                    file_path,
                ],
                capture_output=True,
                text=True,
            )

            data = json.loads(result.stdout)

            metrics = QualityMetrics()
            format_info = data.get("format", {})

            metrics.file_size_bytes = int(format_info.get("size", 0))
            metrics.duration_seconds = float(format_info.get("duration", 0))

            # Extract stream info
            for stream in data.get("streams", []):
                if stream.get("codec_type") == "video":
                    metrics.video_resolution = (
                        f"{stream.get('width', 0)}x{stream.get('height', 0)}"
                    )
                    metrics.video_bitrate = int(stream.get("bit_rate", 0)) // 1000

                    # Parse frame rate
                    r_frame_rate = stream.get("r_frame_rate", "0/1")
                    if "/" in r_frame_rate:
                        num, den = r_frame_rate.split("/")
                        metrics.video_frame_rate = (
                            float(num) / float(den) if float(den) else 0
                        )

                elif stream.get("codec_type") == "audio":
                    metrics.audio_bitrate = int(stream.get("bit_rate", 0)) // 1000
                    metrics.audio_sample_rate = int(stream.get("sample_rate", 0))
                    metrics.audio_channels = int(stream.get("channels", 0))

            return metrics
        except Exception as e:
            logger.error(f"Quality analysis failed: {e}")
            return QualityMetrics()


class SermonProcessor:
    """Main sermon processing orchestrator"""

    def __init__(self):
        self.location_detector = LocationDetector()
        self.modal_detector = MultiModalDetector()
        self.ai_analyzer = AISermonAnalyzer()
        self.team_assigner = TeamAssignmentService()
        self.quality_analyzer = QualityAnalyzer()
        self.profiles = OPTIMIZATION_PROFILES

    async def process_sermon(
        self,
        file_paths: List[str],
        church_id: Optional[str] = None,
        series_title: Optional[str] = None,
        on_progress: Optional[Callable[[str, float], None]] = None,
    ) -> Dict[str, Any]:
        """Process a sermon through the full pipeline"""
        results = {
            "metadata": SermonMetadata(),
            "quality": {},
            "optimized_files": [],
            "errors": [],
        }

        # Step 1: Detect components
        if on_progress:
            on_progress("detecting_components", 0.1)

        components = self.modal_detector.detect_components(file_paths)
        results["metadata"].has_video = components["has_video"]
        results["metadata"].has_audio = components["has_audio"]
        results["metadata"].has_transcript = components["has_transcript"]
        results["metadata"].has_artwork = components["has_artwork"]

        # Get duration from primary media file
        for path in file_paths:
            if Path(path).suffix.lower() in self.modal_detector.VIDEO_FORMATS.union(
                self.modal_detector.AUDIO_FORMATS
            ):
                results["metadata"].duration_seconds = self.modal_detector.get_duration(
                    path
                )
                break

        # Step 2: Extract location
        if on_progress:
            on_progress("extracting_location", 0.2)

        for path in file_paths:
            if Path(path).suffix.lower() in self.modal_detector.AUDIO_FORMATS:
                location = await self.location_detector.extract_location(path)
                if location:
                    results["metadata"].recording_location = location
                break

        # Step 3: AI analysis of transcript
        if on_progress:
            on_progress("analyzing_transcript", 0.4)

        for path in file_paths:
            if Path(path).suffix.lower() in self.modal_detector.TRANSCRIPT_FORMATS:
                analysis = await self.ai_analyzer.analyze_transcript(path)
                if analysis:
                    results["metadata"].series_title = (
                        analysis.get("series_title") or series_title
                    )
                    results["metadata"].sermon_title = analysis.get("sermon_title")
                    results["metadata"].theme_scripture = analysis.get(
                        "theme_scripture"
                    )
                    results["metadata"].analysis_complete = True
                break

        # Step 4: Quality analysis
        if on_progress:
            on_progress("analyzing_quality", 0.6)

        for path in file_paths:
            if Path(path).suffix.lower() in self.modal_detector.VIDEO_FORMATS.union(
                self.modal_detector.AUDIO_FORMATS
            ):
                quality = self.quality_analyzer.analyze(path)
                results["quality"] = quality.to_dict()
                results["metadata"].quality_metrics = quality.to_dict()
                break

        # Step 5: Team assignment
        if on_progress:
            on_progress("assigning_team", 0.8)

        if church_id:
            team = await self.team_assigner.assign_team(
                str(datetime.now(timezone.utc).timestamp()), church_id
            )
            results["metadata"].assigned_team = team

        if on_progress:
            on_progress("complete", 1.0)

        return results

    def optimize(
        self,
        input_path: str,
        profile_name: str = "sermon_web",
        output_dir: Optional[str] = None,
        max_file_size: int = 4 * 1024 * 1024 * 1024,  # 4GB default
    ) -> Optional[Dict[str, str]]:
        """Optimize a media file using a profile with file size constraints"""
        if profile_name not in self.profiles:
            logger.error(f"Unknown profile: {profile_name}")
            return None

        profile = self.profiles[profile_name]
        input_path = Path(input_path)

        if output_dir is None:
            output_dir = input_path.parent
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

        output_name = input_path.stem + f"_{profile.name}" + profile.output_extension
        output_path = output_dir / output_name

        if profile.apply(str(input_path), str(output_path)):
            # Check if output file is within size constraints
            output_size = output_path.stat().st_size
            
            if output_size > max_file_size:
                logger.warning(
                    f"Optimized file ({output_size} bytes) exceeds maximum size ({max_file_size} bytes)"
                )
                
                # Try to reduce bitrate if file is too large
                logger.info("Attempting to reduce bitrate to meet size constraints")
                reduced_profile = self._create_reduced_bitrate_profile(profile)
                
                # Generate new output path
                reduced_output_name = input_path.stem + f"_{profile.name}_reduced" + profile.output_extension
                reduced_output_path = output_dir / reduced_output_name
                
                if reduced_profile.apply(str(input_path), str(reduced_output_path)):
                    reduced_size = reduced_output_path.stat().st_size
                    
                    if reduced_size <= max_file_size:
                        logger.info(
                            f"Successfully optimized to {reduced_size} bytes"
                        )
                        return {
                            "input_path": str(input_path),
                            "output_path": str(reduced_output_path),
                            "profile": profile_name,
                            "file_size": reduced_size,
                            "original_size": output_size,
                            "bitrate_reduced": True,
                        }
                    else:
                        logger.error(
                            f"Failed to meet size constraints. Reduced file size ({reduced_size} bytes) still exceeds {max_file_size} bytes"
                        )
                        reduced_output_path.unlink(missing_ok=True)
                
                output_path.unlink(missing_ok=True)
                return None
            
            logger.info(f"Optimization completed. File size: {output_size} bytes")
            return {
                "input_path": str(input_path),
                "output_path": str(output_path),
                "profile": profile_name,
                "file_size": output_size,
            }

        return None

    def _create_reduced_bitrate_profile(self, base_profile: OptimizationProfile) -> OptimizationProfile:
        """Create a profile with reduced bitrate for size optimization"""
        reduced_profile = OptimizationProfile(
            name=base_profile.name + "_reduced",
            description=f"{base_profile.description} (reduced bitrate)",
            video_settings=base_profile.video_settings.copy(),
            audio_settings=base_profile.audio_settings.copy(),
            output_extension=base_profile.output_extension,
        )

        # Reduce video bitrate by 30%
        if "bitrate" in reduced_profile.video_settings:
            original_bitrate = int(reduced_profile.video_settings["bitrate"].replace("k", ""))
            reduced_bitrate = int(original_bitrate * 0.7)
            reduced_profile.video_settings["bitrate"] = f"{reduced_bitrate}k"

        # Reduce CRF by 3 for better compression (if available)
        if "crf" in reduced_profile.video_settings:
            reduced_profile.video_settings["crf"] = min(reduced_profile.video_settings["crf"] + 3, 30)

        # Reduce audio bitrate by 25%
        if "bitrate" in reduced_profile.audio_settings:
            original_audio_bitrate = reduced_profile.audio_settings["bitrate"]
            reduced_audio_bitrate = int(original_audio_bitrate * 0.75)
            reduced_profile.audio_settings["bitrate"] = max(reduced_audio_bitrate, 128)  # Minimum 128kbps

        return reduced_profile

    def optimize_batch(
        self,
        file_paths: List[str],
        profile_name: str = "sermon_web",
        output_dir: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Optimize multiple files"""
        results = []
        for path in file_paths:
            result = self.optimize(path, profile_name, output_dir)
            if result:
                results.append(result)
        return results


def create_sermon_processor() -> SermonProcessor:
    """Factory function to create sermon processor"""
    return SermonProcessor()
