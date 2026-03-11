import { useState } from 'react'
import ImageUploader from './components/ImageUploader'
import AnalysisResults from './components/AnalysisResults'
import Header from './components/Header'
import { ThemeProvider } from './contexts/ThemeContext'
import { LanguageProvider, useLanguage } from './contexts/LanguageContext'

function AppContent() {
  const [analysisResult, setAnalysisResult] = useState(null)
  const { t } = useLanguage()

  const handleFileSelect = (file) => {
    // Handle file selection (optional)
    console.log('File selected:', file)
  }

  const handleScanComplete = (result) => {
    setAnalysisResult(result)
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors">
      <Header />
      <div className="flex flex-col items-center justify-center p-4 pt-8">
        <div className="max-w-md w-full bg-white dark:bg-slate-800 rounded-lg shadow-lg p-6 text-center">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-4">{t('appTitle')}</h1>
          <p className="text-slate-600 dark:text-slate-400 mb-6">{t('appSubtitle')}</p>
          <ImageUploader onFileSelect={handleFileSelect} onScanComplete={handleScanComplete} />
        </div>
        {analysisResult && (
          <AnalysisResults result={analysisResult} />
        )}
      </div>
    </div>
  )
}

function App() {
  return (
    <ThemeProvider>
      <LanguageProvider>
        <AppContent />
      </LanguageProvider>
    </ThemeProvider>
  )
}

export default App
