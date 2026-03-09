import { useNavigate } from "react-router-dom";
import { useVettingStore } from "@/lib/vetting-store";
import { Activity, Clock, CheckCircle, AlertTriangle, Plus, Loader2 } from "lucide-react";
import { VettingCard } from "@/components/VettingCard";
import { useState, useMemo, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Link } from "react-router-dom";

export default function Dashboard() {
  const { vettings, loading, loadVettings } = useVettingStore();
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [sortBy, setSortBy] = useState<string>("recent");

  useEffect(() => {
    loadVettings();
  }, [loadVettings]);

  const completedYear = vettings.filter((v) => {
    if (!v.completed_at) return false;
    const d = new Date(v.completed_at);
    return d.getFullYear() === new Date().getFullYear();
  }).length;
  const completedMonth = vettings.filter((v) => {
    if (!v.completed_at) return false;
    const d = new Date(v.completed_at);
    const now = new Date();
    return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear();
  }).length;


  const filtered = useMemo(() => {
    let result = [...vettings];
    if (search) result = result.filter((v) => v.subject_name.toLowerCase().includes(search.toLowerCase()));
    if (statusFilter !== "all") result = result.filter((v) => v.status === statusFilter);
    switch (sortBy) {
      case "recent": result.sort((a, b) => new Date(b.requested_at).getTime() - new Date(a.requested_at).getTime()); break;
      case "risk": result.sort((a, b) => (b.composite_score ?? -1) - (a.composite_score ?? -1)); break;
      case "oldest": result.sort((a, b) => new Date(a.requested_at).getTime() - new Date(b.requested_at).getTime()); break;
      case "awaiting": result.sort((a, b) => {
        const aWait = a.status === "completed" && !a.decision ? 1 : 0;
        const bWait = b.status === "completed" && !b.decision ? 1 : 0;
        return bWait - aWait;
      }); break;
    }
    return result;
  }, [vettings, search, statusFilter, sortBy]);

  const stats = [
    { 
      label: "Completed This Month", 
      value: completedMonth, 
      icon: CheckCircle, 
      color: "text-[hsl(var(--risk-low))]",
      bgColor: "bg-[hsl(var(--risk-low)/0.08)]",
    },
    { 
      label: "Total Vettings 2026", 
      value: completedYear, 
      icon: Clock, 
      color: "text-accent",
      bgColor: "bg-accent/8",
    },
  ];

  return (
    <div className="page-container">
      {/* Page Header */}
      <div className="flex items-center justify-end mb-8">
        <Link to="/submit">
          <Button className="gap-2">
            <Plus className="w-4 h-4" />
            New Vetting
          </Button>
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-8">
        {stats.map((s) => (
          <div key={s.label} className="glass-card px-3 py-4 group text-center">
            <div className={`inline-flex p-2 rounded-xl ${s.bgColor} mb-2`}>
              <s.icon className={`w-4 h-4 ${s.color}`} />
            </div>
            <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
            <p className="text-xs text-muted-foreground font-medium mt-0.5">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <div className="relative flex-1 max-w-sm">
          <Input
            placeholder="Search by subject name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-card pl-4"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[160px] bg-card"><SelectValue placeholder="Status" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="running">Running</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="gates_failed">Gates Failed</SelectItem>
            <SelectItem value="error">Error</SelectItem>
          </SelectContent>
        </Select>
        <Select value={sortBy} onValueChange={setSortBy}>
          <SelectTrigger className="w-[180px] bg-card"><SelectValue placeholder="Sort" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="recent">Most Recent</SelectItem>
            <SelectItem value="risk">Highest Risk</SelectItem>
            <SelectItem value="oldest">Oldest First</SelectItem>
            <SelectItem value="awaiting">Awaiting Decision</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Vetting Cards */}
      <div className="space-y-3">
        {loading && (
          <div className="glass-card p-16 text-center">
            <Loader2 className="w-8 h-8 animate-spin text-muted-foreground mx-auto mb-3" />
            <p className="text-muted-foreground">Loading vettings...</p>
          </div>
        )}
        {!loading && filtered.map((v) => (
          <VettingCard key={v.id} vetting={v} onClick={() => navigate(`/vetting/${v.id}`)} />
        ))}
        {!loading && filtered.length === 0 && (
          <div className="glass-card p-16 text-center">
            <p className="text-muted-foreground text-lg">No vetting requests found.</p>
            
            <Link to="/submit">
              <Button className="mt-4 gap-2">
                <Plus className="w-4 h-4" />
                Submit New Vetting
              </Button>
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
