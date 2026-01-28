"""Custom Preacher Voice Model Training - Fine-tuned ECAPA-TDNN"""

import os
import logging  # noqa: F401
import json  # noqa: F401
from pathlib import Path  # noqa: F401
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

import torch
import torch.nn as nn
import torchaudio
from torch.utils.data import Dataset, DataLoader
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:  # noqa: N801
    """Training configuration"""

    data_dir: str = "backend/data/preacher_voices"
    model_output_path: str = "backend/models/preacher_classifier.pt"
    sample_rate: int = 16000
    n_mels: int = 80
    n_fft: int = 400
    hop_length: int = 160
    batch_size: int = 8
    epochs: int = 50
    learning_rate: float = 0.001
    num_workers: int = 4
    use_cuda: bool = torch.cuda.is_available()
    pretrained_source: str = "speechbrain/spkrec-ecapa-voxceleb"


class PreacherDataset(Dataset):
    """Dataset for preacher voice samples"""

    def __init__(
        self,
        data_dir: str,
        sample_rate: int = 16000,
        transform=None,
        label_encoder: Optional[LabelEncoder] = None,
    ):
        self.data_dir = Path(data_dir)
        self.sample_rate = sample_rate
        self.transform = transform
        self.files: List[str] = []
        self.labels: List[int] = []
        self.preacher_names: List[str] = []

        # Get all preacher directories
        if not self.data_dir.exists():
            raise ValueError(f"Data directory not found: {data_dir}")

        preachers = [d for d in self.data_dir.iterdir() if d.is_dir()]

        if label_encoder is None:
            self.label_encoder = LabelEncoder()
            self.label_encoder.fit([p.name for p in preachers])
        else:
            self.label_encoder = label_encoder

        for preacher_dir in preachers:
            wav_files = list(preacher_dir.glob("*.wav"))
            wav_files.extend(preacher_dir.glob("*.mp3"))
            wav_files.extend(preacher_dir.glob("*.flac"))
            wav_files.extend(preacher_dir.glob("*.m4a"))

            for wav_file in wav_files:
                self.files.append(str(wav_file))
                self.labels.append(self.label_encoder.transform([preacher_dir.name])[0])
                self.preacher_names.append(preacher_dir.name)

        logger.info(f"Loaded {len(self.files)} samples from {len(preachers)} preachers")

    def __len__(self) -> int:
        return len(self.files)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, str]:
        file_path = self.files[idx]
        label = self.labels[idx]
        preacher_name = self.preacher_names[idx]

        # Load audio
        try:
            waveform, sr = torchaudio.load(file_path)
        except Exception as e:
            logger.warning(f"Failed to load {file_path}: {e}")
            # Return zeros if file fails
            waveform = torch.zeros(1, self.sample_rate)
            sr = self.sample_rate

        # Resample if needed
        if sr != self.sample_rate:
            resampler = torchaudio.transforms.Resample(sr, self.sample_rate)
            waveform = resampler(waveform)

        # Trim or pad to 3 seconds
        target_length = self.sample_rate * 3
        if waveform.shape[1] > target_length:
            # Random crop
            start = torch.randint(0, waveform.shape[1] - target_length, (1,)).item()
            waveform = waveform[:, start : start + target_length]
        elif waveform.shape[1] < target_length:
            # Pad
            pad_length = target_length - waveform.shape[1]
            waveform = torch.nn.functional.pad(waveform, (0, pad_length))

        # Extract mel spectrogram
        mel_transform = torchaudio.transforms.MelSpectrogram(
            sample_rate=self.sample_rate, n_mels=80, n_fft=400, hop_length=160
        )
        mel_spec = mel_transform(waveform)
        mel_spec = torch.log(mel_spec + 1e-9)  # Log scale

        # Normalize
        if self.transform:
            mel_spec = self.transform(mel_spec)

        return mel_spec.squeeze(0), torch.tensor(label, dtype=torch.long), preacher_name


def get_collate_fn():
    """Custom collate function for variable length spectrograms"""

    def collate_fn(batch):
        mel_specs, labels, names = zip(*batch)

        # Pad mel spectrograms
        max_len = max(m.shape[1] for m in mel_specs)
        padded_mels = []

        for mel in mel_specs:
            if mel.shape[1] < max_len:
                pad = torch.zeros(mel.shape[0], max_len - mel.shape[1])
                mel = torch.cat([mel, pad], dim=1)
            padded_mels.append(mel)

        return torch.stack(padded_mels), torch.stack(labels), names

    return collate_fn


class ECAPAClassifier(nn.Module):
    """ECAPA-TDNN based classifier for preacher identification"""

    def __init__(
        self,
        num_classes: int,
        pretrained_source: str = "speechbrain/spkrec-ecapa-voxceleb",
    ):
        super().__init__()

        # Load pretrained ECAPA-TDNN encoder
        try:
            from speechbrain.pretrained import EncoderClassifier

            self.encoder = EncoderClassifier.from_hparams(
                source=pretrained_source,
                savedir="pretrained_models/spkrec-ecapa-voxceleb",
            )
            # Get embedding dimension
            emb_dim = (
                self.encoder.modules.encoder.emb.shape[1]
                if hasattr(self.encoder.modules.encoder, "emb")
                else 192
            )
            self.embedding_dim = emb_dim
        except Exception as e:
            logger.warning(f"Failed to load pretrained model: {e}")
            self.embedding_dim = 192
            self.encoder = None

        # Classifier head
        self.classifier = nn.Sequential(
            nn.BatchNorm1d(self.embedding_dim),
            nn.Linear(self.embedding_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.BatchNorm1d(256),
            nn.Linear(256, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: [batch, channels, n_mels, time]

        if self.encoder is not None:
            # Get embeddings
            with torch.no_grad():
                embeddings = self.encoder.encode_batch(x)
                embeddings = embeddings.squeeze(-1).squeeze(-1)  # [batch, emb_dim]

            # Freeze encoder for fine-tuning
            for param in self.encoder.parameters():
                param.requires_grad = False
        else:
            # Fallback: simple CNN
            x = x.mean(dim=1)  # [batch, n_mels, time]
            x = x.permute(0, 2, 1)  # [batch, time, n_mels]
            x = torch.nn.functional.adaptive_avg_pool1d(x, 64)
            embeddings = x.flatten(1)

        return self.classifier(embeddings)

    def get_embeddings(self, x: torch.Tensor) -> torch.Tensor:
        """Get embeddings for verification"""
        if self.encoder is not None:
            with torch.no_grad():
                embeddings = self.encoder.encode_batch(x)
                return embeddings.squeeze(-1).squeeze(-1)
        else:
            x = x.mean(dim=1)
            x = x.permute(0, 2, 1)
            x = torch.nn.functional.adaptive_avg_pool1d(x, 64)
            return x.flatten(1)


class PreacherVoiceTrainer:
    """Trainer for custom preacher voice models"""

    def __init__(self, config: TrainingConfig = None):
        self.config = config or TrainingConfig()
        self.device = torch.device("cuda" if self.config.use_cuda else "cpu")
        self.model: Optional[ECAPAClassifier] = None
        self.label_encoder: Optional[LabelEncoder] = None

    def prepare_data(self, data_dir: str = None) -> Tuple[Dataset, Dataset]:
        """Prepare train/validation datasets"""
        data_dir = data_dir or self.config.data_dir

        # Create full dataset
        full_dataset = PreacherDataset(
            data_dir, self.config.sample_rate, label_encoder=None
        )

        self.label_encoder = full_dataset.label_encoder

        # Split into train/val
        train_idx, val_idx = train_test_split(
            range(len(full_dataset)), test_size=0.2, stratify=full_dataset.labels
        )

        train_dataset = torch.utils.data.Subset(full_dataset, train_idx)
        val_dataset = torch.utils.data.Subset(full_dataset, val_idx)

        return train_dataset, val_dataset

    def train(self, train_dataset: Dataset, val_dataset: Dataset = None) -> Dict:
        """Train the model"""

        num_classes = len(self.label_encoder.classes_)
        self.model = ECAPAClassifier(num_classes, self.config.pretrained_source)
        self.model.to(self.device)

        # Create data loaders
        train_loader = DataLoader(
            train_dataset,
            batch_size=self.config.batch_size,
            shuffle=True,
            collate_fn=get_collate_fn(),
            num_workers=self.config.num_workers,
        )

        val_loader = None
        if val_dataset:
            val_loader = DataLoader(
                val_dataset,
                batch_size=self.config.batch_size,
                shuffle=False,
                collate_fn=get_collate_fn(),
                num_workers=self.config.num_workers,
            )

        # Training setup
        optimizer = torch.optim.Adam(
            filter(lambda p: p.requires_grad, self.model.parameters()),
            lr=self.config.learning_rate,
        )
        scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=20, gamma=0.5)
        criterion = nn.CrossEntropyLoss()

        # Training loop
        history = {"train_loss": [], "val_loss": [], "val_accuracy": []}

        for epoch in range(self.config.epochs):
            # Training
            self.model.train()
            train_loss = 0.0
            train_correct = 0
            train_total = 0

            for mel_specs, labels, _ in train_loader:
                mel_specs = mel_specs.to(self.device)
                labels = labels.to(self.device)

                optimizer.zero_grad()
                outputs = self.model(mel_specs)
                loss = criterion(outputs, labels)

                loss.backward()
                optimizer.step()

                train_loss += loss.item()
                _, predicted = outputs.max(1)
                train_total += labels.size(0)
                train_correct += predicted.eq(labels).sum().item()

            train_loss /= len(train_loader)
            train_acc = 100.0 * train_correct / train_total

            # Validation
            val_loss = 0.0
            val_correct = 0
            val_total = 0

            if val_loader:
                self.model.eval()
                with torch.no_grad():
                    for mel_specs, labels, _ in val_loader:
                        mel_specs = mel_specs.to(self.device)
                        labels = labels.to(self.device)

                        outputs = self.model(mel_specs)
                        loss = criterion(outputs, labels)

                        val_loss += loss.item()
                        _, predicted = outputs.max(1)
                        val_total += labels.size(0)
                        val_correct += predicted.eq(labels).sum().item()

                val_loss /= len(val_loader)
                val_acc = 100.0 * val_correct / val_total

                history["val_loss"].append(val_loss)
                history["val_accuracy"].append(val_acc)

            history["train_loss"].append(train_loss)

            scheduler.step()

            logger.info(
                f"Epoch {epoch+1}/{self.config.epochs} - "
                f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.1f}% "
                f"{f'- Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.1f}%' if val_loader else ''}"
            )

        return history

    def save_model(self, path: str = None) -> str:
        """Save trained model and metadata"""
        path = path or self.config.model_output_path
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        checkpoint = {
            "model_state_dict": self.model.state_dict(),
            "label_encoder_classes": self.label_encoder.classes_.tolist(),
            "config": {
                "sample_rate": self.config.sample_rate,
                "n_mels": self.config.n_mels,
                "n_fft": self.config.n_fft,
                "hop_length": self.config.hop_length,
            },
            "num_classes": len(self.label_encoder.classes_),
        }

        torch.save(checkpoint, path)
        logger.info(f"Model saved to {path}")
        return path

    def load_model(self, path: str) -> "ECAPAClassifier":
        """Load trained model"""
        checkpoint = torch.load(path, map_location=self.device)

        self.label_encoder = LabelEncoder()
        self.label_encoder.classes_ = np.array(checkpoint["label_encoder_classes"])

        self.model = ECAPAClassifier(
            checkpoint["num_classes"], self.config.pretrained_source
        )
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.model.to(self.device)
        self.model.eval()

        return self.model

    def evaluate(self, test_dataset: Dataset) -> Dict:
        """Evaluate model on test set"""
        if not self.model:
            raise ValueError("Model not trained or loaded")

        self.model.eval()
        test_loader = DataLoader(
            test_dataset,
            batch_size=self.config.batch_size,
            shuffle=False,
            collate_fn=get_collate_fn(),
        )

        all_preds = []
        all_labels = []
        all_names = []

        with torch.no_grad():
            for mel_specs, labels, names in test_loader:
                mel_specs = mel_specs.to(self.device)
                outputs = self.model(mel_specs)
                _, predicted = outputs.max(1)

                all_preds.extend(predicted.cpu().numpy())
                all_labels.extend(labels.numpy())
                all_names.extend(names)

        # Calculate metrics
        from sklearn.metrics import classification_report, confusion_matrix

        report = classification_report(
            all_labels,
            all_preds,
            target_names=self.label_encoder.classes_,
            output_dict=True,
        )

        return {
            "accuracy": report["accuracy"],
            "per_class": report,
            "confusion_matrix": confusion_matrix(all_labels, all_preds).tolist(),
            "predictions": list(
                zip(all_names, [self.label_encoder.classes_[p] for p in all_preds])
            ),
        }


class ContinuousLearningTrainer:
    """Continuous learning from confirmed identifications"""

    def __init__(self, model_path: str, supabase_client=None):
        self.base_model_path = model_path
        self.supabase = supabase_client
        self.trainer = PreacherVoiceTrainer()

    def collect_training_data(
        self, min_confidence: float = 0.9, limit_per_preacher: int = 50
    ) -> Tuple[List[str], List[str]]:
        """Collect confirmed identifications from database"""

        if not self.supabase:
            logger.warning("Supabase not configured, using local data")
            return [], []

        try:
            # Get confirmed sermons
            result = (
                self.supabase.table("sermons")
                .select(
                    "id, audio_path, primary_preacher_id, primary_preacher:profiles!primary_preacher_id_fkey(full_name)"
                )
                .gte("speaker_confidence_avg", min_confidence)
                .execute()
            )

            files = []
            labels = []

            for row in result.data:
                if row.get("audio_path") and row.get("primary_preacher_id"):
                    # Limit per preacher
                    preacher_files = [
                        f
                        for l, f in zip(labels, files)
                        if l == row["primary_preacher_id"]
                    ]
                    if len(preacher_files) < limit_per_preacher:
                        files.append(row["audio_path"])
                        labels.append(row["primary_preacher_id"])

            return files, labels

        except Exception as e:
            logger.error(f"Failed to collect training data: {e}")
            return [], []

    def fine_tune(self, files: List[str], labels: List[str], epochs: int = 10) -> Dict:
        """Fine-tune existing model with new data"""

        if not files:
            return {"status": "no_data"}

        # Load existing model
        try:
            self.trainer.load_model(self.base_model_path)
            start_classes = len(self.trainer.label_encoder.classes_)
        except FileNotFoundError:
            logger.info("No existing model, training from scratch")
            start_classes = 0

        # Add new classes if needed
        unique_labels = set(labels)
        for label in unique_labels:
            if label not in self.trainer.label_encoder.classes_:
                # Will be handled by new training
                logger.info(f"New preacher detected: {label}")

        # Fine-tune with new data
        history = self.trainer.train(
            PreacherDataset("backend/data/preacher_voices"), epochs=epochs  # Base data
        )

        # Save new model
        self.trainer.save_model(self.base_model_path.replace(".pt", "_v2.pt"))

        return {
            "status": "trained",
            "new_classes_added": len(unique_labels),
            "history": history,
        }


# ==================== Convenience Functions ====================


def train_preacher_model(
    data_dir: str = "backend/data/preacher_voices",
    model_path: str = "backend/models/preacher_classifier.pt",
    epochs: int = 50,
) -> str:
    """Train preacher classifier from scratch"""

    config = TrainingConfig(
        data_dir=data_dir, model_output_path=model_path, epochs=epochs
    )

    trainer = PreacherVoiceTrainer(config)
    train_dataset, val_dataset = trainer.prepare_data()
    trainer.train(train_dataset, val_dataset)

    return trainer.save_model()


def evaluate_preacher_model(
    model_path: str, test_data_dir: str = "backend/data/preacher_voices"
) -> Dict:
    """Evaluate trained model"""

    trainer = PreacherVoiceTrainer()
    trainer.load_model(model_path)

    # Create test dataset
    test_dataset = PreacherDataset(test_data_dir)
    test_dataset.label_encoder = trainer.label_encoder

    return trainer.evaluate(test_dataset)


# ==================== Supabase Integration ====================
"""
-- Run in Supabase SQL Editor for training data collection:

CREATE TABLE confirmed_preacher_samples (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sermon_id UUID REFERENCES sermons(id),
    audio_path TEXT NOT NULL,
    preacher_id UUID REFERENCES profiles(id),
    confidence_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE POLICY "Admin collects training samples" ON confirmed_preacher_samples
    FOR INSERT WITH CHECK (auth.role() IN ('admin', 'super_admin'));
"""


# ==================== Admin API Endpoints ====================
"""
Add to backend/api/v1/admin.py:

from backend.ml.train_preacher_model import train_preacher_model, ContinuousLearningTrainer

@router.post("/retrain-voice-model")
async def retrain_voice_model():
    '''Retrain preacher voice model with new data'''
    try:
        model_path = train_preacher_model(
            data_dir="backend/data/preacher_voices",
            epochs=30
        )
        return {"status": "success", "model_path": model_path}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/continuous-learning")
async def continuous_learning():
    '''Fine-tune with confirmed identifications'''
    trainer = ContinuousLearningTrainer("backend/models/preacher_classifier.pt")
    files, labels = trainer.collect_training_data()
    result = trainer.fine_tune(files, labels, epochs=10)
    return result
"""
