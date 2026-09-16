import { useState, useRef, useEffect } from 'react';
import api from '../services/api';
import { useLanguage } from '../contexts/LanguageContext';

const SCAN_MESSAGE_KEYS = ['analyzingBranding', 'checkingUrls', 'evaluatingTone'];

const ImageUploader = ({ onFileSelect, onScanComplete }) => {
  const { t, language } = useLanguage();
  const [dragActive, setDragActive] = useState(false);
  const [preview, setPreview] = useState(null);
  const [uploadState, setUploadState] = useState('IDLE'); // IDLE, UPLOADING, SCANNING, RESULT, ERROR
  const [scanIndex, setScanIndex] = useState(0);
  const fileInputRef = useRef(null);
  const abortRef = useRef(null);

  // Cycle the scan messages while scanning. Only depends on uploadState,
  // so re-renders caused by the message change don't restart anything.
  useEffect(() => {
    if (uploadState !== 'SCANNING') return;
    const intervalId = setInterval(() => {
      setScanIndex((index) => (index + 1) % SCAN_MESSAGE_KEYS.length);
    }, 1500);
    return () => clearInterval(intervalId);
  }, [uploadState]);

  // Abort any in-flight request on unmount
  useEffect(() => () => abortRef.current?.abort(), []);

  const abortScan = () => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
  };

  // Sends exactly one request per selected file
  const startScan = (file) => {
    const controller = new AbortController();
    abortRef.current = controller;
    setScanIndex(0);
    setUploadState('SCANNING');

    api.uploadFile('/api/analyze', file, language, controller.signal)
      .then((result) => {
        if (controller.signal.aborted) return;
        setUploadState('RESULT');
        if (typeof onScanComplete === 'function') {
          try { onScanComplete(result); } catch (e) { console.error(e); }
        }
      })
      .catch((error) => {
        if (error.name === 'AbortError') return;
        console.error('API Error:', error);
        setUploadState('ERROR');
      })
      .finally(() => {
        if (abortRef.current === controller) abortRef.current = null;
      });
  };

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

    // A new file replaces any scan that is still running
    abortScan();
    setUploadState('UPLOADING');
    const reader = new FileReader();
    reader.onload = (e) => {
      setPreview(e.target.result);
      startScan(file);
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
    // Reset so picking the same file again (e.g. after Cancel) still fires onChange
    e.target.value = '';
  };

  const handleCancel = (e) => {
    // Keep the click from reaching the drop zone, which would open the file picker
    e.stopPropagation();
    abortScan();
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
                    <div className="text-white text-lg font-semibold z-20">{t(SCAN_MESSAGE_KEYS[scanIndex])}</div>
                  </div>
                  <button
                    onClick={handleCancel}
                    className="absolute top-2 right-2 z-30 bg-white bg-opacity-90 text-xs px-2 py-1 rounded"
                  >
                    {t('cancel')}
                  </button>
                  <div className="absolute left-0 w-full h-0.5 bg-red-400 scan-line z-20"></div>
                </>
              )}
            </div>
            {uploadState === 'ERROR' ? (
              <p className="text-red-600 text-sm">{t('analysisFailed')}</p>
            ) : (
              <p className="text-slate-600 dark:text-slate-400">{t('clickDifferent')}</p>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            <div className="text-4xl">📁</div>
            <p className="text-slate-700 dark:text-slate-300 font-medium">
              {uploadState === 'UPLOADING' ? t('uploading') : t('dragDrop')}
            </p>
            <p className="text-slate-500 dark:text-slate-400 text-sm">{t('orBrowse')}</p>
            <p className="text-slate-400 dark:text-slate-500 text-xs">{t('supports')}</p>
          </div>
        )}
      </div>

      <div className="mt-4 p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
        <p className="text-amber-800 dark:text-amber-200 text-sm font-medium">{t('privacyNotice')}</p>
        <p className="text-amber-700 dark:text-amber-300 text-xs mt-1">
          {t('privacyText')}
        </p>
      </div>
    </div>
  );
};

export default ImageUploader;