"use client"

import { Dashboard } from "@/components/ui/dashboard"
import { ChatbotUIContext } from "@/context/context"
import { getAssistantWorkspacesByWorkspaceId } from "@/db/assistants"
import { getChatsByWorkspaceId } from "@/db/chats"
import { getCollectionWorkspacesByWorkspaceId } from "@/db/collections"
import { getFileWorkspacesByWorkspaceId } from "@/db/files"
import { getFoldersByWorkspaceId } from "@/db/folders"
import { getModelWorkspacesByWorkspaceId } from "@/db/models"
import { getPresetWorkspacesByWorkspaceId } from "@/db/presets"
import { getPromptWorkspacesByWorkspaceId } from "@/db/prompts"
import { getAssistantImageFromStorage } from "@/db/storage/assistant-images"
import { getToolWorkspacesByWorkspaceId } from "@/db/tools"
import { getWorkspaceById } from "@/db/workspaces"
import { convertBlobToBase64 } from "@/lib/blob-to-b64"
import { supabase } from "@/lib/supabase/browser-client"
import { LLMID } from "@/types"
import { useParams, useRouter, useSearchParams } from "next/navigation"
import { ReactNode, useContext, useEffect, useState } from "react"
import Loading from "../loading"

interface WorkspaceLayoutProps {
  children: ReactNode
}

export default function WorkspaceLayout({ children }: WorkspaceLayoutProps) {
  const router = useRouter()

  const params = useParams()
  const searchParams = useSearchParams()
  const workspaceId = params.workspaceid as string

  const {
    setChatSettings,
    setAssistants,
    setAssistantImages,
    setChats,
    setCollections,
    setFolders,
    setFiles,
    setPresets,
    setPrompts,
    setTools,
    setModels,
    selectedWorkspace,
    setSelectedWorkspace,
    setSelectedChat,
    setChatMessages,
    setUserInput,
    setIsGenerating,
    setFirstTokenReceived,
    setChatFiles,
    setChatImages,
    setNewMessageFiles,
    setNewMessageImages,
    setShowFilesDisplay
  } = useContext(ChatbotUIContext)

  const [loading, setLoading] = useState(true)

  useEffect(() => {
    ;(async () => {
      // Skip authentication and use mock data for Supervisor Agent
      await initializeMockWorkspace(workspaceId)
    })()
  }, [])

  useEffect(() => {
    setUserInput("")
    setChatMessages([])
    setSelectedChat(null)

    setIsGenerating(false)
    setFirstTokenReceived(false)

    setChatFiles([])
    setChatImages([])
    setNewMessageFiles([])
    setNewMessageImages([])
    setShowFilesDisplay(false)
  }, [workspaceId])

  const initializeMockWorkspace = async (workspaceId: string) => {
    setLoading(true)

    // Create mock workspace that matches the one in GlobalState
    const mockWorkspace = {
      id: workspaceId,
      user_id: "supervisor-user",
      name: "Chat with Supervisor Agent",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      image_path: "",
      instructions: "",
      default_context_length: 4000,
      default_model: "supervisor-agent",
      default_prompt: "You are a helpful AI assistant.",
      default_temperature: 0.5,
      embeddings_provider: "openai",
      include_profile_context: false,
      include_workspace_instructions: false,
      is_home: true,
      sharing: "private"
    } as any

    setSelectedWorkspace(mockWorkspace)

    // Set empty data for all workspace items since we're using supervisor agent only
    setAssistants([])
    setAssistantImages([])
    setChats([])
    setCollections([])
    setFolders([])
    setFiles([])
    setPresets([])
    setPrompts([])
    setTools([])
    setModels([])

    setChatSettings({
      model: "supervisor-agent" as LLMID,
      prompt: "You are a helpful AI assistant.",
      temperature: 0.5,
      contextLength: 4000,
      includeProfileContext: false,
      includeWorkspaceInstructions: false,
      embeddingsProvider: "openai"
    })

    setLoading(false)
  }

  if (loading) {
    return <Loading />
  }

  return <Dashboard>{children}</Dashboard>
}
