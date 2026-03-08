const API_BASE = "http://localhost:8000";

export interface SubmitVettingPayload {
  subject_name: string;
  subject_type: string;
  company_affiliation?: string | null;
  country?: string | null;
  city?: string | null;
  brief_bio?: string | null;
  referral_source?: string | null;
  engagement_type: string;
  vetting_level: string;
  requested_by: string;
}

export interface VettingStatusResponse {
  id: string;
  status: string;
  current_step?: string | null;
  result_json?: any | null;
  error?: string | null;
}

export interface HealthResponse {
  status: string;
  api_keys_configured: boolean;
  active_jobs: number;
  total_jobs: number;
}

export async function submitVetting(payload: SubmitVettingPayload): Promise<VettingStatusResponse> {
  const res = await fetch(`${API_BASE}/api/vettings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Submit failed: ${res.status}`);
  return res.json();
}

export async function pollVettingStatus(id: string): Promise<VettingStatusResponse> {
  const res = await fetch(`${API_BASE}/api/vettings/${id}`);
  if (!res.ok) throw new Error(`Poll failed: ${res.status}`);
  return res.json();
}

export async function checkHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/api/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}
