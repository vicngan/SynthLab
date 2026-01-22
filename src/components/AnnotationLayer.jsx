import React, { useState } from 'react';
import axios from 'axios';

const AnnotationLayer = ({ experimentId, graphId, annotations = [], onAnnotationsChange }) => {
    const [isAddingMode, setIsAddingMode] = useState(false);
    const [selectedAnnotation, setSelectedAnnotation] = useState(null);
    const [newComment, setNewComment] = useState('');
    const [pendingPosition, setPendingPosition] = useState(null);

    const handleLayerClick = (e) => {
        if (!isAddingMode) return;

        const rect = e.currentTarget.getBoundingClientRect();
        const x = ((e.clientX - rect.left) / rect.width) * 100;
        const y = ((e.clientY - rect.top) / rect.height) * 100;

        setPendingPosition({ x, y });
        setNewComment('');
    };

    const handleSaveAnnotation = async () => {
        if (!pendingPosition || !newComment.trim()) return;

        try {
            const response = await axios.post(
                `http://127.0.0.1:8000/api/experiments/${experimentId}/annotations`,
                {
                    graphId,
                    x: pendingPosition.x,
                    y: pendingPosition.y,
                    comment: newComment.trim(),
                    author: 'User'
                }
            );

            onAnnotationsChange([...annotations, response.data]);
            setPendingPosition(null);
            setNewComment('');
            setIsAddingMode(false);
        } catch (error) {
            console.error('Failed to save annotation:', error);
        }
    };

    const handleDeleteAnnotation = async (annotationId) => {
        try {
            await axios.delete(
                `http://127.0.0.1:8000/api/experiments/${experimentId}/annotations/${annotationId}`
            );
            onAnnotationsChange(annotations.filter(a => a.id !== annotationId));
            setSelectedAnnotation(null);
        } catch (error) {
            console.error('Failed to delete annotation:', error);
        }
    };

    const graphAnnotations = annotations.filter(a => a.graphId === graphId);

    return (
        <div className="relative w-full h-full">
            {/* Annotation toggle button */}
            <div className="absolute top-2 right-2 z-20 flex gap-2">
                <button
                    onClick={() => {
                        setIsAddingMode(!isAddingMode);
                        setPendingPosition(null);
                        setSelectedAnnotation(null);
                    }}
                    className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                        isAddingMode
                            ? 'bg-teal-500 text-white'
                            : 'bg-white border border-slate-300 text-slate-600 hover:bg-slate-50'
                    }`}
                >
                    {isAddingMode ? 'Cancel' : '+ Add Note'}
                </button>
            </div>

            {/* Clickable overlay for adding annotations */}
            {isAddingMode && (
                <div
                    className="absolute inset-0 cursor-crosshair z-10"
                    onClick={handleLayerClick}
                    style={{ background: 'rgba(0,0,0,0.02)' }}
                />
            )}

            {/* Annotation markers */}
            {graphAnnotations.map((annotation) => (
                <div
                    key={annotation.id}
                    className="absolute z-10 cursor-pointer transform -translate-x-1/2 -translate-y-1/2"
                    style={{ left: `${annotation.x}%`, top: `${annotation.y}%` }}
                    onClick={(e) => {
                        e.stopPropagation();
                        setSelectedAnnotation(selectedAnnotation?.id === annotation.id ? null : annotation);
                    }}
                >
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shadow-md transition-transform hover:scale-110 ${
                        selectedAnnotation?.id === annotation.id
                            ? 'bg-teal-500 text-white ring-2 ring-teal-300'
                            : 'bg-amber-400 text-amber-900'
                    }`}>
                        !
                    </div>
                </div>
            ))}

            {/* Pending annotation input */}
            {pendingPosition && (
                <div
                    className="absolute z-30 bg-white rounded-lg shadow-xl border border-slate-200 p-3 w-64"
                    style={{
                        left: `${Math.min(pendingPosition.x, 70)}%`,
                        top: `${Math.min(pendingPosition.y, 70)}%`
                    }}
                    onClick={(e) => e.stopPropagation()}
                >
                    <div className="text-xs font-medium text-slate-500 mb-2">Add annotation</div>
                    <textarea
                        value={newComment}
                        onChange={(e) => setNewComment(e.target.value)}
                        placeholder="Enter your note..."
                        className="w-full p-2 text-sm border border-slate-200 rounded-md resize-none focus:outline-none focus:ring-1 focus:ring-teal-500"
                        rows={3}
                        autoFocus
                    />
                    <div className="flex justify-end gap-2 mt-2">
                        <button
                            onClick={() => {
                                setPendingPosition(null);
                                setNewComment('');
                            }}
                            className="px-3 py-1 text-xs text-slate-500 hover:text-slate-700"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={handleSaveAnnotation}
                            disabled={!newComment.trim()}
                            className="px-3 py-1 text-xs bg-teal-500 text-white rounded-md hover:bg-teal-600 disabled:opacity-50"
                        >
                            Save
                        </button>
                    </div>
                </div>
            )}

            {/* Selected annotation detail */}
            {selectedAnnotation && !pendingPosition && (
                <div
                    className="absolute z-30 bg-white rounded-lg shadow-xl border border-slate-200 p-3 w-64"
                    style={{
                        left: `${Math.min(selectedAnnotation.x, 70)}%`,
                        top: `${Math.min(selectedAnnotation.y + 5, 70)}%`
                    }}
                    onClick={(e) => e.stopPropagation()}
                >
                    <div className="flex justify-between items-start mb-2">
                        <span className="text-xs text-slate-400">
                            {selectedAnnotation.author} &middot; {new Date(selectedAnnotation.timestamp).toLocaleDateString()}
                        </span>
                        <button
                            onClick={() => handleDeleteAnnotation(selectedAnnotation.id)}
                            className="text-red-400 hover:text-red-600 text-xs"
                        >
                            Delete
                        </button>
                    </div>
                    <p className="text-sm text-slate-700">{selectedAnnotation.comment}</p>
                </div>
            )}

            {/* Annotation count badge */}
            {graphAnnotations.length > 0 && !isAddingMode && (
                <div className="absolute bottom-2 right-2 z-10 bg-amber-100 text-amber-800 px-2 py-1 rounded-full text-xs font-medium">
                    {graphAnnotations.length} note{graphAnnotations.length !== 1 ? 's' : ''}
                </div>
            )}
        </div>
    );
};

export default AnnotationLayer;
