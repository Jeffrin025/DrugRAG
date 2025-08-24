import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { RefreshCw, Send, Bot, User, History, X, Plus, Trash2 } from "lucide-react";

const ChatBot = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [databaseInfo, setDatabaseInfo] = useState(null);
  const [currentSession, setCurrentSession] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [showSessions, setShowSessions] = useState(false);
  const messagesEndRef = useRef(null);

  // Load from localStorage and initialize session
  useEffect(() => {
    const savedMessages = JSON.parse(localStorage.getItem("chatMessages")) || [];
    const savedSession = localStorage.getItem("currentSession");
    const savedSessions = JSON.parse(localStorage.getItem("chatSessions")) || [];
    
    setMessages(savedMessages);
    setCurrentSession(savedSession);
    setSessions(savedSessions);
    
    fetchDatabaseInfo();
    fetchSessions();
  }, []);

  // Save to localStorage
  useEffect(() => {
    localStorage.setItem("chatMessages", JSON.stringify(messages));
    localStorage.setItem("currentSession", currentSession);
    localStorage.setItem("chatSessions", JSON.stringify(sessions));
    scrollToBottom();
  }, [messages, currentSession, sessions]);

  const fetchDatabaseInfo = async () => {
    try {
      const response = await fetch("http://localhost:5000/api/database-info");
      const data = await response.json();
      setDatabaseInfo(data);
    } catch (error) {
      console.error("Error fetching database info:", error);
    }
  };

  const fetchSessions = async () => {
    try {
      const response = await fetch("http://localhost:5000/api/sessions");
      const data = await response.json();
      if (data.sessions) {
        setSessions(data.sessions);
      }
    } catch (error) {
      console.error("Error fetching sessions:", error);
    }
  };

  const createNewSession = () => {
    const newSessionId = `session_${Date.now()}`;
    setCurrentSession(newSessionId);
    setMessages([]);
    setShowSessions(false);
  };

  const loadSession = async (sessionId) => {
    try {
      const response = await fetch(`http://localhost:5000/api/conversation-history?session_id=${sessionId}`);
      const data = await response.json();
      
      if (data.messages) {
        const formattedMessages = data.messages.map(msg => ({
          id: Date.now() + Math.random(),
          text: msg.content,
          sender: msg.role === "User" ? "user" : "bot",
          timestamp: new Date(msg.timestamp).toLocaleTimeString(),
        }));
        
        setMessages(formattedMessages);
        setCurrentSession(sessionId);
        setShowSessions(false);
      }
    } catch (error) {
      console.error("Error loading session:", error);
    }
  };

  const deleteSession = async (sessionId) => {
    try {
      const response = await fetch(`http://localhost:5000/api/session/${sessionId}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        setSessions(sessions.filter(s => s.session_id !== sessionId));
        if (currentSession === sessionId) {
          createNewSession();
        }
      }
    } catch (error) {
      console.error("Error deleting session:", error);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();

    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      text: inputMessage,
      sender: "user",
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage("");
    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:5000/api/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ 
          query: inputMessage,
          session_id: currentSession 
        }),
      });

      const data = await response.json();

      if (data.success) {
        const botMessage = {
          id: Date.now() + 1,
          text: data.response,
          sender: "bot",
          timestamp: new Date().toLocaleTimeString(),
        };
        setMessages((prev) => [...prev, botMessage]);
        
        // Update sessions list after new message
        fetchSessions();
      } else {
        throw new Error(data.error || "Failed to get response");
      }
    } catch (error) {
      const errorMessage = {
        id: Date.now() + 1,
        text: `⚠️ ${error.message}`,
        sender: "error",
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Sessions Sidebar */}
      <AnimatePresence>
        {showSessions && (
          <motion.div
            initial={{ x: -300, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -300, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="w-80 bg-white border-r border-gray-200 shadow-lg flex flex-col"
          >
            <div className="p-4 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h2 className="text-lg font-semibold">Chat Sessions</h2>
                <button
                  onClick={() => setShowSessions(false)}
                  className="p-1 hover:bg-gray-100 rounded"
                >
                  <X size={20} />
                </button>
              </div>
              
              <button
                onClick={createNewSession}
                className="w-full mt-4 bg-blue-600 text-white py-2 px-3 rounded-md flex items-center justify-center space-x-2 hover:bg-blue-700 transition"
              >
                <Plus size={16} />
                <span>New Session</span>
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-2">
              {sessions.length === 0 ? (
                <div className="text-center text-gray-500 py-8">
                  <p>No sessions yet</p>
                  <p className="text-sm mt-1">Start a conversation to create one!</p>
                </div>
              ) : (
                sessions.map((session) => (
                  <div
                    key={session.session_id}
                    className={`p-3 rounded-lg mb-2 cursor-pointer transition ${
                      currentSession === session.session_id
                        ? "bg-blue-100 border border-blue-300"
                        : "bg-gray-50 hover:bg-gray-100"
                    }`}
                    onClick={() => loadSession(session.session_id)}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <p className="text-sm font-medium truncate">
                          Session {session.session_id.slice(0, 8)}
                        </p>
                        <p className="text-xs text-gray-500">
                          {new Date(session.last_accessed).toLocaleDateString()}
                        </p>
                        <p className="text-xs text-gray-500">
                          {session.message_count} messages
                        </p>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteSession(session.session_id);
                        }}
                        className="p-1 text-red-500 hover:bg-red-50 rounded"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-blue-600 text-white p-4 shadow-lg flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setShowSessions(!showSessions)}
              className="p-2 hover:bg-blue-700 rounded transition"
            >
              <History size={20} />
            </button>
            <div>
              <h1 className="text-xl font-bold">💊 Medical RAG ChatBot</h1>
              {databaseInfo && (
                <div className="text-sm opacity-90 mt-1">
                  {databaseInfo.document_count} docs loaded
                  {currentSession && (
                    <span className="ml-2">• Session: {currentSession.slice(0, 8)}</span>
                  )}
                </div>
              )}
            </div>
          </div>
          <button
            onClick={fetchDatabaseInfo}
            className="flex items-center space-x-1 text-sm bg-white text-blue-600 px-3 py-1 rounded-md shadow hover:bg-gray-100 transition"
          >
            <RefreshCw size={14} /> <span>Refresh</span>
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="text-center text-gray-500 mt-8">
              <p className="text-lg">👋 Welcome to Medical RAG ChatBot!</p>
              <p className="text-sm mt-2">
                Ask questions about drug information and medical documents.
              </p>
              <button
                onClick={createNewSession}
                className="mt-4 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition"
              >
                Start New Conversation
              </button>
            </div>
          ) : (
            messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className={`flex ${
                  message.sender === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div className="flex items-end space-x-2 max-w-xl">
                  {message.sender !== "user" && (
                    <div className="w-8 h-8 rounded-full bg-blue-200 flex items-center justify-center shadow">
                      {message.sender === "bot" ? (
                        <Bot size={18} className="text-blue-600" />
                      ) : (
                        "⚠️"
                      )}
                    </div>
                  )}
                  <div
                    className={`rounded-2xl px-4 py-2 shadow-md ${
                      message.sender === "user"
                        ? "bg-blue-600 text-white rounded-br-none"
                        : message.sender === "error"
                        ? "bg-red-100 text-red-800 border border-red-300"
                        : "bg-white text-gray-800 rounded-bl-none"
                    }`}
                  >
                    <p className="text-sm whitespace-pre-wrap">{message.text}</p>
                    <span className="text-xs opacity-70 block mt-1 text-right">
                      {message.timestamp}
                    </span>
                  </div>
                  {message.sender === "user" && (
                    <div className="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center shadow">
                      <User size={18} className="text-gray-700" />
                    </div>
                  )}
                </div>
              </motion.div>
            ))
          )}

          {/* Loading typing dots */}
          {isLoading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex justify-start"
            >
              <div className="flex items-center space-x-2 bg-white shadow-md rounded-2xl px-4 py-2 max-w-xs">
                <Bot size={18} className="text-blue-600" />
                <div className="flex space-x-1">
                  <motion.div
                    className="w-2 h-2 bg-gray-400 rounded-full"
                    animate={{ y: [0, -4, 0] }}
                    transition={{
                      duration: 0.6,
                      repeat: Infinity,
                      delay: 0,
                    }}
                  />
                  <motion.div
                    className="w-2 h-2 bg-gray-400 rounded-full"
                    animate={{ y: [0, -4, 0] }}
                    transition={{
                      duration: 0.6,
                      repeat: Infinity,
                      delay: 0.2,
                    }}
                  />
                  <motion.div
                    className="w-2 h-2 bg-gray-400 rounded-full"
                    animate={{ y: [0, -4, 0] }}
                    transition={{
                      duration: 0.6,
                      repeat: Infinity,
                      delay: 0.4,
                    }}
                  />
                </div>
              </div>
            </motion.div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <form
          onSubmit={handleSendMessage}
          className="p-4 bg-white border-t shadow-md"
        >
          <div className="flex space-x-2">
            <textarea
              rows={1}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage(e);
                }
              }}
              placeholder="Ask about medical information..."
              className="flex-1 border border-gray-300 rounded-lg px-4 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !inputMessage.trim()}
              className="bg-blue-600 text-white p-3 rounded-lg shadow hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
            >
              <Send size={18} />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ChatBot;