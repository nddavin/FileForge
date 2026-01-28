"""Sermon Workflow Celery Tasks - Master Orchestration System"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pathlib import Path

from celery import Celery, chord, group  # noqa: F401
from celery.exceptions import MaxRetriesExceededError  # noqa: F401
from celery.result import AsyncResult  # noqa: F401

logger = logging.getLogger(__name__)

# Initialize Celery app
app = Celery(
    "fileforge", broker="redis://localhost:6379/0", backend="redis://localhost:6379/1"
)

# Celery configuration
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour per task
    task_soft_time_limit=3300,  # Soft limit at 55 minutes
    worker_prefetch_multiplier=1,
    worker_concurrency=4,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    result_expires=86400,  # Results expire in 24 hours
)


# ==================== Database Models (for reference) ====================
# These would be created as SQLAlchemy models in production
"""
CREATE TABLE sermon_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sermon_id UUID REFERENCES sermons(id),
    task_type TEXT CHECK (task_type IN (
        'transcription', 'video_processing', 'location_tagging', 
        'metadata_ai', 'quality_optimization', 'thumbnail_generation',
        'social_clip', 'distribution'
    )),
    status TEXT DEFAULT 'pending' CHECK (status IN (
        'pending', 'assigned', 'in_progress', 'completed', 'failed',
        'cancelled'
    )),
    assigned_to UUID REFERENCES profiles(id),
    priority INTEGER DEFAULT 1 CHECK (priority BETWEEN 1 AND 5),
    deadline TIMESTAMP,
    ai_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    result_data JSONB
);

CREATE INDEX idx_sermon_tasks_sermon_id ON sermon_tasks(sermon_id);
CREATE INDEX idx_sermon_tasks_assigned_to ON sermon_tasks(assigned_to);
CREATE INDEX idx_sermon_tasks_status ON sermon_tasks(status);
"""


# ==================== Supabase Client ====================
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


# ==================== AI Team Assignment ====================
async def ai_assign_team(sermon_id: str, task_types: List[str]) -> Dict[str, str]:
    """AI matches tasks to team members by skill + availability"""
    import os
    import openai

    supabase = get_supabase_client()
    if not supabase:
        return {}

    try:
        # Query available team members with their skills
        response = (
            supabase.table("profiles")
            .select(
                "id, email, full_name, skills, availability, workload_score, "
                "completed_tasks_count"
            )
            .eq("role", "media_team")
            .eq("active", True)
            .execute()
        )

        team = response.data
        if not team:
            logger.warning("No team members found for assignment")
            return {}

        # AI skill matching using GPT-4o-mini
        openai.api_key = os.getenv("OPENAI_API_KEY") or ""

        prompt = f"""
        Sermon ID: {sermon_id}
        Required Task Types: {task_types}
        
        Team Members:
        {json.dumps(team, indent=2, default=str)}
        
        Skills mapping:
        - transcription: needs 'transcription', 'whisper', 'typing_speed'
        - video_processing: needs 'premiere', 'ffmpeg', 'video_editing'
        - location_tagging: needs 'gps', 'metadata', 'geocoding'
        - metadata_ai: needs 'ai', 'analysis', 'llm'
        - quality_optimization: needs 'encoding', 'ffmpeg', 'quality'
        - thumbnail_generation: needs 'design', 'ffmpeg', 'thumbnails'
        - social_clip: needs 'social', 'editing', 'shorts'
        - distribution: needs 'upload', 'platforms', 'scheduling'
        
        Assign each task to the best available person based on:
        1. Skill match score
        2. Current workload (lower workload_score is better)
        3. Recent activity (avoid overloading)
        
        Return ONLY valid JSON:
        {{"transcription": "user_id", "video_processing": "user_id", ...}}
        """

        response = await openai.ChatCompletion.acreate(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )

        assignments = json.loads(response.choices[0].message.content)
        return assignments

    except Exception as e:
        logger.error(f"AI team assignment failed: {e}")
        return {}


# ==================== Task Creation ====================
def create_sermon_tasks(
    sermon_id: str, assignments: Dict[str, str], has_video: bool = False
) -> List[str]:
    """Create task records in Supabase and return task IDs"""
    supabase = get_supabase_client()
    if not supabase:
        return []

    task_specs = [
        {"type": "transcription", "priority": 1, "ai_weight": 0.9},
        {"type": "location_tagging", "priority": 2, "ai_weight": 0.7},
        {"type": "metadata_ai", "priority": 2, "ai_weight": 0.85},
        {"type": "quality_optimization", "priority": 3, "ai_weight": 0.8},
    ]

    if has_video:
        task_specs.extend(
            [
                {"type": "video_processing", "priority": 1, "ai_weight": 0.85},
                {"type": "thumbnail_generation", "priority": 3, "ai_weight": 0.6},
                {"type": "social_clip", "priority": 4, "ai_weight": 0.5},
            ]
        )

    task_ids = []
    for spec in task_specs:
        task_type = spec["type"]
        assigned_to = assignments.get(task_type)

        if not assigned_to:
            continue

        try:
            result = (
                supabase.table("sermon_tasks")
                .insert(
                    {
                        "sermon_id": sermon_id,
                        "task_type": task_type,
                        "status": "assigned",
                        "assigned_to": assigned_to,
                        "priority": spec["priority"],
                        "ai_score": spec["ai_weight"],
                    }
                )
                .execute()
            )

            if result.data:
                task_ids.append(result.data[0]["id"])
                logger.info(f"Created task {task_type} for sermon {sermon_id}")

        except Exception as e:
            logger.error(f"Failed to create task {task_type}: {e}")

    return task_ids


# ==================== Master Orchestrator ====================
@app.task(bind=True, max_retries=3, default_retry_delay=60)
def sermon_intake_pipeline(
    self, sermon_id: str, uploaded_files: List[str], church_id: Optional[str] = None
):
    """Master orchestrator - AI assigns tasks based on team skills"""

    logger.info(f"Starting sermon intake pipeline: {sermon_id}")

    supabase = get_supabase_client()
    if not supabase:
        raise self.retry(exc=Exception("Supabase not configured"))

    try:
        # Step 1: Update sermon status
        supabase.table("sermons").update(
            {
                "processing_status": "intake",
                "pipeline_started_at": datetime.now(timezone.utc).isoformat(),
            }
        ).eq("id", sermon_id).execute()

        # Step 2: AI Team Matching
        task_types = [
            "transcription",
            "location_tagging",
            "metadata_ai",
            "quality_optimization",
            "thumbnail_generation",
        ]

        has_video = any(
            Path(f).suffix.lower() in [".mp4", ".mov", ".mkv"] for f in uploaded_files
        )

        if has_video:
            task_types.extend(["video_processing", "social_clip"])

        # Run AI assignment (synchronously for task creation)
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            assignments = loop.run_until_complete(ai_assign_team(sermon_id, task_types))
        finally:
            loop.close()

        if not assignments:
            # Fallback: assign to default user or skip assignment
            logger.warning(f"No AI assignments for {sermon_id}, using defaults")
            assignments = {}

        # Step 3: Create task records
        task_ids = create_sermon_tasks(sermon_id, assignments, has_video)

        # Step 4: Dispatch parallel Celery tasks
        workflow = []

        # Transcription task (always required)
        transcribe_task = transcribe_sermon.delay(
            sermon_id, assignments.get("transcription")
        )
        workflow.append(transcribe_task.id)

        # Location tagging
        gps_task = extract_gps_location.delay(
            sermon_id, assignments.get("location_tagging")
        )
        workflow.append(gps_task.id)

        # Metadata AI analysis
        ai_task = analyze_sermon_metadata.delay(
            sermon_id, assignments.get("metadata_ai")
        )
        workflow.append(ai_task.id)

        # Quality optimization
        quality_task = optimize_quality.delay(
            sermon_id, assignments.get("quality_optimization")
        )
        workflow.append(quality_task.id)

        # Conditional parallel tasks
        if has_video:
            video_task = process_video.delay(
                sermon_id, assignments.get("video_processing")
            )
            workflow.append(video_task.id)

            thumbnail_task = generate_thumbnails.delay(
                sermon_id, assignments.get("thumbnail_generation")
            )
            workflow.append(thumbnail_task.id)

            social_task = create_social_clips.delay(
                sermon_id, assignments.get("social_clip")
            )
            workflow.append(social_task.id)

        # Step 5: Chord for final sync when all tasks complete
        finalize_workflow = chord(group(workflow))(
            finalize_sermon_pipeline.s(sermon_id)
        )

        return {
            "sermon_id": sermon_id,
            "tasks_created": len(task_ids),
            "workflow_ids": workflow,
            "status": "intake_complete",
        }

    except Exception as e:
        logger.error(f"Sermon intake pipeline failed: {e}")

        # Update error status
        if supabase:
            supabase.table("sermons").update(
                {"processing_status": "failed", "error_message": str(e)}
            ).eq("id", sermon_id).execute()

        raise self.retry(exc=e)


# ==================== Individual Task Workers ====================


@app.task(bind=True, max_retries=3)
def transcribe_sermon(self, sermon_id: str, assigned_user: Optional[str] = None):
    """Whisper + human review workflow"""

    supabase = get_supabase_client()

    try:
        # Update task status
        if supabase and assigned_user:
            supabase.table("sermon_tasks").update(
                {
                    "status": "in_progress",
                    "started_at": datetime.now(timezone.utc).isoformat(),
                }
            ).eq("sermon_id", sermon_id).eq("task_type", "transcription").execute()

        # Get sermon audio path
        sermon = supabase.table("sermons").select("*").eq("id", sermon_id).execute()
        audio_path = sermon.data[0].get("audio_path") if sermon.data else None

        if not audio_path:
            raise ValueError(f"No audio path found for sermon {sermon_id}")

        # Whisper transcription (using OpenAI Whisper or local whisper)
        try:
            import whisper

            model = whisper.load_model("base")
            result = model.transcribe(audio_path)

            transcript_text = result["text"]
            segments = result.get("segments", [])

        except ImportError:
            # Fallback to OpenAI Whisper API
            import openai

            audio_file = open(audio_path, "rb")
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
            transcript_text = transcript.text
            segments = []

        # Store raw transcript
        transcript_record = (
            supabase.table("sermon_transcripts")
            .insert(
                {
                    "sermon_id": sermon_id,
                    "raw_text": transcript_text,
                    "speaker_timestamps": segments,
                    "language": result.get("language", "en"),
                    "confidence_score": result.get("confidence", 0.0),
                }
            )
            .execute()
        )

        transcript_id = (
            transcript_record.data[0]["id"] if transcript_record.data else None
        )

        # Update task completion
        if supabase:
            supabase.table("sermon_tasks").update(
                {
                    "status": "completed",
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "result_data": {"transcript_id": transcript_id},
                }
            ).eq("sermon_id", sermon_id).eq("task_type", "transcription").execute()

        return {"status": "completed", "transcript_id": transcript_id}

    except Exception as e:
        logger.error(f"Transcription failed for {sermon_id}: {e}")
        _handle_task_failure(
            supabase, sermon_id, "transcription", e, self.request.retries
        )
        raise


@app.task(bind=True, max_retries=2)
def process_video(self, sermon_id: str, assigned_user: Optional[str] = None):
    """FFmpeg optimization + quality analysis"""

    supabase = get_supabase_client()

    try:
        if supabase and assigned_user:
            supabase.table("sermon_tasks").update(
                {
                    "status": "in_progress",
                    "started_at": datetime.now(timezone.utc).isoformat(),
                }
            ).eq("sermon_id", sermon_id).eq("task_type", "video_processing").execute()

        # Get sermon and video path
        sermon = supabase.table("sermons").select("*").eq("id", sermon_id).execute()
        video_path = sermon.data[0].get("video_path") if sermon.data else None

        if not video_path:
            raise ValueError(f"No video path found for sermon {sermon_id}")

        # Import and use existing optimization pipeline
        from file_processor.services.sermon_processor import (
            SermonProcessor,
            OPTIMIZATION_PROFILES,
        )

        processor = SermonProcessor()

        # Run web optimization
        web_result = processor.optimize(
            video_path,
            profile_name="sermon_web",
            output_dir=str(Path(video_path).parent / "optimized"),
        )

        # Run archive optimization
        archive_result = processor.optimize(
            video_path,
            profile_name="sermon_archive",
            output_dir=str(Path(video_path).parent / "archive"),
        )

        # Store optimized paths
        if supabase:
            update_data = {
                "optimized_web_path": (
                    web_result.get("output_path") if web_result else None
                ),
                "archive_path": (
                    archive_result.get("output_path") if archive_result else None
                ),
            }
            supabase.table("sermons").update(update_data).eq("id", sermon_id).execute()

            supabase.table("sermon_tasks").update(
                {
                    "status": "completed",
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "result_data": {
                        "web_optimized": web_result,
                        "archive": archive_result,
                    },
                }
            ).eq("sermon_id", sermon_id).eq("task_type", "video_processing").execute()

        return {"status": "completed", "web": web_result, "archive": archive_result}

    except Exception as e:
        logger.error(f"Video processing failed for {sermon_id}: {e}")
        _handle_task_failure(
            supabase, sermon_id, "video_processing", e, self.request.retries
        )
        raise


@app.task(bind=True, max_retries=2)
def extract_gps_location(self, sermon_id: str, assigned_user: Optional[str] = None):
    """Extract GPS coordinates from audio/video metadata"""

    supabase = get_supabase_client()

    try:
        if supabase and assigned_user:
            supabase.table("sermon_tasks").update(
                {
                    "status": "in_progress",
                    "started_at": datetime.now(timezone.utc).isoformat(),
                }
            ).eq("sermon_id", sermon_id).eq("task_type", "location_tagging").execute()

        # Use GPS extractor
        from file_processor.services.gps_extractor import GPSExtractor
        from geopy.geocoders import Nominatim

        geolocator = Nominatim(user_agent="fileforge-sermon", timeout=10)
        gps_extractor = GPSExtractor(geolocator=geolocator)

        # Get audio path
        sermon = supabase.table("sermons").select("*").eq("id", sermon_id).execute()
        audio_path = sermon.data[0].get("audio_path") if sermon.data else None

        if not audio_path:
            # Try video path
            audio_path = sermon.data[0].get("video_path") if sermon.data else None

        if audio_path:
            gps_data = gps_extractor.extract(audio_path)

            if supabase:
                supabase.table("sermons").update(
                    {
                        "recording_location": gps_data.readable_location,
                        "latitude": gps_data.lat,
                        "longitude": gps_data.lon,
                        "location_source": gps_data.source,
                        "location_confidence": gps_data.confidence,
                    }
                ).eq("id", sermon_id).execute()

                supabase.table("sermon_tasks").update(
                    {
                        "status": "completed",
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                        "result_data": gps_data.to_dict(),
                    }
                ).eq("sermon_id", sermon_id).eq(
                    "task_type", "location_tagging"
                ).execute()

            return {"status": "completed", "gps": gps_data.to_dict()}

        return {"status": "skipped", "reason": "No media file found"}

    except Exception as e:
        logger.error(f"GPS extraction failed for {sermon_id}: {e}")
        _handle_task_failure(
            supabase, sermon_id, "location_tagging", e, self.request.retries
        )
        raise


@app.task(bind=True, max_retries=2)
def analyze_sermon_metadata(self, sermon_id: str, assigned_user: Optional[str] = None):
    """AI extracts title, scripture, series, themes from transcript"""

    supabase = get_supabase_client()

    try:
        if supabase and assigned_user:
            supabase.table("sermon_tasks").update(
                {
                    "status": "in_progress",
                    "started_at": datetime.now(timezone.utc).isoformat(),
                }
            ).eq("sermon_id", sermon_id).eq("task_type", "metadata_ai").execute()

        # Get transcript
        transcript = (
            supabase.table("sermon_transcripts")
            .select("*")
            .eq("sermon_id", sermon_id)
            .order("created_at", ascending=False)
            .limit(1)
            .execute()
        )

        if not transcript.data:
            raise ValueError(f"No transcript found for sermon {sermon_id}")

        transcript_text = transcript.data[0].get("raw_text", "")[:8000]

        # AI analysis using GPT-4o-mini
        import openai

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are a sermon analysis assistant. Extract metadata precisely.
                    
Return JSON with:
- sermon_title: 1-2 sentence title capturing the main message
- series_title: Name of sermon series (if mentioned, otherwise null)
- theme_scripture: Bible verses/books referenced (format: "Book Chapter:Verses")
- main_themes: Array of 3-5 key themes/topics
- sermon_type: One of (expository, topical, narrative, devotional)
- key_quotes: 2-3 memorable quotes from the sermon
- target_audience: Primary audience (youth, families, general, etc.)
- suggested_tags: Array of 5-10 searchable tags""",
                },
                {
                    "role": "user",
                    "content": f"Analyze this sermon transcript:\n\n{transcript_text}",
                },
            ],
            response_format={"type": "json_object"},
        )

        metadata = json.loads(response.choices[0].message.content)

        # Store metadata
        if supabase:
            supabase.table("sermons").update(
                {
                    "metadata": metadata,
                    "sermon_title": metadata.get("sermon_title"),
                    "series_title": metadata.get("series_title"),
                    "theme_scripture": metadata.get("theme_scripture"),
                    "tags": metadata.get("suggested_tags", []),
                }
            ).eq("id", sermon_id).execute()

            supabase.table("sermon_tasks").update(
                {
                    "status": "completed",
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "result_data": metadata,
                }
            ).eq("sermon_id", sermon_id).eq("task_type", "metadata_ai").execute()

            # Trigger auto-sorting
            auto_sort_sermon.delay(sermon_id, metadata)

        return {"status": "completed", "metadata": metadata}

    except Exception as e:
        logger.error(f"Metadata AI failed for {sermon_id}: {e}")
        _handle_task_failure(
            supabase, sermon_id, "metadata_ai", e, self.request.retries
        )
        raise


@app.task(bind=True, max_retries=2)
def optimize_quality(self, sermon_id: str, assigned_user: Optional[str] = None):
    """Quality metrics and audio optimization"""

    supabase = get_supabase_client()

    try:
        if supabase and assigned_user:
            supabase.table("sermon_tasks").update(
                {
                    "status": "in_progress",
                    "started_at": datetime.now(timezone.utc).isoformat(),
                }
            ).eq("sermon_id", sermon_id).eq(
                "task_type", "quality_optimization"
            ).execute()

        from file_processor.services.sermon_processor import QualityAnalyzer

        sermon = supabase.table("sermons").select("*").eq("id", sermon_id).execute()
        media_path = sermon.data[0].get("audio_path") if sermon.data else None

        if not media_path:
            media_path = sermon.data[0].get("video_path") if sermon.data else None

        if media_path:
            analyzer = QualityAnalyzer()
            metrics = analyzer.analyze(media_path)

            if supabase:
                supabase.table("sermons").update(
                    {"quality_metrics": metrics.to_dict()}
                ).eq("id", sermon_id).execute()

                supabase.table("sermon_tasks").update(
                    {
                        "status": "completed",
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                        "result_data": metrics.to_dict(),
                    }
                ).eq("sermon_id", sermon_id).eq(
                    "task_type", "quality_optimization"
                ).execute()

            return {"status": "completed", "metrics": metrics.to_dict()}

        return {"status": "skipped"}

    except Exception as e:
        logger.error(f"Quality optimization failed for {sermon_id}: {e}")
        _handle_task_failure(
            supabase, sermon_id, "quality_optimization", e, self.request.retries
        )
        raise


@app.task(bind=True, max_retries=2)
def generate_thumbnails(self, sermon_id: str, assigned_user: Optional[str] = None):
    """Generate sermon thumbnails at key moments"""

    supabase = get_supabase_client()

    try:
        if supabase and assigned_user:
            supabase.table("sermon_tasks").update(
                {
                    "status": "in_progress",
                    "started_at": datetime.now(timezone.utc).isoformat(),
                }
            ).eq("sermon_id", sermon_id).eq(
                "task_type", "thumbnail_generation"
            ).execute()

        # Get video path
        sermon = supabase.table("sermons").select("*").eq("id", sermon_id).execute()
        video_path = sermon.data[0].get("video_path") if sermon.data else None

        if not video_path:
            return {"status": "skipped", "reason": "No video file"}

        import subprocess
        import os

        # Generate 3 thumbnails at 10%, 50%, 90% of video
        thumbnails = []
        output_dir = Path(video_path).parent / "thumbnails"
        output_dir.mkdir(exist_ok=True)

        # Get video duration
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                video_path,
            ],
            capture_output=True,
            text=True,
        )

        duration = float(result.stdout.strip())
        timestamps = [0.1, 0.5, 0.9]  # 10%, 50%, 90%

        for i, ts in enumerate(timestamps):
            time_sec = int(duration * ts)
            output_path = str(output_dir / f"thumbnail_{i+1}.jpg")

            subprocess.run(
                [
                    "ffmpeg",
                    "-ss",
                    str(time_sec),
                    "-i",
                    video_path,
                    "-vframes",
                    "1",
                    "-q:v",
                    "2",
                    output_path,
                    "-y",
                ],
                capture_output=True,
            )

            if Path(output_path).exists():
                thumbnails.append(output_path)

        # Upload thumbnails to Supabase Storage
        thumbnail_urls = []
        if supabase:
            for thumb_path in thumbnails:
                filename = Path(thumb_path).name
                with open(thumb_path, "rb") as f:
                    supabase.storage.from_("sermon-thumbnails").upload(
                        f"{sermon_id}/{filename}",
                        f.read(),
                        {"content-type": "image/jpeg"},
                    )

                url = supabase.storage.from_("sermon-thumbnails").get_public_url(
                    f"{sermon_id}/{filename}"
                )
                thumbnail_urls.append(url)

        if supabase:
            supabase.table("sermons").update({"thumbnail_urls": thumbnail_urls}).eq(
                "id", sermon_id
            ).execute()

            supabase.table("sermon_tasks").update(
                {
                    "status": "completed",
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "result_data": {"thumbnails": thumbnail_urls},
                }
            ).eq("sermon_id", sermon_id).eq(
                "task_type", "thumbnail_generation"
            ).execute()

        return {"status": "completed", "thumbnails": thumbnail_urls}

    except Exception as e:
        logger.error(f"Thumbnail generation failed for {sermon_id}: {e}")
        _handle_task_failure(
            supabase, sermon_id, "thumbnail_generation", e, self.request.retries
        )
        raise


@app.task(bind=True, max_retries=1)
def create_social_clips(self, sermon_id: str, assigned_user: Optional[str] = None):
    """Create short social media clips from sermon"""

    supabase = get_supabase_client()

    try:
        if supabase and assigned_user:
            supabase.table("sermon_tasks").update(
                {
                    "status": "in_progress",
                    "started_at": datetime.now(timezone.utc).isoformat(),
                }
            ).eq("sermon_id", sermon_id).eq("task_type", "social_clip").execute()

        # Implementation would use FFmpeg to create short clips
        # This is a placeholder for the actual implementation

        return {"status": "completed", "clips": []}

    except Exception as e:
        logger.error(f"Social clip creation failed for {sermon_id}: {e}")
        _handle_task_failure(
            supabase, sermon_id, "social_clip", e, self.request.retries
        )
        raise


@app.task(bind=True, max_retries=2)
def auto_sort_sermon(self, sermon_id: str, metadata: Dict[str, Any]):
    """Auto-categorize sermon by series, topic, scripture"""

    supabase = get_supabase_client()

    try:
        series_title = metadata.get("series_title")
        theme_scripture = metadata.get("theme_scripture")
        main_themes = metadata.get("main_themes", [])

        # Find or create series
        if series_title and supabase:
            # Check if series exists
            series = (
                supabase.table("sermon_series")
                .select("id")
                .ilike("title", series_title)
                .execute()
            )

            if not series.data:
                # Create new series
                new_series = (
                    supabase.table("sermon_series")
                    .insert(
                        {
                            "title": series_title,
                            "church_id": supabase.table("sermons")
                            .select("church_id")
                            .eq("id", sermon_id)
                            .execute()
                            .data[0]
                            .get("church_id"),
                        }
                    )
                    .execute()
                )
                series_id = new_series.data[0]["id"] if new_series.data else None
            else:
                series_id = series.data[0]["id"]

            # Update sermon with series
            if series_id:
                supabase.table("sermons").update({"series_id": series_id}).eq(
                    "id", sermon_id
                ).execute()

        # Add tags
        if supabase:
            tags = metadata.get("suggested_tags", [])
            for tag in tags:
                supabase.table("sermon_tags").upsert(
                    {"sermon_id": sermon_id, "tag": tag}, on_conflict="sermon_id,tag"
                )

        return {"status": "completed"}

    except Exception as e:
        logger.error(f"Auto-sort failed for {sermon_id}: {e}")
        raise


@app.task(bind=True)
def finalize_sermon_pipeline(self, results: List[Dict], sermon_id: str):
    """Finalize pipeline when all tasks complete"""

    supabase = get_supabase_client()

    try:
        # Check all task statuses
        tasks = (
            supabase.table("sermon_tasks")
            .select("status")
            .eq("sermon_id", sermon_id)
            .execute()
        )

        statuses = [t["status"] for t in tasks.data]

        if all(s == "completed" for s in statuses):
            # All tasks complete
            supabase.table("sermons").update(
                {
                    "processing_status": "completed",
                    "pipeline_completed_at": datetime.now(timezone.utc).isoformat(),
                }
            ).eq("id", sermon_id).execute()

            logger.info(f"Sermon pipeline completed: {sermon_id}")

            # Trigger distribution if configured
            # distribute_sermon.delay(sermon_id)

        elif "failed" in statuses:
            # Some tasks failed
            supabase.table("sermons").update(
                {"processing_status": "partial_failure"}
            ).eq("id", sermon_id).execute()

        return {"sermon_id": sermon_id, "pipeline_status": "finalized"}

    except Exception as e:
        logger.error(f"Pipeline finalization failed: {e}")
        raise


# ==================== Helper Functions ====================
def _handle_task_failure(
    supabase, sermon_id: str, task_type: str, error: Exception, retry_count: int
):
    """Handle task failure with retry logic"""

    if supabase:
        max_retries = 3
        new_status = "pending" if retry_count < max_retries else "failed"

        supabase.table("sermon_tasks").update(
            {
                "status": new_status,
                "error_message": str(error),
                "retry_count": retry_count + 1,
            }
        ).eq("sermon_id", sermon_id).eq("task_type", task_type).execute()


# ==================== Celery Beat Schedule (for periodic tasks) ====================
app.conf.beat_schedule = {
    "cleanup-stale-tasks": {
        "task": "cleanup_stale_tasks",
        "schedule": 300.0,  # Every 5 minutes
    },
    "retry-failed-tasks": {
        "task": "retry_failed_tasks",
        "schedule": 600.0,  # Every 10 minutes
    },
}


@app.task
def cleanup_stale_tasks():
    """Mark tasks stuck in 'in_progress' for too long as pending"""
    supabase = get_supabase_client()
    if not supabase:
        return

    # Tasks in progress for more than 2 hours
    cutoff = datetime.now(timezone.utc)

    supabase.table("sermon_tasks").update(
        {
            "status": "pending",
            "assigned_to": None,  # Unassign so they can be re-picked up
        }
    ).eq("status", "in_progress").lt("started_at", cutoff.timestamp() - 7200).execute()


@app.task
def retry_failed_tasks():
    """Retry tasks that failed with retryable errors"""
    supabase = get_supabase_client()
    if not supabase:
        return

    failed_tasks = (
        supabase.table("sermon_tasks")
        .select("*")
        .eq("status", "failed")
        .lte("retry_count", 2)
        .execute()
    )

    for task in failed_tasks.data:
        task_type = task["task_type"]
        sermon_id = task["sermon_id"]

        # Re-queue based on task type
        task_map = {
            "transcription": transcribe_sermon,
            "video_processing": process_video,
            "location_tagging": extract_gps_location,
            "metadata_ai": analyze_sermon_metadata,
            "quality_optimization": optimize_quality,
            "thumbnail_generation": generate_thumbnails,
            "social_clip": create_social_clips,
        }

        if task_type in task_map:
            task_map[task_type].delay(sermon_id, task.get("assigned_to"))

            supabase.table("sermon_tasks").update(
                {"status": "pending", "retry_count": task.get("retry_count", 0) + 1}
            ).eq("id", task["id"]).execute()
