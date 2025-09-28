export {};

interface ConversationType {
  id: number;
  name: string;
  lastMessage?: string;
  last_message_time: number;
  unreadCount: number;
}

interface MessageType {
  id: number;
  conversation_id: number;
  content: string;
  timestamp: number;
  sender: string;
}

interface AttachmentType {
  id: number;
  conversation_id: number;
  filename: string;
  timestamp: number;
}
