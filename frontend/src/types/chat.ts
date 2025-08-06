export interface Message {
  id: number;
  chat_uuid: string;
  sender: 'user' | 'assistant';
  message_type: 'text' | 'button_response' | 'multi_select_response' | 'single-select' | 'multi-select' | 'button_prompt' | 'feeling-select' | 'feeling_response';
  content: string;
  structured_data?: {
    options?: string[];
    selected_options?: string[];
    max_selections?: number;
  };
  created_at: string;
}

export interface ChatSession {
  chat_uuid: string;
  conversation_state: string;
  messages: Message[];
  is_new_session: boolean;
}

export type ResponseType = 'text' | 'button_prompt' | 'multi_select' | 'button_response' | 'multi_select_response' | 'feeling-select' | 'feeling_response'; 