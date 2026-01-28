# ADR-003: Celery-Based Sermon Processing Pipeline

| ADR ID | Title | Status |
|--------|-------|--------|
| 003 | Celery-Based Sermon Processing Pipeline | Accepted |

## Context

Sermon processing in FileForge involves:
- File format conversion (transcoding)
- Metadata extraction (ID3, EXIF, etc.)
- AI transcription (Whisper)
- Speaker identification
- Thumbnail generation
- Search indexing

These are long-running, CPU-intensive tasks that shouldn't block the API.

## Decision

We use **Celery** with **Redis** as the message broker for async task processing.

### Pipeline Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Upload     │────▶│   Queue      │────▶│   Worker 1   │
│   Endpoint   │     │   (Redis)    │     │  (Extract)   │
└──────────────┘     └──────────────┘     └──────────────┘
                                                 │
                                                 ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Results    │◀────│   Storage    │◀────│   Worker 2   │
│   API        │     │   (S3)       │     │  (Transcribe)│
└──────────────┘     └──────────────┘     └──────────────┘
                                                 │
                                                 ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Webhook    │     │   Events     │     │   Worker 3   │
│   Callback   │     │   (Webhook)  │     │  (Index)     │
└──────────────┘     └──────────────┘     └──────────────┘
```

### Task Flow

```python
# tasks.py
from celery import Celery
from celery.exceptions import MaxRetriesExceededError

app = Celery('fileforge', broker='redis://localhost:6379/0')

@app.task(bind=True, max_retries=3)
def process_sermon(self, file_id: str):
    """Main sermon processing pipeline."""
    try:
        # Step 1: Extract metadata
        metadata = extract_metadata(file_id)
        
        # Step 2: Transcode if needed
        if needs_transcoding(metadata):
            transcoded = transcode_file(file_id)
        else:
            transcoded = file_id
        
        # Step 3: Transcribe audio
        transcript = transcribe_audio(transcoded)
        
        # Step 4: Identify speakers
        speakers = identify_speakers(transcoded)
        
        # Step 5: Generate thumbnails
        thumbnails = generate_thumbnails(transcoded)
        
        # Step 6: Update search index
        index_sermon(file_id, metadata, transcript, speakers)
        
        # Step 7: Notify completion
        notify_webhook(file_id, 'completed')
        
        return {'status': 'completed', 'file_id': file_id}
    
    except TransientError as e:
        self.retry(exc=e, countdown=60)
```

## Consequences

### Positive

- **Scalability**: Add workers horizontally
- **Reliability**: Automatic retries for failures
- **Observability**: Celery flower for monitoring
- **Flexibility**: Task priorities, rate limiting
- **Distribution**: Workers can run on separate machines

### Negative

- **Complexity**: Additional infrastructure
- **Latency**: Async means delayed results
- **Failure modes**: Distributed systems complexity
- **Monitoring**: Need to track task states

## Implementation

### Celery Configuration

```python
# celery_config.py
broker_url = 'redis://localhost:6379/0'
result_backend = 'redis://localhost:6379/1'

task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']

timezone = 'UTC'
enable_utc = True

task_routes = {
    'tasks.extract_metadata': {'queue': 'metadata'},
    'tasks.transcribe': {'queue': 'ai'},
    'tasks.identify_speaker': {'queue': 'ai'},
    'tasks.generate_thumbnails': {'queue': 'media'},
}

task_acks_late = True
worker_prefetch_multiplier = 1

task_soft_time_limit = 3600  # 1 hour
task_time_limit = 4000  # 1 hour + buffer
```

### Scaling Workers

```bash
# Scale metadata workers
celery -A fileforge worker -Q metadata --concurrency=4

# Scale AI workers (GPU recommended)
celery -A fileforge worker -Q ai --concurrency=2

# Scale media workers
celery -A fileforge worker -Q media --concurrency=4
```

### Monitoring with Flower

```bash
# Start flower
celery -A fileforge flower --port=5555

# Access at http://localhost:5555
```

## Date

2024-01-15
