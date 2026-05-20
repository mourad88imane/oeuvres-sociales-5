import { useToast } from "@shared/components/ui/index";
import { useNotificationPreferences, useUpdatePreferences } from "../api/index";

const DIGEST_OPTIONS = [
  { value: "instant", label: "Instantané" },
  { value: "daily", label: "Quotidien" },
  { value: "weekly", label: "Hebdomadaire" },
] as const;

export function NotificationPreferencesPage() {
  const { data: prefs, isLoading } = useNotificationPreferences();
  const update = useUpdatePreferences();
  const { success } = useToast();

  if (isLoading) return <div className="p-6 text-gray-500">Chargement…</div>;
  if (!prefs) return <div className="p-6 text-gray-500">Impossible de charger les préférences.</div>;

  const toggle = (field: "email_alerts" | "sms_alerts" | "push_alerts") => {
    update.mutate(
      { [field]: !prefs[field] },
      { onSuccess: () => success("Préférence mise à jour") },
    );
  };

  const changeDigest = (digest_frequency: "instant" | "daily" | "weekly") => {
    update.mutate(
      { digest_frequency },
      { onSuccess: () => success("Fréquence de digest mise à jour") },
    );
  };

  return (
    <div className="max-w-lg mx-auto py-8 px-4">
      <h1 className="text-xl font-bold text-gray-900 mb-6">Préférences de notifications</h1>

      {/* Canaux */}
      <section className="space-y-4 mb-8">
        <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wider">Canaux</h2>
        {(["email_alerts", "sms_alerts", "push_alerts"] as const).map(ch => (
          <label key={ch} className="flex items-center justify-between py-3 px-4 bg-white rounded-xl border border-gray-200 hover:border-gray-300 cursor-pointer transition-colors">
            <span className="text-sm font-medium text-gray-800">
              {ch === "email_alerts" ? "Notifications par email" :
               ch === "sms_alerts" ? "Notifications par SMS" : "Notifications push"}
            </span>
            <input type="checkbox" checked={prefs[ch]} onChange={() => toggle(ch)}
              className="w-5 h-5 rounded border-gray-300 text-brand focus:ring-brand cursor-pointer" />
          </label>
        ))}
      </section>

      {/* Digest */}
      <section className="space-y-3 mb-8">
        <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wider">Fréquence de digest</h2>
        <div className="grid grid-cols-3 gap-2">
          {DIGEST_OPTIONS.map(opt => (
            <button key={opt.value} onClick={() => changeDigest(opt.value)}
              className={`py-2.5 px-3 text-sm font-medium rounded-lg border transition-colors ${
                prefs.digest_frequency === opt.value
                  ? "bg-brand text-white border-brand"
                  : "bg-white text-gray-700 border-gray-300 hover:border-gray-400"
              }`}>
              {opt.label}
            </button>
          ))}
        </div>
      </section>

      {/* Horaires silencieux */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wider">Horaires silencieux</h2>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Début</label>
            <input type="time" value={prefs.quiet_hours_start ?? ""}
              onChange={e => update.mutate({ quiet_hours_start: e.target.value || null })}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500" />
          </div>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Fin</label>
            <input type="time" value={prefs.quiet_hours_end ?? ""}
              onChange={e => update.mutate({ quiet_hours_end: e.target.value || null })}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500" />
          </div>
        </div>
      </section>
    </div>
  );
}
