/**
 * FINANCE UTILS — Formateurs et helpers
 */

/** Formate un montant en DZD */
export const fmtDZD = (amount: number | null | undefined, compact = false): string => {
  if (amount == null) return "—";
  if (compact && Math.abs(amount) >= 1_000_000) {
    return `${(amount / 1_000_000).toFixed(1)} MDZ`;
  }
  if (compact && Math.abs(amount) >= 1_000) {
    return `${(amount / 1_000).toFixed(0)} KDZ`;
  }
  return new Intl.NumberFormat("fr-DZ", {
    style: "currency", currency: "DZD", maximumFractionDigits: 0,
  }).format(amount);
};

/** Formate un pourcentage */
export const fmtPct = (value: number | null | undefined, decimals = 1): string => {
  if (value == null) return "—";
  return `${value.toFixed(decimals)} %`;
};

/** Couleur selon le taux de consommation */
export const consumptionColor = (rate: number): string => {
  if (rate >= 100) return "text-red-700";
  if (rate >= 85)  return "text-orange-600";
  if (rate >= 70)  return "text-amber-600";
  return "text-green-600";
};

/** Background selon le taux */
export const consumptionBg = (rate: number): string => {
  if (rate >= 100) return "bg-red-500";
  if (rate >= 85)  return "bg-orange-400";
  if (rate >= 70)  return "bg-amber-400";
  return "bg-green-500";
};

/** Barre de progression colorée */
export const progressBarClass = (rate: number): string => {
  if (rate >= 100) return "bg-red-500";
  if (rate >= 85)  return "bg-orange-400";
  if (rate >= 70)  return "bg-amber-400";
  return "bg-emerald-500";
};

/** Formate une date */
export const fmtDate = (d: string | null | undefined): string =>
  d ? new Date(d).toLocaleDateString("fr-DZ", { day:"2-digit", month:"short", year:"numeric" }) : "—";

export const fmtDateTime = (d: string | null | undefined): string =>
  d ? new Date(d).toLocaleString("fr-DZ", { day:"2-digit", month:"short", year:"numeric", hour:"2-digit", minute:"2-digit" }) : "—";

/** Génère les couleurs d'un graphique */
export const CHART_COLORS = [
  "#1A3C6E", "#2E75B6", "#10B981", "#F59E0B",
  "#EF4444", "#8B5CF6", "#06B6D4", "#F97316",
];
