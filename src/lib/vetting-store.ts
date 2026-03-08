import { create } from "zustand";
import { VettingRequest, Decision, VettingResultJSON } from "./types";

interface VettingStore {
  vettings: VettingRequest[];
  loading: boolean;
  loaded: boolean;
  loadVettings: () => Promise<void>;
  makeDecision: (id: string, decision: Decision, decided_by: string, notes: string) => void;
  reopenVetting: (id: string, performed_by: string) => void;
  uploadResults: (id: string, result: VettingResultJSON) => void;
}

function resultToVettingRequest(result: VettingResultJSON, filename: string): VettingRequest {
  const id = filename.replace(".json", "");
  return {
    id,
    subject_name: result.subject.name,
    subject_type: (result.subject.type as "individual" | "organization") || "individual",
    company_affiliation: result.subject.company || null,
    country: result.subject.country || null,
    city: result.subject.city || null,
    brief_bio: null,
    referral_source: null,
    engagement_type: (result.metadata?.vetting_level?.includes("fara") ? "fara_foreign_political" : "domestic_political") as any,
    vetting_level: (result.metadata?.vetting_level as any) || "standard_vet",
    requested_by: "Pipeline",
    requested_at: result.metadata?.started_at || new Date().toISOString(),
    status: result.gates.sanctions.status === "FAIL" || result.gates.debarment.status === "FAIL" ? "gates_failed" : "completed",
    pipeline_progress: null,
    result_json: result,
    composite_score: result.scoring.final_composite,
    risk_tier: result.scoring.risk_tier,
    recommendation: result.scoring.recommendation,
    confidence: "HIGH",
    decision: null,
    decided_by: null,
    decided_at: null,
    decision_notes: null,
    completed_at: result.metadata?.completed_at || new Date().toISOString(),
    flags: result.flags,
  };
}

export const useVettingStore = create<VettingStore>((set, get) => ({
  vettings: [],
  loading: false,
  loaded: false,
  loadVettings: async () => {
    if (get().loaded || get().loading) return;
    set({ loading: true });
    try {
      const indexRes = await fetch("/data/vettings-index.json");
      if (!indexRes.ok) {
        set({ loading: false, loaded: true });
        return;
      }
      const index: { files: string[] } = await indexRes.json();
      const results = await Promise.all(
        index.files.map(async (file) => {
          try {
            const res = await fetch(`/data/vettings/${file}`);
            if (!res.ok) return null;
            const result: VettingResultJSON = await res.json();
            return resultToVettingRequest(result, file);
          } catch {
            return null;
          }
        })
      );
      set({ vettings: results.filter(Boolean) as VettingRequest[], loading: false, loaded: true });
    } catch {
      set({ loading: false, loaded: true });
    }
  },
  makeDecision: (id, decision, decided_by, notes) => {
    set((s) => ({
      vettings: s.vettings.map((v) =>
        v.id === id ? { ...v, decision, decided_by, decided_at: new Date().toISOString(), decision_notes: notes } : v
      ),
    }));
  },
  reopenVetting: (id, _performed_by) => {
    set((s) => ({
      vettings: s.vettings.map((v) =>
        v.id === id ? { ...v, decision: null, decided_by: null, decided_at: null, decision_notes: null } : v
      ),
    }));
  },
  uploadResults: (id, result) => {
    set((s) => ({
      vettings: s.vettings.map((v) =>
        v.id === id
          ? {
              ...v,
              status: result.gates.sanctions.status === "FAIL" || result.gates.debarment.status === "FAIL" ? "gates_failed" : "completed",
              result_json: result,
              composite_score: result.scoring.final_composite,
              risk_tier: result.scoring.risk_tier,
              recommendation: result.scoring.recommendation,
              confidence: "HIGH",
              completed_at: new Date().toISOString(),
              flags: result.flags,
              pipeline_progress: null,
            }
          : v
      ),
    }));
  },
}));
