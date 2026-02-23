import { useState, useRef } from 'react';

const ImageUploader = ({ onFileSelect }) => {
  const [dragActive, setDragActive] = useState(false);
  const [preview, setPreview] = useState(null);
  const [uploadState, setUploadState] = useState('IDLE'); // IDLE, UPLOADING
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFile = (file) => {
    const allowedTypes = ['image/png', 'image/jpg', 'image/jpeg'];
    if (!allowedTypes.includes(file.type)) {
      alert('Please upload a PNG, JPG, or JPEG file.');
      return;
    }

    setUploadState('UPLOADING');
    const reader = new FileReader();
    reader.onload = (e) => {
      setPreview(e.target.result);
      setUploadState('IDLE'); // For now, back to IDLE after preview
      onFileSelect && onFileSelect(file);
    };
    reader.readAsDataURL(file);
  };

  const handleClick = () => {
    fileInputRef.current.click();
  };

  const handleFileInputChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto">
      <div
        className={`relative border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          dragActive ? 'border-indigo-500 bg-indigo-50' : 'border-slate-300 hover:border-slate-400'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".png,.jpg,.jpeg"
          onChange={handleFileInputChange}
          className="hidden"
        />
        {preview ? (
          <div className="space-y-4">
            <img src={preview} alt="Preview" className="max-w-full max-h-64 object-contain rounded-lg shadow-md mx-auto" />
            <p className="text-slate-600">Click to upload a different image</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="text-4xl">📁</div>
            <p className="text-slate-700 font-medium">
              {uploadState === 'UPLOADING' ? 'Uploading...' : 'Drag & drop your image here'}
            </p>
            <p className="text-slate-500 text-sm">or click to browse</p>
            <p className="text-slate-400 text-xs">Supports PNG, JPG, JPEG</p>
          </div>
        )}
      </div>

      <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-lg">
        <p className="text-amber-800 text-sm font-medium">Privacy Notice</p>
        <p className="text-amber-700 text-xs mt-1">
          Before uploading, please crop out any sensitive personal information (such as faces, addresses, or personal details) to protect your privacy.
        </p>
      </div>
    </div>
  );
};

export default ImageUploader;