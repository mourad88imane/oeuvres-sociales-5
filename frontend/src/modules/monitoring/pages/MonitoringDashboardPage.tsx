import { useState } from "react";
import {
  Activity, AlertTriangle, Server, CheckCircle2, XCircle,
  TrendingUp, Users, Shield, ArrowUp, ArrowDown, BarChart3, Eye,
  Database, HardDrive,
} from "lucide-react";
import { clsx } from "clsx";
import { useDashboardStats, useApiLogs, useSecurityEvents, useEndpointStatus, useAuditStats, useSystemHealth } from "../api/index";
import { Spinner } from "@shared/components/ui/index";

type Tab = "overview" | "api" | "security" | "endpoints" | "audit" | "health";

const SEVERITY_COLORS: Record<string, string> = {
  LOW: "text-gray-600 bg-gray-100",
  MEDIUM: "text-yellow-600 bg-yellow-100",
  HIGH: "text-orange-600 bg-orange-100",
  CRITICAL: "text-red-600 bg-red-100",
};

function StatCard({ icon: Icon, label, value, sub, trend }: {
  icon: React.ElementType; label: string; value: string | number;
  sub?: string; trend?: "up" | "down" | "neutral";
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 flex items-start gap-4">
      <div className="p-2.5 rounded-lg bg-brand/10 text-brand shrink-0">
        <Icon className="w-5 h-5" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">{label}</p>
        <p className="text-xl font-bold text-gray-900 mt-0.5">{value}</p>
        {sub && <p className="text-xs text-gray-500 mt-0.5">{sub}</p>}
        {trend && (
          <div className="flex items-center gap-1 mt-1">
            {trend === "up" ? <ArrowUp className="w-3 h-3 text-green-500" /> :
             trend === "down" ? <ArrowDown className="w-3 h-3 text-red-500" /> :
             <BarChart3 className="w-3 h-3 text-gray-400" />}
          </div>
        )}
      </div>
    </div>
  );
}

export function MonitoringDashboardPage() {
  const [tab, setTab] = useState<Tab>("overview");

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Monitoring</h1>
          <p className="text-sm text-gray-500 mt-0.5">Supervision technique et sécurité</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-1 bg-gray-100 rounded-lg w-fit flex-wrap">
        {(["overview", "api", "security", "endpoints", "audit", "health"] as Tab[]).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={clsx("px-4 py-1.5 text-sm font-medium rounded-md transition-colors capitalize",
              tab === t ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"
            )}>
            {t === "overview" && "Vue d'ensemble"}
            {t === "api" && "Requêtes API"}
            {t === "security" && "Sécurité"}
            {t === "endpoints" && "Endpoints"}
            {t === "audit" && "Audit"}
            {t === "health" && "Santé"}
          </button>
        ))}
      </div>

      {tab === "overview" && <OverviewTab />}
      {tab === "api" && <APILogsTab />}
      {tab === "security" && <SecurityTab />}
      {tab === "endpoints" && <EndpointsTab />}
      {tab === "audit" && <AuditTab />}
      {tab === "health" && <HealthTab />}
    </div>
  );
}

function OverviewTab() {
  const { data: stats, isLoading } = useDashboardStats(24);

  if (isLoading) return <div className="py-12 text-center"><Spinner /></div>;
  if (!stats) return <div className="py-12 text-center text-gray-400 text-sm">Aucune donnée disponible</div>;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Activity} label="Requêtes (24h)" value={stats.total_calls} sub={`${stats.avg_duration_ms}ms en moyenne`} />
        <StatCard icon={XCircle} label="Erreurs" value={stats.errors} sub={`${stats.error_rate}% d'erreur`}
          trend={stats.error_rate > 5 ? "up" : stats.error_rate > 0 ? "down" : "neutral"} />
        <StatCard icon={Shield} label="Alertes sécurité" value={stats.security_alerts}
          trend={stats.security_alerts > 0 ? "up" : "neutral"} />
        <StatCard icon={Server} label="Endpoints dégradés" value={stats.degraded_endpoints}
          trend={stats.degraded_endpoints > 0 ? "up" : "neutral"} />
      </div>

      {/* Top endpoints */}
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">Top Endpoints</h3>
        <div className="space-y-2">
          {stats.top_endpoints.map((ep, i) => (
            <div key={i} className="flex items-center justify-between py-2 px-3 rounded-lg bg-gray-50">
              <div className="flex items-center gap-2 min-w-0">
                <span className={clsx("text-[10px] font-mono font-bold px-1.5 py-0.5 rounded",
                  ep.method === "GET" ? "text-green-600 bg-green-100" :
                  ep.method === "POST" ? "text-blue-600 bg-blue-100" :
                  ep.method === "PUT" ? "text-orange-600 bg-orange-100" :
                  ep.method === "DELETE" ? "text-red-600 bg-red-100" : "text-gray-600 bg-gray-200"
                )}>{ep.method}</span>
                <span className="text-sm text-gray-700 truncate">{ep.endpoint}</span>
              </div>
              <div className="flex items-center gap-4 text-xs text-gray-500 shrink-0">
                <span>{ep.count} appels</span>
                <span>{Math.round(ep.avg_dur)}ms</span>
                {ep.err_count > 0 && <span className="text-red-500">{ep.err_count} err.</span>}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Top users */}
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <Users className="w-4 h-4" /> Top Utilisateurs
        </h3>
        <div className="space-y-2">
          {stats.top_users.map((u, i) => (
            <div key={i} className="flex items-center justify-between py-1.5 px-3 rounded-lg bg-gray-50 text-sm">
              <span className="text-gray-700">{u.user__email}</span>
              <span className="text-gray-500 text-xs">{u.count} requêtes</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function APILogsTab() {
  const [showErrorsOnly, setShowErrorsOnly] = useState(false);
  const { data: logs, isLoading } = useApiLogs({ is_error: showErrorsOnly || undefined, limit: 100 });

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <input id="err-only" type="checkbox" checked={showErrorsOnly}
          onChange={e => setShowErrorsOnly(e.target.checked)}
          className="w-4 h-4 rounded border-gray-300 text-brand focus:ring-brand" />
        <label htmlFor="err-only" className="text-sm text-gray-600">Erreurs uniquement</label>
      </div>
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
              <tr>
                <th className="text-left px-4 py-2">Méthode</th>
                <th className="text-left px-4 py-2">Endpoint</th>
                <th className="text-center px-4 py-2">Status</th>
                <th className="text-right px-4 py-2">Durée</th>
                <th className="text-right px-4 py-2">Utilisateur</th>
                <th className="text-right px-4 py-2">Quand</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {isLoading ? (
                <tr><td colSpan={6} className="py-8 text-center"><Spinner size="sm" /></td></tr>
              ) : !logs?.length ? (
                <tr><td colSpan={6} className="py-8 text-center text-gray-400">Aucune requête</td></tr>
              ) : logs.map(log => (
                <tr key={log.id} className={clsx(log.is_error && "bg-red-50/50")}>
                  <td className="px-4 py-2">
                    <span className={clsx("text-xs font-mono font-bold px-1.5 py-0.5 rounded",
                      log.method === "GET" ? "text-green-600 bg-green-100" :
                      log.method === "POST" ? "text-blue-600 bg-blue-100" :
                      log.method === "PUT" ? "text-orange-600 bg-orange-100" :
                      "text-red-600 bg-red-100"
                    )}>{log.method}</span>
                  </td>
                  <td className="px-4 py-2 text-gray-700 font-mono text-xs truncate max-w-[300px]">{log.endpoint}</td>
                  <td className="px-4 py-2 text-center">
                    <span className={clsx(
                      log.status_code < 300 ? "text-green-600" :
                      log.status_code < 400 ? "text-yellow-600" : "text-red-600"
                    )}>{log.status_code}</span>
                  </td>
                  <td className="px-4 py-2 text-right text-gray-600">{log.duration_ms}ms</td>
                  <td className="px-4 py-2 text-right text-gray-500 text-xs">{log.user_email || "-"}</td>
                  <td className="px-4 py-2 text-right text-gray-400 text-xs">{log.time_ago}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function SecurityTab() {
  const [filter, setFilter] = useState<string>("");
  const { data: events, isLoading } = useSecurityEvents({ severity: filter || undefined });

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        {["", "INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"].map(s => (
          <button key={s} onClick={() => setFilter(s)}
            className={clsx("px-3 py-1 text-xs font-medium rounded-full border transition-colors",
              filter === s ? "bg-brand text-white border-brand" : "bg-white text-gray-600 border-gray-300 hover:border-gray-400"
            )}>{s || "Tous"}</button>
        ))}
      </div>
      <div className="space-y-2">
        {isLoading ? <div className="py-8 text-center"><Spinner /></div> :
         !events?.length ? <div className="py-8 text-center text-gray-400 text-sm">Aucun événement de sécurité</div> :
         events.map(ev => (
          <div key={ev.id} className={clsx("bg-white rounded-xl border p-4",
            ev.resolved ? "border-gray-200" : "border-red-200"
          )}>
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-start gap-3 min-w-0 flex-1">
                <div className={clsx("p-1.5 rounded-lg shrink-0", SEVERITY_COLORS[ev.severity] || "bg-gray-100 text-gray-500")}>
                  {ev.severity === "CRITICAL" || ev.severity === "HIGH" ? <AlertTriangle className="w-4 h-4" /> :
                   <Shield className="w-4 h-4" />}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-gray-900">{ev.event_type_display}</span>
                    <span className={clsx("text-[10px] font-medium px-1.5 py-0.5 rounded-full",
                      SEVERITY_COLORS[ev.severity] || "bg-gray-100 text-gray-500"
                    )}>{ev.severity}</span>
                    {ev.resolved && <span className="text-[10px] text-green-600 font-medium">✓ Résolu</span>}
                  </div>
                  {ev.user_email && <p className="text-xs text-gray-500 mt-0.5">{ev.user_email} · {ev.ip_address}</p>}
                  {ev.endpoint && <p className="text-xs text-gray-400 font-mono mt-0.5">{ev.endpoint}</p>}
                  {ev.details && Object.keys(ev.details).length > 0 && (
                    <pre className="text-xs text-gray-500 mt-1 bg-gray-50 p-2 rounded-lg overflow-x-auto">
                      {JSON.stringify(ev.details, null, 2)}
                    </pre>
                  )}
                  {ev.resolved && ev.resolution_note && (
                    <p className="text-xs text-gray-500 mt-1 italic">{ev.resolution_note}</p>
                  )}
                </div>
              </div>
              <div className="text-right shrink-0">
                <p className="text-[11px] text-gray-400">{ev.time_ago}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function EndpointsTab() {
  const { data: endpoints, isLoading } = useEndpointStatus();

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
            <tr>
              <th className="text-left px-4 py-2">Endpoint</th>
              <th className="text-center px-4 py-2">Appels</th>
              <th className="text-center px-4 py-2">Erreurs</th>
              <th className="text-center px-4 py-2">Taux err.</th>
              <th className="text-right px-4 py-2">Moy. durée</th>
              <th className="text-center px-4 py-2">État</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {isLoading ? (
              <tr><td colSpan={6} className="py-8 text-center"><Spinner size="sm" /></td></tr>
            ) : !endpoints?.length ? (
              <tr><td colSpan={6} className="py-8 text-center text-gray-400">Aucun endpoint</td></tr>
            ) : endpoints.map(ep => (
              <tr key={`${ep.method}-${ep.endpoint}`} className={clsx(ep.is_degraded && "bg-red-50/50")}>
                <td className="px-4 py-2 flex items-center gap-2">
                  <span className={clsx("text-xs font-mono font-bold px-1.5 py-0.5 rounded",
                    ep.method === "GET" ? "text-green-600 bg-green-100" :
                    ep.method === "POST" ? "text-blue-600 bg-blue-100" :
                    "text-orange-600 bg-orange-100"
                  )}>{ep.method}</span>
                  <span className="text-gray-700 font-mono text-xs">{ep.endpoint}</span>
                </td>
                <td className="px-4 py-2 text-center text-gray-700">{ep.total_calls}</td>
                <td className="px-4 py-2 text-center text-gray-700">{ep.error_count}</td>
                <td className="px-4 py-2 text-center">
                  <span className={clsx(ep.error_rate > 10 ? "text-red-600 font-medium" : "text-gray-600")}>
                    {ep.error_rate}%
                  </span>
                </td>
                <td className="px-4 py-2 text-right text-gray-600">{Math.round(ep.avg_duration_ms)}ms</td>
                <td className="px-4 py-2 text-center">
                  {ep.is_degraded ? (
                    <span className="inline-flex items-center gap-1 text-xs text-red-600">
                      <XCircle className="w-3 h-3" /> Dégradé
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-xs text-green-600">
                      <CheckCircle2 className="w-3 h-3" /> OK
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function HealthTab() {
  const { data: health, isLoading } = useSystemHealth();
  if (isLoading) return <div className="py-12 text-center"><Spinner /></div>;
  if (!health) return <div className="py-12 text-center text-gray-400 text-sm">Aucune donnée</div>;

  const checks = health.checks || {};
  const allHealthy = health.status === "ok";

  return (
    <div className="space-y-4">
      <div className={`rounded-xl p-4 flex items-center gap-3 ${allHealthy ? "bg-green-50" : "bg-red-50"}`}>
        {allHealthy ? <CheckCircle2 className="w-5 h-5 text-green-600" /> : <XCircle className="w-5 h-5 text-red-600" />}
        <span className={`font-bold ${allHealthy ? "text-green-700" : "text-red-700"}`}>
          Système {allHealthy ? "en santé" : "dégradé"}
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {checks.database && (
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="flex items-center gap-2 mb-3">
              <Database className="w-4 h-4 text-blue-500" />
              <h3 className="font-semibold text-gray-900">Base de données</h3>
              {checks.database.healthy ? <CheckCircle2 className="w-3.5 h-3.5 text-green-500 ml-auto" /> : <XCircle className="w-3.5 h-3.5 text-red-500 ml-auto" />}
            </div>
            {checks.database.healthy ? (
              <div className="space-y-1 text-sm">
                <p className="text-gray-600">Tables: <span className="font-semibold">{checks.database.table_count}</span></p>
                <p className="text-gray-600">Taille: <span className="font-semibold">{checks.database.size_mb} MB</span></p>
              </div>
            ) : (
              <p className="text-sm text-red-600">{checks.database.error}</p>
            )}
          </div>
        )}

        {checks.cache && (
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="flex items-center gap-2 mb-3">
              <HardDrive className="w-4 h-4 text-amber-500" />
              <h3 className="font-semibold text-gray-900">Cache</h3>
              {checks.cache.healthy ? <CheckCircle2 className="w-3.5 h-3.5 text-green-500 ml-auto" /> : <XCircle className="w-3.5 h-3.5 text-red-500 ml-auto" />}
            </div>
            <p className="text-sm text-gray-600">{checks.cache.healthy ? "Redis opérationnel" : "Cache indisponible"}</p>
          </div>
        )}

        {checks.celery && (
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="flex items-center gap-2 mb-3">
              <Activity className="w-4 h-4 text-purple-500" />
              <h3 className="font-semibold text-gray-900">Celery</h3>
              {checks.celery.healthy ? <CheckCircle2 className="w-3.5 h-3.5 text-green-500 ml-auto" /> : <XCircle className="w-3.5 h-3.5 text-red-500 ml-auto" />}
            </div>
            {checks.celery.healthy ? (
              <p className="text-sm text-gray-600">{checks.celery.workers?.length || 0} worker(s) actif(s)</p>
            ) : (
              <p className="text-sm text-red-600">Aucun worker détecté</p>
            )}
          </div>
        )}

        {checks.python && (
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="flex items-center gap-2 mb-3">
              <Server className="w-4 h-4 text-gray-500" />
              <h3 className="font-semibold text-gray-900">Environnement</h3>
            </div>
            <div className="space-y-1 text-sm">
              <p className="text-gray-600">Python: <span className="font-semibold">{checks.python.version || "—"}</span></p>
              <p className="text-gray-600">Django: <span className="font-semibold">{checks.python.django_version || "—"}</span></p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function AuditTab() {
  const { data: stats } = useAuditStats(30);
  const { data: logs } = useApiLogs({ limit: 50 });

  return (
    <div className="space-y-6">
      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard icon={Eye} label="Actions totales (30j)" value={stats.total} />
          <StatCard icon={TrendingUp} label={`${stats.by_action?.[0]?.action || ""}`}
            value={stats.by_action?.[0]?.count || 0} sub="Action la plus fréquente" />
          <StatCard icon={Users} label="Utilisateurs actifs" value={stats.top_users?.length || 0} />
          <StatCard icon={Shield} label="Critique"
            value={stats.by_severity?.find(s => s.severity === "CRITICAL")?.count || 0} />
        </div>
      )}

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <h3 className="text-sm font-semibold text-gray-900 px-4 py-3 border-b border-gray-100">
          Dernières actions auditées
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
              <tr>
                <th className="text-left px-4 py-2">Action</th>
                <th className="text-left px-4 py-2">Objet</th>
                <th className="text-left px-4 py-2">Utilisateur</th>
                <th className="text-right px-4 py-2">IP</th>
                <th className="text-right px-4 py-2">Quand</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {!logs?.length ? (
                <tr><td colSpan={5} className="py-8 text-center text-gray-400">Aucun log d'audit</td></tr>
              ) : logs.map((log: any) => (
                <tr key={log.id}>
                  <td className="px-4 py-2">
                    <span className={clsx("text-xs font-medium px-1.5 py-0.5 rounded",
                      log.action === "CREATE" ? "text-green-600 bg-green-100" :
                      log.action === "UPDATE" ? "text-blue-600 bg-blue-100" :
                      log.action === "DELETE" ? "text-red-600 bg-red-100" :
                      "text-gray-600 bg-gray-100"
                    )}>{log.action_display}</span>
                  </td>
                  <td className="px-4 py-2 text-gray-700 text-xs max-w-[200px] truncate">
                    {log.object_repr || `${log.content_type_name}#${log.object_id}`}
                  </td>
                  <td className="px-4 py-2 text-gray-600 text-xs">{log.user_email || "-"}</td>
                  <td className="px-4 py-2 text-right text-gray-400 text-xs font-mono">{log.ip_address || "-"}</td>
                  <td className="px-4 py-2 text-right text-gray-400 text-xs">{log.timestamp ? new Date(log.timestamp).toLocaleString() : "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
