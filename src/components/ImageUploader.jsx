import { useState, useRef, useEffect } from 'react';

const scanMessages = ["Analyzing Branding...", "Checking URLs...", "Evaluating Tone..."];

const ImageUploader = ({ onFileSelect }) => {
  const [dragActive, setDragActive] = useState(false);
  const [preview, setPreview] = useState(null);
  const [uploadState, setUploadState] = useState('IDLE'); // IDLE, UPLOADING, SCANNING, SUCCESS
  const [scanText, setScanText] = useState('');
  const fileInputRef = useRef(null);
  const intervalRef = useRef(null);
  const timeoutRef = useRef(null);

  useEffect(() => {
    // Start scanning cycle when entering SCANNING
    if (uploadState === 'SCANNING') {
      // initialize text and start cycling
      let index = 0;
      intervalRef.current = setInterval(() => {
        index = (index + 1) % scanMessages.length;
        setScanText(scanMessages[index]);
      }, 1500);

      // Simulate scan duration (3.5s) then set SUCCESS
      timeoutRef.current = setTimeout(() => {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
        setScanText('');
        setUploadState('SUCCESS');
      }, 3500);
    }

    // Cleanup when leaving SCANNING or unmounting
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    };
  }, [uploadState]);

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
      // start with first message then enter SCANNING
      setScanText(scanMessages[0]);
      setUploadState('SCANNING');
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

  const handleCancel = () => {
    // stop timers and return to IDLE
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    setScanText('');
    setUploadState('IDLE');
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
            <div className="relative overflow-hidden rounded-lg mx-auto inline-block">
              <img src={preview} alt="Preview" className="max-w-full max-h-64 object-contain shadow-md" />
              {uploadState === 'SCANNING' && (
                <>
                  <div className="absolute inset-0 bg-black bg-opacity-40 z-10 flex items-center justify-center">
                    <div className="text-white text-lg font-semibold z-20">{scanText}</div>
                  </div>
                  <button
                    onClick={handleCancel}
                    className="absolute top-2 right-2 z-30 bg-white bg-opacity-90 text-xs px-2 py-1 rounded"
                  >
                    Cancel
                  </button>
                  <div className="absolute left-0 w-full h-0.5 bg-red-400 scan-line z-20"></div>
                </>
              )}
            </div>
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