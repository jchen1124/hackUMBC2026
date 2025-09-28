import React, { useState, useRef, useEffect } from "react";
import { Send, Mic, Plus, Smile, Download, FileText, Quote } from "lucide-react";
import './AIChatbot.css';
import { nanoid } from "nanoid"; 

interface Message {
  id: number;
  content: string;
  isUser: boolean;
  timestamp: Date;
  isTyping?: boolean;
  fileUrl?: string;
  fileName?: string;
  fileType?: string;
  isMessageResponse?: boolean;
  isSummarizeResponse?: boolean;
}

interface AIChatbotProps {
  className?: string;
}

export default function AIChatbot({ className = "" }: AIChatbotProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      content: "Hello! I'm your AI assistant. How can I help you today?",
      isUser: false,
      timestamp: new Date(),
    }
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [inputMessage]);

  const formatTime = (timestamp: Date) => {
    return timestamp.toLocaleTimeString('en-US', { 
      hour: 'numeric', 
      minute: '2-digit',
      hour12: true 
    });
  };

  const handleFileDownload = (fileUrl: string, fileName: string) => {
    const link = document.createElement('a');
    link.href = fileUrl;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Format message content for quote-style display
  const formatQuoteContent = (content: string) => {
    // Handle null/undefined content
    if (!content) {
      return <p className="message-text">No content available</p>;
    }

    const items = content.split('\n\n\n').filter(item => item.trim());
    
    if (items.length <= 1) {
      return <p className="message-text">{content}</p>;
    }

    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        margin: 0
      }}>
        {items.map((item, index) => (
          <div key={index} style={{ position: 'relative' }}>
            {index > 0 && (
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '8px 0',
                position: 'relative'
              }}>
                <div style={{
                  width: '2px',
                  height: '20px',
                  background: 'linear-gradient(to bottom, transparent 0%, rgba(0, 122, 255, 0.3) 20%, rgba(0, 122, 255, 0.6) 50%, rgba(0, 122, 255, 0.3) 80%, transparent 100%)',
                  borderRadius: '1px'
                }}></div>
                <div style={{
                  position: 'absolute',
                  width: '6px',
                  height: '6px',
                  background: '#007AFF',
                  borderRadius: '50%',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  boxShadow: '0 0 0 2px #ffffff, 0 0 0 3px rgba(0, 122, 255, 0.2)'
                }}></div>
              </div>
            )}
            <div style={{
              position: 'relative',
              background: '#f2f2f7',
              border: '1px solid rgba(0, 0, 0, 0.08)',
              borderLeft: '4px solid #007AFF',
              borderRadius: '12px',
              padding: '16px',
              margin: 0,
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
              transition: 'all 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94)',
              animation: `slideInQuote 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94) ${index * 100}ms both`
            }}>
              <div style={{
                position: 'absolute',
                top: '12px',
                left: '12px',
                color: '#007AFF',
                opacity: 0.7
              }}>
                <Quote size={14} />
              </div>
              <div style={{
                marginLeft: '24px',
                marginRight: '24px'
              }}>
                <p style={{
                  margin: 0,
                  lineHeight: 1.4,
                  color: '#1d1d1f',
                  fontSize: '30px',
                  fontWeight: 400,
                  letterSpacing: '-0.1px'
                }}>{item.trim()}</p>
              </div>
            </div>
          </div>
        ))}
        <style>{`
          @keyframes slideInQuote {
            from {
              opacity: 0;
              transform: translateX(-20px);
            }
            to {
              opacity: 1;
              transform: translateX(0);
            }
          }
        `}</style>
      </div>
    );
  };

  // Fetch AI response from Flask backend
  const fetchAIResponse = async (userMessage: string) => {
    setIsTyping(true);

    // Add typing indicator
    const typingMessage: Message = {
      id: Date.now(),
      content: "",
      isUser: false,
      timestamp: new Date(),
      isTyping: true
    };
    setMessages(prev => [...prev, typingMessage]);

    try {
      const res = await fetch("http://127.0.0.1:5000/api/ai-response", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage })
      });

      const data = await res.json();
      const isMessageResponse = data.is_message === true;
      const isSummarizeResponse = data.is_summarize === true;

      setMessages(prev =>
        prev.map(msg =>
          msg.isTyping
            ? { 
                ...msg, 
                content: data.content || "No content received", 
                isTyping: false,
                timestamp: new Date(data.timestamp || Date.now()),
                fileUrl: data.file_url,
                fileName: data.file_name,
                fileType: data.file_type,
                isMessageResponse: isMessageResponse,
                isSummarizeResponse: isSummarizeResponse
              }
            : msg
        )
      );
    } catch (err) {
      console.error("Error fetching AI response:", err);
      setMessages(prev =>
        prev.map(msg =>
          msg.isTyping
            ? { ...msg, content: "Error: Could not reach AI backend.", isTyping: false }
            : msg
        )
      );
    } finally {
      setIsTyping(false);
    }
  };

  const handleSendMessage = () => {
    if (!inputMessage.trim()) return;

    const newMessage: Message = {
      id: Date.now(),
      content: inputMessage,
      isUser: true,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, newMessage]);
    fetchAIResponse(inputMessage);  // call Flask backend
    setInputMessage("");
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className={`ai-chatbot ${className}`}>
      {/* Header */}
      <div className="chat-header">
        <div className="ai-avatar">
          <div className="ai-icon">AI</div>
          <div className="online-status"></div>
        </div>
        <div className="ai-info">
          <h2 className="ai-name">AI Assistant</h2>
          <p className="ai-status">Online • Always here to help</p>
        </div>
      </div>

      {/* Messages Container */}
      <div className="messages-container">
        <div className="messages-list">
          {messages.map((message) => (
            <div key={message.id} className={`message-wrapper ${message.isUser ? 'user' : 'ai'}`}>
              {!message.isUser && (
                <div className="message-avatar">
                  <div className="ai-avatar-small">AI</div>
                </div>
              )}
              <div className="message-content">
                <div className={`message-bubble ${message.isUser ? 'user-bubble' : 'ai-bubble'}`}>
                  {message.isTyping ? (
                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  ) : (
                    <>
                      {message.isMessageResponse || message.isSummarizeResponse ? 
                        formatQuoteContent(message.content) : 
                        <p className="message-text">{message.content}</p>
                      }
                      {message.fileUrl && message.fileName && (
                        <div className="file-attachment" style={{
                          marginTop: '10px',
                          padding: '10px',
                          backgroundColor: message.isUser ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.05)',
                          borderRadius: '8px',
                          border: '1px solid rgba(0,0,0,0.1)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between'
                        }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <FileText size={16} style={{ color: message.isUser ? '#fff' : '#666' }} />
                            <span style={{ 
                              fontSize: '14px', 
                              color: message.isUser ? '#fff' : '#333',
                              fontWeight: '500'
                            }}>
                              {message.fileName}
                            </span>
                          </div>
                          <button
                            onClick={() => handleFileDownload(message.fileUrl!, message.fileName!)}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: '4px',
                              padding: '6px 12px',
                              backgroundColor: message.isUser ? 'rgba(255,255,255,0.2)' : '#007AFF',
                              color: message.isUser ? '#fff' : '#fff',
                              border: 'none',
                              borderRadius: '4px',
                              fontSize: '12px',
                              cursor: 'pointer',
                              fontWeight: '500'
                            }}
                            onMouseEnter={(e) => {
                              e.currentTarget.style.backgroundColor = message.isUser ? 'rgba(255,255,255,0.3)' : '#0051D5';
                            }}
                            onMouseLeave={(e) => {
                              e.currentTarget.style.backgroundColor = message.isUser ? 'rgba(255,255,255,0.2)' : '#007AFF';
                            }}
                          >
                            <Download size={12} />
                            Download
                          </button>
                        </div>
                      )}
                    </>
                  )}
                </div>
                <div className="message-time">
                  {formatTime(message.timestamp)}
                </div>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="input-container">
        <div className="input-wrapper">
          <button className="attachment-button">
            <Plus size={20} />
          </button>
          <div className="text-input-container">
            <textarea
              ref={textareaRef}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Message AI Assistant..."
              className="message-input"
              rows={1}
              maxLength={2000}
            />
            <div className="input-actions">
              <button className="emoji-button">
                <Smile size={18} />
              </button>
              <button className="mic-button">
                <Mic size={18} />
              </button>
            </div>
          </div>
          <button 
            className={`send-button ${inputMessage.trim() ? 'active' : ''}`}
            onClick={handleSendMessage}
            disabled={!inputMessage.trim()}
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}