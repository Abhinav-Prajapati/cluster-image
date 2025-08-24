from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime
from typing import Dict, Any, Union
import logging

logger = logging.getLogger(__name__)

def _sanitize_string(value: Union[str, bytes]) -> str:
    """
    Decodes bytes if necessary, removes null characters, and strips whitespace.
    This prevents database errors with malformed EXIF string data.
    """
    if isinstance(value, bytes):
        try:
            value = value.decode('utf-8', 'replace')
        except Exception:
            return "" # Return an empty string if decoding fails for any reason
    
    return value.replace('\x00', '').strip()

def extract_exif_data(image_path: str) -> Dict[str, Any]:
    """
    Extracts relevant EXIF metadata from an image file, ensuring all
    string values are sanitized before returning.
    """
    metadata = {}
    try:
        img = Image.open(image_path)
        metadata['width'] = img.width
        metadata['height'] = img.height

        exif_data = img._getexif()
        if not exif_data:
            return metadata

        for tag_id, value in exif_data.items():
            tag_name = TAGS.get(tag_id, tag_id)
            
            if isinstance(value, (str, bytes)):
                value = _sanitize_string(value)

            if tag_name == 'DateTimeOriginal' and isinstance(value, str):
                try:
                    metadata['shot_at'] = datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                except (ValueError, TypeError):
                    pass
            elif tag_name == 'Make' and value:
                metadata['camera_make'] = value
            elif tag_name == 'Model' and value:
                metadata['camera_model'] = value
            elif tag_name == 'FNumber':
                metadata['f_number'] = float(value)
            elif tag_name == 'ExposureTime':
                if float(value) > 0:
                    metadata['exposure_time'] = f"1/{int(1/float(value))}"
            elif tag_name == 'ISOSpeedRatings':
                metadata['iso'] = int(value)
            elif tag_name == 'FocalLength':
                metadata['focal_length'] = f"{int(value)}mm"

    except Exception as e:
        logger.warning(f"Could not read metadata for {image_path}: {e}")
    
    return metadata