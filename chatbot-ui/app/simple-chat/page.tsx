"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import ReactMarkdown from "react-markdown"
import rehypeRaw from "rehype-raw"

// Render message content with markdown and HTML support
function renderMessageContent(content: string) {
  return (
    <ReactMarkdown
      rehypePlugins={[rehypeRaw]}
      components={{
        // Style paragraphs
        p: ({ node, ...props }) => <p className="mb-2" {...props} />,
        // Style unordered lists
        ul: ({ node, ...props }) => (
          <ul className="list-disc pl-6 my-2 space-y-1" {...props} />
        ),
        // Style list items
        li: ({ node, ...props }) => <li className="mb-1" {...props} />,
        // Style strong/bold
        strong: ({ node, ...props }) => (
          <strong className="font-semibold" {...props} />
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  )
}

export default function SimpleChat() {
  const [messages, setMessages] = useState<{role: string, content: string}[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  const sendMessage = async () => {
    if (!input.trim()) return
    
    const userMessage = { role: "user", content: input }
    setMessages(prev => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    try {
      const response = await fetch("/api/chat/supervisor", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          messages: [...messages, userMessage]
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let assistantContent = ""

      const assistantMessage = { role: "assistant", content: "" }
      setMessages(prev => [...prev, assistantMessage])

      if (reader) {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          
          const chunk = decoder.decode(value)
          assistantContent += chunk
          
          setMessages(prev => {
            const updated = [...prev]
            updated[updated.length - 1] = { role: "assistant", content: assistantContent }
            return updated
          })
        }
      }
    } catch (error) {
      console.error("Error:", error)
      setMessages(prev => [...prev, { role: "assistant", content: "Sorry, there was an error connecting to the Supervisor Agent." }])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4 text-center">Supervisor Agent Chat</h1>
      
      <div className="flex-1 overflow-y-auto space-y-4 mb-4 p-4 border rounded-lg">
        {messages.length === 0 && (
          <div className="text-center text-gray-500">
            Start a conversation with your Supervisor Agent
          </div>
        )}
        {messages.map((message, index) => (
          <div
            key={index}
            className={`p-3 rounded-lg ${
              message.role === "user"
                ? "bg-blue-100 ml-12 text-right"
                : "bg-gray-100 mr-12"
            }`}
          >
            <div className="font-semibold text-sm mb-1">
              {message.role === "user" ? "You" : "Supervisor Agent"}
            </div>
            <div className="break-words" style={{ lineHeight: '1.6' }}>
              {renderMessageContent(message.content)}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="bg-gray-100 mr-12 p-3 rounded-lg">
            <div className="font-semibold text-sm mb-1">Supervisor Agent</div>
            <div className="animate-pulse">Thinking...</div>
          </div>
        )}
      </div>
      
      <div className="flex space-x-2">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === "Enter" && !isLoading && sendMessage()}
          placeholder="Type your message..."
          disabled={isLoading}
          className="flex-1"
        />
        <Button onClick={sendMessage} disabled={isLoading || !input.trim()}>
          Send
        </Button>
      </div>
    </div>
  )
}