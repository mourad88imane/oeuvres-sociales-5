/**
 * APP LAYOUT — Layout principal avec sidebar et header
 */
import { useState } from "react";
import { Outlet } from "react-router-dom";
import { Search, Menu } from "lucide-react";
import { Sidebar } from "./Sidebar";
import { NotificationBell } from "@modules/notifications/components/NotificationBell";
import { useAuthStore } from "@modules/auth/store/authStore";
import { ToastProvider, ToastViewport } from "@shared/components/ui/index";
import { AIAssistantBubble } from "@modules/ai/components/AIAssistantBubble";

export function AppLayout() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const { user } = useAuthStore();

  return (
    <ToastProvider>
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* ── Sidebar desktop ──────────────────────────── */}
      <div className="hidden md:flex">
        <Sidebar
          collapsed={sidebarCollapsed}
          onCollapse={setSidebarCollapsed}
        />
      </div>

      {/* ── Sidebar mobile (overlay) ──────────────────── */}
      {mobileSidebarOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setMobileSidebarOpen(false)}
          />
          <div className="relative z-50 flex h-full w-64">
            <Sidebar
              collapsed={false}
              onCollapse={() => setMobileSidebarOpen(false)}
            />
          </div>
        </div>
      )}

      {/* ── Contenu principal ─────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* ── Header ──────────────────────────────────── */}
        <header className="h-14 bg-white border-b border-gray-200 flex items-center px-4 gap-4 shrink-0">
          {/* Bouton menu mobile */}
          <button
            className="md:hidden p-1.5 rounded-lg hover:bg-gray-100"
            onClick={() => setMobileSidebarOpen(true)}
          >
            <Menu className="w-5 h-5" />
          </button>

          {/* Barre de recherche */}
          <div className="flex-1 max-w-md hidden sm:block">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Rechercher..."
                className="w-full pl-9 pr-4 py-1.5 text-sm border border-gray-200 rounded-lg
                  bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:bg-white"
              />
            </div>
          </div>

          <div className="flex-1" />

          {/* Actions header */}
          <div className="flex items-center gap-2">
            <NotificationBell />

            {/* Avatar utilisateur */}
            <button className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-gray-100 transition-colors">
              <div className="w-7 h-7 rounded-full bg-brand flex items-center justify-center text-white text-xs font-bold">
                {user?.full_name?.charAt(0).toUpperCase() || "?"}
              </div>
              <span className="text-sm font-medium text-gray-700 hidden sm:block">
                {user?.full_name}
              </span>
            </button>
          </div>
        </header>

        {/* ── Zone de contenu des pages ─────────────── */}
        <main className="flex-1 overflow-y-auto">
          <div className="p-6">
            <Outlet />
          </div>
        </main>
      </div>
      <ToastViewport />
      <AIAssistantBubble />
    </div>
    </ToastProvider>
  );
}
