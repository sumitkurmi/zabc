import React, { useState } from 'react';
import { Upload, FileText, AlertCircle, CheckCircle2 } from 'lucide-react';

interface UploadDropzoneProps {
  onUpload: (file: File) => Promise<void>;
  isUploading: boolean;
}

export const UploadDropzone: React.FC<UploadDropzoneProps> = ({ onUpload, isUploading }) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const validateAndSetFile = (file: File) => {
    setError(null);
    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    if (!['.pdf', '.docx', '.txt'].includes(ext)) {
      setError('Invalid file type. Allowed formats: .pdf, .docx, .txt');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setError('File exceeds maximum size of 10 MB');
      return;
    }

    setSelectedFile(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleSubmit = async () => {
    if (!selectedFile) return;
    try {
      await onUpload(selectedFile);
      setSelectedFile(null);
    } catch (err: any) {
      setError(err.message || 'Upload failed');
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 mb-8">
      <h3 className="text-sm font-bold text-slate-800 mb-3">Upload Knowledge Document</h3>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 p-3 rounded-xl text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-2xl p-8 text-center transition-colors ${
          dragActive
            ? 'border-blue-600 bg-blue-50/50'
            : 'border-slate-300 hover:border-slate-400 bg-slate-50/50'
        }`}
      >
        <Upload className="w-8 h-8 text-slate-400 mx-auto mb-2" />
        <p className="text-xs font-semibold text-slate-700 mb-1">
          Drag & drop document here, or{' '}
          <label className="text-blue-600 hover:underline cursor-pointer">
            browse files
            <input
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={handleFileSelect}
              className="hidden"
            />
          </label>
        </p>
        <p className="text-[11px] text-slate-400">Supports PDF, DOCX, TXT up to 10 MB</p>

        {selectedFile && (
          <div className="mt-4 p-3 bg-white rounded-xl border border-slate-200 inline-flex items-center gap-3">
            <FileText className="w-5 h-5 text-mnnit-blue" />
            <div className="text-left">
              <p className="text-xs font-semibold text-slate-800">{selectedFile.name}</p>
              <p className="text-[10px] text-slate-400">{(selectedFile.size / 1024).toFixed(1)} KB</p>
            </div>
            <button
              onClick={handleSubmit}
              disabled={isUploading}
              className="ml-3 px-3 py-1.5 bg-mnnit-blue hover:bg-blue-800 text-white text-xs font-semibold rounded-lg disabled:opacity-50"
            >
              {isUploading ? 'Uploading...' : 'Upload & Index'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
