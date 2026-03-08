import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { SubjectType, EngagementType, VettingLevel, TEAM_MEMBERS, ENGAGEMENT_LABELS, ENGAGEMENT_MULTIPLIERS, VETTING_LEVEL_LABELS } from "@/lib/types";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { useToast } from "@/hooks/use-toast";
import { Shield, Zap, Search, Microscope, Upload, AlertTriangle, Check } from "lucide-react";

export default function SubmitVetting() {
  const navigate = useNavigate();
  const { toast } = useToast();

  const [subjectName, setSubjectName] = useState("");
  const [subjectType, setSubjectType] = useState<SubjectType>("individual");
  const [companyAffiliation, setCompanyAffiliation] = useState("");
  const [country, setCountry] = useState("");
  const [city, setCity] = useState("");
  const [briefBio, setBriefBio] = useState("");
  const [referralSource, setReferralSource] = useState("");
  const [engagementType, setEngagementType] = useState<EngagementType>("domestic_political");
  const [vettingLevel, setVettingLevel] = useState<VettingLevel>("standard_vet");
  const [requestedBy, setRequestedBy] = useState("");
  const [otherName, setOtherName] = useState("");
  const [notify, setNotify] = useState<string[]>(["Tara"]);
  const [showConfirm, setShowConfirm] = useState(false);

  const canSubmit = subjectName.trim() && (requestedBy || otherName);

  const handleSubmit = () => {
    const by = requestedBy === "Other" ? otherName : requestedBy;
    setShowConfirm(false);

    const subject = `New Vetting Request: ${subjectName.trim()}`;
    const body = [
      `Subject Name: ${subjectName.trim()}`,
      `Subject Type: ${subjectType}`,
      `Company Affiliation: ${companyAffiliation || "N/A"}`,
      `Country: ${country || "N/A"}`,
      `City: ${city || "N/A"}`,
      `Brief Bio: ${briefBio || "N/A"}`,
      `Referral Source: ${referralSource || "N/A"}`,
      `Engagement Type: ${ENGAGEMENT_LABELS[engagementType]}`,
      `Vetting Level: ${VETTING_LEVEL_LABELS[vettingLevel].title}`,
      `Requested By: ${by}`,
    ].join("\n");

    window.location.href = `mailto:shannon@themessinagroup.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;

    toast({
      title: "Vetting request emailed to Shannon.",
      description: `Request for ${subjectName.trim()} has been prepared.`,
    });

    setTimeout(() => navigate("/"), 500);
  };

  const vettingLevelCards: { key: VettingLevel; icon: React.ReactNode; steps: string[] }[] = [
    {
      key: "quick_screen",
      icon: <Zap className="w-5 h-5" />,
      steps: ["Sanctions Check", "Debarment Check", "Basic News Scan", "AI Synthesis"],
    },
    {
      key: "standard_vet",
      icon: <Search className="w-5 h-5" />,
      steps: ["Sanctions", "Debarment", "News", "Litigation", "Corporate Filings", "Campaign Finance", "SEC Filings", "Lobbying"],
    },
    {
      key: "deep_dive",
      icon: <Microscope className="w-5 h-5" />,
      steps: ["All Standard +", "Bankruptcy", "Expanded Media", "Social Media", "International/PEP Checks"],
    },
  ];

  return (
    <div className="page-container max-w-3xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-foreground">Submit New Vetting</h1>
        <p className="text-sm text-muted-foreground mt-1">Enter details about the potential client to begin the vetting process</p>
      </div>

      <div className="space-y-6">
        {/* Who are we vetting? */}
        <section className="glass-card p-6">
          <h2 className="section-title flex items-center gap-2"><Shield className="w-4 h-4" /> Who are we vetting?</h2>
          <div className="space-y-4">
            <div>
              <Label htmlFor="subject-name">Subject Name *</Label>
              <Input id="subject-name" value={subjectName} onChange={(e) => setSubjectName(e.target.value)} placeholder="Full name of person or company" className="mt-1.5 bg-background" />
            </div>
            <div>
              <Label>Subject Type</Label>
              <RadioGroup value={subjectType} onValueChange={(v) => setSubjectType(v as SubjectType)} className="flex gap-4 mt-2">
                <div className="flex items-center gap-2">
                  <RadioGroupItem value="individual" id="individual" />
                  <Label htmlFor="individual" className="cursor-pointer font-normal">Individual</Label>
                </div>
                <div className="flex items-center gap-2">
                  <RadioGroupItem value="organization" id="organization" />
                  <Label htmlFor="organization" className="cursor-pointer font-normal">Organization</Label>
                </div>
              </RadioGroup>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="company">Company Affiliation</Label>
                <Input id="company" value={companyAffiliation} onChange={(e) => setCompanyAffiliation(e.target.value)} placeholder="Company or organization name" className="mt-1.5 bg-background" />
              </div>
              <div>
                <Label htmlFor="country">Country</Label>
                <Input id="country" value={country} onChange={(e) => setCountry(e.target.value)} placeholder="Country of origin or primary operations" className="mt-1.5 bg-background" />
              </div>
            </div>
            <div>
              <Label htmlFor="city">City</Label>
              <Input id="city" value={city} onChange={(e) => setCity(e.target.value)} placeholder="City" className="mt-1.5 max-w-xs bg-background" />
            </div>
          </div>
        </section>

        {/* Background */}
        <section className="glass-card p-6">
          <h2 className="section-title">Background Information</h2>
          <div className="space-y-4">
            <div>
              <Label htmlFor="bio">Brief Bio</Label>
              <Textarea id="bio" value={briefBio} onChange={(e) => setBriefBio(e.target.value)} placeholder="Any background info, context about who they are, how they came to us, what we know so far..." rows={4} className="mt-1.5 bg-background" />
            </div>
            <div>
              <Label htmlFor="referral">Referral Source</Label>
              <Input id="referral" value={referralSource} onChange={(e) => setReferralSource(e.target.value)} placeholder="Who referred them? How did they find TMG?" className="mt-1.5 bg-background" />
            </div>
            <div>
              <Label>Engagement Type *</Label>
              <Select value={engagementType} onValueChange={(v) => setEngagementType(v as EngagementType)}>
                <SelectTrigger className="mt-1.5 bg-background"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {(Object.keys(ENGAGEMENT_LABELS) as EngagementType[]).map((key) => (
                    <SelectItem key={key} value={key}>
                      <div className="flex items-center gap-2">
                        <span>{ENGAGEMENT_LABELS[key]}</span>
                        {ENGAGEMENT_MULTIPLIERS[key] && (
                          <span className={`text-xs px-1.5 py-0.5 rounded ${key === "domestic_corporate" ? "bg-[hsl(var(--risk-low)/0.12)] text-[hsl(var(--risk-low))]" : "bg-[hsl(var(--fara)/0.12)] text-[hsl(var(--fara))]"}`}>
                            {ENGAGEMENT_MULTIPLIERS[key]}
                          </span>
                        )}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </section>

        {/* Vetting Level */}
        <section className="glass-card p-6">
          <h2 className="section-title">Vetting Configuration</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {vettingLevelCards.map((card) => {
              const info = VETTING_LEVEL_LABELS[card.key];
              const selected = vettingLevel === card.key;
              return (
                <button
                  key={card.key}
                  type="button"
                  onClick={() => setVettingLevel(card.key)}
                  className={`text-left p-4 rounded-xl border-2 transition-all duration-200 ${
                    selected
                      ? "border-primary bg-[hsl(var(--primary)/0.04)] shadow-sm"
                      : "border-border hover:border-primary/30 bg-card"
                  }`}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span className={selected ? "text-primary" : "text-muted-foreground"}>{card.icon}</span>
                    <span className="font-semibold text-sm text-foreground">{info.title}</span>
                    {card.key === "standard_vet" && (
                      <span className="text-[10px] bg-primary/10 text-primary px-1.5 py-0.5 rounded-full font-medium">Recommended</span>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground mb-1">{info.description}. {info.time}</p>
                  <p className="text-xs text-muted-foreground italic">Best for: {info.bestFor}</p>
                  <div className="mt-3 flex flex-wrap gap-1">
                    {card.steps.map((s) => (
                      <span key={s} className="text-[10px] bg-muted text-muted-foreground px-1.5 py-0.5 rounded">{s}</span>
                    ))}
                  </div>
                </button>
              );
            })}
          </div>
        </section>

        {/* Attachments */}
        <section className="glass-card p-6">
          <h2 className="section-title">Attachments (Optional)</h2>
          <div className="border-2 border-dashed border-border rounded-xl p-8 text-center hover:border-primary/30 transition-colors cursor-pointer bg-background">
            <Upload className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">Drop resumes, bios, email chains, or any relevant documents here</p>
            <p className="text-xs text-muted-foreground mt-1">PDF, DOCX, images accepted</p>
          </div>
        </section>

        {/* Submitted By */}
        <section className="glass-card p-6">
          <h2 className="section-title">Submitted By</h2>
          <div className="space-y-4">
            <div>
              <Label>Your Name *</Label>
              <Select value={requestedBy} onValueChange={setRequestedBy}>
                <SelectTrigger className="mt-1.5 max-w-xs bg-background"><SelectValue placeholder="Select your name" /></SelectTrigger>
                <SelectContent>
                  {TEAM_MEMBERS.map((m) => <SelectItem key={m} value={m}>{m}</SelectItem>)}
                  <SelectItem value="Other">Other</SelectItem>
                </SelectContent>
              </Select>
              {requestedBy === "Other" && (
                <Input value={otherName} onChange={(e) => setOtherName(e.target.value)} placeholder="Enter your name" className="mt-2 max-w-xs bg-background" />
              )}
            </div>
          </div>
        </section>

        <Button
          size="lg"
          disabled={!canSubmit}
          onClick={() => setShowConfirm(true)}
          className="w-full bg-[hsl(var(--risk-low))] hover:bg-[hsl(var(--risk-low)/0.9)] text-[hsl(var(--risk-low-foreground))] font-semibold text-base py-6 rounded-xl"
        >
          <Check className="w-5 h-5 mr-2" /> Start Vetting
        </Button>
      </div>

      <Dialog open={showConfirm} onOpenChange={setShowConfirm}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Vetting Submission</DialogTitle>
            <DialogDescription>Review the details before submitting</DialogDescription>
          </DialogHeader>
          <div className="space-y-2 text-sm">
            <p><strong>Subject:</strong> {subjectName} ({subjectType})</p>
            {companyAffiliation && <p><strong>Company:</strong> {companyAffiliation}</p>}
            {country && <p><strong>Location:</strong> {country}{city ? `, ${city}` : ""}</p>}
            <p><strong>Engagement:</strong> {ENGAGEMENT_LABELS[engagementType]}</p>
            <p><strong>Level:</strong> {VETTING_LEVEL_LABELS[vettingLevel].title}</p>
            <p><strong>Submitted by:</strong> {requestedBy === "Other" ? otherName : requestedBy}</p>
            {engagementType === "fara_foreign_political" && (
              <div className="flex items-center gap-2 p-2 rounded-lg bg-[hsl(var(--fara)/0.08)] text-[hsl(var(--fara))]">
                <AlertTriangle className="w-4 h-4" />
                <span className="text-xs font-medium">FARA engagement — 1.3x risk multiplier will be applied</span>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowConfirm(false)}>Cancel</Button>
            <Button onClick={handleSubmit} className="bg-[hsl(var(--risk-low))] hover:bg-[hsl(var(--risk-low)/0.9)] text-[hsl(var(--risk-low-foreground))]">
              Confirm & Start Vetting
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}