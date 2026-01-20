import React, { useState } from 'react';
import Plot from 'react-plotly.js';

const TabButton = ({ children, isActive, onClick }) => (
    <button
        onClick={onClick}
        className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors
            ${isActive
                ? 'border-teal-500 text-teal-600'
                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
            }`
        }
    >
        {children}
    </button>
);

const MetricCard = ({ label, value, unit = '', helpText = '' }) => (
    <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
        <p className="text-sm text-slate-500">{label}</p>
        <p className="text-2xl font-semibold text-slate-900 mt-1">
            {value}
            <span className="text-lg ml-1 font-medium text-slate-600">{unit}</span>
        </p>
        {helpText && <p className="text-xs text-slate-400 mt-1">{helpText}</p>}
    </div>
);


const Results = ({ data }) => {
    const [activeTab, setActiveTab] = useState('data');

    if (!data) return null;

    const renderActiveTab = () => {
        switch (activeTab) {
            case 'data':
                return <DataTable data={data.synthetic_data} />;
            case 'quality':
                return <QualityReport data={data.quality_report} />;
            case 'privacy':
                return <PrivacyReport data={data.privacy_report} />;
            case 'plots':
                return <Plots data={data.plots} />;
            default:
                return null;
        }
    };

    return (
        <div>
            <div className="border-b border-slate-200">
                <nav className="-mb-px flex space-x-6" aria-label="Tabs">
                    <TabButton isActive={activeTab === 'data'} onClick={() => setActiveTab('data')}>Synthetic Data</TabButton>
                    <TabButton isActive={activeTab === 'quality'} onClick={() => setActiveTab('quality')}>Quality</TabButton>
                    <TabButton isActive={activeTab === 'privacy'} onClick={() => setActiveTab('privacy')}>Privacy</TabButton>
                    <TabButton isActive={activeTab === 'plots'} onClick={() => setActiveTab('plots')}>Distribution Plots</TabButton>
                </nav>
            </div>
            <div className="mt-6">
                {renderActiveTab()}
            </div>
        </div>
    );
};


const DataTable = ({ data }) => {
    if (!data || data.length === 0) {
        return <p>No synthetic data to display.</p>;
    }
    const headers = Object.keys(data[0]);
    return (
        <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 border border-slate-200 rounded-lg">
                <thead className="bg-slate-50">
                    <tr>
                        {headers.map(header => (
                            <th key={header} scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                                {header}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody className="bg-white divide-y divide-slate-200">
                    {data.slice(0, 100).map((row, i) => ( // Show first 100 rows
                        <tr key={i}>
                            {headers.map(header => (
                                <td key={header} className="px-6 py-4 whitespace-nowrap text-sm text-slate-700">
                                    {row[header]}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

const QualityReport = ({ data }) => {
    const stats = data.column_stats;
    return (
        <div className="space-y-4">
             <h3 className="text-lg font-semibold text-slate-800">Column Statistics Comparison</h3>
            <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 border border-slate-200 rounded-lg">
                    <thead className="bg-slate-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Metric</th>
                            {Object.keys(stats).map(col => <th key={col} className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">{col}</th>)}
                        </tr>
                    </thead>
                     <tbody className="bg-white divide-y divide-slate-200">
                        {['mean', 'std', 'min', '25%', '50%', '75%', 'max'].map(metric => (
                            <tr key={metric}>
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-800">{metric}</td>
                                {Object.keys(stats).map(col => (
                                    <td key={col} className="px-6 py-4 whitespace-nowrap text-sm text-slate-700">
                                        {stats[col][metric] ? stats[col][metric].toFixed(4) : 'N/A'}
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

const PrivacyReport = ({ data }) => (
    <div className="space-y-4">
        <h3 className="text-lg font-semibold text-slate-800">Privacy Check</h3>
         <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <MetricCard label="Real Rows" value={data.total_real_rows} />
            <MetricCard label="Synthetic Rows" value={data.total_synthetic_rows} />
            <MetricCard
                label="Leaked Rows"
                value={data.leaked_rows}
                helpText={data.leaked_rows > 0 ? `Privacy Score: ${data.leaked_percentage.toFixed(2)}%` : 'No exact matches found.'}
            />
        </div>
        {data.leaked_rows > 0 ? (
            <div className="p-4 bg-amber-50 text-amber-800 border border-amber-200 rounded-lg">
                <p className="font-medium">Warning: {data.leaked_rows} rows from the synthetic data are exact copies of rows in the real data. Consider adjusting model parameters.</p>
            </div>
        ) : (
             <div className="p-4 bg-green-50 text-green-800 border border-green-200 rounded-lg">
                <p className="font-medium">Success: The synthetic data appears to be privacy-safe, with no leaked rows detected.</p>
            </div>
        )}
    </div>
);

const Plots = ({ data }) => (
    <div className="space-y-8">
        <div>
            <h3 className="text-lg font-semibold text-slate-800 mb-4">Correlation Heatmaps</h3>
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                <div className="bg-white p-2 border border-slate-200 rounded-lg">
                    <h4 className="text-sm font-medium text-center mb-2">Real Data</h4>
                    <Plot data={JSON.parse(data.correlations.real).data} layout={JSON.parse(data.correlations.real).layout} config={{responsive: true}} useResizeHandler={true} style={{width: "100%", height: "100%"}} />
                </div>
                 <div className="bg-white p-2 border border-slate-200 rounded-lg">
                    <h4 className="text-sm font-medium text-center mb-2">Synthetic Data</h4>
                    <Plot data={JSON.parse(data.correlations.synthetic).data} layout={JSON.parse(data.correlations.synthetic).layout} config={{responsive: true}} useResizeHandler={true} style={{width: "100%", height: "100%"}}/>
                </div>
            </div>
        </div>
        <div>
            <h3 className="text-lg font-semibold text-slate-800 mb-4">Column Distributions</h3>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                 {Object.keys(data.distributions).map(col => (
                    <div key={col} className="bg-white p-4 border border-slate-200 rounded-lg">
                         <Plot data={JSON.parse(data.distributions[col]).data} layout={JSON.parse(data.distributions[col]).layout} config={{responsive: true}} useResizeHandler={true} style={{width: "100%", height: "100%"}}/>
                    </div>
                ))}
            </div>
        </div>
    </div>
);


export default Results;
