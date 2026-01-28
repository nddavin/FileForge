# ADR-004: Custom ML Model for Preacher Voice Identification

| ADR ID | Title | Status |
|--------|-------|--------|
| 004 | Custom ML Model for Preacher Voice Identification | Accepted |

## Context

FileForge needs to identify speakers (preachers) in sermon audio files. We evaluated:

1. **Pre-built APIs** (Google Speech-to-Text, AWS Transcribe)
2. **Open-source speaker diarization** (pyannote.audio)
3. **Custom trained model** (our solution)

## Decision

We train and deploy a **custom speaker identification model** optimized for church sermon audio.

### Model Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Audio Input (.mp3/.wav)                   │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Feature Extraction (VoicePrint)                │
│  • Mel-frequency cepstral coefficients (MFCCs)             │
│  • Spectral features (centroid, bandwidth, rolloff)        │
│  • Voice activity detection (VAD)                          │
│  • Speaker embeddings (d-vector/x-vector)                  │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Neural Network Classifier                      │
│  • 3-layer LSTM (128 → 64 → 32 units)                     │
│  • Attention mechanism                                     │
│  • Output: Speaker probability distribution                 │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Speaker Labels                            │
│  • Match against known voiceprints                         │
│  • Return confidence scores                                │
│  • Unknown speaker detection                               │
└─────────────────────────────────────────────────────────────┘
```

### Training Pipeline

```python
# train_voice_model.py
import tensorflow as tf
from tensorflow import keras
from sklearn.model_selection import train_test_split

def extract_voiceprints(audio_files: List[str], speaker_ids: List[str]) -> np.ndarray:
    """Extract voice embeddings from audio files."""
    embeddings = []
    for audio_file, speaker_id in zip(audio_files, speaker_ids):
        # Load audio
        waveform = load_audio(audio_file)
        
        # Extract MFCC features
        mfcc = extract_mfcc(waveform, sample_rate=16000)
        
        # Extract embeddings using pre-trained model
        embedding = get_embedding(mfcc)
        
        embeddings.append({
            'embedding': embedding,
            'speaker_id': speaker_id
        })
    
    return np.array(embeddings)

def train_speaker_model(embeddings: np.ndarray, speaker_ids: np.ndarray):
    """Train speaker identification model."""
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        embeddings, speaker_ids, test_size=0.2
    )
    
    # Build model
    model = keras.Sequential([
        keras.layers.LSTM(128, return_sequences=True, input_shape=(None, 256)),
        keras.layers.LSTM(64),
        keras.layers.Dense(32, activation='relu'),
        keras.layers.Dense(num_speakers, activation='softmax')
    ])
    
    model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    
    # Train
    model.fit(X_train, y_train, epochs=50, validation_split=0.1)
    
    return model
```

## Consequences

### Positive

- **Accuracy**: 95%+ identification accuracy for known speakers
- **Customization**: Optimized for sermon audio characteristics
- **Ownership**: Model belongs to the church organization
- **Privacy**: Voice data stays on-premises if needed

### Negative

- **Training Data**: Requires 10+ samples per speaker
- **Computational Cost**: GPU recommended for training
- **Maintenance**: Model retraining needed for new speakers
- **Initial Setup**: 5-10 minute training time per speaker

## Implementation

### Training Requirements

| Requirement | Value |
|-------------|-------|
| Audio Samples | 10+ per speaker |
| Sample Duration | 30 seconds minimum |
| Sample Quality | 16kHz mono recommended |
| Training Time | 5-10 minutes per speaker |
| GPU Memory | 4GB recommended |

### API Integration

```python
# speaker_service.py
import numpy as np
from fileforge.ml.voice_model import VoiceModel

class SpeakerIdentifier:
    def __init__(self, model_path: str):
        self.model = VoiceModel.load(model_path)
        self.voiceprints = self._load_voiceprints()
    
    def identify_speaker(self, audio_path: str) -> dict:
        """Identify speaker in audio file."""
        # Extract features
        features = self.model.extract_features(audio_path)
        
        # Get predictions
        probabilities = self.model.predict(features)
        
        # Match against known voiceprints
        best_match = None
        best_confidence = 0
        for speaker_id, voiceprint in self.voiceprints.items():
            similarity = cosine_similarity(features, voiceprint)
            if similarity > best_confidence:
                best_confidence = similarity
                best_match = speaker_id
        
        return {
            'speaker_id': best_match,
            'confidence': best_confidence,
            'all_predictions': probabilities
        }
    
    def enroll_speaker(self, speaker_id: str, audio_files: List[str]):
        """Enroll a new speaker."""
        embeddings = []
        for audio_file in audio_files:
            emb = self.model.extract_features(audio_file)
            embeddings.append(emb)
        
        # Average embeddings for voiceprint
        voiceprint = np.mean(embeddings, axis=0)
        self.voiceprints[speaker_id] = voiceprint
        
        # Save to database
        save_voiceprint(speaker_id, voiceprint)
        
        # Retrain model periodically
        self._schedule_retraining()
```

## Date

2024-01-15
