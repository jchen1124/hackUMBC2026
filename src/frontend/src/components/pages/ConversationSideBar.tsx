import React, { useState } from "react";
import { Search, MessageCircle, Edit } from "lucide-react";
import './ConversationSideBar.css';
interface ConversationSidebarProps {
  conversations: any[];
  selectedConversation: any | null;
  onSelectConversation: (conv: any) => void;
}

export default function ConversationSidebar({
  conversations,
  selectedConversation,
  onSelectConversation
}: ConversationSidebarProps) {
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Filter conversations by name and last message
  const filteredConversations = conversations.filter(conv =>
    conv.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (conv.lastMessage && conv.lastMessage.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const formatTime = (timestamp: number | string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      return date.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
      });
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return date.toLocaleDateString('en-US', { weekday: 'short' });
    } else {
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric' 
      });
    }
  };

  const getInitials = (name: string) => {
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  const getAvatarColorClass = (name: string) => {
    const colors = [
      'avatar-1', 'avatar-2', 'avatar-3', 'avatar-4',
      'avatar-5', 'avatar-6', 'avatar-7', 'avatar-8'
    ];
    const index = name.length % colors.length;
    return colors[index];
  };

  // Sample conversations for demo
  const sampleConversations = conversations.length ? conversations : [
    {
      id: 1,
      name: "Sarah Wilson",
      lastMessage: "Hey! Are we still on for dinner tonight?",
      timestamp: Date.now() - 300000,
      unreadCount: 2,
      isOnline: true
    },
    {
      id: 2,
      name: "Mom",
      lastMessage: "Don't forget to call grandma on her birthday!",
      timestamp: Date.now() - 3600000,
      unreadCount: 0,
      isOnline: false
    },
    {
      id: 3,
      name: "Work Team",
      lastMessage: "Meeting moved to 3 PM tomorrow",
      timestamp: Date.now() - 7200000,
      unreadCount: 1,
      isOnline: true
    },
    {
      id: 4,
      name: "John Smith",
      lastMessage: "Thanks for the help with the project!",
      timestamp: Date.now() - 86400000,
      unreadCount: 0,
      isOnline: false
    }
  ];

  const displayConversations = filteredConversations.length ? filteredConversations : sampleConversations;

  return (
    <div className="imessage-sidebar">
      {/* Header */}
      <div className="sidebar-header">
        <div className="header-top">
          <h1 className="header-title">Messages</h1>
          <button className="edit-button">
            <Edit size={16} />
          </button>
        </div>
        
        {/* Search Bar */}
        <div className="search-container">
          <input
            type="text"
            placeholder="Search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
          <Search className="search-icon" size={16} />
        </div>
      </div>

      {/* Conversation List */}
      <div className="conversation-list">
        {displayConversations.map((conversation) => (
          <div
            key={conversation.id}
            onClick={() => onSelectConversation(conversation)}
            className={`conversation-item ${
              selectedConversation?.id === conversation.id ? 'selected' : ''
            }`}
          >
            {/* Avatar */}
            <div className="avatar-container">
              <div className={`avatar ${getAvatarColorClass(conversation.name)}`}>
                {getInitials(conversation.name)}
              </div>
              {conversation.isOnline && (
                <div className="online-indicator"></div>
              )}
            </div>

            {/* Content */}
            <div className="conversation-content">
              <div className="conversation-header">
                <h3 className={`conversation-name ${
                  conversation.unreadCount > 0 ? 'unread' : ''
                }`}>
                  {conversation.name}
                </h3>
                <span className="conversation-time">
                  {formatTime(conversation.timestamp || Date.now())}
                </span>
              </div>

              {/* Last Message Preview */}
              <div className="conversation-preview">
                <p className={`last-message ${
                  conversation.unreadCount > 0 ? 'unread' : ''
                }`}>
                  {conversation.lastMessage || "No messages yet"}
                </p>
                
                {/* Unread Badge */}
                {conversation.unreadCount > 0 && (
                  <span className="unread-badge">
                    {conversation.unreadCount > 99 ? '99+' : conversation.unreadCount}
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}

        {/* Empty State */}
        {displayConversations.length === 0 && (
          <div className="empty-state">
            <div className="empty-icon">
              <MessageCircle size={40} />
            </div>
            <h3 className="empty-title">
              {searchQuery ? "No Results" : "No Messages"}
            </h3>
            <p className="empty-subtitle">
              {searchQuery 
                ? `No conversations found for "${searchQuery}"`
                : "Your conversations will appear here"
              }
            </p>
          </div>
        )}
      </div>

      {/* Bottom Status */}
      <div className="sidebar-footer">
        <p className="footer-text">
          {displayConversations.length} conversation{displayConversations.length !== 1 ? 's' : ''}
        </p>
      </div>
    </div>
  );
}