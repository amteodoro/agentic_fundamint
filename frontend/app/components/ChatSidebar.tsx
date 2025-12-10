"use client";

import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { useChatContext } from '@/app/context/ChatContext';

const ChatSidebar = () => {
  const { ticker, setActiveTab } = useChatContext();
  const [messages, setMessages] = useState<{ sender: string; text: string }[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (input.trim() === '' || isLoading) return;

    const newMessages = [...messages, { sender: 'user', text: input }];
    setMessages(newMessages);
    const messageToSend = input;
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8100/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: messageToSend,
          thread_id: 'fundamint-chat-thread', // Using a static thread_id for now
          context: { ticker },
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response from the bot.');
      }

      const data = await response.json();
      let botMessage = data.message;

      // Parse for tab switching commands [SWITCH_TAB: tab_name]
      const tabSwitchMatch = botMessage.match(/\[SWITCH_TAB:\s*([^\]]+)\]/);
      if (tabSwitchMatch) {
        const targetTab = tabSwitchMatch[1].trim();
        // Remove the command from the displayed message
        botMessage = botMessage.replace(/\[SWITCH_TAB:\s*([^\]]+)\]/, '').trim();

        // Switch to the tab
        setActiveTab(targetTab);
      }

      setMessages([...newMessages, { sender: 'bot', text: botMessage }]);
    } catch (error) {
      console.error("Chat API error:", error);
      setMessages([...newMessages, { sender: 'bot', text: 'Sorry, I encountered an error.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative h-full w-80 border-l bg-gray-50 dark:bg-gray-900 hidden md:block">
      <div className="absolute top-0 left-0 right-0 bottom-20 p-4 overflow-y-auto">
        {messages.map((msg, index) => (
          <div key={index} className={`my-2 ${msg.sender === 'user' ? 'text-right' : 'text-left'}`}>
            <div className={`inline-block p-2 rounded-lg max-w-full ${msg.sender === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100'}`}>
              {msg.sender === 'bot' ? (
                <div className="prose prose-sm dark:prose-invert prose-headings:text-base prose-headings:font-semibold prose-headings:mt-3 prose-headings:mb-1 prose-p:my-1 prose-ul:my-1 prose-li:my-0.5 prose-strong:font-semibold max-w-none text-left">
                  <ReactMarkdown>{msg.text}</ReactMarkdown>
                </div>
              ) : (
                msg.text
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
        {isLoading && (
          <div className="my-2 text-left">
            <div className="inline-block p-2 rounded-lg bg-gray-200 dark:bg-gray-700 animate-pulse">
              Thinking...
            </div>
          </div>
        )}
      </div>
      <div className="absolute bottom-0 left-0 right-0 p-4 border-t">
        <div className="flex space-x-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder={ticker ? `Ask about ${ticker}...` : 'Ask a question...'}
            disabled={isLoading}
          />
          <Button onClick={handleSend} disabled={isLoading}>
            {isLoading ? 'Sending...' : 'Send'}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ChatSidebar;
