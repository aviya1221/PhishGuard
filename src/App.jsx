import { useState } from 'react'
import ImageUploader from './components/ImageUploader'
import AnalysisResults from './components/AnalysisResults'

function App() {
  const [analysisResult, setAnalysisResult] = useState(null)

  const handleFileSelect = (file) => {
    // Handle file selection (optional)
    console.log('File selected:', file)
  }

  const handleScanComplete = (result) => {
    setAnalysisResult(result)
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6 text-center">
        <h1 className="text-3xl font-bold text-slate-900 mb-4">PhishGuard AI</h1>
        <p className="text-slate-600 mb-6">Secure your digital world with advanced AI protection.</p>
        <ImageUploader onFileSelect={handleFileSelect} onScanComplete={handleScanComplete} />
      </div>
      {analysisResult && (
        <AnalysisResults result={analysisResult} />
      )}
    </div>
  )
}

export default App
