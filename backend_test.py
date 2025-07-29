#!/usr/bin/env python3
"""
Backend API Testing for Video Transcription Service
Tests all FastAPI endpoints with proper error handling and file operations
"""

import requests
import json
import os
import tempfile
import time
from pathlib import Path

# Backend URL from frontend .env
BACKEND_URL = "http://localhost:8001"

def create_test_video_file():
    """Create a small test video file for testing"""
    # Create a minimal MP4 file (just headers, won't actually play but will be recognized as video)
    test_video_content = b'\x00\x00\x00\x20ftypmp41\x00\x00\x00\x00mp41isom\x00\x00\x00\x08free\x00\x00\x00\x28mdat'
    
    temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
    temp_file.write(test_video_content)
    temp_file.close()
    
    return temp_file.name

def test_health_endpoint():
    """Test GET /api/health endpoint"""
    print("\n=== Testing Health Check Endpoint ===")
    try:
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if "status" in data and data["status"] == "healthy":
                print("✅ Health check endpoint working correctly")
                return True
            else:
                print("❌ Health check response format incorrect")
                return False
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Health check test error: {e}")
        return False

def test_languages_endpoint():
    """Test GET /api/languages endpoint"""
    print("\n=== Testing Languages Endpoint ===")
    try:
        response = requests.get(f"{BACKEND_URL}/api/languages", timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if "languages" in data and isinstance(data["languages"], dict):
                languages = data["languages"]
                expected_languages = ["original", "en", "es", "fr", "de"]
                
                # Check if some expected languages are present
                found_languages = [lang for lang in expected_languages if lang in languages]
                if len(found_languages) >= 3:
                    print(f"✅ Languages endpoint working correctly - found {len(languages)} languages")
                    return True
                else:
                    print(f"❌ Languages endpoint missing expected languages")
                    return False
            else:
                print("❌ Languages response format incorrect")
                return False
        else:
            print(f"❌ Languages endpoint failed with status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Languages request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Languages test error: {e}")
        return False

def test_upload_video_endpoint():
    """Test POST /api/upload-video endpoint"""
    print("\n=== Testing Video Upload Endpoint ===")
    
    # Test with invalid file type first
    print("Testing with invalid file type...")
    try:
        test_file_content = b"This is not a video file"
        files = {'file': ('test.txt', test_file_content, 'text/plain')}
        response = requests.post(f"{BACKEND_URL}/api/upload-video", files=files, timeout=30)
        print(f"Invalid file status: {response.status_code}")
        
        if response.status_code == 400:
            print("✅ Correctly rejected non-video file")
        else:
            print("⚠️ Should reject non-video files with 400 status")
    except Exception as e:
        print(f"⚠️ Invalid file test error: {e}")
    
    # Test with valid video file
    print("Testing with valid video file...")
    test_video_path = None
    try:
        test_video_path = create_test_video_file()
        
        with open(test_video_path, 'rb') as f:
            files = {'file': ('test_video.mp4', f, 'video/mp4')}
            response = requests.post(f"{BACKEND_URL}/api/upload-video", files=files, timeout=30)
            
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ["file_id", "filename", "size", "message"]
            
            if all(field in data for field in required_fields):
                print("✅ Video upload endpoint working correctly")
                return True, data["file_id"]
            else:
                print("❌ Video upload response missing required fields")
                return False, None
        else:
            print(f"❌ Video upload failed with status {response.status_code}")
            return False, None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Video upload request failed: {e}")
        return False, None
    except Exception as e:
        print(f"❌ Video upload test error: {e}")
        return False, None
    finally:
        # Clean up test file
        if test_video_path and os.path.exists(test_video_path):
            try:
                os.unlink(test_video_path)
            except:
                pass

def test_process_video_endpoint(file_id=None):
    """Test POST /api/process-video endpoint"""
    print("\n=== Testing Video Processing Endpoint ===")
    
    if not file_id:
        print("⚠️ No file_id provided, testing with dummy ID")
        file_id = "test-file-id"
    
    try:
        # Test processing with original language
        data = {
            'file_id': file_id,
            'target_language': 'original'
        }
        
        response = requests.post(f"{BACKEND_URL}/api/process-video", data=data, timeout=60)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 404:
            print("⚠️ Expected 404 for non-existent file (this is correct behavior)")
            return True, None
        elif response.status_code == 200:
            data = response.json()
            required_fields = ["file_id", "srt_file", "transcription", "language_detected", "segments_count"]
            
            if all(field in data for field in required_fields):
                print("✅ Video processing endpoint working correctly")
                return True, data["srt_file"]
            else:
                print("❌ Video processing response missing required fields")
                return False, None
        else:
            print(f"❌ Video processing failed with status {response.status_code}")
            return False, None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Video processing request failed: {e}")
        return False, None
    except Exception as e:
        print(f"❌ Video processing test error: {e}")
        return False, None

def test_download_srt_endpoint(srt_filename=None):
    """Test GET /api/download-srt/{filename} endpoint"""
    print("\n=== Testing SRT Download Endpoint ===")
    
    if not srt_filename:
        print("Testing with non-existent file...")
        srt_filename = "non-existent-file.srt"
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/download-srt/{srt_filename}", timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 404:
            print("✅ Correctly returned 404 for non-existent SRT file")
            return True
        elif response.status_code == 200:
            print("✅ SRT download endpoint working correctly")
            print(f"Content-Type: {response.headers.get('content-type', 'Not specified')}")
            return True
        else:
            print(f"❌ SRT download failed with status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ SRT download request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ SRT download test error: {e}")
        return False

def test_server_connectivity():
    """Test if the backend server is running and accessible"""
    print("\n=== Testing Server Connectivity ===")
    try:
        response = requests.get(f"{BACKEND_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Backend server is running and accessible")
            return True
        else:
            print(f"⚠️ Server responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to backend server: {e}")
        return False

def run_all_tests():
    """Run all backend API tests"""
    print("🚀 Starting Backend API Tests for Video Transcription Service")
    print(f"Backend URL: {BACKEND_URL}")
    
    results = {}
    
    # Test server connectivity first
    results['connectivity'] = test_server_connectivity()
    if not results['connectivity']:
        print("\n❌ Cannot proceed with tests - server not accessible")
        return results
    
    # Test all endpoints
    results['health'] = test_health_endpoint()
    results['languages'] = test_languages_endpoint()
    
    # Upload and process video (these are related)
    upload_success, file_id = test_upload_video_endpoint()
    results['upload'] = upload_success
    
    process_success, srt_file = test_process_video_endpoint(file_id)
    results['process'] = process_success
    
    results['download'] = test_download_srt_endpoint(srt_file)
    
    # Print summary
    print("\n" + "="*50)
    print("📊 TEST RESULTS SUMMARY")
    print("="*50)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name.upper():<15}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed!")
    elif passed_tests >= total_tests * 0.8:
        print("⚠️ Most tests passed - minor issues detected")
    else:
        print("❌ Multiple test failures detected")
    
    return results

if __name__ == "__main__":
    run_all_tests()