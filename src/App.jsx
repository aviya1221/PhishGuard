import ImageUploader from './components/ImageUploader'

function App() {
  const handleFileSelect = (file) => {
    // Handle file selection
    console.log('File selected:', file)
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6 text-center">
        <h1 className="text-3xl font-bold text-slate-900 mb-4">PhishGuard AI</h1>
        <p className="text-slate-600 mb-6">Secure your digital world with advanced AI protection.</p>
        <ImageUploader onFileSelect={handleFileSelect} />
      </div>
    </div>
  )
}

export default App
