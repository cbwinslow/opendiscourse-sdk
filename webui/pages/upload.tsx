import { useState, useCallback } from 'react';
import Layout from '../components/Layout';
import { Upload, FileText, AlertCircle, CheckCircle } from 'lucide-react';

export default function UploadPage() {
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0] || null;
    setFile(selectedFile);
    setError(null);
    setUploadResult(null);
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setError(null);
    setUploadResult(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Upload failed');
      }

      setUploadResult(result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <Layout title="Upload Document">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Upload Document for Analysis
          </h1>
          <p className="text-gray-600">
            Upload political documents for AI-powered analysis. Supported formats: PDF, DOC, DOCX, TXT, MD, XML
          </p>
        </div>

        {/* Upload Form */}
        <div className="bg-white p-6 rounded-lg shadow">
          <form onSubmit={handleUpload} className="space-y-4">
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
              <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              
              {uploading ? (
                <div>
                  <p className="text-lg font-medium text-gray-900">Uploading...</p>
                  <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-blue-600 h-2 rounded-full animate-pulse"></div>
                  </div>
                </div>
              ) : (
                <div>
                  <input
                    type="file"
                    onChange={handleFileChange}
                    accept=".pdf,.doc,.docx,.txt,.md,.xml"
                    className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                  />
                  
                  {file && (
                    <div className="mt-4">
                      <p className="text-sm text-gray-600">
                        Selected: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                      </p>
                      <button
                        type="submit"
                        className="mt-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                      >
                        Upload Document
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </form>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center">
              <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
              <h3 className="text-sm font-medium text-red-800">Upload Error</h3>
            </div>
            <p className="text-sm text-red-700 mt-1">{error}</p>
          </div>
        )}

        {/* Success Message */}
        {uploadResult && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center mb-3">
              <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
              <h3 className="text-sm font-medium text-green-800">Upload Successful</h3>
            </div>
            
            <div className="space-y-2">
              <p className="text-sm text-green-700">
                <strong>Document processed successfully!</strong>
              </p>
              {uploadResult.chunks_created && (
                <p className="text-sm text-green-700">
                  Chunks created: {uploadResult.chunks_created}
                </p>
              )}
            </div>
          </div>
        )}

        {/* Instructions */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-blue-900 mb-3">What happens after upload?</h3>
          <ul className="space-y-2 text-sm text-blue-800">
            <li className="flex items-start">
              <FileText className="h-4 w-4 mt-0.5 mr-2 flex-shrink-0" />
              <span>Document is processed and analyzed using advanced NLP</span>
            </li>
            <li className="flex items-start">
              <FileText className="h-4 w-4 mt-0.5 mr-2 flex-shrink-0" />
              <span>Entities (people, organizations, locations) are extracted</span>
            </li>
            <li className="flex items-start">
              <FileText className="h-4 w-4 mt-0.5 mr-2 flex-shrink-0" />
              <span>Document is indexed for semantic search</span>
            </li>
            <li className="flex items-start">
              <FileText className="h-4 w-4 mt-0.5 mr-2 flex-shrink-0" />
              <span>Embeddings are generated for similarity matching</span>
            </li>
          </ul>
        </div>
      </div>
    </Layout>
  );
}
