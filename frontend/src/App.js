import React, { useState } from 'react';
import axios from 'axios';
import { useDropzone } from 'react-dropzone';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [file, setFile] = useState(null);
  const [fileId, setFileId] = useState('');
  const [processing, setProcessing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [targetLanguage, setTargetLanguage] = useState('original');
  const [languages, setLanguages] = useState({});

  // Load supported languages on component mount
  React.useEffect(() => {
    loadLanguages();
  }, []);

  const loadLanguages = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/languages`);
      setLanguages(response.data.languages);
    } catch (err) {
      console.error('Failed to load languages:', err);
    }
  };

  const onDrop = (acceptedFiles) => {
    const selectedFile = acceptedFiles[0];
    if (selectedFile) {
      // Check if it's a video file
      if (!selectedFile.type.startsWith('video/')) {
        setError('Please select a video file');
        return;
      }
      setFile(selectedFile);
      setError('');
      setResult(null);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'video/*': ['.mp4', '.avi', '.mov', '.mkv', '.webm']
    },
    multiple: false
  });

  const uploadFile = async () => {
    if (!file) return;

    try {
      setProcessing(true);
      setCurrentStep('Uploading video...');
      setError('');

      const formData = new FormData();
      formData.append('file', file);

      const uploadResponse = await axios.post(
        `${BACKEND_URL}/api/upload-video`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (progressEvent) => {
            const progress = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            setUploadProgress(progress);
          }
        }
      );

      setFileId(uploadResponse.data.file_id);
      setCurrentStep('Processing video...');
      
      // Process the video
      await processVideo(uploadResponse.data.file_id);

    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed');
      setProcessing(false);
    }
  };

  const processVideo = async (fileId) => {
    try {
      setCurrentStep('Extracting audio...');
      
      const formData = new FormData();
      formData.append('file_id', fileId);
      formData.append('target_language', targetLanguage);

      const response = await axios.post(
        `${BACKEND_URL}/api/process-video`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' }
        }
      );

      setResult(response.data);
      setCurrentStep('Complete!');
      setProcessing(false);

    } catch (err) {
      setError(err.response?.data?.detail || 'Processing failed');
      setProcessing(false);
    }
  };

  const downloadSRT = async () => {
    if (!result?.srt_file) return;

    try {
      const response = await axios.get(
        `${BACKEND_URL}/api/download-srt/${result.srt_file}`,
        { responseType: 'blob' }
      );

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', result.srt_file);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

    } catch (err) {
      setError('Download failed');
    }
  };

  const resetApp = () => {
    setFile(null);
    setFileId('');
    setProcessing(false);
    setUploadProgress(0);
    setCurrentStep('');
    setResult(null);
    setError('');
    setTargetLanguage('original');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8">
      <div className="container mx-auto px-4 max-w-4xl">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            Video Transcription & Translation
          </h1>
          <p className="text-gray-600">
            Upload a video to generate subtitles with optional translation
          </p>
        </div>

        {/* Main Card */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          {!processing && !result && (
            <>
              {/* File Upload Area */}
              <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                  isDragActive
                    ? 'border-blue-400 bg-blue-50'
                    : 'border-gray-300 hover:border-blue-400'
                }`}
              >
                <input {...getInputProps()} />
                <div className="space-y-4">
                  <svg
                    className="mx-auto h-12 w-12 text-gray-400"
                    stroke="currentColor"
                    fill="none"
                    viewBox="0 0 48 48"
                  >
                    <path
                      d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                      strokeWidth={2}
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                  {file ? (
                    <div>
                      <p className="text-lg font-medium text-gray-900">
                        {file.name}
                      </p>
                      <p className="text-sm text-gray-500">
                        {(file.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                  ) : (
                    <div>
                      <p className="text-lg font-medium text-gray-900">
                        {isDragActive
                          ? 'Drop your video here'
                          : 'Drag & drop a video file'}
                      </p>
                      <p className="text-sm text-gray-500">
                        or click to browse (MP4, AVI, MOV, MKV, WebM)
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Language Selection */}
              {file && (
                <div className="mt-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Target Language for Translation
                  </label>
                  <select
                    value={targetLanguage}
                    onChange={(e) => setTargetLanguage(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {Object.entries(languages).map(([code, name]) => (
                      <option key={code} value={code}>
                        {name}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Process Button */}
              {file && (
                <div className="mt-6">
                  <button
                    onClick={uploadFile}
                    className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 font-medium transition-colors"
                  >
                    Process Video
                  </button>
                </div>
              )}
            </>
          )}

          {/* Processing Status */}
          {processing && (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {currentStep}
              </h3>
              {uploadProgress > 0 && uploadProgress < 100 && (
                <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
              )}
              <p className="text-sm text-gray-500">
                This may take a few minutes depending on video length...
              </p>
            </div>
          )}

          {/* Results */}
          {result && (
            <div className="space-y-6">
              <div className="text-center pb-4 border-b">
                <h3 className="text-lg font-medium text-green-600 mb-2">
                  ✅ Processing Complete!
                </h3>
                <p className="text-sm text-gray-600">
                  Detected Language: {result.language_detected} | 
                  Segments: {result.segments_count}
                </p>
              </div>

              {/* Transcription Preview */}
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Transcription:</h4>
                <div className="bg-gray-50 p-4 rounded-md max-h-40 overflow-y-auto">
                  <p className="text-sm text-gray-700">{result.transcription}</p>
                </div>
              </div>

              {/* Download Button */}
              <div className="flex space-x-4">
                <button
                  onClick={downloadSRT}
                  className="flex-1 bg-green-600 text-white py-3 px-4 rounded-md hover:bg-green-700 font-medium transition-colors"
                >
                  Download SRT File
                </button>
                <button
                  onClick={resetApp}
                  className="flex-1 bg-gray-600 text-white py-3 px-4 rounded-md hover:bg-gray-700 font-medium transition-colors"
                >
                  Process Another Video
                </button>
              </div>
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
              <p className="text-red-800">{error}</p>
              <button
                onClick={() => setError('')}
                className="mt-2 text-sm text-red-600 hover:text-red-800"
              >
                Dismiss
              </button>
            </div>
          )}
        </div>

        {/* Features List */}
        <div className="mt-8 grid md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="bg-blue-100 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4v16l13-8L7 4z" />
              </svg>
            </div>
            <h3 className="font-medium text-gray-900">Video Upload</h3>
            <p className="text-sm text-gray-600 mt-1">Support for multiple video formats</p>
          </div>
          <div className="text-center">
            <div className="bg-green-100 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
              </svg>
            </div>
            <h3 className="font-medium text-gray-900">AI Transcription</h3>
            <p className="text-sm text-gray-600 mt-1">Powered by OpenAI Whisper</p>
          </div>
          <div className="text-center">
            <div className="bg-purple-100 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
              <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
              </svg>
            </div>
            <h3 className="font-medium text-gray-900">Translation</h3>
            <p className="text-sm text-gray-600 mt-1">Multi-language subtitle support</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;