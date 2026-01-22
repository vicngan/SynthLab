import React, { useState, useEffect } from 'react';
import axios from 'axios';

const LiteratureHistory = ({ onLoadSession }) => {
    const [sessions, setSessions] = useState([]);
    const [selectedSession, setSelectedSession] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchSessions();
    }, []);

    const fetchSessions = async () => {
        try {
            setLoading(true);
            const response = await axios.get('http://127.0.0.1:8000/api/literature/sessions');
            setSessions(response.data);
            setError(null);
        } catch (err) {
            setError('Failed to load literature sessions');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleLoadSession = async (sessionId) => {
        try {
            const response = await axios.get(`http://127.0.0.1:8000/api/literature/sessions/${sessionId}/load`);
            onLoadSession(response.data);
        } catch (err) {
            alert('Failed to load session: ' + (err.response?.data?.detail || err.message));
        }
    };

    const handleDeleteSession = async (sessionId) => {
        if (!window.confirm('Are you sure you want to delete this session? This cannot be undone.')) {
            return;
        }

        try {
            await axios.delete(`http://127.0.0.1:8000/api/literature/sessions/${sessionId}`);
            setSessions(sessions.filter(s => s.session_id !== sessionId));
            if (selectedSession?.session_id === sessionId) {
                setSelectedSession(null);
            }
        } catch (err) {
            alert('Failed to delete session');
        }
    };

    const fetchSessionQueries = async (sessionId) => {
        try {
            const response = await axios.get(`http://127.0.0.1:8000/api/literature/sessions/${sessionId}/queries`);
            return response.data.queries || [];
        } catch (err) {
            console.error('Failed to load queries:', err);
            return [];
        }
    };

    const handleSelectSession = async (session) => {
        const queries = await fetchSessionQueries(session.session_id);
        setSelectedSession({ ...session, queries });
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-teal-500"></div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-4 bg-red-50 text-red-600 rounded-md">
                {error}
                <button onClick={fetchSessions} className="ml-4 text-sm underline">
                    Retry
                </button>
            </div>
        );
    }

    if (sessions.length === 0) {
        return (
            <div className="text-center py-12">
                <div className="text-slate-400 mb-4">
                    <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                    </svg>
                </div>
                <h3 className="text-lg font-medium text-slate-700 mb-2">No saved sessions</h3>
                <p className="text-sm text-slate-500">Upload PDFs and save your literature review sessions to see them here.</p>
            </div>
        );
    }

    return (
        <div className="flex h-[600px] border border-slate-200 rounded-lg overflow-hidden">
            {/* Session List */}
            <div className="w-1/3 border-r border-slate-200 overflow-y-auto bg-slate-50">
                <div className="p-3 border-b border-slate-200 bg-white">
                    <h3 className="font-semibold text-slate-700">Saved Sessions</h3>
                </div>
                <div className="divide-y divide-slate-200">
                    {sessions.map((session) => (
                        <div
                            key={session.session_id}
                            onClick={() => handleSelectSession(session)}
                            className={`p-4 cursor-pointer hover:bg-white transition-colors ${
                                selectedSession?.session_id === session.session_id ? 'bg-white border-l-2 border-teal-500' : ''
                            }`}
                        >
                            <h4 className="font-medium text-slate-800 truncate">{session.name}</h4>
                            <p className="text-xs text-slate-500 mt-1">
                                {session.stats?.num_documents || 0} files &middot; {session.stats?.num_pages || 0} pages
                            </p>
                            <p className="text-xs text-slate-400 mt-1">
                                {new Date(session.created_at).toLocaleDateString()}
                            </p>
                        </div>
                    ))}
                </div>
            </div>

            {/* Session Detail */}
            <div className="w-2/3 overflow-y-auto">
                {selectedSession ? (
                    <div className="p-6">
                        <div className="flex justify-between items-start mb-6">
                            <div>
                                <h2 className="text-xl font-bold text-slate-800">{selectedSession.name}</h2>
                                <p className="text-sm text-slate-500 mt-1">
                                    Created {new Date(selectedSession.created_at).toLocaleString()}
                                </p>
                            </div>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => handleLoadSession(selectedSession.session_id)}
                                    className="px-4 py-2 bg-teal-500 text-white text-sm font-medium rounded-md hover:bg-teal-600 transition-colors"
                                >
                                    Load Session
                                </button>
                                <button
                                    onClick={() => handleDeleteSession(selectedSession.session_id)}
                                    className="px-4 py-2 border border-red-300 text-red-600 text-sm font-medium rounded-md hover:bg-red-50 transition-colors"
                                >
                                    Delete
                                </button>
                            </div>
                        </div>

                        {/* Files */}
                        <div className="mb-6">
                            <h3 className="text-sm font-semibold text-slate-600 uppercase tracking-wide mb-3">
                                Indexed Files
                            </h3>
                            <div className="bg-slate-50 rounded-lg p-4">
                                {selectedSession.files && selectedSession.files.length > 0 ? (
                                    <ul className="space-y-2">
                                        {selectedSession.files.map((file, i) => (
                                            <li key={i} className="flex items-center gap-2 text-sm text-slate-700">
                                                <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                                                </svg>
                                                {typeof file === 'string' ? file : file.filename || file}
                                            </li>
                                        ))}
                                    </ul>
                                ) : (
                                    <p className="text-sm text-slate-500">No files recorded</p>
                                )}
                            </div>
                        </div>

                        {/* Query History */}
                        <div>
                            <h3 className="text-sm font-semibold text-slate-600 uppercase tracking-wide mb-3">
                                Search History
                            </h3>
                            {selectedSession.queries && selectedSession.queries.length > 0 ? (
                                <div className="space-y-3">
                                    {selectedSession.queries.map((q, i) => (
                                        <div key={q.id || i} className="bg-white border border-slate-200 rounded-lg p-4">
                                            <div className="flex justify-between items-start">
                                                <p className="font-medium text-slate-800">&ldquo;{q.query}&rdquo;</p>
                                                <span className="text-xs text-slate-400">
                                                    {new Date(q.timestamp).toLocaleString()}
                                                </span>
                                            </div>
                                            {q.summary && (
                                                <p className="mt-2 text-sm text-slate-600 line-clamp-3">
                                                    {q.summary}
                                                </p>
                                            )}
                                            {q.results && q.results.length > 0 && (
                                                <p className="mt-2 text-xs text-slate-400">
                                                    {q.results.length} result{q.results.length !== 1 ? 's' : ''}
                                                </p>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="bg-slate-50 rounded-lg p-4 text-center">
                                    <p className="text-sm text-slate-500">No searches recorded</p>
                                </div>
                            )}
                        </div>
                    </div>
                ) : (
                    <div className="flex items-center justify-center h-full text-slate-400">
                        <p>Select a session to view details</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default LiteratureHistory;
