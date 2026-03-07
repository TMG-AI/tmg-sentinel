import { create } from "zustand";
import { VettingRequest, Decision, VettingResultJSON } from "./types";
import { MOCK_VETTINGS } from "./mock-data";

interface VettingStore {
  vettings: VettingRequest[];
  addVetting: (v: Omit<VettingRequest, "id" | "requested_at" | "status" | "pipeline_progress" | "result_json" | "composite_score" | "risk_tier" | "recommendation" | "confidence" | "decision" | "decided_by" | "decided_at" | "decision_notes" | "completed_at" | "flags">) => string;
  makeDecision: (id: string, decision: Decision, decided_by: string, notes: string) => void;
  reopenVetting: (id: string, performed_by: string) => void;
  uploadResults: (id: string, result: VettingResultJSON) => void;
}

export const useVettingStore = create<VettingStore>((set, get) => ({
  vettings: MOCK_VETTINGS,
  addVetting: (v) => {
    const id = crypto.randomUUID();
    const newVetting: VettingRequest = {
      ...v,
      id,
      requested_at: new Date().toISOString(),
      status: "pending",
      pipeline_progress: null,
      result_json: null,
      composite_score: null,
      risk_tier: null,
      recommendation: null,
      confidence: null,
      decision: null,
      decided_by: null,
      decided_at: null,
      decision_notes: null,
      completed_at: null,
      flags: null,
    };
    set((s) => ({ vettings: [newVetting, ...s.vettings] }));
    return id;
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
