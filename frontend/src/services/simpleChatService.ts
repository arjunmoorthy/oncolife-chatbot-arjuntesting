// Use Modal API endpoints
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'https://arjunmoorthy--oncolife-chatbot-test-chat-endpoint-dev.modal.run';

export const simpleChatService = {
  getTodaySession: async () => {
    try {
      // For now, return a mock session since Modal doesn't have session endpoints
      return {
        success: true,
        status: 200,
        data: {
          chat_uuid: "default-chat",
          conversation_state: "ACTIVE",
          messages: []
        }
      };
    } catch (error) {
      console.error('Failed to fetch chat session:', error);
      throw error;
    }
  },

  startNewSession: async () => {
    // For now, return a mock session
    return {
      chat_uuid: `chat-${Date.now()}`,
      conversation_state: "ACTIVE",
      messages: []
    };
  },

  sendMessage: async (message: string, chat_uuid: string) => {
    try {
      const response = await fetch(`${API_BASE}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: message,
          chat_uuid: chat_uuid
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to send message');
      }
      
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Failed to send message:', error);
      throw error;
    }
  }
}; 