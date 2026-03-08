import { useState, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Plus, Trash2, CheckCircle, XCircle, RefreshCw } from "lucide-react";
interface HealthResponse {
  status: string;
  api_keys_configured: boolean;
  active_jobs: number;
  total_jobs: number;
}


interface Client {
  id: string;
  client_name: string;
  industry: string;
  engagement_type: string;
  active: boolean;
}

const INITIAL_CLIENTS: Client[] = [
  { id: "1", client_name: "Apex Industries", industry: "Defense", engagement_type: "Domestic Corporate", active: true },
  { id: "2", client_name: "GlobalTech Solutions", industry: "Technology", engagement_type: "Foreign Corporate", active: true },
  { id: "3", client_name: "Citizens for Progress PAC", industry: "Political", engagement_type: "Domestic Political", active: true },
  { id: "4", client_name: "Nordic Energy Partners", industry: "Energy", engagement_type: "Foreign Corporate", active: false },
];

export default function SettingsPage() {
  const [clients, setClients] = useState<Client[]>(INITIAL_CLIENTS);
  const [newName, setNewName] = useState("");
  const [newIndustry, setNewIndustry] = useState("");

  const addClient = () => {
    if (!newName.trim()) return;
    setClients([...clients, { id: crypto.randomUUID(), client_name: newName, industry: newIndustry, engagement_type: "", active: true }]);
    setNewName("");
    setNewIndustry("");
  };

  const toggleActive = (id: string) => {
    setClients(clients.map((c) => c.id === id ? { ...c, active: !c.active } : c));
  };

  const removeClient = (id: string) => {
    setClients(clients.filter((c) => c.id !== id));
  };

  return (
    <div className="page-container max-w-4xl">
      <h1 className="text-2xl font-bold text-foreground mb-6">Settings</h1>

      <Tabs defaultValue="clients">
        <TabsList className="mb-6">
          <TabsTrigger value="clients">TMG Client List</TabsTrigger>
          <TabsTrigger value="team">Team Members</TabsTrigger>
          <TabsTrigger value="pipeline">Pipeline Status</TabsTrigger>
        </TabsList>

        <TabsContent value="clients">
          <div className="glass-card p-6">
            <h2 className="section-title">Current TMG Clients</h2>
            <p className="text-sm text-muted-foreground mb-4">Manage the client list used for conflict of interest checks.</p>

            <div className="flex items-end gap-3 mb-6">
              <div className="flex-1">
                <Input placeholder="Client name" value={newName} onChange={(e) => setNewName(e.target.value)} className="bg-background" />
              </div>
              <div className="flex-1">
                <Input placeholder="Industry" value={newIndustry} onChange={(e) => setNewIndustry(e.target.value)} className="bg-background" />
              </div>
              <Button onClick={addClient} disabled={!newName.trim()} size="sm">
                <Plus className="w-4 h-4 mr-1" /> Add
              </Button>
            </div>

            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Client Name</TableHead>
                  <TableHead>Industry</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-20">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {clients.map((c) => (
                  <TableRow key={c.id}>
                    <TableCell className="font-medium text-foreground">{c.client_name}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">{c.industry || "—"}</TableCell>
                    <TableCell>
                      <button onClick={() => toggleActive(c.id)}>
                        {c.active ? (
                          <Badge variant="outline" className="bg-[hsl(var(--risk-low)/0.08)] text-risk-low border-[hsl(var(--risk-low)/0.15)] cursor-pointer">
                            <CheckCircle className="w-3 h-3 mr-1" /> Active
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="text-muted-foreground cursor-pointer">
                            <XCircle className="w-3 h-3 mr-1" /> Inactive
                          </Badge>
                        )}
                      </button>
                    </TableCell>
                    <TableCell>
                      <Button variant="ghost" size="sm" onClick={() => removeClient(c.id)}>
                        <Trash2 className="w-3.5 h-3.5 text-muted-foreground" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </TabsContent>

        <TabsContent value="team">
          <div className="glass-card p-6">
            <h2 className="section-title">Team Members</h2>
            <div className="space-y-3">
              {[
                { name: "Liza", role: "Admin / Reviewer" },
                { name: "Jim", role: "Reviewer" },
                { name: "Ben", role: "Reviewer" },
                { name: "Tara", role: "Reviewer" },
              ].map((m) => (
                <div key={m.name} className="flex items-center justify-between p-3 rounded-xl bg-muted">
                  <div>
                    <span className="font-medium text-sm text-foreground">{m.name}</span>
                  </div>
                  <Badge variant="outline">{m.role}</Badge>
                </div>
              ))}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="pipeline">
          <PipelineStatusPanel />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function PipelineStatusPanel() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  const ping = async () => {
    setLoading(true);
    setError(false);
    // Pipeline runs locally — no remote health check available
    setHealth(null);
    setError(true);
    setLoading(false);
  };

  useEffect(() => { ping(); }, []);

  const connected = health?.status === "ok";

  return (
    <div className="glass-card p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="section-title mb-0">Pipeline Status</h2>
        <Button variant="outline" size="sm" onClick={ping} disabled={loading}>
          <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} /> Refresh
        </Button>
      </div>
      <div className="space-y-4">
        <div className="flex items-center justify-between p-4 rounded-xl bg-muted">
          <div>
            <p className="font-medium text-sm text-foreground">Python Pipeline Backend</p>
            <p className="text-xs text-muted-foreground">http://localhost:8000</p>
          </div>
          {connected ? (
            <Badge variant="outline" className="bg-[hsl(var(--risk-low)/0.08)] text-risk-low border-[hsl(var(--risk-low)/0.15)]">
              <CheckCircle className="w-3 h-3 mr-1" /> Connected
            </Badge>
          ) : (
            <Badge variant="outline" className="text-destructive">
              <XCircle className="w-3 h-3 mr-1" /> {error ? "Disconnected" : "Checking..."}
            </Badge>
          )}
        </div>
        {connected && health && (
          <div className="grid grid-cols-3 gap-3">
            <div className="p-3 rounded-lg bg-muted text-center">
              <p className="text-lg font-bold text-foreground">{health.active_jobs}</p>
              <p className="text-xs text-muted-foreground">Active Jobs</p>
            </div>
            <div className="p-3 rounded-lg bg-muted text-center">
              <p className="text-lg font-bold text-foreground">{health.total_jobs}</p>
              <p className="text-xs text-muted-foreground">Total Jobs</p>
            </div>
            <div className="p-3 rounded-lg bg-muted text-center">
              <p className="text-lg font-bold text-foreground">{health.api_keys_configured ? "✓" : "✗"}</p>
              <p className="text-xs text-muted-foreground">API Keys</p>
            </div>
          </div>
        )}
        {error && (
          <p className="text-xs text-muted-foreground">
            Cannot reach the pipeline backend. Make sure the server is running: <code className="text-xs bg-muted px-1.5 py-0.5 rounded">uvicorn server:app --reload --port 8000</code>
          </p>
        )}
      </div>
    </div>
  );
}
