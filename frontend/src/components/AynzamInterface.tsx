"use client"

import { useState, useEffect, useRef } from 'react';
import { Menu, ChevronDown, Search, Plus, MessageCircle, User, Settings, HelpCircle, Clock, Zap, Database, FileText, BarChart, Book, Download, Layers, File, Mic, MoreHorizontal, Send, Sun, Moon, RefreshCw } from 'lucide-react';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Array<{
    title: string;
    content: string;
    page_number?: number;
    metadata?: Record<string, any>;
  }>;
  isOpenAI?: boolean; // Flag to indicate if response is from direct OpenAI
}

interface ApiResponse {
  message: string;
  sources?: Array<{
    title: string;
    content: string;
    page_number?: number;
    metadata?: Record<string, any>;
  }>;
}

const API_BASE_URL = 'http://localhost:8000';

export default function AynzamInterface() {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [activeTab, setActiveTab] = useState<'answer' | 'sources' | 'videos'>('answer');
  const [showOpenAIFallback, setShowOpenAIFallback] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [recentChats, setRecentChats] = useState<string[]>([
    "Integration von Datenquellen",
    "Mitarbeiter-Onboarding Dokumente",
    "Firmenhandbuch durchsuchen"
  ]);

  // Detect system theme preference
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    setIsDarkMode(mediaQuery.matches);

    const handler = (e: MediaQueryListEvent) => setIsDarkMode(e.matches);
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
  };

  // Enhanced markdown-like formatting for German text
  const formatMessageContent = (content: string) => {
    // Split by double line breaks for paragraphs
    const paragraphs = content.split(/\n\s*\n/).filter(p => p.trim());

    return paragraphs.map((paragraph, index) => {
      const trimmedParagraph = paragraph.trim();

      // Handle numbered lists (1. 2. 3. etc.)
      if (/^\d+\.\s/.test(trimmedParagraph)) {
        const items = trimmedParagraph.split(/(?=\d+\.\s)/g).filter(item => item.trim());
        return (
          <ol key={index} className="list-decimal list-inside mb-6 space-y-3 ml-4">
            {items.map((item, i) => (
              <li key={i} className="text-sm leading-relaxed text-gray-800 dark:text-gray-200 pl-2">
                {formatInlineText(item.replace(/^\d+\.\s*/, ''))}
              </li>
            ))}
          </ol>
        );
      }

      // Handle bullet points (• - * etc.)
      if (/^[•\-\*]\s/.test(trimmedParagraph) || trimmedParagraph.includes('\n• ') || trimmedParagraph.includes('\n- ') || trimmedParagraph.includes('\n* ')) {
        const items = trimmedParagraph.split(/\n(?=[•\-\*]\s)/).filter(item => item.trim());
        return (
          <ul key={index} className="list-disc list-inside mb-6 space-y-3 ml-4">
            {items.map((item, i) => (
              <li key={i} className="text-sm leading-relaxed text-gray-800 dark:text-gray-200 pl-2">
                {formatInlineText(item.replace(/^[•\-\*]\s*/, ''))}
              </li>
            ))}
          </ul>
        );
      }

      // Handle headings (text with ## or **text** at start)
      if (trimmedParagraph.startsWith('##') || (trimmedParagraph.startsWith('**') && trimmedParagraph.includes('**'))) {
        return (
          <h3 key={index} className="text-lg font-semibold mb-4 mt-6 text-gray-900 dark:text-gray-100 border-b border-gray-300 dark:border-gray-600 pb-2">
            {formatInlineText(trimmedParagraph.replace(/^##\s*/, '').replace(/^\*\*(.*?)\*\*/, '$1'))}
          </h3>
        );
      }

      // Regular paragraph with improved line breaks
      const formattedParagraph = trimmedParagraph.replace(/\n/g, ' ').trim();

      return (
        <div key={index} className="mb-5 text-sm leading-relaxed text-gray-800 dark:text-gray-200">
          {formatInlineText(formattedParagraph)}
        </div>
      );
    });
  };

  // Format inline text (bold, italic, code, etc.)
  const formatInlineText = (text: string) => {
    // Split text by formatting patterns
    const parts = text.split(/(\*\*.*?\*\*|\*.*?\*|`.*?`|_.*?_)/g);

    return parts.map((part, index) => {
      // Bold text (**text**)
      if (part.startsWith('**') && part.endsWith('**')) {
        return (
          <strong key={index} className="font-semibold text-gray-900 dark:text-gray-100">
            {part.slice(2, -2)}
          </strong>
        );
      }

      // Italic text (*text* or _text_)
      if ((part.startsWith('*') && part.endsWith('*') && !part.startsWith('**')) ||
          (part.startsWith('_') && part.endsWith('_'))) {
        return (
          <em key={index} className="italic text-gray-800 dark:text-gray-200">
            {part.slice(1, -1)}
          </em>
        );
      }

      // Code text (`text`)
      if (part.startsWith('`') && part.endsWith('`')) {
        return (
          <code key={index} className="bg-gray-200 dark:bg-gray-700 px-1.5 py-0.5 rounded text-xs font-mono text-gray-800 dark:text-gray-200">
            {part.slice(1, -1)}
          </code>
        );
      }

      // Regular text
      return part;
    });
  };

  // Enhanced detection for "no information" messages in German
  const isNoInfoMessage = (content: string) => {
    const noInfoIndicators = [
      'leider enthalten die bereitgestellten dokumentenauszüge keine',
      'es wurden keine relevanten informationen',
      'keine spezifischen informationen',
      'die bereitgestellten dokumentenauszüge enthalten keine',
      'in den bereitgestellten dokumenten',
      'keine informationen zu',
      'nicht in den dokumenten',
      'keine passenden dokumente',
      'enthalten keine spezifischen informationen',
      'sind jedoch nicht ausreichend'
    ];

    const lowerContent = content.toLowerCase();
    return noInfoIndicators.some(indicator => lowerContent.includes(indicator));
  };

  const sendMessage = async (useOpenAI = false) => {
    if (!message.trim() || isLoading || isStreaming) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: message,
      timestamp: new Date()
    };

    const currentMessage = message;
    setMessage('');
    setIsLoading(true);
    setIsStreaming(false);
    setError(null);
    setShowOpenAIFallback(false);

    // Add user message first
    setMessages(prev => [...prev, userMessage]);

    // Create a placeholder assistant message for streaming
    const assistantMessage: ChatMessage = {
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      sources: [],
      isOpenAI: useOpenAI
    };

    // Add empty assistant message
    setMessages(prev => [...prev, assistantMessage]);

    try {
      const endpoint = useOpenAI ? '/api/chat/openai/stream' : '/api/chat/stream';
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: currentMessage,
          conversation_history: messages.map(m => ({
            role: m.role,
            content: m.content
          })),
          temperature: 0.0
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP Fehler! Status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('Kein Response Body Reader verfügbar');
      }

      const decoder = new TextDecoder();
      let accumulatedContent = '';

      setIsLoading(false);
      setIsStreaming(true);

      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);

            if (data === '[DONE]') {
              break;
            }

            if (data.trim()) {
              accumulatedContent += data;

              // Update the last message (assistant message) with streamed content
              setMessages(prev => {
                const updated = [...prev];
                if (updated.length > 0) {
                  updated[updated.length - 1] = {
                    ...updated[updated.length - 1],
                    content: accumulatedContent
                  };
                }
                return updated;
              });
            }
          }
        }
      }

      setIsStreaming(false);

      // Check if we should show OpenAI fallback
      if (!useOpenAI && isNoInfoMessage(accumulatedContent)) {
        setShowOpenAIFallback(true);
      }

      // After streaming is complete, get sources (only for RAG responses)
      if (!useOpenAI) {
        try {
          const sourcesResponse = await fetch(`${API_BASE_URL}/api/search`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              query: currentMessage,
              limit: 3
            }),
          });

          if (sourcesResponse.ok) {
            const sourcesData = await sourcesResponse.json();
            const sources = sourcesData.results.map((result: any) => ({
              title: result.title,
              content: result.content,
              page_number: result.page_number,
              metadata: result.metadata
            }));

            // Update the last message with sources
            setMessages(prev => {
              const updated = [...prev];
              if (updated.length > 0) {
                updated[updated.length - 1] = {
                  ...updated[updated.length - 1],
                  sources: sources
                };
              }
              return updated;
            });
          }
        } catch (sourcesErr) {
          console.warn('Fehler beim Laden der Quellen:', sourcesErr);
        }
      }

      // Update recent chats
      if (!recentChats.includes(currentMessage)) {
        setRecentChats(prev => [currentMessage, ...prev.slice(0, 2)]);
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ein Fehler ist aufgetreten');
      console.error('Fehler beim Senden der Nachricht:', err);

      // Remove the empty assistant message on error
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setIsLoading(false);
      setIsStreaming(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([]);
    setError(null);
    setShowOpenAIFallback(false);
  };

  const formatTimestamp = (timestamp: Date) => {
    return timestamp.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
  };

  const suggestionCards = [
    {
      title: "Firmendokumente finden",
      description: "Internes Wissen durchsuchen"
    },
    {
      title: "Quartalsbericht erstellen",
      description: "Basierend auf aktuellen Daten"
    },
    {
      title: "Kundenfeedback analysieren",
      description: "Aus Umfragen und Tickets"
    }
  ];

  const handleSuggestionClick = (suggestion: string) => {
    setMessage(suggestion);
  };

  // Apply dark mode class to document with darker colors
  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
      document.documentElement.style.setProperty('--bg-dark-primary', '#0a0a0b');
      document.documentElement.style.setProperty('--bg-dark-secondary', '#1a1a1c');
      document.documentElement.style.setProperty('--bg-dark-tertiary', '#2d2d30');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode]);

  return (
    <div className="flex h-screen w-full bg-white dark:bg-[#0a0a0b] overflow-hidden font-sans transition-colors duration-300">
      {/* Sidebar */}
      <div className="w-64 h-full bg-gray-50 dark:bg-[#1a1a1c] flex flex-col border-r border-gray-200 dark:border-gray-800 transition-colors duration-300">
        {/* Sidebar Header */}
        <div className="flex items-center justify-between px-4 py-3">
          <button className="p-2 rounded-full hover:bg-gray-200 dark:hover:bg-[#2d2d30] transition-colors">
            <Menu className="h-5 w-5 text-gray-600 dark:text-gray-300" />
          </button>
          <button
            onClick={toggleDarkMode}
            className="p-2 rounded-full hover:bg-gray-200 dark:hover:bg-[#2d2d30] transition-colors"
          >
            {isDarkMode ? (
              <Sun className="h-5 w-5 text-gray-600 dark:text-gray-300" />
            ) : (
              <Moon className="h-5 w-5 text-gray-600 dark:text-gray-300" />
            )}
          </button>
        </div>

        {/* New Chat Button */}
        <div className="px-4 py-2">
          <button
            onClick={clearChat}
            className="flex items-center space-x-2 w-full px-4 py-2 text-sm bg-gray-200 dark:bg-[#2d2d30] hover:bg-gray-300 dark:hover:bg-gray-700 rounded-full text-gray-700 dark:text-gray-200 transition-colors"
          >
            <Plus className="h-4 w-4" />
            <span>Neuer Chat</span>
          </button>
        </div>

        {/* Recent Chats */}
        <div className="px-2 mt-6">
          <div className="px-2 pb-2 text-sm font-medium text-gray-600 dark:text-gray-400">
            Letzte
          </div>
          <div className="space-y-1">
            {recentChats.map((chat, i) => (
              <button
                key={i}
                onClick={() => setMessage(chat)}
                className="flex items-center w-full px-3 py-2 text-left text-sm hover:bg-gray-200 dark:hover:bg-[#2d2d30] rounded-md text-gray-800 dark:text-gray-200 transition-colors"
              >
                <MessageCircle className="h-4 w-4 mr-2 flex-shrink-0 text-gray-500 dark:text-gray-400" />
                <span className="truncate">{chat}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Projects */}
        <div className="px-2 mt-6">
          <div className="px-2 pb-2 text-sm font-medium text-gray-600 dark:text-gray-400">
            Projekte
          </div>
          <div className="space-y-1">
            {[
              { name: "Interne Wissensdatenbank", icon: <Database className="h-4 w-4" /> },
              { name: "Kundensupport Dokumente", icon: <FileText className="h-4 w-4" /> },
              { name: "Produkt-Analytics", icon: <BarChart className="h-4 w-4" /> }
            ].map((project, i) => (
              <button key={i} className="flex items-center w-full px-3 py-2 text-left text-sm hover:bg-gray-200 dark:hover:bg-[#2d2d30] rounded-md text-gray-800 dark:text-gray-200 transition-colors">
                <div className="mr-2 flex-shrink-0 text-gray-500 dark:text-gray-400">
                  {project.icon}
                </div>
                <span className="truncate">{project.name}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Sources Section */}
        <div className="px-2 mt-6">
          <div className="px-2 pb-2 text-sm font-medium text-gray-600 dark:text-gray-400">
            Quellen
          </div>
          <div className="space-y-1">
            {[
              { name: "Confluence", icon: <Book className="h-4 w-4" /> },
              { name: "OneDrive", icon: <Download className="h-4 w-4" /> },
              { name: "Firmen-Wiki", icon: <Layers className="h-4 w-4" /> },
              { name: "Präsentationen", icon: <File className="h-4 w-4" /> }
            ].map((source, i) => (
              <button key={i} className="flex items-center w-full px-3 py-2 text-left text-sm hover:bg-gray-200 dark:hover:bg-[#2d2d30] rounded-md text-gray-800 dark:text-gray-200 transition-colors">
                <div className="mr-2 flex-shrink-0 text-gray-500 dark:text-gray-400">
                  {source.icon}
                </div>
                <span className="truncate">{source.name}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Spacer */}
        <div className="flex-grow"></div>

        {/* Footer Navigation */}
        <div className="mt-6 mb-4">
          <div className="px-2 space-y-1 pb-4">
            <button className="flex items-center w-full px-3 py-2 text-left text-sm hover:bg-gray-200 dark:hover:bg-[#2d2d30] rounded-md text-gray-800 dark:text-gray-200 transition-colors">
              <HelpCircle className="h-4 w-4 mr-2 flex-shrink-0 text-gray-500 dark:text-gray-400" />
              <span>Hilfe</span>
            </button>
            <button className="flex items-center w-full px-3 py-2 text-left text-sm hover:bg-gray-200 dark:hover:bg-[#2d2d30] rounded-md text-gray-800 dark:text-gray-200 transition-colors">
              <Clock className="h-4 w-4 mr-2 flex-shrink-0 text-gray-500 dark:text-gray-400" />
              <span>Aktivität</span>
            </button>
            <button className="flex items-center w-full px-3 py-2 text-left text-sm hover:bg-gray-200 dark:hover:bg-[#2d2d30] rounded-md text-gray-800 dark:text-gray-200 transition-colors">
              <Settings className="h-4 w-4 mr-2 flex-shrink-0 text-gray-500 dark:text-gray-400" />
              <span>Einstellungen</span>
            </button>
          </div>
          <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-800">
            <div className="flex items-center text-xs text-gray-500 dark:text-gray-400">
              <div className="h-2 w-2 rounded-full bg-green-500 mr-2"></div>
              München-Ludwigsvorstadt, Deutschland
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex-shrink-0 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-[#0a0a0b] transition-colors duration-300">
          <div className="flex items-center justify-between h-14 px-4">
            <div className="flex items-center">
              <div className="font-medium text-gray-800 dark:text-gray-200 tracking-wide font-poppins">
                <span className="font-semibold">A</span>ynzam
              </div>
              <ChevronDown className="ml-1 h-4 w-4 text-gray-500 dark:text-gray-400" />
              <div className="ml-2 text-sm text-gray-500 dark:text-gray-400">(enterprise)</div>
            </div>
            <div className="flex items-center space-x-2">
              <button className="px-3 py-1.5 text-sm bg-gray-100 dark:bg-[#2d2d30] hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg text-gray-800 dark:text-gray-200 flex items-center transition-colors">
                <Zap className="h-4 w-4 mr-1.5 text-blue-500" />
                <span>Probieren Sie <span className="font-poppins"><span className="font-semibold">A</span>ynzam Advanced</span></span>
              </button>
              <button className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-[#2d2d30] transition-colors">
                <User className="h-5 w-5 text-gray-600 dark:text-gray-300" />
              </button>
            </div>
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto flex flex-col bg-white dark:bg-[#0a0a0b] transition-colors duration-300">
          {messages.length === 0 ? (
            /* Welcome Screen */
            <div className="flex-1 flex flex-col items-center justify-center p-6">
              <div className="max-w-2xl w-full flex flex-col items-center justify-center">
                <h1 className="text-4xl mb-10 text-center">
                  <span className="text-blue-500 dark:text-blue-400">Hallo, wie kann ich Ihnen helfen?</span>
                </h1>

                {/* Suggestion Cards */}
                <div className="grid grid-cols-3 gap-4 w-full mb-5 max-w-lg mx-auto">
                  {suggestionCards.map((card, i) => (
                    <div
                      key={i}
                      onClick={() => handleSuggestionClick(card.title)}
                      className="p-3 bg-gray-50 dark:bg-[#1a1a1c] border border-gray-200 dark:border-gray-700 rounded-lg text-left cursor-pointer transition-all duration-200 hover:shadow-md hover:bg-gray-100 dark:hover:bg-[#2d2d30] h-16"
                    >
                      <h3 className="text-[10px] font-medium text-gray-800 dark:text-gray-200 mb-0.5">
                        {card.title}
                      </h3>
                      <p className="text-[10px] text-gray-500 dark:text-gray-400 leading-tight">
                        {card.description}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            /* Chat Messages */
            <div className="flex-1 p-4 space-y-6 max-w-4xl mx-auto w-full">
              {messages.map((msg, i) => (
                <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-4xl w-full ${msg.role === 'user' ? '' : 'space-y-4'}`}>
                    {msg.role === 'user' ? (
                      /* User Message */
                      <div className="flex justify-end">
                        <div className="bg-blue-500 text-white rounded-lg px-4 py-2 max-w-2xl">
                          <div className="whitespace-pre-wrap text-sm">{msg.content}</div>
                          <div className="text-xs mt-1 text-blue-100">
                            {formatTimestamp(msg.timestamp)}
                          </div>
                        </div>
                      </div>
                    ) : (
                      /* Assistant Message with Tabs */
                      <div className="space-y-4">
                        {/* Message Source Indicator */}
                        {msg.isOpenAI && (
                          <div className="flex items-center space-x-2 text-xs text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-900/20 px-3 py-2 rounded-lg border border-orange-200 dark:border-orange-800">
                            <RefreshCw className="h-3 w-3" />
                            <span>Antwort von OpenAI (nicht aus Dokumenten)</span>
                          </div>
                        )}

                        {/* Tabs */}
                        <div className="border-b border-gray-200 dark:border-gray-700">
                          <nav className="flex space-x-8">
                            <button
                              onClick={() => setActiveTab('answer')}
                              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                                activeTab === 'answer'
                                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                                  : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                              } transition-colors`}
                            >
                              Antwort
                            </button>
                            {msg.sources && msg.sources.length > 0 && (
                              <button
                                onClick={() => setActiveTab('sources')}
                                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                                  activeTab === 'sources'
                                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                                } transition-colors`}
                              >
                                Quellen
                                <span className="ml-1 bg-gray-200 dark:bg-gray-600 text-gray-600 dark:text-gray-300 px-1.5 py-0.5 rounded-full text-xs">
                                  {msg.sources.length}
                                </span>
                              </button>
                            )}
                          </nav>
                        </div>

                        {/* Tab Content */}
                        <div className="bg-gray-50 dark:bg-[#1a1a1c] rounded-lg p-6 min-h-[100px] transition-colors duration-300 border border-gray-200 dark:border-gray-800">
                          {activeTab === 'answer' && (
                            <div className="prose prose-sm dark:prose-invert max-w-none">
                              <div className="text-gray-800 dark:text-gray-200">
                                {formatMessageContent(msg.content)}
                                {/* Show cursor for the last assistant message if streaming */}
                                {i === messages.length - 1 && isStreaming && (
                                  <span className="inline-block w-0.5 h-4 bg-blue-500 ml-1 animate-pulse"></span>
                                )}
                              </div>
                              <div className="text-xs mt-4 text-gray-500 dark:text-gray-400 border-t border-gray-200 dark:border-gray-700 pt-3">
                                {formatTimestamp(msg.timestamp)}
                              </div>
                            </div>
                          )}

                          {activeTab === 'sources' && msg.sources && (
                            <div className="space-y-3">
                              {msg.sources.map((source, idx) => (
                                <div key={idx} className="bg-white dark:bg-[#2d2d30] p-4 rounded-lg border border-gray-200 dark:border-gray-600 transition-colors shadow-sm">
                                  <div className="flex items-start space-x-3">
                                    <div className="flex-shrink-0 w-6 h-6 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full flex items-center justify-center text-xs font-medium">
                                      {idx + 1}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                      <div className="font-medium text-sm text-gray-900 dark:text-gray-100">
                                        {source.title}
                                      </div>
                                      {source.page_number && (
                                        <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                          Seite {source.page_number}
                                        </div>
                                      )}
                                      <div className="text-sm text-gray-600 dark:text-gray-300 mt-2 leading-relaxed">
                                        {source.content}
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>

                        {/* Enhanced OpenAI Fallback in German */}
                        {showOpenAIFallback && i === messages.length - 1 && !msg.isOpenAI && (
                          <div className="bg-gradient-to-r from-orange-50 to-yellow-50 dark:from-orange-900/20 dark:to-yellow-900/20 border border-orange-200 dark:border-orange-800 rounded-xl p-5 shadow-sm">
                            <div className="flex items-start space-x-4">
                              <div className="flex-shrink-0">
                                <div className="w-10 h-10 bg-orange-100 dark:bg-orange-900 rounded-full flex items-center justify-center">
                                  <RefreshCw className="h-5 w-5 text-orange-600 dark:text-orange-400" />
                                </div>
                              </div>
                              <div className="flex-1">
                                <div className="text-sm font-semibold text-orange-900 dark:text-orange-200 mb-1">
                                  Keine Informationen in Ihren Dokumenten gefunden
                                </div>
                                <div className="text-sm text-orange-700 dark:text-orange-300 mb-3">
                                  Die gesuchten Informationen existieren nicht in Ihren verbundenen Datenquellen.
                                  Möchten Sie stattdessen eine Internetsuche mit OpenAI durchführen?
                                </div>
                                <button
                                  onClick={() => sendMessage(true)}
                                  className="inline-flex items-center px-4 py-2 bg-orange-600 hover:bg-orange-700 dark:bg-orange-700 dark:hover:bg-orange-600 text-white text-sm rounded-lg font-medium transition-all duration-200 shadow-sm hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
                                  disabled={isLoading || isStreaming}
                                >
                                  <RefreshCw className="h-4 w-4 mr-2" />
                                  Mit OpenAI suchen
                                </button>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {isLoading && !isStreaming && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 dark:bg-[#1a1a1c] rounded-lg px-4 py-2 transition-colors border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-pulse"></div>
                      <div className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-pulse" style={{animationDelay: '0.2s'}}></div>
                      <div className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-pulse" style={{animationDelay: '0.4s'}}></div>
                      <span className="text-sm text-gray-500 dark:text-gray-400 ml-2">Aynzam denkt nach...</span>
                    </div>
                  </div>
                </div>
              )}

              {error && (
                <div className="flex justify-center">
                  <div className="bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200 rounded-lg px-4 py-2 text-sm transition-colors border border-red-200 dark:border-red-800">
                    Fehler: {error}
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Chat Input - Fixed at bottom */}
        <div className="flex-shrink-0 p-4 border-t border-gray-200 dark:border-gray-800 bg-white dark:bg-[#0a0a0b] transition-colors duration-300">
          <div className="w-full max-w-4xl mx-auto">
            <div className="relative flex items-center">
              <div className="absolute inset-0 rounded-3xl shadow-lg bg-gray-50 dark:bg-[#1a1a1c] border border-gray-200 dark:border-gray-700 transition-colors duration-300"></div>

              <button className="absolute left-4 z-10 p-2 rounded-full hover:bg-gray-200 dark:hover:bg-[#2d2d30] transition-colors">
                <Plus className="h-5 w-5 text-gray-500 dark:text-gray-400" />
              </button>

              <button className="absolute right-16 z-10 p-2 rounded-full hover:bg-gray-200 dark:hover:bg-[#2d2d30] transition-colors">
                <MoreHorizontal className="h-5 w-5 text-gray-500 dark:text-gray-400" />
              </button>

              <button
                onClick={() => sendMessage()}
                disabled={!message.trim() || isLoading || isStreaming}
                className="absolute right-4 z-10 p-2 rounded-full hover:bg-gray-200 dark:hover:bg-[#2d2d30] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Send className="h-5 w-5 text-gray-500 dark:text-gray-400" />
              </button>

              <textarea
                value={message}
                onChange={e => setMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Fragen Sie Aynzam..."
                className="w-full h-20 pl-16 pr-28 bg-transparent z-10 focus:outline-none text-gray-800 dark:text-gray-200 text-sm resize-none py-6 transition-colors placeholder-gray-500 dark:placeholder-gray-400"
                disabled={isLoading || isStreaming}
              />

              <div className="w-full h-20 rounded-3xl"></div>
            </div>
            <div className="text-xs text-center mt-4 text-gray-500 dark:text-gray-400">
              Aynzams Antworten basieren vollständig auf den bereitgestellten Datenquellen; falls die Antwort nicht in den Datenquellen existiert, können Sie mit OpenAI suchen.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}