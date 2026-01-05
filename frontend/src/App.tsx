/**
 * Main application component with tabs
 */
import React, { useState } from 'react';
import { TranslatorUI } from './components/TranslatorUI';
import { DocumentUpload } from './components/DocumentUpload';
import { RealtimeTranslator } from './components/RealtimeTranslator';

type Tab = 'text' | 'document' | 'realtime';

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('text');
  const [darkMode, setDarkMode] = useState(false);

  React.useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  const tabs: { id: Tab; label: string; icon: string }[] = [
    { id: 'text', label: 'Text Translation', icon: '💬' },
    { id: 'document', label: 'Document Translation', icon: '📄' },
    { id: 'realtime', label: 'Real-time Translation', icon: '⚡' },
  ];

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 transition-colors">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="text-3xl">🌐</div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                  LangGraph Translator
                </h1>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  AI-powered English ↔ Korean Translation
                </p>
              </div>
            </div>
            <button
              onClick={() => setDarkMode(!darkMode)}
              className="p-2 rounded-lg bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 
                       dark:hover:bg-gray-600 transition-colors"
              aria-label="Toggle dark mode"
            >
              {darkMode ? '☀️' : '🌙'}
            </button>
          </div>
        </div>
      </header>

      {/* Tab navigation */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8" aria-label="Tabs">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  py-4 px-1 border-b-2 font-medium text-sm transition-colors
                  ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                  }
                `}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 min-h-[600px]">
          {activeTab === 'text' && <TranslatorUI />}
          {activeTab === 'document' && <DocumentUpload />}
          {activeTab === 'realtime' && <RealtimeTranslator />}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Powered by LangGraph, OpenAI GPT-4, and FastAPI
            </p>
            <div className="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
              <span>✅ Auto Language Detection</span>
              <span>✅ Quality Validation</span>
              <span>✅ 24h Caching</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
