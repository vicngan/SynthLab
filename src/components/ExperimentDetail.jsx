import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Loader2, AlertCircle, SlidersHorizontal, FileText, BookText, Edit, Save, GitFork } from 'lucide-react';
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
...
    return (
        <div className="space-y-8">
            {/* Configuration Section */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
                <div className="flex justify-between items-center mb-4">
                    <h3 className="text-xl font-semibold text-slate-800 flex items-center gap-2">
                        <SlidersHorizontal size={20} />
                        <span>Configuration</span>
                    </h3>
                    <button 
                        onClick={() => onFork(experiment.config)}
                        className="flex items-center gap-1.5 text-sm font-medium px-3 py-1 rounded-md bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200"
                    >
                        <GitFork size={14} />
                        Fork Experiment
                    </button>
                </div>
                <div className="space-y-1">
                    <DetailItem label="Experiment ID" value={config.experiment_id} />
                    <DetailItem label="Timestamp" value={new Date(config.timestamp).toLocaleString()} />
...
                    <DetailItem label="Fairness Column" value={config.sensitive_column || 'N/A'} />
                    <DetailItem label="Privacy (Epsilon)" value={config.epsilon} />
                </div>
            </div>

            {/* Annotations Section */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
...
        </div>
    );
};

export default ExperimentDetail;
