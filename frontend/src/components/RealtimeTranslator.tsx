/**
 * Real-time WebSocket translation component
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { TranslateWebSocket, TranslateResponse } from '../api/client';

export const RealtimeTranslator: React.FC = () => {
  const [inputText, setInputText] = useState('');
  const [result, setResult] = useState<TranslateResponse | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<TranslateWebSocket | null>(null);
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  const handleMessage = useCallback((data: TranslateResponse) => {
    if ('error' in data) {
      setError((data as any).error);
    } else {
      setResult(data);
      setError(null);
    }
  }, []);

  const handleError = useCallback((err: Event) => {
    setError('WebSocket connection error');
    setConnected(false);
  }, []);

  const connectWebSocket = () => {
    if (wsRef.current) {
      wsRef.current.disconnect();
    }

    const ws = new TranslateWebSocket();
    ws.connect(handleMessage, handleError);
    wsRef.current = ws;

    // Check connection status
    setTimeout(() => {
      setConnected(ws.isConnected());
    }, 1000);
  };

  const disconnectWebSocket = () => {
    if (wsRef.current) {
      wsRef.current.disconnect();
      wsRef.current = null;
      setConnected(false);
    }
  };

  useEffect(() => {
    connectWebSocket();

    return () => {
      disconnectWebSocket();
    };
  }, []);

  const handleInputChange = (text: string) => {
    setInputText(text);

    // Clear previous timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // Set new timer for debounced translation
    if (text.trim()) {
      debounceTimerRef.current = setTimeout(() => {
        if (wsRef.current && wsRef.current.isConnected()) {
          wsRef.current.send(text);
        }
      }, 500); // 500ms debounce
    } else {
      setResult(null);
    }
  };

  const getStatusColor = () => {
    if (connected) return 'bg-green-500';
    return 'bg-red-500';
  };

  const getStatusText = () => {
    if (connected) return 'Connected';
    return 'Disconnected';
  };

  return (
    <div className="max-w-6xl mx-auto space-y-4">
      {/* Connection status */}
      <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 
                    rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${getStatusColor()} animate-pulse`} />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {getStatusText()}
            </span>
          </div>
          {connected && (
            <span className="text-xs text-gray-500 dark:text-gray-400">
              Real-time translation active
            </span>
          )}
        </div>
        <div className="flex gap-2">
          <button
            onClick={connectWebSocket}
            disabled={connected}
            className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 
                     text-white rounded-lg transition-colors"
          >
            Connect
          </button>
          <button
            onClick={disconnectWebSocket}
            disabled={!connected}
            className="px-4 py-2 text-sm bg-red-600 hover:bg-red-700 disabled:bg-gray-400 
                     text-white rounded-lg transition-colors"
          >
            Disconnect
          </button>
        </div>
      </div>

      {/* Info message */}
      <div className="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 
                    rounded-lg text-sm text-blue-800 dark:text-blue-200">
        ℹ️ Translation happens automatically as you type (500ms delay)
      </div>

      {/* Input and output areas */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Input area */}
        <div className="flex flex-col gap-2">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Type here...
          </label>
          <textarea
            value={inputText}
            onChange={(e) => handleInputChange(e.target.value)}
            placeholder="Start typing to see real-time translation..."
            disabled={!connected}
            className="h-64 p-4 border border-gray-300 dark:border-gray-600 rounded-lg 
                     focus:ring-2 focus:ring-blue-500 focus:border-transparent
                     dark:bg-gray-700 dark:text-white resize-none
                     disabled:bg-gray-100 dark:disabled:bg-gray-800 disabled:cursor-not-allowed"
          />
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {inputText.length} characters
          </p>
        </div>

        {/* Output area */}
        <div className="flex flex-col gap-2">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Real-time Translation
          </label>
          <div className="h-64 p-4 border border-gray-300 dark:border-gray-600 rounded-lg 
                        bg-gray-50 dark:bg-gray-800 overflow-auto">
            {result ? (
              <div className="space-y-3">
                <div className="flex gap-2">
                  <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 
                                 dark:text-blue-200 text-xs rounded">
                    {result.detected_language === 'en' ? '🇺🇸 English' : '🇰🇷 Korean'}
                  </span>
                  <span className="px-2 py-1 bg-green-100 dark:bg-green-900 text-green-800 
                                 dark:text-green-200 text-xs rounded">
                    Quality: {(result.quality_score * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="text-gray-900 dark:text-gray-100 whitespace-pre-wrap">
                  {result.translation}
                </p>
              </div>
            ) : (
              <p className="text-gray-400 dark:text-gray-500">
                {connected
                  ? 'Translation will appear here as you type...'
                  : 'Connect to start real-time translation'}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="p-4 bg-red-100 dark:bg-red-900 border border-red-300 dark:border-red-700 
                      rounded-lg text-red-800 dark:text-red-200">
          ❌ {error}
        </div>
      )}

      {/* Instructions */}
      <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 
                    dark:border-gray-700">
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          How it works:
        </h3>
        <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1 list-disc list-inside">
          <li>Connect to the WebSocket server</li>
          <li>Start typing in the input area</li>
          <li>Translation appears automatically after 500ms of inactivity</li>
          <li>Language is detected automatically</li>
          <li>Disconnect when finished to save resources</li>
        </ul>
      </div>
    </div>
  );
};
