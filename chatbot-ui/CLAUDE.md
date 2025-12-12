# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Core Development
- `npm run dev` - Start development server at http://localhost:3000
- `npm run build` - Build the application for production
- `npm run start` - Start production server
- `npm run preview` - Build and start production server
- `npm run chat` - Start Supabase and development server (recommended for development)
- `npm run restart` - Stop and restart Supabase with development server

### Database Management
- `npm run db-reset` - Reset local Supabase database and regenerate types
- `npm run db-migrate` - Apply pending migrations and regenerate types
- `npm run db-types` - Generate TypeScript types from Supabase schema
- `npm run db-push` - Push local database changes to hosted instance
- `npm run db-pull` - Pull remote changes to local database

### Code Quality
- `npm run lint` - Run ESLint
- `npm run lint:fix` - Run ESLint with auto-fix
- `npm run type-check` - Run TypeScript type checking
- `npm run format:write` - Format code with Prettier
- `npm run format:check` - Check code formatting
- `npm run clean` - Run lint:fix and format:write together

### Testing & Analysis
- `npm test` - Run Jest tests
- `npm run analyze` - Bundle analysis (set ANALYZE=true)

### Updates
- `npm run update` - Pull latest changes, migrate database, and regenerate types

## High-Level Architecture

### Tech Stack
- **Framework**: Next.js 14 with App Router
- **Database**: Supabase (PostgreSQL) with real-time subscriptions
- **Authentication**: Supabase Auth
- **UI**: Tailwind CSS + Radix UI components
- **AI Providers**: OpenAI, Anthropic, Google, Azure, Mistral, Groq, Perplexity, OpenRouter
- **File Processing**: Support for PDF, DOCX, CSV, JSON, MD, TXT
- **Deployment**: Designed for Vercel (frontend) + Supabase (backend)

### Core Architecture Patterns

**App Router Structure**: Uses Next.js 13+ app directory with nested layouts and internationalization support (`[locale]/[workspaceid]/chat/[chatid]`)

**Global State Management**: React Context (`context/context.tsx`) manages all application state including chats, messages, files, assistants, workspaces, and user settings

**Database Layer**: Supabase client with separate modules in `/db/` for each entity (chats, messages, files, assistants, etc.) with corresponding TypeScript types generated from database schema

**API Routes**: Modular API structure in `app/api/` with separate route handlers for each AI provider, supporting streaming responses and multimodal inputs

**Component Architecture**: 
- `/components/chat/` - Chat interface and message handling
- `/components/sidebar/` - Navigation and item management
- `/components/ui/` - Reusable UI components (shadcn/ui)
- `/components/messages/` - Message rendering with markdown and code highlighting

### Key Features Architecture

**Multi-Provider AI Support**: Each provider has its own API route (`app/api/chat/[provider]/route.ts`) with provider-specific message formatting and streaming

**File Processing Pipeline**: Upload → Processing (in `/lib/retrieval/processing/`) → Chunking → Vector embedding → Storage in Supabase

**Real-time Updates**: Supabase real-time subscriptions for collaborative features and live updates

**Workspace System**: Multi-tenant architecture where users can have multiple workspaces, each with isolated chats, files, and assistants

**Assistant System**: Custom AI assistants with configurable tools, file access, and retrieval capabilities

### Environment Setup

Requires Supabase local development stack:
1. Docker (for Supabase local)
2. Supabase CLI
3. Environment variables in `.env.local` (copy from `.env.local.example`)
4. Database migrations in `/supabase/migrations/`

### Testing
- Jest configured for Next.js with jsdom environment
- Test files in `__tests__/` directory
- Playwright tests in `__tests__/playwright-test/`

### Build Configuration
- Bundle analyzer available with `ANALYZE=true`
- PWA support configured
- Image optimization for external sources
- External packages configured for server components