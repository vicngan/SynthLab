import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { History, ChevronsRight, Loader2 } from 'lucide-react';
import ExperimentDetail from './ExperimentDetail'; // Will create this next

const ExperimentHistory = ({ onFork }) => {
    const [experiments, setExperiments] = useState([]);
    const [selectedExperimentId, setSelectedExperimentId] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchExperiments = async () => {
            try {
                setLoading(true);
                const response = await axios.get('http://127.0.0.1:8000/api/experiments');
                setExperiments(response.data);
                setError(null);
            } catch (err) {
                setError('Failed to fetch experiment history.');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchExperiments();
    }, []);

    const formatDate = (isoString) => {
        if (!isoString) return 'N/A';
        return new Date(isoString).toLocaleString(undefined, {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: 'numeric',
            minute: '2-digit'
        });
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-48">
                <Loader2 className="animate-spin text-violet-500" size={32} />
                <p className="ml-4 text-slate-600">Loading Experiment History...</p>
            </div>
        );
    }
    
    if (error) {
        return <p className="text-red-500">{error}</p>;
    }

    return (
        <div className="flex gap-8 items-start">
            {/* Sidebar with list of experiments */}
            <div className="w-1/3 bg-white rounded-xl shadow-sm border border-slate-200 p-4 self-start">
                <h2 className="text-xl font-semibold text-slate-800 mb-4 flex items-center gap-2">
                    <History size={20} />
                    <span>Run History</span>
                </h2>
                <div className="space-y-2 max-h-[70vh] overflow-y-auto custom-scrollbar">
                    {experiments.length > 0 ? experiments.map(exp => (
                        <button
                            key={exp.experiment_id}
                            onClick={() => setSelectedExperimentId(exp.experiment_id)}
                            className={`w-full text-left p-3 rounded-lg border transition-all ${selectedExperimentId === exp.experiment_id ? 'bg-violet-50 border-violet-300 shadow' : 'bg-slate-50 border-slate-200 hover:bg-slate-100'}`}
                        >
                            <p className="font-semibold text-sm text-slate-700">{exp.method}</p>
                            <p className="text-xs text-slate-500">{formatDate(exp.timestamp)}</p>
                            <p className="text-[10px] font-mono text-slate-400 mt-1 truncate">ID: {exp.experiment_id}</p>
                        </button>
                    )) : <p className="text-sm text-slate-500 p-3">No experiments found.</p>}
                </div>
            </div>

            {/* Main content area for details */}
            <div className="w-2/3">
                {selectedExperimentId ? (
                    <ExperimentDetail experimentId={selectedExperimentId} onFork={onFork} />
                ) : (
                    <div className="flex flex-col items-center justify-center h-96 bg-white rounded-xl shadow-sm border border-slate-200 text-center p-8">
                        <ChevronsRight size={48} className="text-slate-300 mb-4" />
                        <h3 className="text-xl font-semibold text-slate-700">Select an Experiment</h3>
                        <p className="text-slate-500 mt-2">Choose an experiment from the list to view its detailed configuration and results.</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ExperimentHistory;
