import React, { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { RefreshCw, Send, Bot, User } from "lucide-react";

const ChatBot = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [databaseInfo, setDatabaseInfo] = useState(null);
  const messagesEndRef = useRef(null);

  // Scroll to bottom if user is already near bottom
  const scrollToBottom = () => {
    if (
      messagesEndRef.current &&
      Math.abs(
        messagesEndRef.current.parentNode.scrollHeight -
          messagesEndRef.current.parentNode.scrollTop -
          messagesEndRef.current.parentNode.clientHeight
      ) < 100
    ) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  };

  // Load from localStorage
  useEffect(() => {
    const savedMessages =
      JSON.parse(localStorage.getItem("chatMessages")) || [];
    setMessages(savedMessages);
    fetchDatabaseInfo();
  }, []);

  // Save to localStorage
  useEffect(() => {
    localStorage.setItem("chatMessages", JSON.stringify(messages));
    scrollToBottom();
  }, [messages]);

  const fetchDatabaseInfo = async () => {
    try {
      const response = await fetch("http://localhost:5000/api/database-info");
      const data = await response.json();
      setDatabaseInfo(data);
    } catch (error) {
      console.error("Error fetching database info:", error);
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
        body: JSON.stringify({ query: inputMessage }),
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

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <div className="bg-blue-600 text-white p-4 shadow-lg flex justify-between items-center">
        <div>
          <h1 className="text-xl font-bold">💊 Medical RAG ChatBot</h1>
          {databaseInfo && (
            <div className="text-sm opacity-90 mt-1">
              {databaseInfo.document_count} docs loaded{" "}
              {databaseInfo.pdfs_in_database?.length > 0 && (
                <span className="ml-2">
                  ({databaseInfo.pdfs_in_database.join(", ")})
                </span>
              )}
            </div>
          )}
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
  );
};

export default ChatBot;
