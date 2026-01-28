"""Enhanced RSS Feed Monitor for Mixed Media (Audio/Video) Sermon Detection"""

import feedparser
import re
import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from pathlib import Path
from enum import Enum

from celery import shared_task
import httpx

logger = logging.getLogger(__name__)


class MediaType(Enum):
    """Media type classification"""

    AUDIO = "audio"
    VIDEO = "video"
    IMAGE = "image"
    OTHER = "other"


# Media MIME type mappings
MEDIA_TYPES = {
    MediaType.AUDIO: [
        "audio/mpeg",
        "audio/mp4",
        "audio/wav",
        "audio/flac",
        "audio/aac",
        "audio/ogg",
        "audio/mp3",
        "audio/x-m4a",
    ],
    MediaType.VIDEO: [
        "video/mp4",
        "video/quicktime",
        "video/x-msvideo",
        "video/m4v",
        "video/webm",
        "video/x-matroska",
    ],
    MediaType.IMAGE: ["image/jpeg", "image/png", "image/gif", "image/webp"],
}

# Video file extensions
VIDEO_EXTENSIONS = [".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"]
AUDIO_EXTENSIONS = [".mp3", ".m4a", ".wav", ".flac", ".ogg", ".aac"]


def get_supabase_client():
    """Get Supabase client from environment"""
    import os
    from supabase import Client

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")

    if not url or not key:
        logger.error("Supabase credentials not configured")
        return None

    return Client(url, key)


class SermonRSSParser:
    """Enhanced RSS parser for mixed audio/video sermon enclosures"""

    def parse_mixed_enclosures(self, entry) -> Dict[str, List[Dict]]:
        """Handle standard enclosures + Media RSS + podcast:alternateEnclosures"""
        media_groups = {
            MediaType.AUDIO.value: [],
            MediaType.VIDEO.value: [],
            MediaType.IMAGE.value: [],
            MediaType.OTHER.value: [],
        }

        # 1. Standard RSS enclosures
        if hasattr(entry, "enclosures"):
            for enc in entry.enclosures:
                media_type = self.classify_enclosure(enc)
                normalized = self.normalize_enclosure(enc, "standard")
                media_groups[media_type.value].append(normalized)

        # 2. Media RSS namespace (most common for mixed content)
        if hasattr(entry, "media_content"):
            for content in entry.media_content:
                media_type = self.classify_enclosure(content)
                normalized = self.normalize_enclosure(content, "media_rss")
                media_groups[media_type.value].append(normalized)

        # 3. Media RSS thumbnails
        if hasattr(entry, "media_thumbnail"):
            for thumb in entry.media_thumbnail:
                normalized = self.normalize_enclosure(thumb, "media_thumbnail")
                media_groups[MediaType.IMAGE.value].append(normalized)

        # 4. podcast:alternateEnclosure (Apple/Google standard)
        alt_key = "podcast_alternate_enclosures"
        if hasattr(entry, alt_key):
            for alt_enc in getattr(entry, alt_key):
                media_type = self.classify_enclosure(alt_enc)
                normalized = self.normalize_enclosure(alt_enc, "alternate")
                media_groups[media_type.value].append(normalized)

        # 5. Embedded links in description/content
        text_content = entry.get("description", "") or ""
        if hasattr(entry, "content"):
            for content_item in entry.content:
                text_content += content_item.get("value", "")

        embedded_links = self.extract_video_links(text_content)
        for link in embedded_links:
            media_groups[MediaType.VIDEO.value].append(
                {
                    "url": link,
                    "type": "video/mp4",
                    "size": 0,
                    "bitrate": 0,
                    "title": "embedded_video",
                    "duration": None,
                    "source": "embedded",
                }
            )

        return media_groups

    def classify_enclosure(self, enclosure: Dict) -> MediaType:
        """Intelligent media type detection"""
        enc_type = enclosure.get("type", "").lower()
        url = enclosure.get("href", enclosure.get("url", "")).lower()

        # Exact MIME match
        for media_type, mime_types in MEDIA_TYPES.items():
            if enc_type in mime_types:
                return media_type

        # URL extension detection
        if any(ext in url for ext in VIDEO_EXTENSIONS):
            return MediaType.VIDEO
        elif any(ext in url for ext in AUDIO_EXTENSIONS):
            return MediaType.AUDIO

        return MediaType.OTHER

    def normalize_enclosure(self, enclosure: Dict, source: str) -> Dict:
        """Standardize enclosure format across different sources"""
        return {
            "url": enclosure.get("href") or enclosure.get("url"),
            "type": enclosure.get("type"),
            "size": int(enclosure.get("length", 0) or 0),
            "bitrate": int(enclosure.get("bitrate", 0) or 0),
            "title": enclosure.get("title", "media_file"),
            "duration": enclosure.get("duration"),
            "height": enclosure.get("height"),
            "width": enclosure.get("width"),
            "source": source,
        }

    def extract_video_links(self, text: str) -> List[str]:
        """Extract video URLs from text content"""
        patterns = [
            r"(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+",
            r"(?:https?://)?youtu\.be/[\w-]+",
            r"(?:https?://)?vimeo\.com/\d+",
            r"(?:https?://)?streamable\.com/[\w-]+",
            r"(?:https?://)?rumble\.com/[\w-]+",
            r'https?://[^\s<>"\')\]]+\.(?:mp4|mov|mkv|avi|webm)\b',
        ]

        links = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            links.extend(matches)

        return list(set(links))

    def select_primary_media(self, media_groups: Dict) -> Dict[str, Optional[Dict]]:
        """Select best quality media for each type"""
        result = {"video": None, "audio": None, "image": None}

        # Video: largest file = main
        videos = media_groups.get(MediaType.VIDEO.value, [])
        if videos:
            result["video"] = max(videos, key=lambda x: x.get("size", 0))

        # Audio: highest bitrate = best quality
        audios = media_groups.get(MediaType.AUDIO.value, [])
        if audios:
            result["audio"] = max(audios, key=lambda x: x.get("bitrate", 0))

        # Image: first thumbnail
        images = media_groups.get(MediaType.IMAGE.value, [])
        if images:
            result["image"] = images[0]

        return result


class EnhancedRSSMonitor:
    """Enhanced RSS monitoring with mixed media support"""

    def __init__(self):
        self.parser = SermonRSSParser()

    def process_entry(self, entry, feed_title: str) -> Optional[Dict]:
        """Process single RSS entry with mixed media"""
        guid = entry.get("guid", entry.get("id", entry.link))

        # Skip if already processed
        supabase = get_supabase_client()
        if supabase:
            existing = (
                supabase.table("sermon_packages")
                .select("id")
                .eq("rss_guid", guid)
                .execute()
            )
            if existing.data:
                return None

        # Parse enclosures
        media_groups = self.parser.parse_mixed_enclosures(entry)

        # Skip if no audio/video enclosures
        has_media = (
            len(media_groups[MediaType.VIDEO.value]) > 0
            or len(media_groups[MediaType.AUDIO.value]) > 0
        )

        if not has_media:
            return None

        # Select primary media
        primary = self.parser.select_primary_media(media_groups)

        return {
            "title": entry.get("title", "Untitled"),
            "description": entry.get("description", entry.get("summary", "")),
            "published": entry.get("published", entry.get("updated", "")),
            "guid": guid,
            "feed_title": feed_title,
            "media": media_groups,
            "primary_video": primary["video"],
            "primary_audio": primary["audio"],
            "primary_image": primary["image"],
        }


# ==================== Celery Tasks ====================


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def monitor_mixed_media_feed(self, feed_url: str, church_id: str):
    """Enhanced RSS parsing for A/V sermons with mixed enclosures"""

    logger.info(f"Monitoring mixed media feed: {feed_url}")

    supabase = get_supabase_client()
    if not supabase:
        raise self.retry(exc=Exception("Supabase not configured"))

    try:
        feed = feedparser.parse(feed_url)

        if feed.bozo:
            logger.warning(f"Malformed RSS feed: {feed_url}")

        feed_title = feed.feed.get("title", "Unknown Podcast")
        monitor = EnhancedRSSMonitor()

        new_packages = []

        for entry in feed.entries:
            result = monitor.process_entry(entry, feed_title)

            if result:
                new_packages.append(result)

                # Queue processing
                process_mixed_media_sermon.delay(church_id, result)

        # Update feed stats
        supabase.table("podcast_feeds").update(
            {
                "last_checked": datetime.now(timezone.utc).isoformat(),
                "last_entry_count": len(feed.entries),
                "last_package_count": len(new_packages),
            }
        ).eq("rss_url", feed_url).eq("church_id", church_id).execute()

        return {
            "status": "complete",
            "feed_url": feed_url,
            "packages_created": len(new_packages),
        }

    except Exception as e:
        logger.error(f"Feed monitoring failed: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=2, default_retry_delay=600)
def process_mixed_media_sermon(self, church_id: str, entry_data: Dict[str, Any]):
    """Handle complete A/V sermon package from RSS"""

    supabase = get_supabase_client()
    if not supabase:
        raise self.retry(exc=Exception("Supabase not configured"))

    try:
        guid = entry_data.get("guid")

        # Double-check for duplicates
        existing = (
            supabase.table("sermon_packages")
            .select("id")
            .eq("rss_guid", guid)
            .execute()
        )
        if existing.data:
            return {"status": "skipped", "reason": "already_exists"}

        # Store complete media package
        sermon_package = {
            "church_id": church_id,
            "title": entry_data.get("title"),
            "description": entry_data.get("description"),
            "rss_guid": guid,
            "feed_title": entry_data.get("feed_title"),
            "published_date": entry_data.get("published"),
            "media_inventory": entry_data.get("media", {}),
            "primary_video": entry_data.get("primary_video"),
            "primary_audio": entry_data.get("primary_audio"),
            "primary_image": entry_data.get("primary_image"),
            "processing_status": "queued",
        }

        result = supabase.table("sermon_packages").insert(sermon_package).execute()
        package_id = result.data[0]["id"] if result.data else None

        if not package_id:
            raise ValueError("Failed to create sermon package")

        # Trigger parallel processing for each media type
        if entry_data.get("primary_video"):
            process_sermon_video_pipeline.delay(
                package_id,
                entry_data["primary_video"],
                entry_data.get("media", {}).get("video", []),
            )

        if entry_data.get("primary_audio"):
            process_sermon_audio_pipeline.delay(
                package_id,
                entry_data["primary_audio"],
                entry_data.get("media", {}).get("audio", []),
            )

        # Process images/thumbnails
        images = entry_data.get("media", {}).get("image", [])
        if images:
            process_sermon_images.delay(package_id, images)

        return {
            "status": "processing",
            "package_id": package_id,
            "has_video": bool(entry_data.get("primary_video")),
            "has_audio": bool(entry_data.get("primary_audio")),
        }

    except Exception as e:
        logger.error(f"Package processing failed: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=2)
def process_sermon_video_pipeline(
    self, package_id: str, primary_video: Dict, all_videos: List[Dict]
):
    """Process all video variants (main + thumbnails + highlights)"""

    supabase = get_supabase_client()

    try:
        # Download best quality video
        video_path = asyncio.run(download_video_file(primary_video["url"]))

        # Full sermon processing
        from backend.celery_tasks.sermon_workflow import (
            extract_gps_location,
            analyze_sermon_metadata,
        )

        gps_result = extract_gps_location(video_path, None)

        # Store video-specific results
        video_record = {
            "package_id": package_id,
            "file_path": video_path,
            "source_url": primary_video["url"],
            "media_type": "video",
            "variant": "main",
            "file_size": primary_video.get("size", 0),
            "bitrate": primary_video.get("bitrate", 0),
            "metadata": {
                "gps_data": gps_result.to_dict() if gps_result else None,
            },
            "processing_status": "completed",
        }

        supabase.table("sermon_media_files").insert(video_record).execute()

        # Process other video variants
        for variant in all_videos:
            if variant["url"] != primary_video["url"]:
                supabase.table("sermon_media_files").insert(
                    {
                        "package_id": package_id,
                        "source_url": variant["url"],
                        "media_type": "video",
                        "variant": "alternate",
                        "file_size": variant.get("size", 0),
                        "processing_status": "available",
                    }
                ).execute()

        return {"status": "video_complete", "package_id": package_id}

    except Exception as e:
        logger.error(f"Video pipeline failed: {e}")
        return {"status": "failed", "error": str(e)}


@shared_task(bind=True, max_retries=2)
def process_sermon_audio_pipeline(
    self, package_id: str, primary_audio: Dict, all_audio: List[Dict]
):
    """Process all audio variants (main + podcast + clips)"""

    supabase = get_supabase_client()

    try:
        # Download best quality audio
        audio_path = asyncio.run(download_video_file(primary_audio["url"]))

        # Extract audio metadata
        from backend.file_processor.services.gps_extractor import AudioMetadataExtractor

        extractor = AudioMetadataExtractor()
        audio_metadata = extractor.extract_all(audio_path)

        # Whisper transcription from best audio
        from backend.celery_tasks.sermon_workflow import transcribe_sermon

        transcript_result = transcribe_sermon(package_id, None)

        # Store audio-specific results
        audio_record = {
            "package_id": package_id,
            "file_path": audio_path,
            "source_url": primary_audio["url"],
            "media_type": "audio",
            "variant": "main",
            "file_size": primary_audio.get("size", 0),
            "bitrate": primary_audio.get("bitrate", 0),
            "duration": audio_metadata.get("duration"),
            "transcript_id": transcript_result.get("transcript_id"),
            "metadata": audio_metadata,
            "processing_status": "completed",
        }

        supabase.table("sermon_media_files").insert(audio_record).execute()

        # Process other audio variants
        for variant in all_audio:
            if variant["url"] != primary_audio["url"]:
                supabase.table("sermon_media_files").insert(
                    {
                        "package_id": package_id,
                        "source_url": variant["url"],
                        "media_type": "audio",
                        "variant": "alternate",
                        "file_size": variant.get("size", 0),
                        "processing_status": "available",
                    }
                ).execute()

        return {"status": "audio_complete", "package_id": package_id}

    except Exception as e:
        logger.error(f"Audio pipeline failed: {e}")
        return {"status": "failed", "error": str(e)}


@shared_task(bind=True, max_retries=1)
def process_sermon_images(self, package_id: str, images: List[Dict]):
    """Process thumbnail images"""

    supabase = get_supabase_client()

    try:
        for i, image in enumerate(images[:5]):  # Max 5 images
            supabase.table("sermon_media_files").insert(
                {
                    "package_id": package_id,
                    "source_url": image.get("url"),
                    "media_type": "image",
                    "variant": "thumbnail",
                    "file_size": image.get("size", 0),
                    "width": image.get("width"),
                    "height": image.get("height"),
                    "processing_status": "available",
                }
            ).execute()

        return {
            "status": "images_complete",
            "package_id": package_id,
            "count": len(images),
        }

    except Exception as e:
        logger.error(f"Image processing failed: {e}")
        return {"status": "failed", "error": str(e)}


# ==================== Download Utilities ====================


async def download_video_file(url: str) -> str:
    """Download video/audio file to temp storage"""

    import os

    temp_dir = Path("/tmp/sermon_downloads")
    temp_dir.mkdir(exist_ok=True)

    filename = Path(urlparse(url).path).name or f"media_{hash(url)}"

    # Add extension if missing
    if not Path(filename).suffix:
        if any(ext in url for ext in VIDEO_EXTENSIONS):
            filename += ".mp4"
        elif any(ext in url for ext in AUDIO_EXTENSIONS):
            filename += ".mp3"

    output_path = temp_dir / filename

    # YouTube/Vimeo
    if "youtube.com" in url or "youtu.be" in url or "vimeo.com" in url:
        return await download_with_ytdlp(url, temp_dir)

    # Direct download
    async with httpx.AsyncClient(follow_redirects=True, timeout=300.0) as client:
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(response.content)

    return str(output_path)


async def download_with_ytdlp(url: str, temp_dir: Path) -> str:
    """Download using yt-dlp for YouTube/Vimeo"""
    try:
        import yt_dlp

        output_template = str(temp_dir / f"ytdlp_{hash(url)}")

        ydl_opts = {
            "format": "best",
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Find downloaded file
        for f in temp_dir.glob(f"ytdlp_{hash(url)}*"):
            if f.suffix in [".mp4", ".mkv", ".webm", ".m4a", ".mp3"]:
                return str(f)

        raise ValueError("yt-dlp download failed")

    except ImportError:
        logger.warning("yt-dlp not installed")
        # Fallback to direct URL
        return url


# ==================== Utility Functions ====================


def _is_video_enclosure(enclosure: Dict) -> bool:
    """Check if enclosure contains video"""
    enclosure_type = enclosure.get("type", "")
    href = enclosure.get("href", "")

    if enclosure_type in MEDIA_TYPES[MediaType.VIDEO]:
        return True

    href_lower = href.lower()
    return any(ext in href_lower for ext in VIDEO_EXTENSIONS)


def _find_video_links_in_text(text: str) -> List[str]:
    """Extract video URLs from text"""
    patterns = [
        r"(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+",
        r"(?:https?://)?youtu\.be/[\w-]+",
        r"(?:https?://)?vimeo\.com/\d+",
        r'(?:https?://)?[^\s<>"\')\]]+\.(?:mp4|mov|mkv|avi|webm)\b',
    ]

    links = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        links.extend(matches)

    return list(set(links))


@shared_task
def check_all_active_feeds():
    """Check all active podcast feeds for new mixed media"""

    supabase = get_supabase_client()
    if not supabase:
        return {"error": "Supabase not configured"}

    try:
        feeds = supabase.table("podcast_feeds").select("*").eq("active", True).execute()

        for feed in feeds.data:
            monitor_mixed_media_feed.delay(feed["rss_url"], feed["church_id"])

        return {"feeds_checked": len(feeds.data)}

    except Exception as e:
        logger.error(f"Feed check failed: {e}")
        return {"error": str(e)}


# ==================== Supabase SQL Schema ====================
"""
-- Run in Supabase SQL Editor:

CREATE TABLE sermon_packages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    church_id UUID NOT NULL REFERENCES churches(id),
    title TEXT NOT NULL,
    description TEXT,
    rss_guid TEXT UNIQUE,
    feed_title TEXT,
    published_date TIMESTAMP WITH TIME ZONE,
    media_inventory JSONB DEFAULT '{}',
    primary_video JSONB DEFAULT NULL,
    primary_audio JSONB DEFAULT NULL,
    primary_image JSONB DEFAULT NULL,
    processing_status TEXT DEFAULT 'queued' 
        CHECK (processing_status IN ('queued', 'processing', 'completed', 'failed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE sermon_media_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    package_id UUID REFERENCES sermon_packages(id) ON DELETE CASCADE,
    source_url TEXT NOT NULL,
    file_path TEXT,
    media_type TEXT NOT NULL 
        CHECK (media_type IN ('audio', 'video', 'image')),
    variant TEXT DEFAULT 'main'
        CHECK (variant IN ('main', 'alternate', 'thumbnail', 'clip')),
    file_size BIGINT,
    bitrate INTEGER,
    duration INTEGER,
    width INTEGER,
    height INTEGER,
    metadata JSONB DEFAULT '{}',
    transcript_id UUID,
    processing_status TEXT DEFAULT 'pending'
        CHECK (processing_status IN ('pending', 'available', 'processing', 'completed', 'failed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sermon_packages_church ON sermon_packages(church_id);
CREATE INDEX idx_sermon_packages_guid ON sermon_packages(rss_guid);
CREATE INDEX idx_sermon_packages_status ON sermon_packages(processing_status);
CREATE INDEX idx_sermon_media_files_package ON sermon_media_files(package_id);
CREATE INDEX idx_sermon_media_files_type ON sermon_media_files(media_type);

-- RLS Policies
ALTER TABLE sermon_packages ENABLE ROW LEVEL SECURITY;
ALTER TABLE sermon_media_files ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Media team accesses packages" ON sermon_packages
    FOR ALL USING (auth.role() IN ('media_team', 'admin', 'super_admin'));

CREATE POLICY "Media team accesses files" ON sermon_media_files
    FOR ALL USING (auth.role() IN ('media_team', 'admin', 'super_admin'));
"""
