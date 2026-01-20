import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Loader2, AlertCircle, SlidersHorizontal, FileText } from 'lucide-react';
import ComparisonDashboard from './ComparisonDashboard';

const DetailItem = ({ label, value }) => (
    <div className="flex justify-between py-2 border-b border-slate-100">
        <span className="text-sm font-medium text-slate-500">{label}</span>
        <span className="text-sm font-semibold text-slate-700">{value}</span>
    </div>
);

const ExperimentDetail = ({ experimentId }) => {
    const [experiment, setExperiment] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!experimentId) return;

        const fetchExperimentDetails = async () => {
            try {
                setLoading(true);
                setError(null);
                const response = await axios.get(`http://127.0.0.1:8000/api/experiments/${experimentId}`);
                setExperiment(response.data);
            } catch (err) {
                setError('Failed to load experiment details.');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        fetchExperimentDetails();
    }, [experimentId]);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-96">
                <Loader2 className="animate-spin text-violet-500" size={28} />
                <p className="ml-3 text-slate-600">Loading Details...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-4 bg-red-50 text-red-700 border border-red-200 rounded-lg flex items-center">
                <AlertCircle className="w-5 h-5 mr-3"/>{error}
            </div>
        );
    }

    if (!experiment) {
        return null;
    }

    const { config } = experiment;

    return (
        <div className="space-y-8">
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
                <h3 className="text-xl font-semibold text-slate-800 mb-4 flex items-center gap-2">
                    <SlidersHorizontal size={20} />
                    <span>Configuration</span>
                </h3>
                <div className="space-y-1">
                    <DetailItem label="Experiment ID" value={config.experiment_id} />
                    <DetailItem label="Timestamp" value={new Date(config.timestamp).toLocaleString()} />
                    <DetailItem label="Original File" value={config.original_filename} />
                    <DetailItem label="Synthesis Method" value={config.method} />
                    <DetailItem label="Epochs" value={config.epochs} />
                    <DetailItem label="Rows Generated" value={config.num_rows} />
                    <DetailItem label="Fairness Column" value={config.sensitive_column || 'N/A'} />
                    <DetailItem label="Privacy (Epsilon)" value={config.epsilon} />
                </div>
            </div>
            
            <div className="bg-white rounded-xl shadow-sm border border-slate-200">
                <div className="p-8">
                    <h3 className="text-xl font-semibold text-slate-800 mb-4 flex items-center gap-2">
                        <FileText size={20} />
                        <span>Reports & Visuals</span>
                    </h3>
                </div>
                {/* The dashboard is rendered inside a container that doesn't have default padding */}
                <ComparisonDashboard plots={experiment.plots} />
            </div>
        </div>
    );
};

export default ExperimentDetail;
