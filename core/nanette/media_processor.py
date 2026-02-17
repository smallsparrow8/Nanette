"""
Media Processor for Nanette
Handles audio transcription (via Whisper) and video frame extraction
so Nanette can "hear" voice messages and "see" video content.
"""
import base64
import tempfile
import subprocess
import os
from typing import Optional, Dict, Any, List
from shared.config import settings


class MediaProcessor:
    """Process audio/video media for Nanette"""

    def __init__(self):
        self._openai_client = None

    @property
    def openai_client(self):
        if self._openai_client is None:
            if not settings.openai_api_key:
                return None
            from openai import OpenAI
            self._openai_client = OpenAI(
                api_key=settings.openai_api_key
            )
        return self._openai_client

    async def process_media(
        self, media_bytes: bytes, mime_type: str,
        file_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process media and return useful content for Nanette.

        Returns dict with:
        - transcript: str or None (for audio/video)
        - frames: list of base64 images (for video)
        - description: str summary of what was processed
        """
        result = {
            'transcript': None,
            'frames': [],
            'description': None,
        }

        if not self.openai_client:
            result['description'] = (
                'Media processing unavailable (no OpenAI key)'
            )
            return result

        # Audio types → transcribe
        audio_types = [
            'audio/ogg', 'audio/mpeg', 'audio/mp3',
            'audio/wav', 'audio/x-wav', 'audio/flac',
            'audio/aac', 'audio/m4a', 'audio/mp4',
        ]

        # Video types → extract frames + transcribe audio
        video_types = [
            'video/mp4', 'video/webm', 'video/quicktime',
            'video/x-matroska',
        ]

        if mime_type in audio_types:
            transcript = await self._transcribe_audio(
                media_bytes, mime_type, file_name
            )
            if transcript:
                result['transcript'] = transcript
                result['description'] = (
                    f'Voice/audio transcription: "{transcript}"'
                )

        elif mime_type in video_types:
            # Extract frames from video
            frames = await self._extract_video_frames(
                media_bytes, max_frames=3
            )
            if frames:
                result['frames'] = frames
                result['description'] = (
                    f'Extracted {len(frames)} frames from video'
                )

            # Also try to transcribe audio track
            transcript = await self._transcribe_audio(
                media_bytes, mime_type, file_name
            )
            if transcript:
                result['transcript'] = transcript
                if result['description']:
                    result['description'] += (
                        f' with audio: "{transcript}"'
                    )
                else:
                    result['description'] = (
                        f'Video audio: "{transcript}"'
                    )

        return result

    async def _transcribe_audio(
        self, audio_bytes: bytes, mime_type: str,
        file_name: Optional[str] = None
    ) -> Optional[str]:
        """Transcribe audio using OpenAI Whisper"""
        try:
            # Determine file extension from mime type
            ext_map = {
                'audio/ogg': '.ogg',
                'audio/mpeg': '.mp3',
                'audio/mp3': '.mp3',
                'audio/wav': '.wav',
                'audio/x-wav': '.wav',
                'audio/flac': '.flac',
                'audio/aac': '.aac',
                'audio/m4a': '.m4a',
                'audio/mp4': '.m4a',
                'video/mp4': '.mp4',
                'video/webm': '.webm',
                'video/quicktime': '.mov',
                'video/x-matroska': '.mkv',
            }
            ext = ext_map.get(mime_type, '.ogg')

            # Write to temp file (Whisper needs a file)
            with tempfile.NamedTemporaryFile(
                suffix=ext, delete=False
            ) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            try:
                with open(tmp_path, 'rb') as audio_file:
                    response = self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="text"
                    )
                transcript = response.strip()
                if transcript:
                    print(
                        f"[MediaProcessor] Transcribed: "
                        f"{transcript[:100]}..."
                    )
                    return transcript
            finally:
                os.unlink(tmp_path)

        except Exception as e:
            print(f"[MediaProcessor] Transcription error: {e}")
            return None

    async def _extract_video_frames(
        self, video_bytes: bytes, max_frames: int = 3
    ) -> List[str]:
        """
        Extract key frames from video using ffmpeg.
        Returns list of base64-encoded JPEG images.
        """
        frames = []
        try:
            # Write video to temp file
            with tempfile.NamedTemporaryFile(
                suffix='.mp4', delete=False
            ) as tmp:
                tmp.write(video_bytes)
                video_path = tmp.name

            # Create temp dir for frames
            frame_dir = tempfile.mkdtemp()

            try:
                # Use ffmpeg to extract frames
                # Take frames at evenly spaced intervals
                cmd = [
                    'ffmpeg', '-i', video_path,
                    '-vf', f'fps=1/{max_frames}',
                    '-frames:v', str(max_frames),
                    '-q:v', '2',
                    os.path.join(frame_dir, 'frame_%03d.jpg'),
                    '-y', '-loglevel', 'quiet'
                ]

                result = subprocess.run(
                    cmd, capture_output=True,
                    timeout=30
                )

                if result.returncode == 0:
                    # Read extracted frames
                    for fname in sorted(os.listdir(frame_dir)):
                        if fname.endswith('.jpg'):
                            fpath = os.path.join(frame_dir, fname)
                            with open(fpath, 'rb') as f:
                                frame_b64 = base64.b64encode(
                                    f.read()
                                ).decode('utf-8')
                                frames.append(frame_b64)

                    print(
                        f"[MediaProcessor] Extracted "
                        f"{len(frames)} frames"
                    )
                else:
                    print(
                        "[MediaProcessor] ffmpeg not available "
                        "or failed"
                    )

            finally:
                # Cleanup
                os.unlink(video_path)
                for f in os.listdir(frame_dir):
                    os.unlink(os.path.join(frame_dir, f))
                os.rmdir(frame_dir)

        except Exception as e:
            print(f"[MediaProcessor] Frame extraction error: {e}")

        return frames
