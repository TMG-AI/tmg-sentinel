import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type, x-supabase-client-platform, x-supabase-client-platform-version, x-supabase-client-runtime, x-supabase-client-runtime-version",
};

interface VettingPayload {
  subject_name: string;
  subject_type: string;
  company_affiliation?: string;
  country?: string;
  city?: string;
  brief_bio?: string;
  referral_source?: string;
  engagement_type: string;
  vetting_level: string;
  requested_by: string;
}

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const RESEND_API_KEY = Deno.env.get("RESEND_API_KEY");
    if (!RESEND_API_KEY) {
      throw new Error("RESEND_API_KEY is not configured");
    }

    const payload: VettingPayload = await req.json();

    // Validate required fields
    if (!payload.subject_name?.trim()) {
      return new Response(
        JSON.stringify({ error: "Subject name is required" }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const body = [
      `Subject Name: ${payload.subject_name}`,
      `Subject Type: ${payload.subject_type}`,
      `Company Affiliation: ${payload.company_affiliation || "N/A"}`,
      `Country: ${payload.country || "N/A"}`,
      `City: ${payload.city || "N/A"}`,
      `Brief Bio: ${payload.brief_bio || "N/A"}`,
      `Referral Source: ${payload.referral_source || "N/A"}`,
      `Engagement Type: ${payload.engagement_type}`,
      `Vetting Level: ${payload.vetting_level}`,
      `Requested By: ${payload.requested_by}`,
      ``,
      `Submitted at: ${new Date().toISOString()}`,
    ].join("\n");

    const htmlBody = body.split("\n").map((line) => `<p>${line || "&nbsp;"}</p>`).join("");

    const res = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${RESEND_API_KEY}`,
      },
      body: JSON.stringify({
        from: "TMG Sentinel <onboarding@resend.dev>",
        to: ["shannon@themessinagroup.com"],
        subject: `New Vetting Request: ${payload.subject_name}`,
        html: htmlBody,
        text: body,
      }),
    });

    const data = await res.json();

    if (!res.ok) {
      console.error("Resend error:", data);
      return new Response(
        JSON.stringify({ error: "Failed to send email", details: data }),
        { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    return new Response(
      JSON.stringify({ success: true, id: data.id }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  } catch (error) {
    console.error("Error:", error.message);
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }
});
