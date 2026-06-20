import { useState } from "react";
import {
  BarChart3, TrendingUp, Upload, FileText, Loader2, Search,
} from "lucide-react";
import { useForecast, useWhatIf, useAnalyzeDocument, useDocumentAnalyses } from "../api";
import type { ForecastData, WhatIfData, MedicalDocumentAnalysisResult } from "../types";

function formatCurrency(v: number) {
  return new Intl.NumberFormat("fr-DZ", { style: "decimal", maximumFractionDigits: 0 }).format(v);
}

export function PredictiveAnalyticsPage() {
  const [forecastTarget, setForecastTarget] = useState("budget");
  const [forecastMonths, setForecastMonths] = useState(6);
  const [forecastMethod, setForecastMethod] = useState("ensemble");
  const forecastMut = useForecast();
  const whatIfMut = useWhatIf();

  const [budgetChangePct, setBudgetChangePct] = useState(0);
  const [newHires, setNewHires] = useState(0);

  const [selFile, setSelFile] = useState<File | null>(null);
  const [docTitle, setDocTitle] = useState("");
  const [docCategory, setDocCategory] = useState("other");
  const analyzeMut = useAnalyzeDocument();
  const { data: docAnalyses } = useDocumentAnalyses();

  const [activeTab, setActiveTab] = useState<"forecast" | "whatif" | "documents">("forecast");

  const runForecast = () => {
    forecastMut.mutate({ target: forecastTarget, months: forecastMonths, method: forecastMethod });
  };

  const runWhatIf = () => {
    whatIfMut.mutate({ budget_change_pct: budgetChangePct, new_hires: newHires });
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) setSelFile(e.target.files[0]);
  };

  const handleAnalyze = () => {
    if (!selFile) return;
    const fd = new FormData();
    fd.append("file", selFile);
    if (docTitle) fd.append("title", docTitle);
    if (docCategory) fd.append("category", docCategory);
    analyzeMut.mutate(fd);
  };

  const forecast = forecastMut.data as ForecastData | undefined;
  const whatIfResult = whatIfMut.data as WhatIfData | undefined;
  const lastDoc = analyzeMut.data as MedicalDocumentAnalysisResult | undefined;

  const tabClass = (tab: string) =>
    `px-4 py-2.5 rounded-xl text-sm font-semibold transition-all ${
      activeTab === tab
        ? "bg-brand text-[#1a1917]"
        : "text-gray-500 hover:text-gray-700 hover:bg-gray-100"
    }`;

  return (
    <div className="animate-fade-in space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-2">
        <div className="p-2.5 rounded-xl bg-brand/10">
          <BarChart3 className="w-6 h-6 text-brand" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytiques Prédictives</h1>
          <p className="text-sm text-gray-500">Prévisions budgétaires, simulations & analyse de documents</p>
        </div>
      </div>

      {/* Tab bar */}
      <div className="flex gap-2 flex-wrap">
        <button onClick={() => setActiveTab("forecast")} className={tabClass("forecast")}>
          <TrendingUp className="w-4 h-4 inline mr-1.5" />Prévisions
        </button>
        <button onClick={() => setActiveTab("whatif")} className={tabClass("whatif")}>
          <Search className="w-4 h-4 inline mr-1.5" />Scénarios
        </button>
        <button onClick={() => setActiveTab("documents")} className={tabClass("documents")}>
          <FileText className="w-4 h-4 inline mr-1.5" />Analyse de documents
        </button>
      </div>

      {activeTab === "forecast" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Controls */}
          <div className="card space-y-4">
            <h2 className="font-bold text-gray-800">Paramètres</h2>
            <div>
              <label className="block text-xs font-semibold text-gray-500 mb-1">Cible</label>
              <select
                value={forecastTarget}
                onChange={e => setForecastTarget(e.target.value)}
                className="w-full text-sm rounded-xl border border-gray-200 px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="budget">Budget</option>
                <option value="benefits">Prestations</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-500 mb-1">Horizon (mois)</label>
              <input
                type="number" min={1} max={24}
                value={forecastMonths}
                onChange={e => setForecastMonths(Number(e.target.value))}
                className="w-full text-sm rounded-xl border border-gray-200 px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-500 mb-1">Méthode</label>
              <select
                value={forecastMethod}
                onChange={e => setForecastMethod(e.target.value)}
                className="w-full text-sm rounded-xl border border-gray-200 px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="ensemble">Ensemble</option>
                <option value="linear">Régression linéaire</option>
                <option value="monte_carlo">Monte Carlo</option>
                <option value="seasonal">Saisonnier</option>
              </select>
            </div>
            <button
              onClick={runForecast}
              disabled={forecastMut.isPending}
              className="w-full px-4 py-2.5 rounded-xl bg-brand text-[#1a1917] font-bold text-sm hover:brightness-95 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
            >
              {forecastMut.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <TrendingUp className="w-4 h-4" />}
              Lancer la prévision
            </button>
          </div>

          {/* Results */}
          <div className="lg:col-span-2 card space-y-4">
            <h2 className="font-bold text-gray-800">Résultats</h2>
            {!forecast && !forecastMut.isPending && (
              <p className="text-sm text-gray-400">Configurez les paramètres et lancez une prévision.</p>
            )}
            {forecastMut.isPending && (
              <div className="flex items-center gap-3 text-sm text-gray-500">
                <Loader2 className="w-5 h-5 animate-spin" />
                Calcul en cours...
              </div>
            )}
            {forecast && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="bg-gray-50 rounded-xl p-3">
                    <p className="text-xs text-gray-500 font-semibold">Exercice</p>
                    <p className="text-lg font-bold text-gray-900">{forecast.fiscal_year}</p>
                  </div>
                  <div className="bg-gray-50 rounded-xl p-3">
                    <p className="text-xs text-gray-500 font-semibold">Budget total</p>
                    <p className="text-lg font-bold text-gray-900">{formatCurrency(forecast.total_budget)} DA</p>
                  </div>
                  <div className="bg-gray-50 rounded-xl p-3">
                    <p className="text-xs text-gray-500 font-semibold">Méthode</p>
                    <p className="text-lg font-bold text-gray-900 capitalize">{forecast.method}</p>
                  </div>
                  <div className="bg-gray-50 rounded-xl p-3">
                    <p className="text-xs text-gray-500 font-semibold">Historique</p>
                    <p className="text-lg font-bold text-gray-900">{forecast.historical_months} mois</p>
                  </div>
                </div>

                {Object.entries(forecast.forecasts || {}).map(([method, f]) => (
                  <div key={method} className="bg-gray-50 rounded-xl p-4">
                    <h3 className="text-sm font-bold text-gray-700 capitalize mb-3">
                      {method === "linear_regression" ? "Régression linéaire" : method}
                      {f.r_squared != null && (
                        <span className="ml-2 text-xs font-normal text-gray-400">
                          R² = {f.r_squared}
                        </span>
                      )}
                    </h3>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="text-xs text-gray-500 font-semibold">
                            <th className="text-left py-1">Mois</th>
                            <th className="text-right py-1">Prévision (DA)</th>
                            {f.forecasts?.[0]?.n_models != null && (
                              <th className="text-right py-1">Modèles</th>
                            )}
                          </tr>
                        </thead>
                        <tbody>
                          {(f.forecasts || []).map((fc) => (
                            <tr key={fc.step} className="border-t border-gray-200/50">
                              <td className="py-1.5 font-medium text-gray-700">M+{fc.step}</td>
                              <td className="py-1.5 text-right font-bold text-gray-900">
                                {formatCurrency(fc.value)} DA
                              </td>
                              {fc.n_models != null && (
                                <td className="py-1.5 text-right text-gray-500">{fc.n_models}</td>
                              )}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === "whatif" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="card space-y-4">
            <h2 className="font-bold text-gray-800">Scénario What-If</h2>
            <div>
              <label className="block text-xs font-semibold text-gray-500 mb-1">
                Changement budgétaire (%)
              </label>
              <input
                type="number" value={budgetChangePct}
                onChange={e => setBudgetChangePct(Number(e.target.value))}
                className="w-full text-sm rounded-xl border border-gray-200 px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-500 mb-1">
                Nouveaux employés
              </label>
              <input
                type="number" min={0} value={newHires}
                onChange={e => setNewHires(Number(e.target.value))}
                className="w-full text-sm rounded-xl border border-gray-200 px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <button
              onClick={runWhatIf}
              disabled={whatIfMut.isPending}
              className="w-full px-4 py-2.5 rounded-xl bg-brand text-[#1a1917] font-bold text-sm hover:brightness-95 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
            >
              {whatIfMut.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
              Simuler
            </button>
          </div>

          <div className="lg:col-span-2 card space-y-4">
            <h2 className="font-bold text-gray-800">Impact simulé</h2>
            {!whatIfResult && !whatIfMut.isPending && (
              <p className="text-sm text-gray-400">Définissez un scénario et simulez son impact.</p>
            )}
            {whatIfResult && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-gray-50 rounded-xl p-3">
                    <p className="text-xs text-gray-500 font-semibold">Variation budget</p>
                    <p className="text-lg font-bold text-gray-900">{whatIfResult.impact.budget_change}</p>
                  </div>
                  <div className="bg-gray-50 rounded-xl p-3">
                    <p className="text-xs text-gray-500 font-semibold">Coût annuel nouveaux employés</p>
                    <p className="text-lg font-bold text-gray-900">{formatCurrency(whatIfResult.impact.new_annual_cost)} DA</p>
                  </div>
                </div>
                <div className="bg-gray-50 rounded-xl p-4">
                  <h3 className="text-sm font-bold text-gray-700 mb-3">Comparaison mois par mois</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-xs text-gray-500 font-semibold">
                          <th className="text-left py-1">Mois</th>
                          <th className="text-right py-1">Base (DA)</th>
                          <th className="text-right py-1">Ajusté (DA)</th>
                          <th className="text-right py-1">Écart</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(whatIfResult.adjusted_forecasts || []).map((fc) => (
                          <tr key={fc.step} className="border-t border-gray-200/50">
                            <td className="py-1.5 font-medium text-gray-700">M+{fc.step}</td>
                            <td className="py-1.5 text-right text-gray-600">{formatCurrency(fc.base)}</td>
                            <td className="py-1.5 text-right font-bold text-gray-900">{formatCurrency(fc.adjusted)}</td>
                            <td className="py-1.5 text-right font-semibold" style={{ color: fc.adjusted >= fc.base ? "#22c55e" : "#ef4444" }}>
                              {fc.adjusted >= fc.base ? "+" : ""}{formatCurrency(fc.adjusted - fc.base)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === "documents" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Upload */}
          <div className="card space-y-4">
            <h2 className="font-bold text-gray-800">Analyser un document</h2>
            <div>
              <label className="block text-xs font-semibold text-gray-500 mb-1">Fichier</label>
              <input
                type="file"
                onChange={handleFileChange}
                accept=".pdf,.png,.jpg,.jpeg,.tiff,.bmp,.txt"
                className="w-full text-sm file:mr-3 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-brand/10 file:text-brand hover:file:bg-brand/20"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-500 mb-1">Titre (optionnel)</label>
              <input
                type="text" value={docTitle}
                onChange={e => setDocTitle(e.target.value)}
                placeholder="Ex: Ordonnance Dr. Benali"
                className="w-full text-sm rounded-xl border border-gray-200 px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-500 mb-1">Catégorie</label>
              <select
                value={docCategory}
                onChange={e => setDocCategory(e.target.value)}
                className="w-full text-sm rounded-xl border border-gray-200 px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="other">Automatique</option>
                <option value="prescription">Ordonnance</option>
                <option value="report">Rapport médical</option>
                <option value="imaging">Imagerie</option>
                <option value="lab_result">Résultat d'analyse</option>
                <option value="invoice">Facture</option>
                <option value="id_document">Pièce d'identité</option>
              </select>
            </div>
            <button
              onClick={handleAnalyze}
              disabled={!selFile || analyzeMut.isPending}
              className="w-full px-4 py-2.5 rounded-xl bg-brand text-[#1a1917] font-bold text-sm hover:brightness-95 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
            >
              {analyzeMut.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
              Analyser
            </button>
          </div>

          {/* Results */}
          <div className="lg:col-span-2 space-y-4">
            {lastDoc && (
              <div className="card space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="font-bold text-gray-800">
                    {lastDoc.title || lastDoc.file_name}
                  </h2>
                  <span className={`text-xs font-semibold px-2 py-1 rounded-lg ${
                    lastDoc.status === "completed" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                  }`}>
                    {lastDoc.status === "completed" ? "✅ Terminé" : "❌ Échec"}
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="bg-gray-50 rounded-xl p-3">
                    <p className="text-xs text-gray-500 font-semibold">Type</p>
                    <p className="text-sm font-bold text-gray-900">{lastDoc.file_type}</p>
                  </div>
                  <div className="bg-gray-50 rounded-xl p-3">
                    <p className="text-xs text-gray-500 font-semibold">Catégorie</p>
                    <p className="text-sm font-bold text-gray-900">{lastDoc.category_display}</p>
                  </div>
                  <div className="bg-gray-50 rounded-xl p-3">
                    <p className="text-xs text-gray-500 font-semibold">Pages</p>
                    <p className="text-sm font-bold text-gray-900">{lastDoc.page_count ?? "N/A"}</p>
                  </div>
                  <div className="bg-gray-50 rounded-xl p-3">
                    <p className="text-xs text-gray-500 font-semibold">Durée analyse</p>
                    <p className="text-sm font-bold text-gray-900">{lastDoc.analysis_duration_ms} ms</p>
                  </div>
                </div>

                <div className="bg-gray-50 rounded-xl p-4">
                  <h3 className="text-sm font-bold text-gray-700 mb-2">Résumé</h3>
                  <p className="text-sm text-gray-600">{lastDoc.summary || "Aucun résumé disponible."}</p>
                </div>

                {lastDoc.medical_keywords.length > 0 && (
                  <div>
                    <h3 className="text-sm font-bold text-gray-700 mb-2">Mots-clés médicaux</h3>
                    <div className="flex flex-wrap gap-1.5">
                      {lastDoc.medical_keywords.map(kw => (
                        <span key={kw} className="text-xs px-2 py-1 rounded-lg bg-blue-50 text-blue-700 font-medium">
                          {kw}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {lastDoc.diagnosis_mentions.length > 0 && (
                  <div>
                    <h3 className="text-sm font-bold text-gray-700 mb-2">Diagnostics détectés</h3>
                    <div className="flex flex-wrap gap-1.5">
                      {lastDoc.diagnosis_mentions.map(d => (
                        <span key={d} className="text-xs px-2 py-1 rounded-lg bg-amber-50 text-amber-700 font-medium">
                          {d}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {lastDoc.medication_mentions.length > 0 && (
                  <div>
                    <h3 className="text-sm font-bold text-gray-700 mb-2">Médicaments</h3>
                    <div className="flex flex-wrap gap-1.5">
                      {lastDoc.medication_mentions.map(m => (
                        <span key={m} className="text-xs px-2 py-1 rounded-lg bg-purple-50 text-purple-700 font-medium">
                          {m}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* History */}
            {docAnalyses && docAnalyses.length > 0 && (
              <div className="card space-y-3">
                <h2 className="font-bold text-gray-800">Analyses récentes</h2>
                <div className="divide-y divide-gray-100">
                  {docAnalyses.slice(0, 5).map((d) => (
                    <div key={d.id} className="py-3 flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <FileText className="w-4 h-4 text-gray-400" />
                        <div>
                          <p className="text-sm font-medium text-gray-700">{d.title || d.file_name}</p>
                          <p className="text-xs text-gray-400">
                            {d.category_display} &middot; {d.time_ago}
                          </p>
                        </div>
                      </div>
                      <span className={`text-xs font-semibold ${
                        d.status === "completed" ? "text-green-600" : "text-red-400"
                      }`}>
                        {d.status === "completed" ? "Terminé" : "Échec"}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
