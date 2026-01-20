import Results from './components/Results';

// ... (rest of the imports)

// ... (SettingsPanel and FileUploader components)


function App() {
    const [settings, setSettings] = useState({
        method: 'CTGAN',
        num_rows: 1000,
    });
    const [file, setFile] = useState(null);
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // ... (handleSettingsChange, handleFileSelect, handleSubmit functions)
    const handleSettingsChange = (key, value) => {
        setSettings(prev => ({ ...prev, [key]: value }));
    };

    const handleFileSelect = (selectedFile) => {
        setFile(selectedFile);
    };

    const handleSubmit = async () => {
        if (!file) {
            setError('Please select a file first.');
            return;
        }

        setLoading(true);
        setError(null);
        setResults(null);

        const formData = new FormData();
        formData.append('file', file);
        formData.append('method', settings.method);
        formData.append('num_rows', settings.num_rows);

        try {
            const response = await axios.post('http://127.0.0.1:8000/api/synthesize', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            setResults(response.data);
        } catch (err) {
            setError(err.response?.data?.detail || 'An unknown error occurred.');
        } finally {
            setLoading(false);
        }
    };


    return (
        <div className="min-h-screen bg-slate-50 text-slate-800">
            {/* ... (header) */}
            <header className="bg-white shadow-sm">
                <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-4">
                    <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center">
                        <TestTube className="w-7 h-7 mr-2 text-teal-600" />
                        SynthLab <span className="text-base font-medium text-slate-500 ml-2">| React Edition</span>
                    </h1>
                </div>
            </header>

            <main className="py-10">
                <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        {/* ... (Left Column: Settings & Upload) */}
                        <div className="md:col-span-1 space-y-6">
                            <SettingsPanel settings={settings} onSettingsChange={handleSettingsChange} />
                            <FileUploader onFileSelect={handleFileSelect} />
                             {file && (
                                <div className="bg-white p-4 rounded-lg border border-slate-200 text-sm flex items-center justify-between">
                                    <div className="flex items-center">
                                       <FileText className="w-5 h-5 mr-3 text-slate-500" />
                                       <span className="font-medium text-slate-700">{file.name}</span>
                                    </div>
                                    <button onClick={() => setFile(null)} className="text-slate-400 hover:text-slate-600">&times;</button>
                                </div>
                            )}
                            <button
                                onClick={handleSubmit}
                                disabled={!file || loading}
                                className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-teal-600 hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500 disabled:bg-slate-300 disabled:cursor-not-allowed"
                            >
                                {loading ? (
                                    <>
                                        <ClipLoader color="#ffffff" size={20} className="mr-2" />
                                        Generating...
                                    </>
                                ) : 'Generate Synthetic Data'}
                            </button>
                        </div>

                        {/* Right Column: Results */}
                        <div className="md:col-span-2">
                             <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm min-h-[400px]">
                                {loading && (
                                    <div className="flex flex-col items-center justify-center h-full text-slate-500">
                                        <ClipLoader color="#475569" size={40} />
                                        <span className="mt-4 text-sm font-medium">Processing data, this may take a moment...</span>
                                    </div>
                                )}
                                {error && (
                                    <div className="flex flex-col items-center justify-center h-full text-red-600">
                                        <Shield className="w-10 h-10 mb-4" />
                                        <h3 className="text-lg font-semibold">An Error Occurred</h3>
                                        <p className="text-sm">{error}</p>
                                    </div>
                                )}
                                {!loading && !error && !results && (
                                     <div className="flex flex-col items-center justify-center h-full text-slate-500">
                                        <BarChart className="w-10 h-10 mb-4" />
                                        <h3 className="text-lg font-semibold">Results will appear here</h3>
                                        <p className="text-sm">Upload a file and click "Generate" to begin.</p>
                                    </div>
                                )}
                                {results && (
                                    <Results data={results} />
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}

export default App;
