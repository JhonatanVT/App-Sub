#!/usr/bin/env python3
"""
Enhanced Backend API Testing for Video Transcription Service
Tests with real video file containing audio
"""

import requests
import json
import os
import tempfile
import time
from pathlib import Path

# Backend URL from frontend .env
BACKEND_URL = "http://localhost:8001"

def test_with_real_video():
    """Test the complete workflow with a real video file"""
    print("\n=== Testing Complete Workflow with Real Video ===")
    
    video_path = "/tmp/test_video_with_audio.mp4"
    if not os.path.exists(video_path):
        print("❌ Test video file not found")
        return False
    
    try:
        # Step 1: Upload video
        print("Step 1: Uploading video...")
        with open(video_path, 'rb') as f:
            files = {'file': ('test_video_with_audio.mp4', f, 'video/mp4')}
            response = requests.post(f"{BACKEND_URL}/api/upload-video", files=files, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Upload failed: {response.status_code}")
            return False
        
        upload_data = response.json()
        file_id = upload_data["file_id"]
        print(f"✅ Upload successful, file_id: {file_id}")
        
        # Step 2: Process video
        print("Step 2: Processing video...")
        process_data = {
            'file_id': file_id,
            'target_language': 'original'
        }
        
        response = requests.post(f"{BACKEND_URL}/api/process-video", data=process_data, timeout=120)
        
        if response.status_code != 200:
            print(f"❌ Processing failed: {response.status_code}")
            print(f"Error: {response.json()}")
            return False
        
        process_result = response.json()
        srt_filename = process_result["srt_file"]
        print(f"✅ Processing successful, SRT file: {srt_filename}")
        print(f"Transcription: {process_result.get('transcription', 'N/A')[:100]}...")
        
        # Step 3: Download SRT
        print("Step 3: Downloading SRT file...")
        response = requests.get(f"{BACKEND_URL}/api/download-srt/{srt_filename}", timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Download failed: {response.status_code}")
            return False
        
        print(f"✅ Download successful, content length: {len(response.content)} bytes")
        
        # Show first few lines of SRT content
        srt_content = response.content.decode('utf-8')
        lines = srt_content.split('\n')[:10]
        print("SRT Content Preview:")
        for line in lines:
            print(f"  {line}")
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow test error: {e}")
        return False

def test_translation_workflow():
    """Test translation to different languages"""
    print("\n=== Testing Translation Workflow ===")
    
    video_path = "/tmp/test_video_with_audio.mp4"
    if not os.path.exists(video_path):
        print("❌ Test video file not found")
        return False
    
    try:
        # Upload video
        with open(video_path, 'rb') as f:
            files = {'file': ('test_video_with_audio.mp4', f, 'video/mp4')}
            response = requests.post(f"{BACKEND_URL}/api/upload-video", files=files, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Upload failed: {response.status_code}")
            return False
        
        file_id = response.json()["file_id"]
        
        # Test translation to Spanish
        print("Testing translation to Spanish...")
        process_data = {
            'file_id': file_id,
            'target_language': 'es'
        }
        
        response = requests.post(f"{BACKEND_URL}/api/process-video", data=process_data, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Spanish translation successful")
            print(f"Transcription: {result.get('transcription', 'N/A')[:100]}...")
            return True
        else:
            print(f"❌ Translation failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Translation test error: {e}")
        return False

def run_enhanced_tests():
    """Run enhanced tests with real video"""
    print("🚀 Starting Enhanced Backend API Tests")
    print(f"Backend URL: {BACKEND_URL}")
    
    # Check if test video exists
    if not os.path.exists("/tmp/test_video_with_audio.mp4"):
        print("❌ Test video file not found. Please create it first.")
        return
    
    results = {}
    
    # Test complete workflow
    results['complete_workflow'] = test_with_real_video()
    
    # Test translation
    results['translation'] = test_translation_workflow()
    
    # Print summary
    print("\n" + "="*50)
    print("📊 ENHANCED TEST RESULTS")
    print("="*50)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name.upper():<20}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    print(f"\nOverall: {passed_tests}/{total_tests} enhanced tests passed")

if __name__ == "__main__":
    run_enhanced_tests()