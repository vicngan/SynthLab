import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Loader2, AlertCircle, SlidersHorizontal, FileText, BookText, Edit, Save, GitFork, Download, FileSignature, Activity } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import ComparisonDashboard from './ComparisonDashboard';

const DetailItem = ({ label, value }) => (
    <div className="flex justify-between py-2 border-b border-slate-100">
        <span className="text-sm font-medium text-slate-500">{label}</span>
        <span className="text-sm font-semibold text-slate-700">{value}</span>
    </div>
);

const ExperimentDetail = ({ experimentId, onFork }) => {
    const [experiment, setExperiment] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [notes, setNotes] = useState("");
    const [isEditingNotes, setIsEditingNotes] = useState(false);

    useEffect(() => {
        const fetchExperiment = async () => {
            try {
                setLoading(true);
                const response = await axios.get(`http://127.0.0.1:8000/api/experiments/${experimentId}`);
                setExperiment(response.data);
                setNotes(response.data.notes || "");
                setError(null);
            } catch (err) {
                setError('Failed to fetch experiment details.');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        if (experimentId) {
            fetchExperiment();
        }
    }, [experimentId]);

    const handleSaveNotes = async () => {
        try {
            // Assuming an endpoint exists to update notes
            await axios.put(`http://127.0.0.1:8000/api/experiments/${experimentId}/notes`, { notes });
            setIsEditingNotes(false);
        } catch (err) {
            console.error("Failed to save notes", err);
            // In a real app, show a toast notification here
        }
    };

    if (loading) return <div className="flex justify-center p-12"><Loader2 className="animate-spin text-violet-500" size={32} /></div>;
    if (error) return <div className="p-8 text-red-500 flex items-center gap-2"><AlertCircle /> {error}</div>;
    if (!experiment) return null;

    // Handle both flat and nested config structures safely
    const config = experiment?.config || experiment;

    return (
        <div className="space-y-8">
            {/* Configuration Section */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
                <div className="flex justify-between items-center mb-4">
                    <h3 className="text-xl font-semibold text-slate-800 flex items-center gap-2">
                        <SlidersHorizontal size={20} />
                        <span>Configuration</span>
                    </h3>
                    <div className="flex gap-2">
                        {config?.status === 'completed' && (
                            <>
                                <button 
                                    onClick={() => window.open(`http://127.0.0.1:8000/api/experiments/${experimentId}/certificate`, '_blank')}
                                    className="flex items-center gap-1.5 text-sm font-medium px-3 py-1 rounded-md bg-white text-slate-700 hover:bg-slate-50 border border-slate-200 shadow-sm"
                                >
                                    <FileSignature size={14} />
                                    Certificate
                                </button>
                                <button 
                                    onClick={() => window.open(`http://127.0.0.1:8000/api/experiments/${experimentId}/download/fhir`, '_blank')}
                                    className="flex items-center gap-1.5 text-sm font-medium px-3 py-1 rounded-md bg-white text-slate-700 hover:bg-slate-50 border border-slate-200 shadow-sm"
                                >
                                    <Activity size={14} />
                                    FHIR JSON
                                </button>
                                <button 
                                    onClick={() => window.open(`http://127.0.0.1:8000/api/experiments/${experimentId}/download`, '_blank')}
                                    className="flex items-center gap-1.5 text-sm font-medium px-3 py-1 rounded-md bg-white text-slate-700 hover:bg-slate-50 border border-slate-200 shadow-sm"
                                >
                                    <Download size={14} />
                                    Download CSV
                                </button>
                            </>
                        )}
                        <button 
                            onClick={() => onFork(config)}
                            className="flex items-center gap-1.5 text-sm font-medium px-3 py-1 rounded-md bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200"
                        >
                            <GitFork size={14} />
                            Fork Experiment
                        </button>
                    </div>
                </div>
                <div className="space-y-1">
                    <DetailItem label="Experiment ID" value={config?.experiment_id} />
                    <DetailItem label="Timestamp" value={config?.timestamp ? new Date(config.timestamp).toLocaleString() : 'N/A'} />
                    <DetailItem label="Privacy (Epsilon)" value={config?.epsilon} />
                </div>
            </div>

            {/* Annotations Section */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
                <div className="flex justify-between items-center mb-4">
                    <h3 className="text-xl font-semibold text-slate-800 flex items-center gap-2">
                        <FileText size={20} />
                        <span>Lab Notebook / Annotations</span>
                    </h3>
                    <button 
                        onClick={isEditingNotes ? handleSaveNotes : () => setIsEditingNotes(true)}
                        className={`flex items-center gap-1.5 text-sm font-medium px-3 py-1 rounded-md border ${isEditingNotes ? 'bg-teal-50 text-teal-700 border-teal-200 hover:bg-teal-100' : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'}`}
                    >
                        {isEditingNotes ? <><Save size={14} /> Save</> : <><Edit size={14} /> Edit</>}
                    </button>
                </div>
                {isEditingNotes ? (
                    <textarea 
                        value={notes} 
                        onChange={(e) => setNotes(e.target.value)} 
                        className="w-full h-48 p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-transparent font-mono text-sm"
                        placeholder="Add markdown notes here..."
                    />
                ) : (
                    <div className="prose prose-slate max-w-none">
                        {notes ? <ReactMarkdown remarkPlugins={[remarkGfm]}>{notes}</ReactMarkdown> : <p className="text-slate-400 italic">No notes added.</p>}
                    </div>
                )}
            </div>
            
            {/* Results Dashboard */}
            {experiment.plots && <ComparisonDashboard plots={experiment.plots} experimentId={experimentId} />}
        </div>
    );
};

export default ExperimentDetail;
