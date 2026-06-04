import React from 'react'
import { Header } from './Header'

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Header />
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-8">
        {children}
      </main>
      <footer className="bg-gray-900 text-gray-300 text-center py-4 mt-auto">
        <p className="text-sm">
          ISO 20022 GenAI Migration Platform v3 | Powered by FastAPI + React
        </p>
      </footer>
    </div>
  )
}
