import React, { useState } from 'react';
import Plot from 'react-plotly.js';

const SafeComponent = ({ children, data }) => {
    // Check for null, undefined, empty arrays, and empty objects
    const isEmpty = data === undefined ||
                   data === null ||
                   (Array.isArray(data) && data.length === 0) ||
                   (typeof data === 'object' && !Array.isArray(data) && Object.keys(data).length === 0);

    if (isEmpty) {
        return <div className="p-4 text-sm text-slate-500 bg-slate-50 rounded-md">Data not available for this report.</div>;
    }
    return <>{children}</>;
};

const TabButton = ({ children, onClick, isActive }) => (
    <button
        onClick={onClick}
        className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${isActive ? 'border-teal-500 text-teal-600' : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'}`}
    >
        {children}
    </button>
);

const MetricCard = ({ label, value, unit = '', helpText = '' }) => (
    <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
        <p className="text-sm text-slate-500">{label}</p>
        <p className="text-2xl font-semibold text-slate-900 mt-1">
            {value !== undefined && value !== null ? value : 'N/A'}
            <span className="text-lg ml-1 font-medium text-slate-600">{unit}</span>
        </p>
        {helpText && <p className="text-xs text-slate-400 mt-1">{helpText}</p>}
    </div>
);

const PlotlyFigure = ({ jsonFigure }) => {
    if (!jsonFigure) return <div className="p-4 text-sm text-slate-500 bg-slate-50 rounded-md">Plot not available.</div>;
    try {
        const figure = JSON.parse(jsonFigure);
        return <Plot data={figure.data} layout={figure.layout} config={{responsive: true}} useResizeHandler={true} style={{width: "100%", height: "100%"}} />;
    } catch (e) {
        console.error("Failed to parse Plotly JSON:", e);
        return <div className="p-4 text-sm text-red-500 bg-red-50 rounded-md">Could not render plot.</div>;
    }
};

// --- Main Results Component ---
const Results = ({ data }) => {
    const [activeTab, setActiveTab] = useState('data');
    if (!data) return null;

    const renderActiveTab = () => {
        switch (activeTab) {
            case 'data': return <DataTable data={data.synthetic_data} />;
            case 'quality': return <QualityReport data={data.quality_report} />;
            case 'privacy': return <PrivacyReport data={data.privacy_report} />;
            case 'fairness': return <FairnessReport data={data.fairness_report} />;
            case 'visualizations': return <Visualizations data={data.plots} />;
            default: return null;
        }
    };

    return (
        <div>
            <div className="border-b border-slate-200">
                <nav className="-mb-px flex space-x-6" aria-label="Tabs">
                    <TabButton isActive={activeTab === 'data'} onClick={() => setActiveTab('data')}>Synthetic Data</TabButton>
                    <TabButton isActive={activeTab === 'quality'} onClick={() => setActiveTab('quality')}>Quality</TabButton>
                    <TabButton isActive={activeTab === 'visualizations'} onClick={() => setActiveTab('visualizations')}>Visualizations</TabButton>
                    <TabButton isActive={activeTab === 'privacy'} onClick={() => setActiveTab('privacy')}>Privacy</TabButton>
                    {data.fairness_report && <TabButton isActive={activeTab === 'fairness'} onClick={() => setActiveTab('fairness')}>Fairness</TabButton>}
                </nav>
            </div>
            <div className="mt-6">{renderActiveTab()}</div>
        </div>
    );
};

// --- Tab Components ---
const DataTable = ({ data }) => (
    <SafeComponent data={data}>
        <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 border border-slate-200 rounded-lg">
                <thead className="bg-slate-50">
                    <tr>{data && data[0] ? Object.keys(data[0]).map(h => <th key={h} className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">{h}</th>) : null}</tr>
                </thead>
                <tbody className="bg-white divide-y divide-slate-200">
                    {Array.isArray(data) && data.slice(0, 100).map((row, i) => (
                        <tr key={i}>{row ? Object.keys(row).map(h => <td key={h} className="px-6 py-4 whitespace-nowrap text-sm text-slate-700">{row[h]}</td>) : null}</tr>
                    ))}
                </tbody>
            </table>
        </div>
    </SafeComponent>
);

const QualityReport = ({ data }) => {
    const columnStats = data?.column_stats;
    const columns = columnStats ? Object.keys(columnStats) : [];

    return (
        <SafeComponent data={columnStats}>
            <div className="space-y-4">
                <h3 className="text-lg font-semibold text-slate-800">Column Statistics Comparison</h3>
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-slate-200 border border-slate-200 rounded-lg">
                        <thead className="bg-slate-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Metric</th>
                                {columns.map(col => <th key={col} className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">{col}</th>)}
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-slate-200">
                            {['mean', 'std', 'min', '25%', '50%', '75%', 'max'].map(metric => (
                                <tr key={metric}>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-800">{metric}</td>
                                    {columns.map(col => (
                                        <td key={col} className="px-6 py-4 whitespace-nowrap text-sm text-slate-700">{columnStats[col]?.[metric] != null ? columnStats[col][metric].toFixed(4) : 'N/A'}</td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </SafeComponent>
    );
};

const PrivacyReport = ({ data }) => {
    const dcr = data?.dcr;

    return (
        <SafeComponent data={data}>
            <div className="space-y-6">
                <div>
                    <h3 className="text-lg font-semibold text-slate-800">Leakage Detection</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-2">
                        <MetricCard label="Real Rows" value={data?.total_real_rows} />
                        <MetricCard label="Synthetic Rows" value={data?.total_synthetic_rows} />
                        <MetricCard label="Leaked Rows" value={data?.leaked_rows} helpText={data?.leaked_rows > 0 ? `Privacy Score: ${data?.leaked_percentage?.toFixed(2)}%` : 'No exact matches found.'}/>
                    </div>
                </div>
                <SafeComponent data={dcr}>
                    <div>
                        <h3 className="text-lg font-semibold text-slate-800">Distance to Closest Record (DCR)</h3>
                        <p className="text-sm text-slate-600">Measures re-identification risk. Higher distances are better.</p>
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-2">
                            <MetricCard label="Min Distance" value={dcr?.min_distance?.toFixed(4)} />
                            <MetricCard label="Max Distance" value={dcr?.max_distance?.toFixed(4)} />
                            <MetricCard label="Avg Distance" value={dcr?.mean_distance?.toFixed(4)} />
                            <MetricCard label="Records Too Close" value={dcr?.too_close_percentage?.toFixed(2)} unit="%" helpText={dcr?.close_records != null ? `${dcr.close_records} records are highly similar.` : ''} />
                        </div>
                    </div>
                </SafeComponent>
            </div>
        </SafeComponent>
    );
};

const FairnessReport = ({ data }) => (
    <SafeComponent data={data}>
        <div className="space-y-4">
            <h3 className="text-lg font-semibold text-slate-800">Fairness Flip Test for column: <span className="font-mono text-teal-700 bg-teal-50 px-2 py-1 rounded-md">{data.sensitive_column}</span></h3>
             <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <MetricCard label="Fairness Score" value={data.fairness_score?.toFixed(2)} unit="%" helpText="Closer to 100% is better."/>
                <MetricCard label="Total Biased Columns" value={data.total_biased_columns} helpText="Columns with >20% difference."/>
             </div>
            <p className="text-sm text-slate-600 pt-4">The table below shows the percentage difference in outcomes when the sensitive attribute is flipped between its two groups.</p>
            <div className="overflow-x-auto">
                 <table className="min-w-full divide-y divide-slate-200 border border-slate-200 rounded-lg">
                    <thead className="bg-slate-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Column</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Outcome Diff (%)</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Biased</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-slate-200">
                        {Object.entries(data.column_stats).map(([col, stats]) => (
                            <tr key={col}>
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-800">{col}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-700">{stats.diff_percentage?.toFixed(2)}%</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-700">{stats.biased ? 'Yes' : 'No'}</td>
                            </tr>
                        ))}
                    </tbody>
                 </table>
            </div>
        </div>
    </SafeComponent>
);

const Visualizations = ({ data }) => {
    const correlations = data?.correlations;
    const distributions = data?.distributions;
    const distributionKeys = distributions ? Object.keys(distributions) : [];

    return (
        <SafeComponent data={data}>
            <div className="space-y-8">
                <SafeComponent data={correlations}>
                    <div>
                        <h3 className="text-lg font-semibold text-slate-800 mb-4">Correlation Heatmaps</h3>
                        <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
                            <div className="bg-white p-2 border border-slate-200 rounded-lg">
                                <h4 className="text-sm font-medium text-center mb-2">Original Data</h4>
                                <PlotlyFigure jsonFigure={correlations?.real} />
                            </div>
                            <div className="bg-white p-2 border border-slate-200 rounded-lg">
                                <h4 className="text-sm font-medium text-center mb-2">Synthetic Data</h4>
                                <PlotlyFigure jsonFigure={correlations?.synthetic} />
                            </div>
                            <div className="bg-white p-2 border border-slate-200 rounded-lg">
                                <h4 className="text-sm font-medium text-center mb-2">Difference</h4>
                                <PlotlyFigure jsonFigure={correlations?.diff} />
                            </div>
                        </div>
                    </div>
                </SafeComponent>
                <SafeComponent data={distributions}>
                    <div>
                        <h3 className="text-lg font-semibold text-slate-800 mb-4">Column Distributions</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {distributionKeys.map(col => (
                                <div key={col} className="bg-white p-4 border border-slate-200 rounded-lg">
                                    <h4 className="text-sm font-medium text-center mb-2 capitalize">{col.replace(/_/g, ' ')}</h4>
                                    <PlotlyFigure jsonFigure={distributions[col]} />
                                </div>
                            ))}
                        </div>
                    </div>
                </SafeComponent>
            </div>
        </SafeComponent>
    );
};

export default Results;
