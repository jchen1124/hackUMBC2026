// src/components/pages/Dashboard.tsx - Debug Version
import React, { useState } from "react";
import ConversationSidebar from "./ConversationSideBar";
import AIChatbot from "./AIChatbot";

interface ConversationType {
  id: number;
  name: string;
  lastMessage?: string;
  timestamp: number;
  unreadCount: number;
  isOnline?: boolean;
}

const mockConversations: ConversationType[] = [
  {
    id: 1,
    name: "General",
    lastMessage: "Awesome message search!",
    timestamp: Date.now() - 300000,
    unreadCount: 2,
    isOnline: true,
  },
];

export default function Dashboard() {
  const [conversations] = useState<ConversationType[]>(mockConversations);
  const [selectedConversation, setSelectedConversation] =
    useState<ConversationType | null>(mockConversations[0]);

  return (
    <div
      style={{
        display: "flex",
        height: "100vh",
        backgroundColor: "#f9fafb",
        overflow: "hidden",
        width: "100%",
      }}
    >
      {/* Sidebar Container - Force specific dimensions */}
      <div
        style={{
          width: "320px",
          height: "100vh",
          flexShrink: 0,
          flexGrow: 0,
          backgroundColor: "#fff",
          borderRight: "1px solid #e5e7eb",
        }}
      >
        <ConversationSidebar
          conversations={conversations}
          selectedConversation={selectedConversation}
          onSelectConversation={setSelectedConversation}
        />
      </div>

      {/* Chatbot Container - Take remaining space */}
      <div
        style={{
          flex: 1,
          height: "100vh",
          overflow: "hidden",
          backgroundColor: "#fff",
        }}
      >
        <AIChatbot />
      </div>
    </div>
  );
}
