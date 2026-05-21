import { useState, useRef, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Bot, Send, Loader2, Sparkles } from "lucide-react";
import { useAskAssistant } from "../api";
import type { AssistantResponse } from "../types";

export function AIAssistantPage() {
  const { t } = useTranslation();
  const [query, setQuery] = useState("");

  const SUGGESTIONS = [
    t("ai.suggestions.budget"),
    t("ai.suggestions.anomalies"),
    t("ai.suggestions.recommendations"),
    t("ai.suggestions.employees"),
    t("ai.suggestions.pending"),
  ];
  const [messages, setMessages] = useState<{ role: "user" | "assistant"; text: string }[]>([]);
  const { mutate, isPending } = useAskAssistant();
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = (q?: string) => {
    const text = (q || query).trim();
    if (!text || isPending) return;
    setQuery("");
    setMessages(prev => [...prev, { role: "user", text }]);
    mutate(text, {
      onSuccess: (res: AssistantResponse) => {
        const reply = typeof res.response === "string" ? res.response : res.response?.text || JSON.stringify(res.response);
        setMessages(prev => [...prev, { role: "assistant", text: reply }]);
      },
      onError: () => {
        setMessages(prev => [...prev, { role: "assistant", text: t("ai.error") }]);
      },
    });
  };

  return (
    <div className="max-w-3xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2.5 rounded-xl bg-brand/10">
            <Bot className="w-6 h-6 text-brand" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{t("ai.assistant")}</h1>
            <p className="text-sm text-gray-500">{t("ai.askQuestion")}</p>
          </div>
        </div>
      </div>

      {/* Chat */}
      <div className="card p-0 flex flex-col overflow-hidden">
        <div ref={listRef} className="p-4 max-h-96 overflow-y-auto space-y-3 bg-gray-50">
          {messages.length === 0 && (
            <div className="text-center py-8">
              <Sparkles className="w-8 h-8 text-gray-300 mx-auto mb-2" />
              <p className="text-sm text-gray-400 mb-4">{t("ai.suggestions.title")}</p>
              <div className="flex flex-wrap gap-2 justify-center">
                {SUGGESTIONS.map(s => (
                  <button
                    key={s}
                    onClick={() => handleSend(s)}
                    className="text-xs px-3 py-1.5 rounded-full bg-white border border-gray-200 text-gray-600 hover:border-primary-300 hover:text-primary-600 transition-colors"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[80%] rounded-xl px-4 py-2.5 text-sm ${
                m.role === "user"
                  ? "bg-brand text-white rounded-br-sm"
                  : "bg-white text-gray-700 border border-gray-200 rounded-bl-sm"
              }`}>
                {m.text}
              </div>
            </div>
          ))}
          {isPending && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-200 rounded-xl rounded-bl-sm px-4 py-2.5 text-sm text-gray-400 flex items-center gap-2">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                {t("ai.thinking")}
              </div>
            </div>
          )}
        </div>

        <div className="border-t border-gray-200 p-4 flex gap-3">
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleSend()}
            placeholder={t("ai.inputPlaceholder")}
            className="flex-1 text-sm border border-gray-200 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
          <button
            onClick={() => handleSend()}
            disabled={!query.trim() || isPending}
            className="px-4 py-2.5 rounded-lg bg-brand text-white hover:bg-brand-dark disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            <Send className="w-4 h-4" />
            <span className="hidden sm:inline">{t("ai.send")}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
