/**
 * EMPLOYEE DETAIL PAGE — Fiche complète avec onglets
 * Identité | Ayants droit | Historique | Modifier
 */
import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft, Edit2, Trash2, User, Phone, Briefcase,
  Users, Clock, Shield, AlertTriangle, Camera,
  CheckCircle2, XCircle, Plus,
} from "lucide-react";
import {
  useEmployee, useUpdateEmployee, useDeleteEmployee,
  useCreateBeneficiary, useUpdateBeneficiary, useDeleteBeneficiary, useChangeStatus,
} from "../hooks/useEmployees";
import {
  EmployeeStatusBadge, Modal, ConfirmDialog,
  EmptyState, Spinner, Badge,
} from "@shared/components/ui/index";
import { EmployeeForm }    from "../components/EmployeeForm";
import { BeneficiaryForm } from "../components/BeneficiaryForm";
import { EmployeeHistory } from "../components/EmployeeHistory";
import { PhotoUpload }     from "../components/PhotoUpload";
import { RoleGuard }       from "@shared/components/layout/ProtectedRoute";
import type { Beneficiary, EmployeeUpdatePayload, BeneficiaryCreatePayload } from "../types";

type Tab = "identity" | "beneficiaries" | "history" | "security";

const TABS: { id: Tab; label: string; icon: React.ElementType }[] = [
  { id: "identity",      label: "Identité",    icon: User    },
  { id: "beneficiaries", label: "Ayants droit", icon: Users   },
  { id: "history",       label: "Historique",  icon: Clock   },
  { id: "security",      label: "Statut",      icon: Shield  },
];

export function EmployeeDetailPage() {
  const { id }  = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [activeTab,     setActiveTab]     = useState<Tab>("identity");
  const [showEdit,      setShowEdit]      = useState(false);
  const [showDelete,    setShowDelete]    = useState(false);
  const [showPhotoEdit, setShowPhotoEdit] = useState(false);
  const [showAddBene,   setShowAddBene]   = useState(false);
  const [editBene,      setEditBene]      = useState<Beneficiary | null>(null);
  const [deleteBene,    setDeleteBene]    = useState<string | null>(null);
  const [showStatus,    setShowStatus]    = useState(false);
  const [newStatus,     setNewStatus]     = useState("");
  const [statusReason,  setStatusReason]  = useState("");

  const { data: employee, isLoading } = useEmployee(id ?? null);
  const updateMutation  = useUpdateEmployee(id!);
  const deleteMutation  = useDeleteEmployee();
  const changeStatus    = useChangeStatus(id!);
  const createBene      = useCreateBeneficiary(id!);
  const updateBene      = useUpdateBeneficiary(id!);
  const deleteBeneM     = useDeleteBeneficiary(id!);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!employee) {
    return (
      <EmptyState icon={User} title="Employé introuvable"
        description="Cet employé n'existe pas ou a été supprimé."
        action={<button onClick={() => navigate("/employees")} className="btn-primary">Retour à la liste</button>}
      />
    );
  }

  const handleUpdate = async (data: EmployeeUpdatePayload) => {
    await updateMutation.mutateAsync(data);
    setShowEdit(false);
  };

  const handleDelete = async () => {
    await deleteMutation.mutateAsync(id!);
    navigate("/employees");
  };

  const handleChangeStatus = async () => {
    await changeStatus.mutateAsync({ status: newStatus, reason: statusReason });
    setShowStatus(false);
    setStatusReason("");
  };

  const handleAddBene = async (data: BeneficiaryCreatePayload) => {
    await createBene.mutateAsync(data);
    setShowAddBene(false);
  };

  const handleUpdateBene = async (data: Partial<BeneficiaryCreatePayload>) => {
    if (!editBene) return;
    await updateBene.mutateAsync({ id: editBene.id, data });
    setEditBene(null);
  };

  const handleDeleteBene = async () => {
    if (!deleteBene) return;
    await deleteBeneM.mutateAsync(deleteBene);
    setDeleteBene(null);
  };

  const cinExpired = employee.cin_expired;

  return (
    <div className="space-y-5 animate-fade-in">
      {/* ── En-tête ─────────────────────────────────── */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <button onClick={() => navigate("/employees")}
          className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors">
          <ArrowLeft className="w-4 h-4" />Retour
        </button>
        <div className="flex items-center gap-2">
          <RoleGuard roles={["admin", "gestionnaire"]}>
            <button onClick={() => setShowEdit(true)}
              className="flex items-center gap-2 px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50">
              <Edit2 className="w-4 h-4" />Modifier
            </button>
          </RoleGuard>
          <RoleGuard roles={["admin"]}>
            <button onClick={() => setShowDelete(true)}
              className="flex items-center gap-2 px-3 py-2 border border-red-200 rounded-lg text-sm text-red-600 hover:bg-red-50">
              <Trash2 className="w-4 h-4" />Supprimer
            </button>
          </RoleGuard>
        </div>
      </div>

      {/* ── Carte profil ─────────────────────────────── */}
      <div className="card p-6">
        <div className="flex flex-col sm:flex-row gap-6">
          {/* Photo */}
          <div className="shrink-0">
            <RoleGuard roles={["admin", "gestionnaire"]}
              fallback={
                <div className="w-24 h-24 rounded-2xl overflow-hidden">
                  {employee.photo_url
                    ? <img src={employee.photo_url} alt={employee.full_name} className="w-full h-full object-cover" />
                    : <div className="w-24 h-24 rounded-2xl bg-brand flex items-center justify-center text-white text-3xl font-bold">
                        {employee.first_name[0]}{employee.last_name[0]}
                      </div>}
                </div>
              }
            >
              <div className="relative group cursor-pointer" onClick={() => setShowPhotoEdit(true)}>
                {employee.photo_url
                  ? <img src={employee.photo_url} alt={employee.full_name}
                      className="w-24 h-24 rounded-2xl object-cover" />
                  : <div className="w-24 h-24 rounded-2xl bg-brand flex items-center justify-center text-white text-3xl font-bold">
                      {employee.first_name[0]}{employee.last_name[0]}
                    </div>
                }
                <div className="absolute inset-0 bg-black/40 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                  <Camera className="w-6 h-6 text-white" />
                </div>
              </div>
            </RoleGuard>
          </div>

          {/* Infos principales */}
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-start gap-3 mb-2">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{employee.full_name}</h1>
                {employee.first_name_ar && (
                  <p className="text-lg text-gray-500 font-arabic" dir="rtl">
                    {employee.first_name_ar} {employee.last_name_ar}
                  </p>
                )}
              </div>
              <EmployeeStatusBadge status={employee.status} />
              {cinExpired && (
                <Badge variant="error">
                  <AlertTriangle className="w-3 h-3" />CIN expirée
                </Badge>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mt-4">
              <InfoChip label="Matricule" value={employee.matricule} mono />
              <InfoChip label="Poste" value={employee.job_title} />
              <InfoChip label="Département"
                value={`[${employee.department_info?.code}] ${employee.department_info?.name}`} />
              <InfoChip label="Contrat" value={employee.contract_display} />
              <InfoChip label="Grade" value={employee.grade || "—"} />
              <InfoChip label="Ancienneté" value={employee.seniority_label} />
              <InfoChip label="Âge" value={employee.age ? `${employee.age} ans` : "—"} />
              <InfoChip label="Ayants droit"
                value={`${employee.beneficiaries.length} personne${employee.beneficiaries.length > 1 ? "s" : ""}`} />
            </div>
          </div>
        </div>
      </div>

      {/* ── Onglets ──────────────────────────────────── */}
      <div className="flex gap-1 border-b border-gray-200 overflow-x-auto">
        {TABS.map(({ id: tabId, label, icon: Icon }) => (
          <button key={tabId} onClick={() => setActiveTab(tabId)}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-t-lg whitespace-nowrap transition-colors border-b-2 -mb-px
              ${activeTab === tabId ? "text-brand border-brand bg-blue-50" : "text-gray-500 border-transparent hover:text-gray-700"}`}>
            <Icon className="w-4 h-4" />{label}
            {tabId === "beneficiaries" && (
              <span className="ml-1 text-xs bg-gray-200 text-gray-600 px-1.5 py-0.5 rounded-full">
                {employee.beneficiaries.length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* ════════════════════════════════════════════════
          TAB : IDENTITÉ
      ════════════════════════════════════════════════ */}
      {activeTab === "identity" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* État civil */}
          <Section title="État civil" icon={User}>
            <InfoRow label="Nom complet"     value={employee.full_name} />
            <InfoRow label="Genre"           value={employee.gender_display} />
            <InfoRow label="Date naissance"  value={formatDate(employee.date_of_birth)} />
            <InfoRow label="Âge"             value={`${employee.age} ans`} />
            <InfoRow label="Lieu naissance"  value={employee.place_of_birth || "—"} />
            <InfoRow label="Situation fam."  value={employee.marital_display} />
            <InfoRow label="Nationalité"     value={employee.nationality} />
          </Section>

          {/* Contact */}
          <Section title="Coordonnées" icon={Phone}>
            <InfoRow label="Téléphone"       value={employee.phone || "—"} />
            <InfoRow label="Tél. secondaire" value={employee.phone_secondary || "—"} />
            <InfoRow label="Email pro."      value={employee.email_professional || "—"} />
            <InfoRow label="Email perso."    value={employee.email_personal || "—"} />
            <InfoRow label="Adresse"         value={employee.address || "—"} />
            <InfoRow label="Ville / Wilaya"  value={`${employee.city || "—"} / ${employee.wilaya || "—"}`} />
          </Section>

          {/* Documents */}
          <Section title="Documents" icon={Shield}>
            <InfoRow label="NNI / CIN"    value={employee.national_id || "—"} mono />
            <InfoRow label="Expiration CIN"
              value={employee.national_id_expiry ? formatDate(employee.national_id_expiry) : "—"}
              badge={cinExpired ? <Badge variant="error">Expirée</Badge> : undefined}
            />
            <InfoRow label="N° Séc. Sociale" value={employee.social_security_number || "—"} mono />
            <InfoRow label="NIF"             value={employee.tax_id || "—"} mono />
          </Section>

          {/* Poste */}
          <Section title="Poste et carrière" icon={Briefcase}>
            <InfoRow label="Poste"           value={employee.job_title} />
            <InfoRow label="Grade"           value={employee.grade || "—"} />
            <InfoRow label="Niveau grade"    value={employee.grade_level?.toString() || "—"} />
            <InfoRow label="Catégorie CSP"   value={employee.category || "—"} />
            <InfoRow label="Type contrat"    value={employee.contract_display} />
            <InfoRow label="Date embauche"   value={formatDate(employee.date_hired)} />
            {employee.date_end && <InfoRow label="Fin contrat" value={formatDate(employee.date_end)} />}
            <InfoRow label="Ancienneté"      value={employee.seniority_label} />
            {employee.manager_name && <InfoRow label="Responsable" value={employee.manager_name} />}
          </Section>

          {/* Formation */}
          {(employee.education_level || employee.education_field || employee.competencies.length > 0) && (
            <Section title="Formation & Compétences" icon={Briefcase}>
              <InfoRow label="Niveau formation" value={employee.education_level || "—"} />
              <InfoRow label="Domaine"          value={employee.education_field || "—"} />
              {employee.competencies.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {employee.competencies.map((c) => (
                    <Badge key={c} variant="info">{c}</Badge>
                  ))}
                </div>
              )}
            </Section>
          )}

          {/* Notes */}
          {employee.notes && (
            <div className="card p-5">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Notes internes</h3>
              <p className="text-sm text-gray-600 whitespace-pre-wrap">{employee.notes}</p>
            </div>
          )}
        </div>
      )}

      {/* ════════════════════════════════════════════════
          TAB : AYANTS DROIT
      ════════════════════════════════════════════════ */}
      {activeTab === "beneficiaries" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">
              {employee.beneficiaries.length} ayant{employee.beneficiaries.length > 1 ? "s" : ""} droit
              {" — "}{employee.beneficiaries.filter((b) => b.is_eligible).length} éligible{employee.beneficiaries.filter((b) => b.is_eligible).length > 1 ? "s" : ""}
            </p>
            <RoleGuard roles={["admin", "gestionnaire"]}>
              <button onClick={() => setShowAddBene(true)}
                className="flex items-center gap-2 px-3 py-2 bg-brand text-white rounded-lg text-sm hover:bg-brand-light">
                <Plus className="w-4 h-4" />Ajouter
              </button>
            </RoleGuard>
          </div>

          {employee.beneficiaries.length === 0 ? (
            <EmptyState icon={Users} title="Aucun ayant droit"
              description="Ajoutez les personnes à charge de cet employé."
              action={
                <RoleGuard roles={["admin", "gestionnaire"]}>
                  <button onClick={() => setShowAddBene(true)} className="btn-primary">
                    <Plus className="w-4 h-4 inline mr-1" />Ajouter un ayant droit
                  </button>
                </RoleGuard>
              }
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {employee.beneficiaries.map((bene) => (
                <BeneficiaryCard key={bene.id} bene={bene}
                  onEdit={() => setEditBene(bene)}
                  onDelete={() => setDeleteBene(bene.id)}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* ════════════════════════════════════════════════
          TAB : HISTORIQUE
      ════════════════════════════════════════════════ */}
      {activeTab === "history" && (
        <div className="card p-5">
          <EmployeeHistory employeeId={id!} />
        </div>
      )}

      {/* ════════════════════════════════════════════════
          TAB : STATUT
      ════════════════════════════════════════════════ */}
      {activeTab === "security" && (
        <div className="space-y-4">
          <div className="card p-5">
            <h3 className="text-sm font-semibold text-gray-700 mb-4">Statut du dossier</h3>
            <div className="flex items-center gap-4 mb-6">
              <EmployeeStatusBadge status={employee.status} />
              <span className="text-sm text-gray-500">
                Depuis le {formatDate(employee.date_hired)}
              </span>
            </div>
            <RoleGuard roles={["admin", "gestionnaire"]}>
              <div className="space-y-3">
                <p className="text-sm font-medium text-gray-700">Changer le statut</p>
                <div className="flex gap-3 flex-wrap">
                  {[
                    { s: "active",    label: "Activer",   color: "bg-green-600 hover:bg-green-700 text-white" },
                    { s: "inactive",  label: "Désactiver",color: "bg-gray-600 hover:bg-gray-700 text-white"  },
                    { s: "suspended", label: "Suspendre", color: "bg-amber-500 hover:bg-amber-600 text-white"},
                    { s: "retired",   label: "Retraite",  color: "bg-blue-600 hover:bg-blue-700 text-white"  },
                  ].map(({ s, label, color }) => (
                    <button key={s} disabled={employee.status === s}
                      onClick={() => { setNewStatus(s); setShowStatus(true); }}
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${color}`}>
                      {label}
                    </button>
                  ))}
                </div>
              </div>
            </RoleGuard>
          </div>

          {/* Infos audit */}
          <div className="card p-5">
            <h3 className="text-sm font-semibold text-gray-700 mb-4">Informations d'audit</h3>
            <div className="space-y-2">
              <InfoRow label="Créé par"          value={employee.created_by_name || "Système"} />
              <InfoRow label="Date de création"  value={formatDateTime(employee.created_at)} />
              <InfoRow label="Dernière modif."   value={formatDateTime(employee.updated_at)} />
            </div>
          </div>
        </div>
      )}

      {/* ── Modals ───────────────────────────────────── */}
      {/* Edit */}
      <Modal open={showEdit} onClose={() => setShowEdit(false)} title="Modifier l'employé" size="xl">
        <EmployeeForm mode="edit" initialData={employee}
          onSubmit={handleUpdate} onCancel={() => setShowEdit(false)}
          isLoading={updateMutation.isPending} />
      </Modal>

      {/* Photo */}
      <Modal open={showPhotoEdit} onClose={() => setShowPhotoEdit(false)} title="Photo de profil" size="sm">
        <div className="flex justify-center py-4">
          <PhotoUpload employeeId={id!} currentPhotoUrl={employee.photo_url} employeeName={employee.full_name} />
        </div>
      </Modal>

      {/* Delete employee */}
      <ConfirmDialog open={showDelete} onClose={() => setShowDelete(false)}
        onConfirm={handleDelete} title="Supprimer l'employé"
        message={`Supprimer ${employee.full_name} ? Le dossier sera archivé. Cette action est irréversible.`}
        confirmLabel="Supprimer" loading={deleteMutation.isPending} />

      {/* Add beneficiary */}
      <Modal open={showAddBene} onClose={() => setShowAddBene(false)} title="Ajouter un ayant droit" size="lg">
        <BeneficiaryForm onSubmit={handleAddBene} onCancel={() => setShowAddBene(false)}
          isLoading={createBene.isPending} />
      </Modal>

      {/* Edit beneficiary */}
      <Modal open={!!editBene} onClose={() => setEditBene(null)} title="Modifier l'ayant droit" size="lg">
        {editBene && (
          <BeneficiaryForm initialData={editBene}
            onSubmit={handleUpdateBene} onCancel={() => setEditBene(null)}
            isLoading={updateBene.isPending} />
        )}
      </Modal>

      {/* Delete beneficiary */}
      <ConfirmDialog open={!!deleteBene} onClose={() => setDeleteBene(null)}
        onConfirm={handleDeleteBene} title="Supprimer l'ayant droit"
        message="Cet ayant droit sera retiré du dossier. Continuer ?"
        confirmLabel="Supprimer" loading={deleteBeneM.isPending} />

      {/* Change status */}
      <Modal open={showStatus} onClose={() => setShowStatus(false)} title="Changer le statut" size="sm"
        footer={
          <>
            <button onClick={() => setShowStatus(false)}
              className="px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">
              Annuler
            </button>
            <button onClick={handleChangeStatus} disabled={changeStatus.isPending}
              className="px-4 py-2 text-sm bg-brand text-white rounded-lg hover:bg-brand-light disabled:opacity-60">
              Confirmer
            </button>
          </>
        }>
        <div className="space-y-3">
          <p className="text-sm text-gray-600">
            Changer le statut de <strong>{employee.full_name}</strong> vers <strong>{newStatus}</strong>.
          </p>
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">Motif (optionnel)</label>
            <textarea value={statusReason} onChange={(e) => setStatusReason(e.target.value)}
              rows={3} placeholder="Précisez la raison de ce changement..."
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500" />
          </div>
        </div>
      </Modal>
    </div>
  );
}

// ── Composants utilitaires ─────────────────────────────────
function Section({ title, icon: Icon, children }: { title: string; icon: React.ElementType; children: React.ReactNode }) {
  return (
    <div className="card p-5">
      <div className="flex items-center gap-2 mb-4 pb-2 border-b border-gray-100">
        <Icon className="w-4 h-4 text-brand" />
        <h3 className="text-sm font-semibold text-gray-800">{title}</h3>
      </div>
      <div className="space-y-2">{children}</div>
    </div>
  );
}

function InfoRow({ label, value, mono, badge }: { label: string; value: string; mono?: boolean; badge?: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between py-1 border-b border-gray-50 last:border-0">
      <span className="text-xs text-gray-500 shrink-0 w-32">{label}</span>
      <div className="flex items-center gap-2">
        <span className={`text-sm text-gray-800 text-right ${mono ? "font-mono text-xs" : ""}`}>{value}</span>
        {badge}
      </div>
    </div>
  );
}

function InfoChip({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="bg-gray-50 rounded-lg px-3 py-2">
      <p className="text-xs text-gray-400 mb-0.5">{label}</p>
      <p className={`text-sm font-medium text-gray-800 ${mono ? "font-mono" : ""}`}>{value}</p>
    </div>
  );
}

function BeneficiaryCard({ bene, onEdit, onDelete }: { bene: Beneficiary; onEdit: () => void; onDelete: () => void }) {
  const RELATIONSHIP_COLORS: Record<string, string> = {
    spouse: "bg-purple-100 text-purple-700",
    child:  "bg-blue-100 text-blue-700",
    parent: "bg-orange-100 text-orange-700",
    sibling:"bg-teal-100 text-teal-700",
    other:  "bg-gray-100 text-gray-700",
  };

  return (
    <div className={`card p-4 border-l-4 ${bene.is_eligible ? "border-l-green-400" : "border-l-red-400"}`}>
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${RELATIONSHIP_COLORS[bene.relationship] ?? "bg-gray-100 text-gray-700"}`}>
              {bene.relationship_display}
            </span>
            {bene.is_eligible
              ? <CheckCircle2 className="w-4 h-4 text-green-500" title="Éligible" />
              : <XCircle     className="w-4 h-4 text-red-400"   title="Non éligible" />
            }
          </div>
          <p className="font-semibold text-gray-900">{bene.full_name}</p>
          <p className="text-xs text-gray-500">
            {bene.age != null ? `${bene.age} ans` : "Âge inconnu"}
            {bene.is_student && " · Étudiant(e)"}
            {bene.is_handicapped && " · Handicapé(e)"}
          </p>
        </div>
        <RoleGuard roles={["admin", "gestionnaire"]}>
          <div className="flex gap-1">
            <button onClick={onEdit}
              className="p-1.5 text-gray-400 hover:text-brand hover:bg-blue-50 rounded transition-colors">
              <Edit2 className="w-3.5 h-3.5" />
            </button>
            <button onClick={onDelete}
              className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors">
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        </RoleGuard>
      </div>

      {!bene.is_eligible && bene.ineligibility_reason && (
        <div className="flex items-start gap-1.5 text-xs text-red-600 bg-red-50 rounded-lg px-3 py-2 mt-2">
          <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
          {bene.ineligibility_reason}
        </div>
      )}

      {bene.school_name && (
        <p className="text-xs text-gray-500 mt-2">🎓 {bene.school_name} {bene.school_year && `(${bene.school_year})`}</p>
      )}
    </div>
  );
}

// ── Helpers ────────────────────────────────────────────────
const formatDate = (d: string) =>
  d ? new Date(d).toLocaleDateString("fr-DZ", { day: "2-digit", month: "long", year: "numeric" }) : "—";

const formatDateTime = (d: string) =>
  d ? new Date(d).toLocaleString("fr-DZ", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" }) : "—";
