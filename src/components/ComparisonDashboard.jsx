import React from 'react';
import Plot from 'react-plotly.js';

const ComparisonDashboard = ({ plots }) => {
  if (!plots) {
    return null;
  }

  const { distributions, correlations } = plots;

  // Function to render a Plotly figure from JSON string
  const renderPlot = (figJson) => {
    if (!figJson) return null;
    try {
      const fig = JSON.parse(figJson);
      return <Plot data={fig.data} layout={fig.layout} style={{ width: '100%', height: '100%' }} useResizeHandler />;
    } catch (e) {
      console.error("Failed to parse plot JSON:", e);
      return <p>Could not load plot.</p>;
    }
  };

  return (
    <div className="mt-8">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">Data Visualization Dashboard</h2>
      
      {/* Correlation Heatmaps */}
      <div className="mb-8 p-4 border rounded-lg bg-white shadow-sm">
        <h3 className="text-xl font-semibold text-gray-700 mb-3">Correlation Heatmaps</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <h4 className="text-lg font-medium text-center text-gray-600 mb-2">Original Data</h4>
            {renderPlot(correlations.real)}
          </div>
          <div>
            <h4 className="text-lg font-medium text-center text-gray-600 mb-2">Synthetic Data</h4>
            {renderPlot(correlations.synthetic)}
          </div>
          <div>
            <h4 className="text-lg font-medium text-center text-gray-600 mb-2">Difference</h4>
            {renderPlot(correlations.diff)}
          </div>
        </div>
      </div>

      {/* Distribution Plots */}
      <div className="p-4 border rounded-lg bg-white shadow-sm">
        <h3 className="text-xl font-semibold text-gray-700 mb-3">Column Distributions</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Object.keys(distributions).map(column => (
            <div key={column} className="border rounded-md p-2">
              <h4 className="text-lg font-medium text-center text-gray-600 mb-2 capitalize">{column.replace(/_/g, ' ')}</h4>
              {renderPlot(distributions[column])}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ComparisonDashboard;
