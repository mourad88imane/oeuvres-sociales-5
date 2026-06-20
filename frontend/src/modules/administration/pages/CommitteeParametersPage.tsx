import { useEffect, useState } from "react";
import { Card, InputNumber, Button, message, Spin } from "antd";
import { Users, Save } from "lucide-react";
import { fetchSystemParameterByKey, updateSystemParameterByKey } from "../api";

const COMMITTEE_KEYS = [
  {
    key: "coverage_restriction_period_months",
    label: "Période de restriction (mois)",
    description: "Nombre de mois sans demande pour déclencher l'auto-validation",
    suffix: " mois",
    min: 1,
    max: 24,
  },
  {
    key: "coverage_approval_requires_committee",
    label: "Validation par commission requise",
    description: "Activer la validation par commission pour les demandes de couverture",
    isBoolean: true,
  },
  {
    key: "director_escalation_threshold_amount",
    label: "Seuil d'escalade au directeur (DZD)",
    description: "Montant au-dessus duquel la demande est automatiquement transmise au directeur",
    suffix: " DZD",
    min: 10000,
    max: 10000000,
    step: 10000,
  },
  {
    key: "max_annual_coverage_requests",
    label: "Nombre max de demandes par an",
    description: "Nombre maximum de demandes de couverture par employé par année",
    suffix: " demandes",
    min: 1,
    max: 20,
  },
];

export function CommitteeParametersPage() {
  const [values, setValues] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);

  useEffect(() => {
    Promise.all(COMMITTEE_KEYS.map((c) =>
      fetchSystemParameterByKey(c.key).then((r) => ({ key: c.key, value: r?.value }))
    )).then((results) => {
      const map: Record<string, any> = {};
      results.forEach((r) => { map[r.key] = r.value; });
      setValues(map);
      setLoading(false);
    });
  }, []);

  const handleSave = async (key: string) => {
    setSaving(key);
    try {
      await updateSystemParameterByKey(key, { value: String(values[key]) });
      message.success(`${key} mis à jour`);
    } catch {
      message.error("Erreur");
    }
    setSaving(null);
  };

  if (loading) return <Spin className="flex justify-center mt-20" />;

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-2xl bg-[#ffda2d] flex items-center justify-center">
          <Users className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-xl font-bold">Paramètres de la Commission</h1>
          <p className="text-sm text-gray-500">Règles configurables pour les approbations</p>
        </div>
      </div>
      <div className="grid gap-4">
        {COMMITTEE_KEYS.map((c) => (
          <Card key={c.key} size="small">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <p className="font-medium">{c.label}</p>
                <p className="text-xs text-gray-400">{c.description}</p>
              </div>
              <div className="flex items-center gap-3">
                {c.isBoolean ? (
                  <select value={values[c.key] === "true" ? "true" : "false"}
                    onChange={(e) => setValues({ ...values, [c.key]: e.target.value })}
                    className="border rounded-lg px-3 py-1.5 text-sm">
                    <option value="true">Oui</option>
                    <option value="false">Non</option>
                  </select>
                ) : (
                  <InputNumber value={Number(values[c.key]) || 0}
                    onChange={(v) => setValues({ ...values, [c.key]: v })}
                    min={c.min} max={c.max} step={c.step ?? 1}
                    style={{ width: 160 }}
                    addonAfter={c.suffix} />
                )}
                <Button type="primary" size="small" loading={saving === c.key}
                  icon={<Save className="w-3 h-3" />}
                  onClick={() => handleSave(c.key)}
                  style={{ background: "#ffda2d", borderColor: "#ffda2d", color: "#1a1917" }}>
                  Enregistrer
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
