import { NextResponse } from "next/server"
import { ServerRuntime } from "next"

export const runtime: ServerRuntime = "edge"

export async function POST(request: Request) {
  try {
    const json = await request.json()
    const { messages } = json as {
      messages: any[]
    }

    // Get the last message from the user
    const lastMessage = messages[messages.length - 1]
    const userMessage = lastMessage?.content || ""

    // Call your Supervisor Agent streaming API
    const response = await fetch("http://localhost:8000/chat/stream", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: userMessage
      })
    })

    if (!response.ok) {
      throw new Error(`Supervisor Agent API error: ${response.status}`)
    }

    // Pass through the streaming response
    const stream = response.body

    return new Response(stream, {
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
        "Transfer-Encoding": "chunked"
      }
    })
    
  } catch (error: any) {
    console.error("Supervisor Agent API error:", error)
    
    return NextResponse.json(
      { message: error.message || "Failed to connect to Supervisor Agent" },
      { status: 500 }
    )
  }
}