import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, User, ChevronLeft, ChevronRight, Beaker, BookOpen, Settings, UploadCloud, FileText, Loader2, Sparkles, AlertCircle, ChevronDown, History } from 'lucide-react';
import ClipLoader from "react-spinners/ClipLoader";
import Results from './components/Results';
import ComparisonDashboard from './components/ComparisonDashboard';
import ExperimentHistory from './components/ExperimentHistory';

const TabButton = ({ active, onClick, icon, label }) => (
  <button 
    onClick={onClick}
    className={`flex items-center gap-2 px-6 py-3 text-sm font-medium border-b-2 transition-all ${active ? 'border-violet-600 text-violet-700' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
  >
    {icon}
    {label}
  </button>
);

const App = () => {
    const [activeTab, setActiveTab] = useState('generator');
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [isSynthDropdownOpen, setIsSynthDropdownOpen] = useState(false);

    // State for user profile
    const [userProfile, setUserProfile] = useState({
        name: 'Victoria N.',
        status: 'Researching synthetic data models.',
        role: 'Researcher'
    });

    // State for Synthesizer
    const [synthSettings, setSynthSettings] = useState({
        method: 'CTGAN', 
        num_rows: 1000, 
        sensitive_column: '',
        domain: 'Cardiology (MIMIC-III Style)',
        epsilon: 1.2,
        epochs: 300, // Default epochs
        outputFormat: 'csv'
    });
    const [synthFile, setSynthFile] = useState(null);
    const [synthColumns, setSynthColumns] = useState([]);
    const [synthResults, setSynthResults] = useState(null);
    const [synthLoading, setSynthLoading] = useState(false);
    const [synthError, setSynthError] = useState(null);

    // State for Literature
    const [litFiles, setLitFiles] = useState([]);
    const [litSessionId, setLitSessionId] = useState(null);
    const [litStats, setLitStats] = useState(null);
    const [litQuery, setLitQuery] = useState('');
    const [litResults, setLitResults] = useState(null);
    const [litLoading, setLitLoading] = useState({ indexing: false, searching: false });
    const [litError, setLitError] = useState(null);
    
    const theme = { bg: "bg-slate-50", surface: "bg-white", border: "border-slate-200" };
    const synthesizerOptions = ['CTGAN', 'GaussianCopula', 'TVAE'];

    useEffect(() => {
        if (synthFile) {
            const reader = new FileReader();
            reader.onload = (e) => {
                const firstLine = e.target.result.split('\n')[0];
                setSynthColumns(firstLine.split(',').map(h => h.trim()));
            };
            reader.readAsText(synthFile);
        } else {
            setSynthColumns([]);
            setSynthSettings(s => ({ ...s, sensitive_column: '' }));
        }
    }, [synthFile]);

    const handleSynthSubmit = async () => {
        if (!synthFile) { setSynthError('Please select a file first.'); return; }
        setSynthLoading(true);
        setSynthError(null);
        setSynthResults(null);
        const formData = new FormData();
        formData.append('file', synthFile);
        formData.append('method', synthSettings.method);
        formData.append('num_rows', synthSettings.num_rows);
        formData.append('epsilon', synthSettings.epsilon);
        formData.append('epochs', synthSettings.epochs);
        if (synthSettings.sensitive_column) {
            formData.append('sensitive_column', synthSettings.sensitive_column);
        }
        try {
            const response = await axios.post('http://127.0.0.1:8000/api/synthesize', formData);
            setSynthResults(response.data);
        } catch (err) {
            setSynthError(err.response?.data?.detail || 'An unknown error occurred.');
        } finally {
            setSynthLoading(false);
        }
    };

    const handleLitIndex = async () => {
        if (litFiles.length === 0) { setLitError('Please select PDF files.'); return; }
        setLitLoading({ ...litLoading, indexing: true });
        setLitError(null);
        setLitSessionId(null);
        setLitStats(null);
        const formData = new FormData();
        litFiles.forEach(file => formData.append('files', file));
        try {
            const response = await axios.post('http://127.0.0.1:8000/api/literature/upload', formData);
            setLitSessionId(response.data.session_id);
            setLitStats(response.data.stats);
        } catch (err) {
            setLitError(err.response?.data?.detail || 'Failed to index files.');
        } finally {
            setLitLoading({ ...litLoading, indexing: false });
        }
    };

    const handleLitSearch = async () => {
        if (!litQuery) { setLitError('Please enter a search query.'); return; }
        setLitLoading({ ...litLoading, searching: true });
        setLitError(null);
        setLitResults(null);
        const formData = new FormData();
        formData.append('session_id', litSessionId);
        formData.append('query', litQuery);
        try {
            const response = await axios.post('http://127.0.0.1:8000/api/literature/search', formData);
            setLitResults(response.data);
        } catch (err) {
            setLitError(err.response?.data?.detail || 'Failed to perform search.');
        } finally {
            setLitLoading({ ...litLoading, searching: false });
        }
    };

    const renderGeneratorContent = () => (
        <div className="space-y-8">
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
                <h2 className="text-xl font-semibold text-slate-800 mb-4">1. Upload Dataset</h2>
                <div className="flex justify-center rounded-lg border border-dashed border-slate-300 px-6 py-10 text-center">
                    <div className="text-center">
                         <UploadCloud className="mx-auto h-12 w-12 text-slate-400" />
                        <label htmlFor="synth-upload" className="mt-4 text-sm font-semibold text-violet-600 cursor-pointer hover:text-violet-500">Upload a CSV</label>
                        <input id="synth-upload" type="file" className="sr-only" onChange={(e) => setSynthFile(e.target.files[0])} accept=".csv"/>
                    </div>
                </div>
                {synthFile && (
                    <div className="mt-4 bg-slate-50 p-3 rounded-lg border text-sm flex items-center justify-between">
                        <div className="flex items-center gap-3"><FileText className="w-5 h-5 text-slate-500" /><span className="font-medium">{synthFile.name}</span></div>
                        <button onClick={() => setSynthFile(null)} className="text-slate-400 hover:text-slate-600">&times;</button>
                    </div>
                )}
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
                 <h2 className="text-xl font-semibold text-slate-800 mb-4">2. Generate Data</h2>
                 <p className="text-sm text-slate-500 mb-6">Configure parameters in the sidebar, then click generate.</p>
                 <button onClick={handleSynthSubmit} disabled={!synthFile || synthLoading} className="w-full px-6 py-3 bg-violet-600 hover:bg-violet-700 text-white font-medium rounded-lg transition-colors shadow-sm disabled:bg-slate-300 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                    {synthLoading ? <><ClipLoader color="#ffffff" size={20}/> Generating...</> : "Initialize Generation"}
                 </button>
            </div>
            
            {(synthError || synthResults) && (
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8 min-h-[300px]">
                    <h2 className="text-xl font-semibold text-slate-800 mb-4">3. Results</h2>
                    {synthError && <div className="p-4 bg-red-50 text-red-700 border border-red-200 rounded-lg flex items-center"><AlertCircle className="w-5 h-5 mr-3"/>{synthError}</div>}
                    {synthResults && (
                        <>
                            <Results data={synthResults} />
                            <ComparisonDashboard plots={synthResults.plots} />
                        </>
                    )}
                </div>
            )}
        </div>
    );

    const renderLiteratureContent = () => (
         <div className="space-y-8">
             <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
                <h2 className="text-xl font-semibold text-slate-800 mb-4">1. Upload & Index PDFs</h2>
                 <div className="flex justify-center rounded-lg border border-dashed border-slate-300 px-6 py-10 text-center">
                    <div>
                         <UploadCloud className="mx-auto h-12 w-12 text-slate-400" />
                        <label htmlFor="lit-upload" className="mt-4 text-sm font-semibold text-violet-600 cursor-pointer hover:text-violet-500">Upload PDF files</label>
                        <input id="lit-upload" type="file" className="sr-only" onChange={(e) => setLitFiles(Array.from(e.target.files))} accept=".pdf" multiple/>
                    </div>
                </div>
                {litFiles.length > 0 && <ul className="mt-4 list-disc list-inside text-sm text-slate-600">{litFiles.map(f => <li key={f.name}>{f.name}</li>)}</ul>}
                <button onClick={handleLitIndex} disabled={litFiles.length === 0 || litLoading.indexing} className="mt-6 w-full px-6 py-3 bg-violet-600 hover:bg-violet-700 text-white font-medium rounded-lg transition-colors shadow-sm disabled:bg-slate-300 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                    {litLoading.indexing ? <><Loader2 className="animate-spin"/> Indexing...</> : "Index Files"}
                </button>
             </div>
             
             <div className={`bg-white rounded-xl shadow-sm border border-slate-200 p-8 ${!litSessionId ? 'opacity-50 cursor-not-allowed' : ''}`}>
                 <h2 className="text-xl font-semibold text-slate-800 mb-4">2. Search Literature</h2>
                 {litStats && <p className="text-sm text-slate-600 mb-4">Indexed {litStats.num_pages} pages from {litStats.num_documents} documents.</p>}
                 <div className="relative">
                    <input type="text" value={litQuery} onChange={(e) => setLitQuery(e.target.value)} placeholder="e.g., privacy in synthetic data" disabled={!litSessionId || litLoading.searching} className="w-full pl-4 pr-10 py-3 bg-slate-100 border-none rounded-md text-sm focus:ring-2 focus:ring-violet-500 outline-none"/>
                    <Search className="absolute right-4 top-3.5 h-5 w-5 text-slate-400" />
                 </div>
                 <button onClick={handleLitSearch} disabled={!litSessionId || !litQuery || litLoading.searching} className="mt-6 w-full px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors shadow-sm disabled:bg-slate-300 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                    {litLoading.searching ? <><Loader2 className="animate-spin"/> Searching...</> : "Search"}
                 </button>
             </div>
             
             {(litError || litResults) && (
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8 min-h-[300px]">
                    <h2 className="text-xl font-semibold text-slate-800 mb-4">3. Search Results</h2>
                    {litError && <div className="p-4 bg-red-50 text-red-700 border border-red-200 rounded-lg flex items-center"><AlertCircle className="w-5 h-5 mr-3"/>{litError}</div>}
                    {litResults && (
                        <div className="space-y-6">
                            <div>
                                <h3 className="font-semibold flex items-center gap-2"><Sparkles className="text-violet-500"/>AI Summary</h3>
                                <p className="text-sm text-slate-600 mt-2 bg-slate-50 p-4 rounded-md border">{litResults.summary}</p>
                            </div>
                            <div>
                                <h3 className="font-semibold">Sources</h3>
                                <div className="space-y-2 mt-2">
                                    {litResults.results?.map((res, i) => (
                                        <details key={i} className="bg-slate-50 p-3 rounded-md border text-sm"><summary className="font-medium cursor-pointer">Score: {res.score.toFixed(3)} - {res.filename}</summary><p className="mt-2 pt-2 border-t">{res.text}</p></details>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
             )}
         </div>
    );
    
    const renderHistoryContent = () => (
        <ExperimentHistory onFork={handleForkExperiment} />
    );

    const renderSettingsContent = () => (
        <div className="space-y-8">
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
                <h2 className="text-xl font-semibold text-slate-800 mb-6">User Profile & Settings</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {/* Left side: Form */}
                    <div className="space-y-6">
                        <div className="space-y-1">
                            <label className="text-sm font-medium text-slate-700">Display Name</label>
                            <input 
                                type="text" 
                                value={userProfile.name}
                                onChange={(e) => setUserProfile(p => ({...p, name: e.target.value}))}
                                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-sm focus:ring-1 focus:ring-violet-500 outline-none" 
                            />
                        </div>
                        <div className="space-y-1">
                            <label className="text-sm font-medium text-slate-700">Status</label>
                            <input 
                                type="text" 
                                value={userProfile.status}
                                onChange={(e) => setUserProfile(p => ({...p, status: e.target.value}))}
                                placeholder="What are you working on?"
                                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-sm focus:ring-1 focus:ring-violet-500 outline-none" 
                            />
                        </div>
                        <div className="space-y-1">
                            <label className="text-sm font-medium text-slate-700">Role</label>
                            <select 
                                value={userProfile.role}
                                onChange={(e) => setUserProfile(p => ({...p, role: e.target.value}))}
                                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-sm outline-none cursor-pointer"
                            >
                                <option>Researcher</option>
                                <option>Student</option>
                                <option>Professor</option>
                                <option>Public Use</option>
                            </select>
                        </div>
                    </div>
    
                    {/* Right side: Preview */}
                    <div className="bg-slate-50 rounded-lg p-6 border border-slate-200">
                        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">Profile Preview</h3>
                        <div className="flex items-center gap-4">
                            <div className="h-16 w-16 rounded-full bg-violet-200 flex items-center justify-center text-violet-700 font-bold text-2xl">
                                {userProfile.name ? userProfile.name.charAt(0) : '?'}
                            </div>
                            <div>
                                <p className="font-semibold text-slate-800">{userProfile.name}</p>
                                <p className="text-sm text-slate-500">{userProfile.status}</p>
                                <span className="mt-2 inline-block text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full border border-blue-200">{userProfile.role}</span>
                            </div>
                        </div>
                    </div>
                </div>
                 <div className="mt-8 pt-6 border-t border-slate-200 flex justify-end">
                    <button className="px-5 py-2 bg-violet-600 hover:bg-violet-700 text-white font-medium rounded-lg transition-colors shadow-sm">
                        Save Changes
                    </button>
                </div>
            </div>
        </div>
    );

    const handleForkExperiment = (config) => {
        setSynthSettings(prevSettings => ({
            ...prevSettings,
            method: config.method,
            num_rows: config.num_rows,
            sensitive_column: config.sensitive_column || '',
            epsilon: config.epsilon,
            epochs: config.epochs,
        }));
        // Note: The original file is not re-selected automatically for security reasons.
        // The user must re-select the file to run the forked experiment.
        setSynthFile(null); 
        setSynthResults(null);
        setSynthError(null);
        setActiveTab('generator');
    };

    return (
        <div className={`h-screen w-full flex flex-col ${theme.bg} text-slate-800 font-sans`}>
            <nav className={`h-16 ${theme.surface} border-b ${theme.border} flex items-center justify-between px-6 shadow-sm z-10 flex-shrink-0`}>
                <div className="flex items-center gap-2">
                    <div className="h-8 w-8 bg-violet-600 rounded-lg flex items-center justify-center text-white font-bold">SL</div>
                    <span className="text-lg font-semibold tracking-tight">SynthLab</span>
                     <div className="relative">
                        <button onClick={() => setIsSynthDropdownOpen(!isSynthDropdownOpen)} className="flex items-center gap-1 text-sm font-medium text-slate-600 hover:text-violet-700 bg-slate-100 px-2 py-1 rounded-md">
                            <span>{synthSettings.method}</span>
                            <ChevronDown size={14} className={`transition-transform ${isSynthDropdownOpen ? 'rotate-180' : ''}`} />
                        </button>
                        {isSynthDropdownOpen && (
                            <div className="absolute top-9 left-0 bg-white border border-slate-200 rounded-md shadow-lg py-1 w-40 z-20">
                            {synthesizerOptions.map(option => (
                                <a href="#" key={option} onClick={(e) => {
                                e.preventDefault();
                                setSynthSettings(s => ({ ...s, method: option }));
                                setIsSynthDropdownOpen(false);
                                }} className="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-100">{option}</a>
                            ))}
                            </div>
                        )}
                    </div>
                </div>
                <div className="flex-1 max-w-2xl mx-8 relative"><Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" /><input type="text" placeholder="Search..." className="w-full pl-10 pr-4 py-2 bg-slate-100 border-none rounded-md text-sm focus:ring-2 focus:ring-violet-500 outline-none"/></div>
                <div className="flex items-center gap-4">
                    <button className="text-sm font-medium hover:text-violet-700">Docs</button>
                    <div className="h-8 w-8 rounded-full bg-violet-100 flex items-center justify-center cursor-pointer border border-violet-200 text-violet-700 font-bold text-xs">
                        {userProfile.name ? userProfile.name.split(' ').map(n => n[0]).join('') : <User className="h-4 w-4" />}
                    </div>
                </div>
            </nav>

            <div className="flex flex-1 overflow-hidden">
                <aside className={`${isSidebarOpen ? 'w-80' : 'w-20'} transition-all duration-300 ease-in-out ${theme.surface} border-r ${theme.border} flex flex-col relative z-20`}>
  
                  <button 
                    onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                    className="absolute -right-3 top-6 bg-white border border-slate-200 rounded-full p-1 shadow-sm hover:text-violet-600 z-30"
                  >
                    {isSidebarOpen ? <ChevronLeft size={14} /> : <ChevronRight size={14} />}
                  </button>

                  {/* Sidebar Content */}
                  <div className="flex-1 overflow-y-auto custom-scrollbar">

                    {/* 1. Retention / Context Box (Top) */}
                    {isSidebarOpen ? (
                      <div className="p-4 border-b border-slate-100">
                        <div className="bg-violet-50/50 rounded-lg p-3 border border-violet-100 mb-2">
                          <div className="flex items-center gap-2 mb-2">
                            <div className={`h-2 w-2 rounded-full ${litSessionId ? 'bg-green-500 animate-pulse' : 'bg-slate-400'}`}></div>
                            <h3 className="text-xs font-bold text-violet-800 uppercase tracking-wider">Active Session</h3>
                          </div>
                          <p className="text-xs text-violet-900 leading-relaxed font-mono">
                            ID: <span className="opacity-70">{litSessionId ? litSessionId.slice(0, 9) : 'N/A'}</span><br />
                            Status: <span className={litSessionId ? "text-green-700" : "text-slate-500"}>{litSessionId ? 'Ready' : 'Idle'}</span>
                          </p>
                        </div>
                      </div>
                    ) : (
                      <div className="py-6 flex flex-col items-center gap-4">
                        <Beaker className="text-violet-500" />
                        <Settings className="text-slate-400" />
                      </div>
                    )}

                    {/* 2. Configuration Form (Only visible when open and on generator tab) */}
                    {isSidebarOpen && activeTab === 'generator' && (
                      <div className="p-4 space-y-6">

                        {/* Dataset Parameters */}
                        <div className="space-y-3">
                          <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Generation Params</h4>

                          <div className="space-y-1">
                            <label className="text-sm font-medium text-slate-700">Row Count</label>
                            <input
                              type="number"
                              value={synthSettings.num_rows}
                              onChange={(e) => setSynthSettings(s => ({ ...s, num_rows: parseInt(e.target.value) || 0 }))}
                              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-sm focus:ring-1 focus:ring-violet-500 outline-none"
                            />
                          </div>
                          
                          <div className="space-y-1">
                            <label className="text-sm font-medium text-slate-700">Epochs</label>
                            <input
                              type="number"
                              step="50"
                              value={synthSettings.epochs}
                              onChange={(e) => setSynthSettings(s => ({ ...s, epochs: parseInt(e.target.value) || 0 }))}
                              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-sm focus:ring-1 focus:ring-violet-500 outline-none"
                            />
                          </div>

                          <div className="space-y-1">
                            <label className="text-sm font-medium text-slate-700">Domain</label>
                            <select
                              value={synthSettings.domain}
                              onChange={(e) => setSynthSettings(s => ({ ...s, domain: e.target.value }))}
                              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-sm outline-none cursor-pointer">
                              <option>Cardiology (MIMIC-III Style)</option>
                              <option>Oncology</option>
                              <option>General Demographics</option>
                            </select>
                          </div>
                           <div className="space-y-1">
                              <label htmlFor="sensitive_column" className="text-sm font-medium text-slate-700">Fairness Column</label>
                              <select id="sensitive_column" name="sensitive_column" className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-sm outline-none cursor-pointer disabled:bg-slate-200" value={synthSettings.sensitive_column} onChange={(e) => setSynthSettings(s => ({...s, sensitive_column: e.target.value}))} disabled={!synthColumns || synthColumns.length === 0}>
                                  <option value="">None</option>
                                  {synthColumns.map(col => <option key={col} value={col}>{col}</option>)}
                              </select>
                          </div>
                        </div>

                        {/* Privacy Controls (The "Researcher" Feature) */}
                        <div className="space-y-3">
                          <div className="flex items-center justify-between">
                            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Privacy (DP)</h4>
                            <span className="text-[10px] px-1.5 py-0.5 bg-green-100 text-green-700 rounded border border-green-200">HIPAA</span>
                          </div>

                          <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                              <label className="text-slate-700">Epsilon (ε)</label>
                              <span className="font-mono text-violet-600">{synthSettings.epsilon}</span>
                            </div>
                            <input
                              type="range"
                              min="0.1"
                              max="10"
                              step="0.1"
                              value={synthSettings.epsilon}
                              onChange={(e) => setSynthSettings(s => ({ ...s, epsilon: parseFloat(e.target.value) }))}
                              className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-violet-600"
                            />
                            <p className="text-[10px] text-slate-400 leading-tight">
                              Lower ε values offer stronger privacy but lower utility. Recommended: 1.0 - 3.0.
                            </p>
                          </div>
                        </div>

                        {/* Output Format */}
                        <div className="space-y-3 pt-2 border-t border-slate-100">
                          <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Output</h4>
                          <div className="grid grid-cols-2 gap-2">
                            <button
                              onClick={() => setSynthSettings(s => ({ ...s, outputFormat: 'csv' }))}
                              className={`px-3 py-2 text-xs font-medium rounded shadow-sm transition ${synthSettings.outputFormat === 'csv' ? 'bg-violet-600 text-white' : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'}`}>
                              CSV / Pandas
                            </button>
                            <button
                              onClick={() => setSynthSettings(s => ({ ...s, outputFormat: 'fhir' }))}
                              className={`px-3 py-2 text-xs font-medium rounded shadow-sm transition ${synthSettings.outputFormat === 'fhir' ? 'bg-violet-600 text-white' : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'}`}>
                              FHIR JSON
                            </button>
                          </div>
                        </div>

                      </div>
                    )}
                    
                    {isSidebarOpen && activeTab !== 'generator' && (
                        <div className="p-4 space-y-6">
                            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                                {activeTab === 'literature' ? 'Literature' : (activeTab === 'history' ? 'Experiment History' : 'Settings')}
                            </h4>
                            <p className="text-sm text-slate-500">
                                {activeTab === 'literature' 
                                    ? 'The Literature RAG module allows you to upload research papers and perform semantic search to find relevant information.'
                                    : (activeTab === 'history' 
                                        ? 'Browse, review, and compare previous synthetic data generation runs.' 
                                        : 'Modify your user profile and application preferences in the main view.')
                                }
                            </p>
                        </div>
                    )}
                  </div>
  
                  {/* Footer User Info */}
                  {isSidebarOpen && (
                    <div className="p-4 border-t border-slate-200 bg-slate-50">
                      <div className="flex items-center gap-3">
                        <div className="h-8 w-8 rounded-full bg-violet-200 flex items-center justify-center text-violet-700 font-bold text-xs">
                             {userProfile.name ? userProfile.name.split(' ').map(n => n[0]).join('') : '?'}
                        </div>
                        <div className="flex flex-col">
                          <span className="text-sm font-medium text-slate-700">{userProfile.name}</span>
                          <span className="text-[10px] text-slate-500">{userProfile.role}</span>
                        </div>
                      </div>
                    </div>
                  )}
                </aside>

                <main className="flex-1 overflow-y-auto p-8 relative">
                    <div className="flex items-center gap-1 mb-8 border-b border-slate-200">
                        <TabButton active={activeTab === 'generator'} onClick={() => setActiveTab('generator')} icon={<Beaker size={16} />} label="Data Generator" />
                        <TabButton active={activeTab === 'history'} onClick={() => setActiveTab('history')} icon={<History size={16} />} label="History" />
                        <TabButton active={activeTab === 'literature'} onClick={() => setActiveTab('literature')} icon={<BookOpen size={16} />} label="Literature Review" />
                        <TabButton active={activeTab === 'settings'} onClick={() => setActiveTab('settings')} icon={<Settings size={16} />} label="Settings" />
                    </div>
                    <div className="max-w-7xl mx-auto">
                        {activeTab === 'generator' && renderGeneratorContent()}
                        {activeTab === 'history' && renderHistoryContent()}
                        {activeTab === 'literature' && renderLiteratureContent()}
                        {activeTab === 'settings' && renderSettingsContent()}
                    </div>
                </main>
            </div>
        </div>
    );
};

export default App;