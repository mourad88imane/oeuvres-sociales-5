/**
 * COMMENTS SECTION — Fil de discussion sur une prestation
 */
import { useState } from "react";
import { MessageCircle, Send, Lock, MessageSquare, Loader2 } from "lucide-react";
import { clsx } from "clsx";
import { useAddComment } from "../hooks/useBenefits";
import type { Comment, CommentType } from "../types";

const TYPE_CONFIG: Record<CommentType, { icon: React.ElementType; label: string; bg: string; border: string }> = {
  internal:  { icon: Lock,          label: "Note interne",       bg: "bg-amber-50", border: "border-amber-200"  },
  requester: { icon: MessageSquare, label: "Message demandeur",  bg: "bg-blue-50",  border: "border-blue-200"   },
  system:    { icon: MessageCircle, label: "Système",            bg: "bg-gray-50",  border: "border-gray-200"   },
};

interface CommentsSectionProps {
  benefitId: string;
  comments: Comment[];
  canComment?: boolean;
}

export function CommentsSection({ benefitId, comments, canComment = true }: CommentsSectionProps) {
  const [content,     setContent]     = useState("");
  const [commentType, setCommentType] = useState<CommentType>("internal");
  const addComment = useAddComment(benefitId);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) return;
    await addComment.mutateAsync({ content: content.trim(), commentType });
    setContent("");
  };

  return (
    <div className="space-y-4">
      {/* ── Formulaire ───────────────────────────────── */}
      {canComment && (
        <form onSubmit={handleSubmit} className="space-y-2">
          <div className="flex gap-2">
            {(["internal","requester"] as CommentType[]).map(t => {
              const cfg = TYPE_CONFIG[t];
              const Icon = cfg.icon;
              return (
                <button type="button" key={t} onClick={() => setCommentType(t)}
                  className={clsx(
                    "flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg border transition-colors",
                    commentType === t
                      ? `${cfg.bg} ${cfg.border} font-medium`
                      : "bg-white border-gray-200 text-gray-500 hover:bg-gray-50",
                  )}>
                  <Icon className="w-3 h-3" />
                  {cfg.label}
                </button>
              );
            })}
          </div>
          <div className="relative">
            <textarea value={content} onChange={e => setContent(e.target.value)}
              rows={3} placeholder={commentType === "requester"
                ? "Message visible par le demandeur..."
                : "Note interne (visible uniquement par le personnel)..."}
              className={clsx(
                "w-full px-3 py-2 pr-12 text-sm border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-primary-500",
                commentType === "internal" ? "border-amber-200 bg-amber-50" : "border-blue-200 bg-blue-50",
              )}
            />
            <button type="submit" disabled={!content.trim() || addComment.isPending}
              className="absolute right-2 bottom-2 p-2 bg-brand text-white rounded-lg hover:bg-brand-light disabled:opacity-50 transition-colors">
              {addComment.isPending
                ? <Loader2 className="w-4 h-4 animate-spin" />
                : <Send className="w-4 h-4" />
              }
            </button>
          </div>
        </form>
      )}

      {/* ── Fil de commentaires ──────────────────────── */}
      {comments.length === 0 ? (
        <div className="text-center py-8 text-gray-400">
          <MessageCircle className="w-10 h-10 mx-auto mb-2 opacity-40" />
          <p className="text-sm">Aucun commentaire</p>
        </div>
      ) : (
        <div className="space-y-3">
          {comments.map(c => {
            const cfg  = TYPE_CONFIG[c.comment_type];
            const Icon = cfg.icon;
            return (
              <div key={c.id} className={clsx("rounded-xl p-4 border", cfg.bg, cfg.border)}>
                <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-full bg-brand flex items-center justify-center text-white text-xs font-bold">
                      {c.author_name.charAt(0)}
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-800">{c.author_name}</span>
                      {c.author_role && (
                        <span className="ml-1.5 text-xs text-gray-500">({c.author_role})</span>
                      )}
                    </div>
                    <div className="flex items-center gap-1 text-xs text-gray-500">
                      <Icon className="w-3 h-3" />
                      {cfg.label}
                    </div>
                  </div>
                  <time className="text-xs text-gray-400">
                    {new Date(c.created_at).toLocaleString("fr-DZ", {
                      day: "2-digit", month: "short", year: "numeric",
                      hour: "2-digit", minute: "2-digit",
                    })}
                  </time>
                </div>
                <p className="text-sm text-gray-700 whitespace-pre-wrap">{c.content}</p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
