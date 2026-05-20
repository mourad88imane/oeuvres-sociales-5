/**
 * PAGES D'ERREUR — 404 et 403
 */
import { useNavigate } from "react-router-dom";
import { Home, ArrowLeft, ShieldOff, SearchX } from "lucide-react";

export function NotFoundPage() {
  const navigate = useNavigate();
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6">
      <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mb-6">
        <SearchX className="w-10 h-10 text-gray-400" />
      </div>
      <h1 className="text-5xl font-bold text-gray-800 mb-2">404</h1>
      <h2 className="text-xl font-semibold text-gray-700 mb-3">Page introuvable</h2>
      <p className="text-gray-500 mb-8 max-w-sm">
        La page que vous cherchez n'existe pas ou a été déplacée.
      </p>
      <div className="flex gap-3">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg
            text-gray-700 hover:bg-gray-50 transition-colors text-sm"
        >
          <ArrowLeft className="w-4 h-4" />
          Retour
        </button>
        <button
          onClick={() => navigate("/dashboard")}
          className="flex items-center gap-2 px-4 py-2 bg-brand text-white rounded-lg
            hover:bg-brand-light transition-colors text-sm"
        >
          <Home className="w-4 h-4" />
          Tableau de bord
        </button>
      </div>
    </div>
  );
}

export function ForbiddenPage() {
  const navigate = useNavigate();
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6">
      <div className="w-20 h-20 bg-red-50 rounded-full flex items-center justify-center mb-6">
        <ShieldOff className="w-10 h-10 text-red-400" />
      </div>
      <h1 className="text-5xl font-bold text-gray-800 mb-2">403</h1>
      <h2 className="text-xl font-semibold text-gray-700 mb-3">Accès refusé</h2>
      <p className="text-gray-500 mb-8 max-w-sm">
        Vous n'avez pas les permissions nécessaires pour accéder à cette page.
        Contactez votre administrateur si vous pensez que c'est une erreur.
      </p>
      <button
        onClick={() => navigate("/dashboard")}
        className="flex items-center gap-2 px-4 py-2 bg-brand text-white rounded-lg
          hover:bg-brand-light transition-colors text-sm"
      >
        <Home className="w-4 h-4" />
        Retour au tableau de bord
      </button>
    </div>
  );
}
