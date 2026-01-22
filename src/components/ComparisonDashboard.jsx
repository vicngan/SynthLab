import React, { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';
import axios from 'axios';
import AnnotationLayer from './AnnotationLayer';

const ComparisonDashboard = ({ plots, experimentId }) => {
  const [selectedGraph, setSelectedGraph] = useState(null);
  const [annotations, setAnnotations] = useState([]);

  // Load annotations when experiment ID is available
  useEffect(() => {
    if (experimentId) {
      axios.get(`http://127.0.0.1:8000/api/experiments/${experimentId}/annotations`)
        .then(res => setAnnotations(res.data.graph_annotations || []))
        .catch(err => console.error('Failed to load annotations:', err));
    }
  }, [experimentId]);

  if (!plots) {
    return null;
  }

  // Count annotations per graph
  const getAnnotationCount = (graphId) => {
    return annotations.filter(a => a.graphId === graphId).length;
  };

  const { distributions, correlations } = plots;

  // Function to render a Plotly figure from JSON string (full size)
  const renderPlot = (figJson) => {
    if (!figJson) return <p className="text-sm text-slate-500 p-4 bg-slate-50 rounded">Plot data not available.</p>;
    try {
      const fig = JSON.parse(figJson);
      return <Plot data={fig.data} layout={{...fig.layout, autosize: true}} style={{ width: '100%', height: '100%' }} useResizeHandler />;
    } catch (e) {
      console.error("Failed to parse plot JSON:", e);
      return <p className="text-sm text-red-500">Could not load plot.</p>;
    }
  };

  // Function to render a clickable thumbnail card
  const renderCard = (title, figJson, graphId) => {
    if (!figJson) return (
      <div className="bg-slate-50 p-4 border rounded-lg">
        <h4 className="text-sm font-medium text-center text-slate-600 mb-2">{title}</h4>
        <p className="text-sm text-slate-500 text-center">Not available</p>
      </div>
    );

    try {
      const fig = JSON.parse(figJson);
      const noteCount = getAnnotationCount(graphId);
      return (
        <div
          onClick={() => setSelectedGraph({ title, figJson, graphId })}
          className="bg-white p-3 border rounded-lg cursor-pointer hover:shadow-lg hover:border-teal-300 transition-all relative"
        >
          <h4 className="text-sm font-medium text-center text-slate-700 mb-2">{title}</h4>
          <div className="h-48 pointer-events-none">
            <Plot
              data={fig.data}
              layout={{...fig.layout, autosize: true, showlegend: false, margin: {l: 30, r: 30, t: 20, b: 30}}}
              config={{ staticPlot: true, displayModeBar: false }}
              style={{ width: '100%', height: '100%' }}
            />
          </div>
          <div className="flex items-center justify-center gap-2 mt-2">
            <p className="text-xs text-teal-600">Click to expand</p>
            {noteCount > 0 && (
              <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full">
                {noteCount} note{noteCount !== 1 ? 's' : ''}
              </span>
            )}
          </div>
        </div>
      );
    } catch (e) {
      return (
        <div className="bg-slate-50 p-4 border rounded-lg">
          <h4 className="text-sm font-medium text-center text-slate-600 mb-2">{title}</h4>
          <p className="text-sm text-red-500 text-center">Could not load plot</p>
        </div>
      );
    }
  };

  return (
    <div className="mt-8">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">Data Visualization Dashboard</h2>

      {/* Correlation Heatmaps */}
      {correlations && (
        <div className="mb-8 p-4 border rounded-lg bg-white shadow-sm">
          <h3 className="text-xl font-semibold text-gray-700 mb-3">Correlation Heatmaps</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {renderCard('Original Data', correlations?.real, 'correlations.real')}
            {renderCard('Synthetic Data', correlations?.synthetic, 'correlations.synthetic')}
            {renderCard('Difference', correlations?.diff, 'correlations.diff')}
          </div>
        </div>
      )}

      {/* Distribution Plots */}
      {distributions && Object.keys(distributions).length > 0 && (
        <div className="p-4 border rounded-lg bg-white shadow-sm">
          <h3 className="text-xl font-semibold text-gray-700 mb-3">Column Distributions</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Object.keys(distributions).map(column => (
              <div key={column}>
                {renderCard(column.replace(/_/g, ' '), distributions[column], `distributions.${column}`)}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Graph Modal */}
      {selectedGraph && (
        <div
          className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
          onClick={() => setSelectedGraph(null)}
        >
          <div
            className="bg-white rounded-xl max-w-5xl w-full max-h-[90vh] overflow-hidden shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-center p-4 border-b">
              <h3 className="text-lg font-semibold text-slate-800 capitalize">{selectedGraph.title}</h3>
              <button
                onClick={() => setSelectedGraph(null)}
                className="text-slate-400 hover:text-slate-600 text-2xl leading-none"
              >
                &times;
              </button>
            </div>
            <div className="p-4 relative" style={{ height: '70vh' }}>
              {renderPlot(selectedGraph.figJson)}
              {/* Annotation Layer - only show when viewing from history (experimentId available) */}
              {experimentId && (
                <div className="absolute inset-4">
                  <AnnotationLayer
                    experimentId={experimentId}
                    graphId={selectedGraph.graphId}
                    annotations={annotations}
                    onAnnotationsChange={setAnnotations}
                  />
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ComparisonDashboard;
