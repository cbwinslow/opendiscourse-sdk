import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  status: 'uploading' | 'completed' | 'error';
  progress: number;
  error?: string;
}

interface DocumentUploadProps {
  onUpload?: (files: File[]) => void;
  maxFiles?: number;
  maxSize?: number;
  acceptedTypes?: string[];
}

export function DocumentUpload({
  onUpload,
  maxFiles = 10,
  maxSize = 10 * 1024 * 1024, // 10MB default
  acceptedTypes = ['.pdf', '.docx', '.txt', '.md']
}: DocumentUploadProps) {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    setIsUploading(true);
    
    // Create initial file entries
    const newFiles: UploadedFile[] = acceptedFiles.map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      name: file.name,
      size: file.size,
      type: file.type,
      status: 'uploading' as const,
      progress: 0
    }));

    setUploadedFiles(prev => [...prev, ...newFiles]);

    // Process each file
    for (let i = 0; i < acceptedFiles.length; i++) {
      const file = acceptedFiles[i];
      const fileEntry = newFiles[i];

      try {
        await uploadFile(file, fileEntry.id);
      } catch (error) {
        setUploadedFiles(prev => 
          prev.map(f => 
            f.id === fileEntry.id 
              ? { ...f, status: 'error', error: error instanceof Error ? error.message : 'Upload failed' }
              : f
          )
        );
      }
    }

    setIsUploading(false);
    if (onUpload) {
      onUpload(acceptedFiles);
    }
  }, [onUpload]);

  const uploadFile = async (file: File, fileId: string): Promise<void> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('metadata', JSON.stringify({
      uploadTime: new Date().toISOString(),
      source: 'web_ui'
    }));

    try {
      const response = await fetch('/api/v1/ingest/documents', {
        method: 'POST',
        body: formData,
        headers: {
          // Don't set Content-Type - let browser set it for FormData
        }
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      // Simulate progress updates
      for (let progress = 0; progress <= 100; progress += 20) {
        setUploadedFiles(prev => 
          prev.map(f => 
            f.id === fileId 
              ? { ...f, progress }
              : f
          )
        );
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      await response.json();

      setUploadedFiles(prev => 
        prev.map(f => 
          f.id === fileId 
            ? { ...f, status: 'completed', progress: 100 }
            : f
        )
      );
    } catch (error) {
      throw error;
    }
  };

  const removeFile = (fileId: string) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: acceptedTypes.reduce((acc, type) => {
      acc[`application/${type.replace('.', '')}`] = [type];
      return acc;
    }, {} as Record<string, string[]>),
    maxFiles,
    maxSize,
    multiple: true
  });

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      {/* Upload Zone */}
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
          ${isDragActive 
            ? 'border-primary-400 bg-primary-50' 
            : 'border-secondary-300 hover:border-primary-400 hover:bg-secondary-50'
          }
        `}
      >
        <input {...getInputProps()} />
        <svg
          className="mx-auto h-12 w-12 text-secondary-400 mb-4"
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
        {isDragActive ? (
          <p className="text-lg text-primary-600 font-medium">Drop the files here...</p>
        ) : (
          <div>
            <p className="text-lg text-secondary-600 font-medium mb-2">
              Drag & drop documents here, or click to select files
            </p>
            <p className="text-sm text-secondary-500">
              Supports: {acceptedTypes.join(', ')} • Max {maxFiles} files • {formatFileSize(maxSize)} per file
            </p>
          </div>
        )}
      </div>

      {/* Upload Progress */}
      {uploadedFiles.length > 0 && (
        <div className="bg-white rounded-lg border border-secondary-200 p-6">
          <h3 className="text-lg font-semibold text-secondary-900 mb-4">
            Upload Progress ({uploadedFiles.length} files)
          </h3>
          <div className="space-y-3">
            {uploadedFiles.map((file) => (
              <div key={file.id} className="flex items-center space-x-4 p-3 bg-secondary-50 rounded-lg">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-sm font-medium text-secondary-900 truncate">
                      {file.name}
                    </p>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs text-secondary-500">
                        {formatFileSize(file.size)}
                      </span>
                      {file.status === 'completed' && (
                        <svg className="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                      )}
                      {file.status === 'error' && (
                        <svg className="w-4 h-4 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                        </svg>
                      )}
                      <button
                        onClick={() => removeFile(file.id)}
                        className="text-secondary-400 hover:text-secondary-600"
                      >
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                        </svg>
                      </button>
                    </div>
                  </div>
                  {file.status === 'uploading' && (
                    <div className="w-full bg-secondary-200 rounded-full h-1.5">
                      <div
                        className="bg-primary-600 h-1.5 rounded-full transition-all duration-300"
                        style={{ width: `${file.progress}%` }}
                      />
                    </div>
                  )}
                  {file.status === 'error' && file.error && (
                    <p className="text-xs text-red-600 mt-1">{file.error}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Upload Summary */}
      {uploadedFiles.length > 0 && (
        <div className="bg-secondary-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div>
                <span className="text-sm font-medium text-secondary-900">
                  {uploadedFiles.filter(f => f.status === 'completed').length} of {uploadedFiles.length} completed
                </span>
                {uploadedFiles.some(f => f.status === 'error') && (
                  <span className="ml-2 text-sm text-red-600">
                    • {uploadedFiles.filter(f => f.status === 'error').length} failed
                  </span>
                )}
              </div>
            </div>
            {!isUploading && uploadedFiles.length > 0 && (
              <button
                onClick={() => setUploadedFiles([])}
                className="text-sm text-secondary-600 hover:text-secondary-800"
              >
                Clear All
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default DocumentUpload;
