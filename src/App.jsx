import React, { useState } from 'react';
import { TestTube, BookOpen } from 'lucide-react';
import SynthesizerPage from './pages/Synthesizer';
import LiteraturePage from './pages/Literature';

const NavItem = ({ children, onClick, isActive }) => (
    <button
        onClick={onClick}
        className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors
            ${isActive
                ? 'bg-teal-50 text-teal-700'
                : 'text-slate-700 hover:bg-slate-100'
            }`
        }
    >
        {children}
    </button>
);

function App() {
    const [activePage, setActivePage] = useState('synthesizer');

    const renderActivePage = () => {
        switch (activePage) {
            case 'synthesizer':
                return <SynthesizerPage />;
            case 'literature':
                return <LiteraturePage />;
            default:
                return <SynthesizerPage />;
        }
    }

    return (
        <div className="min-h-screen bg-slate-50 text-slate-800">
            <header className="bg-white shadow-sm sticky top-0 z-10">
                <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center py-3">
                        {/* Logo */}
                        <div className="flex items-center">
                            <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center">
                                <TestTube className="w-7 h-7 mr-2 text-teal-600" />
                                SynthLab
                            </h1>
                        </div>

                        {/* Navigation */}
                        <nav className="flex space-x-4">
                            <NavItem
                                isActive={activePage === 'synthesizer'}
                                onClick={() => setActivePage('synthesizer')}
                            >
                                <TestTube className="w-5 h-5 mr-2" />
                                Synthesizer
                            </NavItem>
                            <NavItem
                                isActive={activePage === 'literature'}
                                onClick={() => setActivePage('literature')}
                            >
                                <BookOpen className="w-5 h-5 mr-2" />
                                Literature RAG
                            </NavItem>
                        </nav>
                    </div>
                </div>
            </header>

            <main className="py-10">
                <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                    {renderActivePage()}
                </div>
            </main>
        </div>
    );
}

export default App;
