import React, { useState } from 'react';
import axios from 'axios';
import { UploadCloud, FileText, Search, Loader2, AlertCircle, Sparkles } from 'lucide-react';

const FileUploader = ({ onFilesSelect, disabled }) => (
    <div className={`rounded-lg border border-dashed border-slate-300 px-6 py-10 ${disabled ? 'bg-slate-50' : ''}`}>
        <div className="text-center">
            <UploadCloud className={`mx-auto h-12 w-12 ${disabled ? 'text-slate-300' : 'text-slate-400'}`} />
            <div className="mt-4 flex text-sm leading-6 text-slate-600">
                <label
                    htmlFor="file-upload"
                    className={`relative cursor-pointer rounded-md bg-white font-semibold text-teal-600 focus-within:outline-none focus-within:ring-2 focus-within:ring-teal-600 focus-within:ring-offset-2 hover:text-teal-500 ${disabled ? 'cursor-not-allowed text-slate-400' : ''}`}
                >
                    <span>Upload PDF files</span>
                    <input id="file-upload" name="file-upload" type="file" className="sr-only" onChange={(e) => onFilesSelect(Array.from(e.target.files))} accept=".pdf" multiple disabled={disabled}/>
                </label>
            </div>
            <p className="text-xs leading-5 text-slate-500">Upload one or more research papers</p>
        </div>
    </div>
);

const SearchResults = ({ data }) => {
    if (!data) return null;
    const { summary, results } = data;

    return (
        <div className="mt-8 space-y-6">
            <div>
                <h3 className="text-lg font-semibold text-slate-900 flex items-center mb-2">
                    <Sparkles className="w-5 h-5 mr-2 text-teal-500" />
                    Quick Summary
                </h3>
                <p className="text-sm text-slate-600 bg-white p-4 rounded-md border">{summary}</p>
            </div>
            <div>
                 <h3 className="text-lg font-semibold text-slate-900 mb-2">Source Documents</h3>
                 <div className="space-y-4">
                    {results && results.length > 0 ? (
                        results.map((result, i) => (
                             <details key={i} className="bg-white p-4 rounded-md border cursor-pointer">
                                <summary className="text-sm font-medium text-slate-800">
                                    <span className="font-semibold text-teal-700">Score: {result.score.toFixed(4)}</span> - {result.filename}
                                </summary>
                                <p className="text-sm text-slate-600 mt-4 border-t pt-4">{result.text}</p>
                            </details>
                        ))
                    ) : <p className="text-sm text-slate-500">No relevant sections found.</p>}
                 </div>
            </div>
        </div>
    );
};


function LiteraturePage() {
    const [files, setFiles] = useState([]);
    const [sessionId, setSessionId] = useState(null);
    const [stats, setStats] = useState(null);
    const [query, setQuery] = useState('');
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState({ indexing: false, searching: false });
    const [error, setError] = useState(null);

    const handleIndexFiles = async () => {
        if (files.length === 0) {
            setError('Please select PDF files to index.');
            return;
        }
        setLoading({ ...loading, indexing: true });
        setError(null);
        setSessionId(null);
        setStats(null);

        const formData = new FormData();
        files.forEach(file => {
            formData.append('files', file);
        });

        try {
            const response = await axios.post('http://127.0.0.1:8000/api/literature/upload', formData);
            setSessionId(response.data.session_id);
            setStats(response.data.stats);
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to index files.');
        } finally {
            setLoading({ ...loading, indexing: false });
        }
    };

    const handleSearch = async () => {
        if (!query) {
            setError('Please enter a search query.');
            return;
        }
        setLoading({ ...loading, searching: true });
        setError(null);
        setResults(null);
        
        const formData = new FormData();
        formData.append('session_id', sessionId);
        formData.append('query', query);

        try {
            const response = await axios.post('http://127.0.0.1:8000/api/literature/search', formData);
            setResults(response.data);
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to perform search.');
        } finally {
            setLoading({ ...loading, searching: false });
        }
    };

    return (
        <div className="max-w-4xl mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
                <div className="space-y-4">
                    <h2 className="text-xl font-bold text-slate-900">1. Index Documents</h2>
                    <FileUploader onFilesSelect={setFiles} disabled={loading.indexing} />
                    {files.length > 0 && (
                        <div className="space-y-2 pt-2">
                            <h4 className="font-medium text-sm">Selected files:</h4>
                            <ul className="list-disc list-inside text-sm text-slate-600">
                                {files.map(f => <li key={f.name}>{f.name}</li>)}
                            </ul>
                        </div>
                    )}
                    <button
                        onClick={handleIndexFiles}
                        disabled={files.length === 0 || loading.indexing}
                        className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-teal-600 hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500 disabled:bg-slate-300"
                    >
                        {loading.indexing ? <><Loader2 className="mr-2 h-5 w-5 animate-spin" /> Indexing...</> : 'Index Files'}
                    </button>
                </div>

                <div className={`space-y-4 ${!sessionId ? 'opacity-50' : ''}`}>
                    <h2 className="text-xl font-bold text-slate-900">2. Search</h2>
                    {stats && (
                        <div className="bg-white p-4 rounded-lg border text-sm">
                            <p className="font-medium">Indexing complete!</p>
                            <p className="text-slate-600">Indexed <span className="font-bold text-teal-700">{stats.num_pages}</span> pages from <span className="font-bold text-teal-700">{stats.num_documents}</span> documents.</p>
                        </div>
                    )}
                    <div className="relative">
                        <input
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="e.g., privacy in synthetic data"
                            disabled={!sessionId || loading.searching}
                            className="block w-full rounded-md border-slate-300 shadow-sm focus:border-teal-500 focus:ring-teal-500 sm:text-sm"
                        />
                        <Search className="absolute top-1/2 right-3 -translate-y-1/2 w-5 h-5 text-slate-400" />
                    </div>
                     <button
                        onClick={handleSearch}
                        disabled={!sessionId || !query || loading.searching}
                        className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-slate-300"
                    >
                        {loading.searching ? <><Loader2 className="mr-2 h-5 w-5 animate-spin" /> Searching...</> : 'Search'}
                    </button>
                </div>
            </div>

            {error && (
                <div className="mt-8 p-4 bg-red-50 text-red-700 border border-red-200 rounded-lg flex items-center">
                    <AlertCircle className="w-5 h-5 mr-3" />
                    {error}
                </div>
            )}
            
            {results && <SearchResults data={results} />}
        </div>
    );
}

export default LiteraturePage;
