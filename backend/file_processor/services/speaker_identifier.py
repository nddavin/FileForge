"""Speaker ID - Diarization, Voice Biometrics, Language Detection"""

import json  # noqa: F401
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from pathlib import Path  # noqa: F401
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SpeakerSegment:
    """Individual speaker segment"""
    start_time: float
    end_time: float
    speaker_id: Optional[str] = None
    speaker_name: Optional[str] = None
    confidence: float = 0.0
    language: Optional[str] = None
    embedding: Optional[List[float]] = None


@dataclass
class SpeakerIdentificationResult:
    """Complete speaker ID result"""
    primary_preacher_id: Optional[str] = None
    primary_preacher_name: Optional[str] = None
    segments: List[SpeakerSegment] = field(default_factory=list)
    speaker_stats: Dict[str, Any] = field(default_factory=dict)
    language_distribution: Dict[str, float] = field(default_factory=dict)
    total_speakers: int = 0
    unidentified_segments: int = 0


class SermonSpeakerIdentifier:
    """Speaker identification with diarization and voice biometrics"""
    
    # Supported languages for local detection
    SUPPORTED_LANGUAGES = ['en', 'lg', 'sw', 'fr', 'de', 'es', 'pt', 'it']
    
    def __init__(self, hf_token: Optional[str] = None):
        self.device = "cuda" if self._has_cuda() else "cpu"
        self.hf_token = hf_token
        self._diarization_pipeline = None
        self._speaker_encoder = None
        self._whisper_model = None
    
    def _has_cuda(self) -> bool:
        """Check if CUDA is available"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    def _load_diarization(self):
        """Load pyannote diarization pipeline"""
        try:
            from pyannote.audio import Pipeline
            self._diarization_pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=self.hf_token
            ).to(self.device)
            logger.info("Loaded pyannote diarization pipeline")
        except ImportError:
            logger.warning("pyannote.audio not installed, using fallback")
        except Exception as e:
            logger.error(f"Failed to load diarization: {e}")
    
    def _load_speaker_encoder(self):
        """Load speechbrain speaker encoder"""
        try:
            from speechbrain.inference.speaker import EncoderClassifier
            self._speaker_encoder = EncoderClassifier.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceleb"
            ).to(self.device)
            logger.info("Loaded speechbrain speaker encoder")
        except ImportError:
            logger.warning("speechbrain not installed, using simple embeddings")
        except Exception as e:
            logger.error(f"Failed to load speaker encoder: {e}")
    
    def _load_whisper(self):
        """Load Whisper model for transcription"""
        try:
            import whisper
            self._whisper_model = whisper.load_model("base")
            logger.info("Loaded Whisper model")
        except ImportError:
            logger.warning("openai-whisper not installed")
        except Exception as e:
            logger.error(f"Failed to load Whisper: {e}")
    
    async def identify_speakers(
        self, 
        audio_path: str, 
        church_team: List[Dict[str, Any]],
        known_voiceprints: Optional[Dict[str, List[float]]] = None
    ) -> SpeakerIdentificationResult:
        """Complete speaker identification pipeline"""
        
        # Lazy load models
        if self._diarization_pipeline is None:
            self._load_diarization()
        if self._speaker_encoder is None:
            self._load_speaker_encoder()
        if self._whisper_model is None:
            self._load_whisper()
        
        result = SpeakerIdentificationResult()
        
        try:
            # Step 1: Diarize audio (who speaks when)
            if self._diarization_pipeline:
                diarization = self._diarization_pipeline(audio_path)
                turns = list(diarization.itertracks(yield_label=True))
            else:
                # Fallback: simple VAD-based segmentation
                turns = await self._fallback_diarization(audio_path)
            
            # Step 2: Load known preacher voiceprints
            embeddings_dict = known_voiceprints or {}
            
            # Step 3: Process each segment
            for turn, _, speaker_label in turns:
                segment_audio = await self._extract_segment(audio_path, turn.start, turn.end)
                
                # Get embedding
                embedding = self._get_embedding(segment_audio)
                
                # Detect language
                language = await self._detect_language(segment_audio)
                
                # Match to known preacher
                match = self._match_speaker(embedding, embeddings_dict)
                
                segment = SpeakerSegment(
                    start_time=turn.start,
                    end_time=turn.end,
                    speaker_id=match.get('id'),
                    confidence=match.get('confidence', 0.0),
                    language=language,
                    embedding=embedding.tolist() if embedding is not None else None
                )
                
                result.segments.append(segment)
            
            # Step 4: Determine primary preacher (most speaking time)
            primary = self._get_primary_speaker(result.segments, church_team)
            result.primary_preacher_id = primary.get('id')
            result.primary_preacher_name = primary.get('name')
            
            # Step 5: Calculate speaker stats
            result.speaker_stats = self._calculate_speaker_stats(result.segments, church_team)
            
            # Step 6: Language distribution
            result.language_distribution = self._calculate_language_distribution(result.segments)
            
            # Count unidentified
            result.unidentified_segments = sum(
                1 for s in result.segments if s.speaker_id is None
            )
            result.total_speakers = len(set(
                s.speaker_id for s in result.segments if s.speaker_id
            ))
            
            return result
        
        except Exception as e:
            logger.error(f"Speaker identification failed: {e}")
            return result
    
    async def _fallback_diarization(self, audio_path: str) -> List:
        """Fallback VAD-based segmentation when pyannote unavailable"""
        try:
            import librosa
            import torch
            
            # Load audio
            y, sr = librosa.load(audio_path, sr=16000)
            
            # Simple energy-based VAD
            energy = np.abs(y)
            threshold = np.mean(energy) + 2 * np.std(energy)
            speech_mask = energy > threshold
            
            # Find speech segments
            segments = []
            in_speech = False
            start = 0
            
            for i, is_speech in enumerate(speech_mask):
                if is_speech and not in_speech:
                    start = i / sr
                    in_speech = True
                elif not is_speech and in_speech:
                    segments.append((start, i / sr, f"speaker_{len(segments)}"))
                    in_speech = False
            
            if in_speech:
                segments.append((start, len(y) / sr, f"speaker_{len(segments)}"))
            
            # Create mock turn objects
            class MockTurn:
                def __init__(self, start, end):
                    self.start = start
                    self.end = end
            
            class MockTrack:
                def __init__(self, start, end, label):
                    self.start = MockTurn(start, end)
                    self.end = None
                    self.label = label
            
            return [MockTrack(s, e, l) for s, e, l in segments]
        
        except Exception as e:
            logger.error(f"Fallback diarization failed: {e}")
            return []
    
    def _get_embedding(self, audio_segment) -> Optional[np.ndarray]:
        """Extract speaker embedding from audio segment"""
        if self._speaker_encoder is not None:
            try:
                if isinstance(audio_segment, str):
                    import librosa
                    waveform, _ = librosa.load(audio_segment, sr=16000)
                else:
                    waveform = audio_segment
                
                # Ensure correct shape [batch, time]
                if waveform.ndim == 1:
                    waveform = waveform[np.newaxis, :]
                
                with torch.no_grad():
                    embedding = self._speaker_encoder.encode_batch(
                        torch.from_numpy(waveform).to(self.device)
                    )
                
                return embedding.cpu().numpy().squeeze()
            
            except Exception as e:
                logger.error(f"Embedding extraction failed: {e}")
        
        return None
    
    def _match_speaker(
        self, 
        test_embedding: np.ndarray, 
        known_embeddings: Dict[str, List[float]]
    ) -> Dict[str, Any]:
        """Cosine similarity matching against known preachers"""
        if test_embedding is None or not known_embeddings:
            return {'id': None, 'confidence': 0.0}
        
        best_match = {'id': None, 'confidence': 0.0}
        threshold = 0.75  # Similarity threshold
        
        test_emb = test_embedding / np.linalg.norm(test_embedding)
        
        for preacher_id, emb_list in known_embeddings.items():
            known_emb = np.array(emb_list)
            known_emb = known_emb / np.linalg.norm(known_emb)
            
            similarity = np.dot(test_emb, known_emb)
            
            if similarity > best_match['confidence'] and similarity > threshold:
                best_match = {'id': preacher_id, 'confidence': float(similarity)}
        
        return best_match if best_match['confidence'] > 0.7 else {'id': None}
    
    async def _detect_language(self, audio_segment) -> str:
        """Detect language from 5-second audio segment"""
        try:
            if self._whisper_model is None:
                self._load_whisper()
            
            if self._whisper_model:
                # Transcribe segment
                result = self._whisper_model.transcribe(audio_segment)
                text = result.get('text', '')
                
                if text.strip():
                    # Use langdetect for language probabilities
                    try:
                        from langdetect import detect_langs
                        langs = detect_langs(text)
                        if langs:
                            return langs[0].lang
                    except Exception:
                        pass
                    
                    # Fallback to Whisper's detected language
                    if result.get('language'):
                        return result['language'][:2]
            
            return 'unknown'
        
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return 'unknown'
    
    async def _extract_segment(
        self, 
        audio_path: str, 
        start: float, 
        end: float
    ) -> str:
        """Extract audio segment to temp file"""
        import tempfile
        import subprocess
        
        temp_path = tempfile.mktemp(suffix='.wav')
        
        try:
            subprocess.run([
                'ffmpeg', '-y', '-i', audio_path,
                '-ss', str(start), '-to', str(end),
                '-ar', '16000', '-ac', '1', temp_path
            ], capture_output=True, check=True)
            
            return temp_path
        
        except subprocess.CalledProcessError:
            # Return original path if ffmpeg fails
            return audio_path
    
    def _get_primary_speaker(
        self, 
        segments: List[SpeakerSegment],
        church_team: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Determine primary preacher (most speaking time)"""
        speaker_times = {}
        
        for segment in segments:
            if segment.speaker_id:
                duration = segment.end_time - segment.start_time
                speaker_times[segment.speaker_id] = (
                    speaker_times.get(segment.speaker_id, 0) + duration
                )
        
        if not speaker_times:
            return {'id': None, 'name': None}
        
        # Get speaker with most speaking time
        primary_id = max(speaker_times, key=speaker_times.get)
        
        # Get speaker name
        primary_name = None
        for member in church_team:
            if member.get('id') == primary_id:
                primary_name = member.get('full_name') or member.get('name')
                break
        
        return {'id': primary_id, 'name': primary_name}
    
    def _calculate_speaker_stats(
        self, 
        segments: List[SpeakerSegment],
        church_team: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate speaking time statistics per speaker"""
        speaker_times = {}
        speaker_confidences = {}
        
        name_map = {
            m.get('id'): m.get('full_name') or m.get('name') 
            for m in church_team
        }
        
        for segment in segments:
            sid = segment.speaker_id or 'unknown'
            duration = segment.end_time - segment.start_time
            
            speaker_times[sid] = speaker_times.get(sid, 0) + duration
            speaker_confidences[sid] = speaker_confidences.get(sid, []) + [segment.confidence]
        
        stats = {}
        for sid, duration in speaker_times.items():
            stats[sid] = {
                'name': name_map.get(sid, 'Unknown'),
                'speaking_time_seconds': round(duration, 2),
                'speaking_time_formatted': self._format_duration(duration),
                'confidence_avg': round(np.mean(speaker_confidences.get(sid, [0])), 2),
                'segment_count': len([s for s in segments if s.speaker_id == sid])
            }
        
        return stats
    
    def _calculate_language_distribution(
        self, 
        segments: List[SpeakerSegment]
    ) -> Dict[str, float]:
        """Calculate percentage of speaking time per language"""
        total_time = sum(
            s.end_time - s.start_time for s in segments
        )
        
        if total_time == 0:
            return {}
        
        lang_time = {}
        
        for segment in segments:
            lang = segment.language or 'unknown'
            duration = segment.end_time - segment.start_time
            lang_time[lang] = lang_time.get(lang, 0) + duration
        
        return {
            lang: round((time / total_time) * 100, 1)
            for lang, time in lang_time.items()
        }
    
    def _format_duration(self, seconds: float) -> str:
        """Format seconds to HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"


class VoiceprintManager:
    """Manage preacher voiceprints in Supabase"""
    
    def __init__(self):
        self.supabase = None
        self.identifier = SermonSpeakerIdentifier()
    
    def _get_supabase(self):
        """Lazy Supabase init"""
        if self.supabase is None:
            import os
            from supabase import Client
            
            url = os.getenv('SUPABASE_URL')
            key = os.getenv('SUPABASE_SERVICE_KEY')
            
            if url and key:
                self.supabase = Client(url, key)
        
        return self.supabase
    
    async def register_preacher_voiceprint(
        self, 
        preacher_id: str, 
        audio_paths: List[str]
    ) -> Dict[str, Any]:
        """Register new preacher with voice samples"""
        
        supabase = self._get_supabase()
        if not supabase:
            return {'status': 'error', 'message': 'Supabase not configured'}
        
        try:
            embeddings = []
            
            for audio_path in audio_paths:
                # Get embedding for each sample
                emb = self.identifier._get_embedding(audio_path)
                if emb is not None:
                    embeddings.append(emb.tolist())
            
            if not embeddings:
                return {'status': 'error', 'message': 'No valid embeddings'}
            
            # Average embeddings for robustness
            avg_embedding = np.mean(embeddings, axis=0).tolist()
            
            # Store in Supabase
            supabase.table('preacher_voiceprints').upsert({
                'preacher_id': preacher_id,
                'embedding': avg_embedding,
                'sample_count': len(audio_paths),
                'created_at': datetime.now(timezone.utc).isoformat()
            }, on_conflict='preacher_id').execute()
            
            return {
                'status': 'success',
                'preacher_id': preacher_id,
                'samples_registered': len(audio_paths)
            }
        
        except Exception as e:
            logger.error(f"Voiceprint registration failed: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def load_voiceprints(self, church_id: str) -> Dict[str, List[float]]:
        """Load all voiceprints for a church"""
        
        supabase = self._get_supabase()
        if not supabase:
            return {}
        
        try:
            result = supabase.table('preacher_voiceprints').select(
                'preacher_id, embedding'
            ).execute()
            
            return {
                r['preacher_id']: r['embedding']
                for r in result.data
                if r.get('embedding')
            }
        
        except Exception as e:
            logger.error(f"Failed to load voiceprints: {e}")
            return {}
    
    async def delete_voiceprint(self, preacher_id: str) -> Dict[str, Any]:
        """Delete preacher voiceprint"""
        
        supabase = self._get_supabase()
        if not supabase:
            return {'status': 'error'}
        
        try:
            supabase.table('preacher_voiceprints').delete().eq(
                'preacher_id', preacher_id
            ).execute()
            
            return {'status': 'success'}
        
        except Exception as e:
            logger.error(f"Voiceprint deletion failed: {e}")
            return {'status': 'error', 'message': str(e)}


# ==================== Supabase SQL Schema ====================
"""
-- Run in Supabase SQL Editor:

-- Add columns to sermons table
ALTER TABLE sermons ADD COLUMN primary_preacher_id UUID REFERENCES profiles(id);
ALTER TABLE sermons ADD COLUMN primary_language TEXT;
ALTER TABLE sermons ADD COLUMN language_distribution JSONB DEFAULT '{}';
ALTER TABLE sermons ADD COLUMN speaker_stats JSONB DEFAULT '{}';
ALTER TABLE sermons ADD COLUMN speaker_confidence_avg FLOAT DEFAULT 0;

-- Create speaker segments table
CREATE TABLE sermon_speaker_segments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sermon_id UUID REFERENCES sermons(id) ON DELETE CASCADE,
    speaker_id UUID REFERENCES profiles(id),
    start_time FLOAT NOT NULL,
    end_time FLOAT NOT NULL,
    confidence FLOAT,
    language TEXT,
    embedding JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_speaker_segments_sermon ON sermon_speaker_segments(sermon_id);
CREATE INDEX idx_speaker_segments_speaker ON sermon_speaker_segments(speaker_id);

-- Create preacher voiceprints table
CREATE TABLE preacher_voiceprints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    preacher_id UUID REFERENCES profiles(id) UNIQUE,
    embedding JSONB NOT NULL,
    sample_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- RLS Policies
ALTER TABLE sermon_speaker_segments ENABLE ROW LEVEL SECURITY;
ALTER TABLE preacher_voiceprints ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Team views speaker segments" ON sermon_speaker_segments
    FOR SELECT USING (auth.role() IN ('media_team', 'admin', 'super_admin'));

CREATE POLICY "Admins manage voiceprints" ON preacher_voiceprints
    FOR ALL USING (auth.role() IN ('admin', 'super_admin'));
"""


# ==================== Convenience Functions ====================

async def identify_sermon_speakers(
    audio_path: str,
    church_id: str,
    supabase_client = None
) -> SpeakerIdentificationResult:
    """Convenience function for full speaker ID pipeline"""
    
    identifier = SermonSpeakerIdentifier()
    
    # Load church team
    if supabase_client is None:
        voiceprint_manager = VoiceprintManager()
        supabase_client = voiceprint_manager._get_supabase()
    
    if supabase_client:
        try:
            team = supabase_client.table('profiles').select(
                'id, full_name'
            ).eq('church_id', church_id).eq('role', 'preacher').execute()
            church_team = team.data or []
            
            # Load known voiceprints
            voiceprints = await voiceprint_manager.load_voiceprints(church_id)
            
            # Run identification
            return await identifier.identify_speakers(audio_path, church_team, voiceprints)
        
        except Exception as e:
            logger.error(f"Sermon speaker ID failed: {e}")
    
    return SpeakerIdentificationResult()


def detect_language_simple(text: str) -> str:
    """Simple language detection from text"""
    try:
        from langdetect import detect_langs
        langs = detect_langs(text)
        return langs[0].lang if langs else 'unknown'
    except Exception:
        return 'unknown'
