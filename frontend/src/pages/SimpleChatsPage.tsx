import React, { useEffect, useState, useRef, useCallback } from 'react';
import { MessageBubble } from '../components/chat/MessageBubble';
import { MessageInput } from '../components/chat/MessageInput';
import { ThinkingBubble } from '../components/chat/ThinkingBubble';
import { CalendarModal } from '../components/chat/CalendarModal';
import { simpleChatService } from '../services/simpleChatService';
import type { ChatSession, Message } from '../types/chat';
import '../components/chat/Chat.css';

const SimpleChatsPage: React.FC = () => {
  const [chatSession, setChatSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isThinking, setIsThinking] = useState(false);
  const [isCalendarModalOpen, setIsCalendarModalOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadTodaySession = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await simpleChatService.getTodaySession();
      const sessionData = response.data;
      setChatSession(sessionData);
      setMessages(sessionData.messages || []);
    } catch (error) {
      setError('Failed to load chat session');
      console.error('Failed to load chat session:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTodaySession();
  }, []);

  const handleStartNewConversation = async () => {
    try {
      setLoading(true);
      setError(null);
      const sessionData = await simpleChatService.startNewSession();
      setChatSession(sessionData);
      setMessages(sessionData.messages || []);
    } catch (error) {
      setError('Failed to start a new chat session');
      console.error('Failed to start a new chat session:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async (content: string) => {
    if (!chatSession || !content.trim()) return;

    const userMessage: Message = {
      id: Date.now(),
      chat_uuid: chatSession.chat_uuid,
      sender: 'user',
      message_type: 'text',
      content: content.trim(),
      created_at: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsThinking(true);

    try {
      const response = await simpleChatService.sendMessage(content.trim(), chatSession.chat_uuid);
      
      const botMessage: Message = {
        id: Date.now() + 1,
        chat_uuid: chatSession.chat_uuid,
        sender: 'assistant',
        message_type: 'text',
        content: response.reply,
        created_at: new Date().toISOString(),
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage: Message = {
        id: Date.now() + 1,
        chat_uuid: chatSession.chat_uuid,
        sender: 'assistant',
        message_type: 'text',
        content: 'Sorry, I encountered an error. Please try again.',
        created_at: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsThinking(false);
    }
  };

  const handleButtonClick = async (option: string) => {
    if (!chatSession) return;

    const userMessage: Message = {
      id: Date.now(),
      chat_uuid: chatSession.chat_uuid,
      sender: 'user',
      message_type: 'button_response',
      content: option,
      created_at: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsThinking(true);

    try {
      const response = await simpleChatService.sendMessage(option, chatSession.chat_uuid);
      
      const botMessage: Message = {
        id: Date.now() + 1,
        chat_uuid: chatSession.chat_uuid,
        sender: 'assistant',
        message_type: 'text',
        content: response.reply,
        created_at: new Date().toISOString(),
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage: Message = {
        id: Date.now() + 1,
        chat_uuid: chatSession.chat_uuid,
        sender: 'assistant',
        message_type: 'text',
        content: 'Sorry, I encountered an error. Please try again.',
        created_at: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsThinking(false);
    }
  };

  const handleMultiSelectSubmit = async (selections: string[]) => {
    if (!chatSession || selections.length === 0) return;

    const userMessage: Message = {
      id: Date.now(),
      chat_uuid: chatSession.chat_uuid,
      sender: 'user',
      message_type: 'multi_select_response',
      content: selections.join(', '),
      created_at: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsThinking(true);

    try {
      const response = await simpleChatService.sendMessage(selections.join(', '), chatSession.chat_uuid);
      
      const botMessage: Message = {
        id: Date.now() + 1,
        chat_uuid: chatSession.chat_uuid,
        sender: 'assistant',
        message_type: 'text',
        content: response.reply,
        created_at: new Date().toISOString(),
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage: Message = {
        id: Date.now() + 1,
        chat_uuid: chatSession.chat_uuid,
        sender: 'assistant',
        message_type: 'text',
        content: 'Sorry, I encountered an error. Please try again.',
        created_at: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsThinking(false);
    }
  };

  const handleFeelingSelect = async (feeling: string) => {
    if (!chatSession) return;

    const userMessage: Message = {
      id: Date.now(),
      chat_uuid: chatSession.chat_uuid,
      sender: 'user',
      message_type: 'feeling_response',
      content: feeling,
      created_at: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsThinking(true);

    try {
      const response = await simpleChatService.sendMessage(feeling, chatSession.chat_uuid);
      
      const botMessage: Message = {
        id: Date.now() + 1,
        chat_uuid: chatSession.chat_uuid,
        sender: 'assistant',
        message_type: 'text',
        content: response.reply,
        created_at: new Date().toISOString(),
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage: Message = {
        id: Date.now() + 1,
        chat_uuid: chatSession.chat_uuid,
        sender: 'assistant',
        message_type: 'text',
        content: 'Sorry, I encountered an error. Please try again.',
        created_at: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsThinking(false);
    }
  };

  const handleCalendarDateSelect = async (selectedDate: Date) => {
    if (!chatSession) return;

    const userMessage: Message = {
      id: Date.now(),
      chat_uuid: chatSession.chat_uuid,
      sender: 'user',
      message_type: 'text',
      content: selectedDate.toISOString().split('T')[0],
      created_at: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsCalendarModalOpen(false);
    setIsThinking(true);

    try {
      const response = await simpleChatService.sendMessage(selectedDate.toISOString().split('T')[0], chatSession.chat_uuid);
      
      const botMessage: Message = {
        id: Date.now() + 1,
        chat_uuid: chatSession.chat_uuid,
        sender: 'assistant',
        message_type: 'text',
        content: response.reply,
        created_at: new Date().toISOString(),
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage: Message = {
        id: Date.now() + 1,
        chat_uuid: chatSession.chat_uuid,
        sender: 'assistant',
        message_type: 'text',
        content: 'Sorry, I encountered an error. Please try again.',
        created_at: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsThinking(false);
    }
  };

  const shouldShowTextInput = () => {
    if (messages.length === 0) return true;
    
    const lastMessage = messages[messages.length - 1];
    if (lastMessage.sender !== 'assistant') return false;
    
    const responseType = lastMessage.message_type;
    return responseType === 'text' || responseType === 'summary' || responseType === 'end';
  };

  const shouldShowInteractiveElements = (message: Message, index: number): boolean => {
    if (message.sender !== 'assistant') return false;
    if (index !== messages.length - 1) return false;
    
    const responseType = message.message_type;
    return responseType === 'single-select' || 
           responseType === 'multi-select' || 
           responseType === 'feeling-select';
  };

  if (loading) {
    return (
      <div className="chat-container">
        <div className="loading">Loading chat...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="chat-container">
        <div className="error">
          <p>{error}</p>
          <button onClick={loadTodaySession}>Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h2>OncoLife Chatbot</h2>
        <button onClick={handleStartNewConversation} className="new-chat-btn">
          Start New Chat
        </button>
      </div>

      <div className="messages-container">
        {messages.map((message, index) => (
          <div key={message.id}>
            <MessageBubble message={message} />
            {shouldShowInteractiveElements(message, index) && (
              <div className="interactive-elements">
                {message.message_type === 'single-select' && message.structured_data?.options && (
                  <div className="button-options">
                    {message.structured_data.options.map((option: string) => (
                      <button
                        key={option}
                        onClick={() => handleButtonClick(option)}
                        className="option-button"
                      >
                        {option}
                      </button>
                    ))}
                  </div>
                )}
                {message.message_type === 'multi-select' && message.structured_data?.options && (
                  <MultiSelectMessage
                    options={message.structured_data.options}
                    onSubmit={handleMultiSelectSubmit}
                  />
                )}
                {message.message_type === 'feeling-select' && (
                  <FeelingSelector onSelect={handleFeelingSelect} />
                )}
              </div>
            )}
          </div>
        ))}
        
        {isThinking && <ThinkingBubble />}
        <div ref={messagesEndRef} />
      </div>

      {shouldShowTextInput() && (
        <MessageInput onSendMessage={handleSendMessage} />
      )}

      <CalendarModal
        isOpen={isCalendarModalOpen}
        onClose={() => setIsCalendarModalOpen(false)}
        onDateSelect={handleCalendarDateSelect}
      />
    </div>
  );
};

export default SimpleChatsPage; 