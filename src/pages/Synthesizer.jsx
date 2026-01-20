import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Settings as SettingsIcon, UploadCloud, FileText, BarChart, Shield } from 'lucide-react';
import ClipLoader from "react-spinners/ClipLoader";
import Results from '../components/Results';

const SettingsPanel = ({ settings, onSettingsChange, columns }) => (
    <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900 flex items-center">
            <SettingsIcon className="w-5 h-5 mr-2 text-slate-500" />
            Settings
        </h2>
        <div className="mt-6 space-y-4">
            <div>
                <label htmlFor="method" className="block text-sm font-medium text-slate-700">
                    Synthesizer Method
                </label>
                <select
                    id="method"
                    name="method"
                    className="mt-1 block w-full rounded-md border-slate-300 shadow-sm focus:border-teal-500 focus:ring-teal-500 sm:text-sm"
                    value={settings.method}
                    onChange={(e) => onSettingsChange('method', e.target.value)}
                >
                    <option>CTGAN</option>
                    <option>GaussianCopula</option>
                    <option>TVAE</option>
                </select>
            </div>
            <div>
                <label htmlFor="num_rows" className="block text-sm font-medium text-slate-700">
                    Number of Rows
                </label>
                <input
                    type="number"
                    name="num_rows"
                    id="num_rows"
                    className="mt-1 block w-full rounded-md border-slate-300 shadow-sm focus:border-teal-500 focus:ring-teal-500 sm:text-sm"
                    value={settings.num_rows}
                    onChange={(e) => onSettingsChange('num_rows', parseInt(e.target.value, 10))}
                />
            </div>
            <div>
                <label htmlFor="sensitive_column" className="block text-sm font-medium text-slate-700">
                    Fairness Test Column (Optional)
                </label>
                <select
                    id="sensitive_column"
                    name="sensitive_column"
                    className="mt-1 block w-full rounded-md border-slate-300 shadow-sm focus:border-teal-500 focus:ring-teal-500 sm:text-sm disabled:bg-slate-50"
                    value={settings.sensitive_column}
                    onChange={(e) => onSettingsChange('sensitive_column', e.target.value)}
                    disabled={!columns || columns.length === 0}
                >
                    <option value="">None</option>
                    {columns.map(col => <option key={col} value={col}>{col}</option>)}
                </select>
            </div>
        </div>
    </div>
);

const FileUploader = ({ onFileSelect }) => (
     <div className="flex justify-center rounded-lg border border-dashed border-slate-300 px-6 py-10">
        <div className="text-center">
            <UploadCloud className="mx-auto h-12 w-12 text-slate-400" />
            <div className="mt-4 flex text-sm leading-6 text-slate-600">
                <label
                    htmlFor="file-upload"
                    className="relative cursor-pointer rounded-md bg-white font-semibold text-teal-600 focus-within:outline-none focus-within:ring-2 focus-within:ring-teal-600 focus-within:ring-offset-2 hover:text-teal-500"
                >
                    <span>Upload a CSV file</span>
                    <input id="file-upload" name="file-upload" type="file" className="sr-only" onChange={(e) => onFileSelect(e.target.files[0])} accept=".csv"/>
                </label>
            </div>
            <p className="text-xs leading-5 text-slate-500">CSV up to 10MB</p>
        </div>
    </div>
);

function SynthesizerPage() {
    const [settings, setSettings] = useState({
        method: 'CTGAN',
        num_rows: 1000,
        sensitive_column: '',
    });
    const [file, setFile] = useState(null);
    const [columns, setColumns] = useState([]);
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                const text = e.target.result;
                const firstLine = text.split('\n')[0];
                const headers = firstLine.split(',').map(h => h.trim());
                setColumns(headers);
            };
            reader.readAsText(file);
        } else {
            setColumns([]);
            setSettings(s => ({ ...s, sensitive_column: ''}));
        }
    }, [file]);

    const handleSettingsChange = (key, value) => {
        setSettings(prev => ({ ...prev, [key]: value }));
    };

    const handleFileSelect = (selectedFile) => {
        setFile(selectedFile);
        setResults(null);
        setError(null);
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
        if (settings.sensitive_column) {
            formData.append('sensitive_column', settings.sensitive_column);
        }

        try {
            const response = await axios.post('http://127.0.0.1:8000/api/synthesize', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            setResults(response.data);
        } catch (err) {
            setError(err.response?.data?.detail || 'An unknown error occurred during synthesis.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-1 space-y-6">
                <SettingsPanel settings={settings} onSettingsChange={handleSettingsChange} columns={columns} />
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
                    className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-teal-600 hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500 disabled:bg-slate-300 disabled:cursor-not-allowed"
                >
                    {loading ? <><ClipLoader color="#ffffff" size={20} className="mr-2" /> Generating...</> : 'Generate Synthetic Data'}
                </button>
            </div>

            <div className="lg:col-span-2">
                 <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm min-h-[500px]">
                    {loading && (
                        <div className="flex flex-col items-center justify-center h-full text-slate-500">
                            <ClipLoader color="#475569" size={40} />
                            <span className="mt-4 text-sm font-medium">Processing data, this may take a moment...</span>
                        </div>
                    )}
                    {error && (
                        <div className="flex flex-col items-center justify-center h-full text-red-600 p-4 text-center">
                            <Shield className="w-10 h-10 mb-4" />
                            <h3 className="text-lg font-semibold">An Error Occurred</h3>
                            <p className="text-sm mt-2">{error}</p>
                        </div>
                    )}
                    {!loading && !error && !results && (
                         <div className="flex flex-col items-center justify-center h-full text-slate-500">
                            <BarChart className="w-10 h-10 mb-4" />
                            <h3 className="text-lg font-semibold">Results will appear here</h3>
                            <p className="text-sm">Upload a file and click "Generate" to begin.</p>
                        </div>
                    )}
                    {results && <Results data={results} />}
                </div>
            </div>
        </div>
    );
}

export default SynthesizerPage;
