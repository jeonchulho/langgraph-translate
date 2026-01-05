/**
 * Document upload and translation component
 */
import React, { useState, useRef } from 'react';
import { apiClient } from '../api/client';

const SUPPORTED_FORMATS = ['.pdf', '.docx', '.txt'];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export const DocumentUpload: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [previewText, setPreviewText] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): string | null => {
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    
    if (!SUPPORTED_FORMATS.includes(extension)) {
      return `Unsupported file format. Supported: ${SUPPORTED_FORMATS.join(', ')}`;
    }
    
    if (file.size > MAX_FILE_SIZE) {
      return 'File too large. Maximum size: 10MB';
    }
    
    return null;
  };

  const handleFileSelect = (selectedFile: File) => {
    const validationError = validateFile(selectedFile);
    
    if (validationError) {
      setError(validationError);
      return;
    }
    
    setFile(selectedFile);
    setError(null);
    setPreviewText(null);
    
    // Show preview for text files
    if (selectedFile.name.endsWith('.txt')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const text = e.target?.result as string;
        setPreviewText(text.substring(0, 1000)); // First 1000 chars
      };
      reader.readAsText(selectedFile);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleDrag = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleTranslate = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    setLoading(true);
    setError(null);
    setProgress(0);

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setProgress((prev) => Math.min(prev + 10, 90));
      }, 500);

      const blob = await apiClient.translateDocument(file);
      
      clearInterval(progressInterval);
      setProgress(100);

      // Download the translated file
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = file.name.replace(/\.[^/.]+$/, '_translated.txt');
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setTimeout(() => {
        setProgress(0);
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Translation failed');
      setProgress(0);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Drag and drop area */}
      <div
        onDrop={handleDrop}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors
                   ${dragActive 
                     ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
                     : 'border-gray-300 dark:border-gray-600'}`}
      >
        <div className="space-y-4">
          <div className="text-6xl">📄</div>
          <div>
            <p className="text-lg font-medium text-gray-700 dark:text-gray-300">
              Drag and drop your document here
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              or
            </p>
          </div>
          <button
            onClick={() => fileInputRef.current?.click()}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg 
                     font-medium transition-colors"
          >
            Choose File
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept={SUPPORTED_FORMATS.join(',')}
            onChange={(e) => e.target.files && handleFileSelect(e.target.files[0])}
            className="hidden"
          />
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Supported formats: {SUPPORTED_FORMATS.join(', ')} (Max 10MB)
          </p>
        </div>
      </div>

      {/* Selected file info */}
      {file && (
        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 
                      dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-3xl">📎</span>
              <div>
                <p className="font-medium text-gray-900 dark:text-gray-100">
                  {file.name}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {(file.size / 1024).toFixed(2)} KB
                </p>
              </div>
            </div>
            <button
              onClick={() => {
                setFile(null);
                setPreviewText(null);
              }}
              className="text-red-600 hover:text-red-800 dark:text-red-400"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Preview for text files */}
      {previewText && (
        <div className="p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 
                      dark:border-gray-700">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Preview (first 1000 characters)
          </h3>
          <pre className="text-sm text-gray-600 dark:text-gray-400 whitespace-pre-wrap 
                        max-h-40 overflow-auto">
            {previewText}
          </pre>
        </div>
      )}

      {/* Translate button */}
      {file && (
        <button
          onClick={handleTranslate}
          disabled={loading}
          className="w-full py-3 px-6 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 
                   text-white font-medium rounded-lg transition-colors"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                  fill="none"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              Translating Document...
            </span>
          ) : (
            'Translate Document'
          )}
        </button>
      )}

      {/* Progress bar */}
      {loading && progress > 0 && (
        <div className="space-y-2">
          <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400">
            <span>Progress</span>
            <span>{progress}%</span>
          </div>
          <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-600 transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="p-4 bg-red-100 dark:bg-red-900 border border-red-300 dark:border-red-700 
                      rounded-lg text-red-800 dark:text-red-200">
          ❌ {error}
        </div>
      )}
    </div>
  );
};
