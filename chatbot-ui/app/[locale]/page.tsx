"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"

export default function HomePage() {
  const router = useRouter()

  useEffect(() => {
    // Redirect directly to chat with a default workspace
    router.push("/default/chat")
  }, [router])

  return (
    <div className="flex size-full flex-col items-center justify-center">
      <div className="text-xl">Redirecting to chat...</div>
    </div>
  )
}
