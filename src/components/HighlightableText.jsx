import React, { useState, useRef, useEffect } from 'react';

const HIGHLIGHT_COLORS = {
    yellow: { bg: 'bg-yellow-200', border: 'border-yellow-300', text: 'text-yellow-800' },
    green: { bg: 'bg-green-200', border: 'border-green-300', text: 'text-green-800' },
    blue: { bg: 'bg-blue-200', border: 'border-blue-300', text: 'text-blue-800' },
    pink: { bg: 'bg-pink-200', border: 'border-pink-300', text: 'text-pink-800' },
};

const HighlightableText = ({
    text,
    highlights = [],
    onAddHighlight,
    onDeleteHighlight,
    readOnly = false
}) => {
    const [selection, setSelection] = useState(null);
    const [showPopup, setShowPopup] = useState(false);
    const [popupPosition, setPopupPosition] = useState({ x: 0, y: 0 });
    const [newComment, setNewComment] = useState('');
    const [selectedColor, setSelectedColor] = useState('yellow');
    const [activeHighlight, setActiveHighlight] = useState(null);
    const containerRef = useRef(null);

    useEffect(() => {
        const handleClickOutside = (e) => {
            if (containerRef.current && !containerRef.current.contains(e.target)) {
                setShowPopup(false);
                setSelection(null);
                setActiveHighlight(null);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleMouseUp = () => {
        if (readOnly) return;

        const sel = window.getSelection();
        if (sel.toString().length > 0 && containerRef.current) {
            const range = sel.getRangeAt(0);
            const rect = range.getBoundingClientRect();
            const containerRect = containerRef.current.getBoundingClientRect();

            // Calculate selection positions relative to text
            const preCaretRange = range.cloneRange();
            preCaretRange.selectNodeContents(containerRef.current);
            preCaretRange.setEnd(range.startContainer, range.startOffset);
            const start = preCaretRange.toString().length;
            const end = start + sel.toString().length;

            setSelection({ start, end, text: sel.toString() });
            setPopupPosition({
                x: rect.left - containerRect.left + rect.width / 2,
                y: rect.top - containerRect.top - 10
            });
            setShowPopup(true);
            setActiveHighlight(null);
        }
    };

    const handleSaveHighlight = () => {
        if (!selection || !onAddHighlight) return;

        onAddHighlight({
            start: selection.start,
            end: selection.end,
            comment: newComment.trim(),
            color: selectedColor
        });

        setSelection(null);
        setShowPopup(false);
        setNewComment('');
        window.getSelection().removeAllRanges();
    };

    const handleHighlightClick = (highlight, e) => {
        e.stopPropagation();
        const rect = e.target.getBoundingClientRect();
        const containerRect = containerRef.current.getBoundingClientRect();

        setActiveHighlight(highlight);
        setPopupPosition({
            x: rect.left - containerRect.left + rect.width / 2,
            y: rect.bottom - containerRect.top + 5
        });
        setShowPopup(true);
        setSelection(null);
    };

    // Render text with highlights
    const renderHighlightedText = () => {
        if (!highlights || highlights.length === 0) {
            return <span>{text}</span>;
        }

        // Sort highlights by start position
        const sortedHighlights = [...highlights].sort((a, b) => a.start - b.start);
        const elements = [];
        let lastEnd = 0;

        sortedHighlights.forEach((highlight, index) => {
            // Text before highlight
            if (highlight.start > lastEnd) {
                elements.push(
                    <span key={`text-${index}`}>
                        {text.slice(lastEnd, highlight.start)}
                    </span>
                );
            }

            // Highlighted text
            const colorClasses = HIGHLIGHT_COLORS[highlight.color] || HIGHLIGHT_COLORS.yellow;
            elements.push(
                <mark
                    key={`highlight-${highlight.id || index}`}
                    className={`${colorClasses.bg} px-0.5 rounded cursor-pointer hover:ring-2 hover:ring-offset-1 ${colorClasses.border}`}
                    onClick={(e) => handleHighlightClick(highlight, e)}
                    title={highlight.comment || 'Click to view'}
                >
                    {text.slice(highlight.start, highlight.end)}
                </mark>
            );

            lastEnd = highlight.end;
        });

        // Text after last highlight
        if (lastEnd < text.length) {
            elements.push(
                <span key="text-end">{text.slice(lastEnd)}</span>
            );
        }

        return elements;
    };

    return (
        <div ref={containerRef} className="relative">
            <div
                onMouseUp={handleMouseUp}
                className="text-sm text-slate-700 leading-relaxed select-text"
            >
                {renderHighlightedText()}
            </div>

            {/* Popup for new highlight or viewing existing */}
            {showPopup && (
                <div
                    className="absolute z-50 bg-white rounded-lg shadow-xl border border-slate-200 p-3 w-72"
                    style={{
                        left: `${Math.min(Math.max(popupPosition.x - 144, 0), 200)}px`,
                        top: `${popupPosition.y}px`,
                        transform: selection ? 'translateY(-100%)' : 'none'
                    }}
                >
                    {selection && !activeHighlight ? (
                        // New highlight form
                        <div className="space-y-3">
                            <div className="text-xs text-slate-500 font-medium">Add Highlight</div>
                            <div className="bg-slate-50 p-2 rounded text-xs text-slate-600 max-h-16 overflow-hidden">
                                "{selection.text.slice(0, 100)}{selection.text.length > 100 ? '...' : ''}"
                            </div>
                            <div className="flex gap-2">
                                {Object.entries(HIGHLIGHT_COLORS).map(([color, classes]) => (
                                    <button
                                        key={color}
                                        onClick={() => setSelectedColor(color)}
                                        className={`w-6 h-6 rounded-full ${classes.bg} ${
                                            selectedColor === color ? 'ring-2 ring-offset-1 ring-slate-400' : ''
                                        }`}
                                    />
                                ))}
                            </div>
                            <textarea
                                value={newComment}
                                onChange={(e) => setNewComment(e.target.value)}
                                placeholder="Add a note (optional)..."
                                className="w-full p-2 text-sm border border-slate-200 rounded resize-none focus:outline-none focus:ring-1 focus:ring-violet-500"
                                rows={2}
                            />
                            <div className="flex justify-end gap-2">
                                <button
                                    onClick={() => {
                                        setShowPopup(false);
                                        setSelection(null);
                                        window.getSelection().removeAllRanges();
                                    }}
                                    className="px-3 py-1 text-xs text-slate-500 hover:text-slate-700"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleSaveHighlight}
                                    className="px-3 py-1 text-xs bg-violet-500 text-white rounded hover:bg-violet-600"
                                >
                                    Highlight
                                </button>
                            </div>
                        </div>
                    ) : activeHighlight ? (
                        // View existing highlight
                        <div className="space-y-2">
                            <div className="flex justify-between items-start">
                                <div className="flex items-center gap-2">
                                    <div className={`w-3 h-3 rounded-full ${HIGHLIGHT_COLORS[activeHighlight.color]?.bg || 'bg-yellow-200'}`} />
                                    <span className="text-xs text-slate-400">
                                        {activeHighlight.timestamp ? new Date(activeHighlight.timestamp).toLocaleDateString() : 'Note'}
                                    </span>
                                </div>
                                {onDeleteHighlight && !readOnly && (
                                    <button
                                        onClick={() => {
                                            onDeleteHighlight(activeHighlight.id);
                                            setShowPopup(false);
                                            setActiveHighlight(null);
                                        }}
                                        className="text-xs text-red-400 hover:text-red-600"
                                    >
                                        Delete
                                    </button>
                                )}
                            </div>
                            {activeHighlight.comment ? (
                                <p className="text-sm text-slate-700">{activeHighlight.comment}</p>
                            ) : (
                                <p className="text-sm text-slate-400 italic">No note added</p>
                            )}
                        </div>
                    ) : null}
                </div>
            )}
        </div>
    );
};

export default HighlightableText;
