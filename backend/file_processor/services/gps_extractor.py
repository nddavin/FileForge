"""GPS Extractor for Audio Files - Extract location from EXIF/metadata"""

import re
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class GPSData:
    """GPS coordinate data"""

    lat: Optional[float] = None
    lon: Optional[float] = None
    altitude: Optional[float] = None
    readable_location: Optional[str] = None
    source: str = "unknown"
    confidence: str = "low"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "altitude": self.altitude,
            "readable_location": self.readable_location,
            "source": self.source,
            "confidence": self.confidence,
        }

    def is_valid(self) -> bool:
        return self.lat is not None and self.lon is not None


class GPSExtractor:
    """Extract GPS coordinates from audio file metadata"""

    def __init__(self, geolocator=None):
        self._geolocator = geolocator

    def extract(self, file_path: str) -> GPSData:
        """Extract GPS data from audio file"""
        gps_data = GPSData()

        try:
            # Method 1: Try mutagen for ID3/Vorbis tags
            mutagen_gps = self._extract_mutagen_gps(file_path)
            if mutagen_gps.is_valid():
                gps_data = mutagen_gps
            else:
                # Method 2: Try parsing from description/comments
                custom_gps = self._extract_custom_gps(file_path)
                if custom_gps.is_valid():
                    gps_data = custom_gps

            # Set confidence based on source
            if gps_data.source == "mutagen":
                gps_data.confidence = "high"
            elif gps_data.source in ["hachoir", "custom"]:
                gps_data.confidence = "medium"

            # Reverse geocode if we have coordinates
            if gps_data.is_valid() and self._geolocator:
                gps_data.readable_location = self._reverse_geocode(
                    gps_data.lat, gps_data.lon
                )

        except Exception as e:
            print(f"GPS extraction error: {e}")

        return gps_data

    def _extract_mutagen_gps(self, file_path: str) -> GPSData:
        """Extract GPS from mutagen audio tags"""
        try:
            import mutagen
            import mutagen  # type: ignore[import]

            audio = mutagen.File(file_path)
            if not audio:
                return GPSData()

            lat, lon = None, None
            source = "mutagen"

            # Get tags
            tags = getattr(audio, "tags", None)
            if not tags:
                return GPSData()

            # Try ID3 TXXX GPS tags
            if hasattr(tags, "getall"):
                for frame in tags.getall("TXXX"):
                    desc = frame.desc.lower() if hasattr(frame, "desc") else ""
                    if "gps" in desc or "geo" in desc:
                        value = str(frame.text[0]) if frame.text else ""
                        coords = self._parse_gps_string(value)
                        if coords:
                            lat, lon = coords
                            break

            # Try common tag keys for different formats
            tag_keys = [
                "location",
                "geolocation",
                "gps_position",
                "GPSLatitude",
                "GPSLongitude",
                "GEO:Location",
            ]

            for key in tag_keys:
                if hasattr(tags, key):
                    value = str(tags[key])
                    coords = self._parse_gps_string(value)
                    if coords:
                        lat, lon = coords
                        break

            if lat is not None and lon is not None:
                return GPSData(lat=lat, lon=lon, source=source, confidence="high")

            return GPSData()

        except ImportError:
            print("mutagen not installed, skipping")
            return GPSData()
        except Exception as e:
            print(f"Mutagen extraction error: {e}")
            return GPSData()

    def _extract_hachoir_gps(self, file_path: str) -> GPSData:
        """Extract GPS from Hachoir metadata (embedded EXIF in containers)"""
        try:
            from hachoir.parser import createParser
            from hachoir.metadata import extractMetadata

            parser = createParser(file_path)
            if not parser:
                return GPSData()

            metadata = extractMetadata(parser)
            if not metadata:
                return GPSData()

            # Search for GPS in metadata
            metadata_text = str(metadata).lower()

            if "gps" in metadata_text or "latitude" in metadata_text:
                # Try to parse coordinates from text
                coords = self._parse_gps_string(metadata_text)
                if coords:
                    return GPSData(
                        lat=coords[0],
                        lon=coords[1],
                        source="hachoir",
                        confidence="medium",
                    )

            return GPSData()

        except ImportError:
            print("hachoir not installed, skipping")
            return GPSData()
        except Exception as e:
            print(f"Hachoir extraction error: {e}")
            return GPSData()

    def _extract_custom_gps(self, file_path: str) -> GPSData:
        """Extract church-specific custom GPS tags"""
        try:
            import mutagen

            audio = mutagen.File(file_path)
            if not audio or not hasattr(audio, "tags") or not audio.tags:
                return GPSData()

            tags = audio.tags
            result = {}

            # Custom church-specific tags
            custom_tags = {
                "recorded_at": "location_name",
                "church_campus": "campus",
                "venue": "venue",
            }

            for tag, field in custom_tags.items():
                value = tags.get(tag)
                if value:
                    result[field] = str(value)

            # Parse coordinates from description/comment
            description = ""
            if hasattr(tags, "comment"):
                description += str(tags.comment)
            if hasattr(tags, "description"):
                description += " " + str(tags.description)

            coords = self._parse_gps_string(description)
            if coords:
                result["lat"] = coords[0]
                result["lon"] = coords[1]
                result["source"] = "custom"

            if "lat" in result and "lon" in result:
                return GPSData(
                    lat=result["lat"],
                    lon=result["lon"],
                    source="custom",
                    confidence="medium",
                    readable_location=result.get("location_name"),
                )

            return GPSData()

        except Exception as e:
            print(f"Custom GPS extraction error: {e}")
            return GPSData()

    def _parse_gps_string(self, gps_string: str) -> Optional[tuple]:
        """Parse various GPS coordinate string formats"""
        if not gps_string:
            return None

        gps_string = gps_string.lower().strip()

        # Pattern 1: "lat, lon" or "lat; lon"
        patterns = [
            r"(-?\d+\.?\d*)\s*[,;]\s*(-?\d+\.?\d*)",  # 1.234, 36.789
            r"(-?\d+\.?\d*)\s*[/]\s*(-?\d+\.?\d*)",  # 1.234/36.789
            r"lat[:\s-]*(-?\d+\.?\d*)[^0-9-]*lon[:\s-]*(-?\d+\.?\d*)",
            r"latitude[:\s-]*(-?\d+\.?\d*)[^0-9-]*longitude[:\s-]*(-?\d+\.?\d*)",
            r"(-?\d+\.?\d*)[ds][\s,]+(?:[ns])?[^0-9-]*(-?\d+\.?\d*)[ds][\s,]+(?:[ew])?",
        ]

        for pattern in patterns:
            match = re.search(pattern, gps_string)
            if match:
                try:
                    lat = float(match.group(1))
                    lon = float(match.group(2))

                    # Validate coordinate ranges
                    if -90 <= lat <= 90 and -180 <= lon <= 180:
                        return (lat, lon)
                except ValueError:
                    continue

        return None

    def _reverse_geocode(self, lat: float, lon: float) -> str:
        """Convert coordinates to readable address"""
        if not self._geolocator:
            return f"{lat}, {lon}"

        try:
            from geopy.geocoders import Nominatim

            geolocator = Nominatim(user_agent="fileforge-sermon", timeout=10)
            location = geolocator.reverse((lat, lon))
            if location:
                return location.address
            return f"{lat}, {lon}"
        except Exception as e:
            print(f"Reverse geocoding error: {e}")
            return f"{lat}, {lon}"

    def extract_from_description(self, description: str) -> GPSData:
        """Extract GPS from a plain text description"""
        coords = self._parse_gps_string(description)
        if coords:
            return GPSData(
                lat=coords[0], lon=coords[1], source="description", confidence="low"
            )
        return GPSData()


class AudioMetadataExtractor:
    """Extended audio metadata extractor with GPS support"""

    def __init__(self):
        self.gps_extractor = GPSExtractor()

    def extract_all(self, file_path: str) -> Dict[str, Any]:
        """Extract all audio metadata including GPS"""
        import mutagen

        metadata = {}

        try:
            audio = mutagen.File(file_path)
            if not audio:
                return {"error": "Could not read audio file"}

            # Basic info
            if hasattr(audio, "info"):
                info = audio.info
                metadata["duration"] = getattr(info, "length", 0)
                metadata["bitrate"] = getattr(info, "bitrate", 0)
                metadata["sample_rate"] = getattr(info, "sample_rate", 0)
                metadata["channels"] = getattr(info, "channels", 0)

            # Tags
            if hasattr(audio, "tags") and audio.tags:
                tags = audio.tags

                # Common tags
                metadata["title"] = self._get_tag(tags, ["title", "TIT2"])
                metadata["artist"] = self._get_tag(tags, ["artist", "TPE1"])
                metadata["album"] = self._get_tag(tags, ["album", "TALB"])
                metadata["date"] = self._get_tag(tags, ["date", "TDRC"])
                metadata["comment"] = self._get_tag(tags, ["comment", "COMM"])

            # GPS extraction
            gps_data = self.gps_extractor.extract(file_path)
            if gps_data.is_valid():
                metadata["sermon_location"] = gps_data.to_dict()
                metadata["has_gps"] = True
            else:
                metadata["has_gps"] = False
                metadata["sermon_location"] = None

        except Exception as e:
            metadata["error"] = str(e)

        return metadata

    def _get_tag(self, tags, keys):
        """Get first matching tag value"""
        for key in keys:
            if hasattr(tags, key):
                value = tags[key]
                if value:
                    return str(value)
        return None


# Convenience function for quick extraction
def get_audio_gps(file_path: str) -> Dict[str, Any]:
    """Quick function to get GPS from audio file"""
    extractor = GPSExtractor()
    gps = extractor.extract(file_path)
    return gps.to_dict()


def get_audio_metadata(file_path: str) -> Dict[str, Any]:
    """Quick function to get all audio metadata"""
    extractor = AudioMetadataExtractor()
    return extractor.extract_all(file_path)
