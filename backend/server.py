from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
import uuid
import subprocess
import whisper
import tempfile
from pathlib import Path
import json
from typing import Optional
import aiofiles
from googletrans import Translator
import re

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Load Whisper model (using base model for speed, can be changed to large for accuracy)
print("Loading Whisper model...")
whisper_model = whisper.load_model("base")
print("Whisper model loaded successfully!")

# Initialize translator
translator = Translator()

def seconds_to_srt_time(seconds):
    """Convert seconds to SRT time format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}".replace('.', ',')

def extract_audio_from_video(video_path, audio_path):
    """Extract audio from video using FFmpeg"""
    try:
        cmd = [
            'ffmpeg', '-i', str(video_path), 
            '-vn', '-acodec', 'pcm_s16le', 
            '-ar', '16000', '-ac', '1', 
            str(audio_path), '-y'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"FFmpeg error: {result.stderr}")
        return True
    except Exception as e:
        print(f"Audio extraction failed: {e}")
        return False

def transcribe_audio(audio_path):
    """Transcribe audio using Whisper"""
    try:
        result = whisper_model.transcribe(str(audio_path))
        return result
    except Exception as e:
        print(f"Transcription failed: {e}")
        return None

def translate_text(text, target_language='en'):
    """Translate text using Google Translate"""
    try:
        translated = translator.translate(text, dest=target_language)
        return translated.text
    except Exception as e:
        print(f"Translation failed: {e}")
        return text  # Return original text if translation fails

def create_srt_file(segments, target_language=None, output_path=None):
    """Create SRT file from transcription segments"""
    if not output_path:
        output_path = OUTPUT_DIR / f"{uuid.uuid4()}.srt"
    
    srt_content = []
    
    for i, segment in enumerate(segments, 1):
        start_time = seconds_to_srt_time(segment['start'])
        end_time = seconds_to_srt_time(segment['end'])
        text = segment['text'].strip()
        
        # Translate if target language is specified
        if target_language and target_language != 'original':
            text = translate_text(text, target_language)
        
        srt_content.append(f"{i}")
        srt_content.append(f"{start_time} --> {end_time}")
        srt_content.append(text)
        srt_content.append("")  # Empty line between subtitles
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(srt_content))
    
    return output_path

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Video transcription service is running"}

@app.post("/api/upload-video")
async def upload_video(file: UploadFile = File(...)):
    """Upload video file and return file ID"""
    try:
        # Validate file type
        if not file.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="File must be a video")
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix
        video_path = UPLOAD_DIR / f"{file_id}{file_extension}"
        
        # Save uploaded file
        async with aiofiles.open(video_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "size": len(content),
            "message": "Video uploaded successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/api/process-video")
async def process_video(
    file_id: str = Form(...),
    target_language: Optional[str] = Form("original")
):
    """Process video: extract audio, transcribe, translate, and generate SRT"""
    try:
        # Find the video file
        video_files = list(UPLOAD_DIR.glob(f"{file_id}.*"))
        if not video_files:
            raise HTTPException(status_code=404, detail="Video file not found")
        
        video_path = video_files[0]
        audio_path = UPLOAD_DIR / f"{file_id}.wav"
        
        # Step 1: Extract audio
        print(f"Extracting audio from {video_path}")
        if not extract_audio_from_video(video_path, audio_path):
            raise HTTPException(status_code=500, detail="Audio extraction failed")
        
        # Step 2: Transcribe audio
        print("Transcribing audio...")
        transcription_result = transcribe_audio(audio_path)
        if not transcription_result:
            raise HTTPException(status_code=500, detail="Transcription failed")
        
        # Step 3: Create SRT file
        print("Creating SRT file...")
        srt_path = create_srt_file(
            transcription_result['segments'], 
            target_language if target_language != "original" else None
        )
        
        # Clean up temporary audio file
        try:
            os.remove(audio_path)
        except:
            pass
        
        return {
            "file_id": file_id,
            "srt_file": srt_path.name,
            "transcription": transcription_result['text'],
            "language_detected": transcription_result.get('language', 'unknown'),
            "segments_count": len(transcription_result['segments']),
            "message": "Video processed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.get("/api/download-srt/{filename}")
async def download_srt(filename: str):
    """Download generated SRT file"""
    try:
        file_path = OUTPUT_DIR / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="SRT file not found")
        
        return FileResponse(
            path=file_path,
            media_type='application/octet-stream',
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@app.get("/api/languages")
async def get_supported_languages():
    """Get list of supported translation languages"""
    languages = {
        "original": "Original Language",
        "en": "English",
        "es": "Spanish", 
        "fr": "French",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "ru": "Russian",
        "ja": "Japanese",
        "ko": "Korean",
        "zh": "Chinese",
        "ar": "Arabic",
        "hi": "Hindi"
    }
    return {"languages": languages}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)