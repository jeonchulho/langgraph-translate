/**
 * Main translator UI component
 */
import React, { useState } from 'react';
import { apiClient, TranslateResponse } from '../api/client';

interface TranslationHistory {
  id: string;
  original: string;
  translation: string;
  timestamp: Date;
}

export const TranslatorUI: React.FC = () => {
  const [inputText, setInputText] = useState('');
  const [result, setResult] = useState<TranslateResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<TranslationHistory[]>([]);

  const handleTranslate = async () => {
    if (!inputText.trim()) {
      setError('Please enter text to translate');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.translateText(inputText);
      setResult(response);

      // Add to history
      const newEntry: TranslationHistory = {
        id: Date.now().toString(),
        original: response.original,
        translation: response.translation,
        timestamp: new Date(),
      };
      setHistory([newEntry, ...history.slice(0, 9)]); // Keep last 10
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Translation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      // Could add a toast notification here
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const getQualityColor = (score: number): string => {
    if (score >= 0.7) return 'bg-green-500';
    if (score >= 0.5) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getLanguageBadge = (lang: string): string => {
    return lang === 'en' ? '🇺🇸 English' : '🇰🇷 Korean';
  };

  const loadFromHistory = (item: TranslationHistory) => {
    setInputText(item.original);
    // Find the result in recent translations
    apiClient.translateText(item.original).then(setResult).catch(console.error);
  };

  return (
    <div className="flex gap-4 h-full">
      {/* Main translation area */}
      <div className="flex-1 flex flex-col gap-4">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 flex-1">
          {/* Input area */}
          <div className="flex flex-col gap-2">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Input Text
            </label>
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Enter text to translate..."
              className="flex-1 p-4 border border-gray-300 dark:border-gray-600 rounded-lg 
                       focus:ring-2 focus:ring-blue-500 focus:border-transparent
                       dark:bg-gray-700 dark:text-white resize-none"
            />
          </div>

          {/* Output area */}
          <div className="flex flex-col gap-2">
            <div className="flex justify-between items-center">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Translation
              </label>
              {result && (
                <button
                  onClick={() => handleCopy(result.translation)}
                  className="text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400"
                >
                  📋 Copy
                </button>
              )}
            </div>
            <div className="flex-1 p-4 border border-gray-300 dark:border-gray-600 rounded-lg 
                          bg-gray-50 dark:bg-gray-800 overflow-auto">
              {result ? (
                <div className="space-y-2">
                  <div className="flex gap-2 mb-2">
                    <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 
                                   dark:text-blue-200 text-xs rounded">
                      {getLanguageBadge(result.detected_language)}
                    </span>
                  </div>
                  <p className="text-gray-900 dark:text-gray-100 whitespace-pre-wrap">
                    {result.translation}
                  </p>
                </div>
              ) : (
                <p className="text-gray-400 dark:text-gray-500">
                  Translation will appear here...
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Translation button and quality score */}
        <div className="flex flex-col gap-2">
          <button
            onClick={handleTranslate}
            disabled={loading || !inputText.trim()}
            className="w-full py-3 px-6 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 
                     text-white font-medium rounded-lg transition-colors"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Translating...
              </span>
            ) : (
              'Translate'
            )}
          </button>

          {/* Quality score */}
          {result && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600 dark:text-gray-400">
                Quality Score:
              </span>
              <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  className={`h-full ${getQualityColor(result.quality_score)} transition-all`}
                  style={{ width: `${result.quality_score * 100}%` }}
                />
              </div>
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                {(result.quality_score * 100).toFixed(0)}%
              </span>
            </div>
          )}

          {/* Error message */}
          {error && (
            <div className="p-3 bg-red-100 dark:bg-red-900 border border-red-300 dark:border-red-700 
                          rounded-lg text-red-800 dark:text-red-200 text-sm">
              ❌ {error}
            </div>
          )}
        </div>
      </div>

      {/* History sidebar */}
      <div className="w-80 hidden xl:flex flex-col gap-2">
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
          Recent Translations
        </h3>
        <div className="flex-1 overflow-auto space-y-2">
          {history.length === 0 ? (
            <p className="text-sm text-gray-400 dark:text-gray-500">
              No recent translations
            </p>
          ) : (
            history.map((item) => (
              <div
                key={item.id}
                onClick={() => loadFromHistory(item)}
                className="p-3 border border-gray-200 dark:border-gray-700 rounded-lg 
                         hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors"
              >
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">
                  {item.timestamp.toLocaleTimeString()}
                </p>
                <p className="text-sm text-gray-900 dark:text-gray-100 truncate">
                  {item.original.substring(0, 50)}...
                </p>
                <p className="text-xs text-gray-600 dark:text-gray-400 truncate mt-1">
                  → {item.translation.substring(0, 50)}...
                </p>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
