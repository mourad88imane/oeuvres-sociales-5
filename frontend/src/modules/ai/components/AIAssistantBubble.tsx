import { useState, useRef, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Bot, X, Send, Loader2 } from "lucide-react";
import { useAskAssistant } from "../api";
import type { AssistantResponse } from "../types";

export function AIAssistantBubble() {
  const { t, i18n } = useTranslation();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<{ role: "user" | "assistant"; text: string }[]>([]);
  const { mutate, isPending } = useAskAssistant();
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = () => {
    const q = query.trim();
    if (!q || isPending) return;
    setQuery("");
    setMessages(prev => [...prev, { role: "user", text: q }]);
    mutate(q, {
      onSuccess: (res: AssistantResponse) => {
        const reply = typeof res.response === "string" ? res.response : res.response?.text || JSON.stringify(res.response);
        setMessages(prev => [...prev, { role: "assistant", text: reply }]);
      },
      onError: () => {
        setMessages(prev => [...prev, { role: "assistant", text: t("ai.errorRetry") }]);
      },
    });
  };

  const isRtl = i18n.language === "ar";

  return (
    <>
      {!open && (
        <button
          onClick={() => setOpen(true)}
          className={`fixed bottom-6 z-50 w-12 h-12 rounded-2xl transition-all flex items-center justify-center ${isRtl ? "left-6" : "right-6"}`}
          style={{
            background: "#ffda2d",
            boxShadow: "0 4px 16px rgba(255,218,45,0.3)",
            color: "#1a1917",
          }}
          title={t("ai.assistant")}
        >
          <Bot className="w-6 h-6" />
        </button>
      )}

      {open && (
        <div className={`fixed bottom-6 z-50 w-80 sm:w-96 flex flex-col overflow-hidden animate-fade-in rounded-[24px] ${isRtl ? "left-6" : "right-6"}`}
          style={{
            background: "#ffffff",
            border: "1px solid rgba(0,0,0,0.06)",
            boxShadow: "0 10px 40px -8px rgba(0,0,0,0.08)",
          }}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3"
            style={{ borderBottom: "1px solid rgba(0,0,0,0.04)" }}
          >
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-xl flex items-center justify-center" style={{ background: "#ffda2d" }}>
                <Bot className="w-4 h-4" style={{ color: "#1a1917" }} />
              </div>
              <span className="text-sm font-bold" style={{ color: "#1a1917" }}>{t("ai.assistant")}</span>
            </div>
            <button onClick={() => setOpen(false)} className="p-1 rounded-lg" style={{ color: "#8a8882" }}>
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Messages */}
          <div ref={listRef} className="flex-1 p-4 space-y-3 max-h-80 overflow-y-auto"
            style={{ background: "#f8f7f4" }}
          >
            {messages.length === 0 && (
              <p className="text-sm text-center py-8 font-medium" style={{ color: "#8a8882" }}>
                {t("ai.askQuestion")}
              </p>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[80%] rounded-xl px-3 py-2 text-sm font-medium ${
                  m.role === "user" ? "rounded-br-sm" : "rounded-bl-sm"
                }`}
                  style={m.role === "user" ? {
                    background: "#ffda2d",
                    color: "#1a1917",
                  } : {
                    background: "#ffffff",
                    border: "1px solid rgba(0,0,0,0.04)",
                    color: "#1a1917",
                  }}
                >
                  {m.text}
                </div>
              </div>
            ))}
            {isPending && (
              <div className="flex justify-start">
                <div className="rounded-xl rounded-bl-sm px-3 py-2 text-sm flex items-center gap-2 font-medium"
                  style={{
                    background: "#ffffff",
                    border: "1px solid rgba(0,0,0,0.04)",
                    color: "#8a8882",
                  }}
                >
                  <Loader2 className="w-3 h-3 animate-spin" />
                  {t("ai.thinking")}
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          <div className="p-3 flex gap-2" style={{ borderTop: "1px solid rgba(0,0,0,0.04)" }}>
            <input
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleSend()}
              placeholder={t("ai.inputPlaceholder")}
              className="flex-1 text-sm rounded-xl px-3 py-2 outline-none font-medium"
              style={{
                background: "#f3f2ee",
                border: "1px solid rgba(0,0,0,0.04)",
                color: "#1a1917",
              }}
            />
            <button
              onClick={handleSend}
              disabled={!query.trim() || isPending}
              className="p-2 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              style={{
                background: "#ffda2d",
                color: "#1a1917",
              }}
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </>
  );
}
