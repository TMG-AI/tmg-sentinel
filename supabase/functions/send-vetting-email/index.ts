import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { SMTPClient } from "https://deno.land/x/denomailer@1.6.0/mod.ts";

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
    const GMAIL_ADDRESS = Deno.env.get("GMAIL_ADDRESS");
    const GMAIL_APP_PASSWORD = Deno.env.get("GMAIL_APP_PASSWORD");

    if (!GMAIL_ADDRESS || !GMAIL_APP_PASSWORD) {
      throw new Error("Gmail credentials are not configured");
    }

    const payload: VettingPayload = await req.json();

    if (!payload.subject_name?.trim()) {
      return new Response(
        JSON.stringify({ error: "Subject name is required" }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const bodyText = [
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

    const htmlBody = bodyText.split("\n").map((line) => `<p>${line || "&nbsp;"}</p>`).join("");

    const client = new SMTPClient({
      connection: {
        hostname: "smtp.gmail.com",
        port: 465,
        tls: true,
        auth: {
          username: GMAIL_ADDRESS,
          password: GMAIL_APP_PASSWORD,
        },
      },
    });

    await client.send({
      from: GMAIL_ADDRESS,
      to: "shannon@themessinagroup.com",
      subject: `New Vetting Request: ${payload.subject_name}`,
      content: bodyText,
      html: htmlBody,
    });

    await client.close();

    return new Response(
      JSON.stringify({ success: true }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  } catch (error: unknown) {
    const msg = error instanceof Error ? error.message : "Unknown error";
    console.error("Error:", msg);
    return new Response(
      JSON.stringify({ error: msg }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }
});
