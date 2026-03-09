import { useNavigate } from "react-router-dom";
import { useVettingStore } from "@/lib/vetting-store";
import { Clock, CheckCircle, Loader2 } from "lucide-react";
import { VettingCard } from "@/components/VettingCard";
import { useState, useMemo, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

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

  return (
    <div className="page-container">
      {/* Stats + Filters Row */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 mb-6">
        {/* Inline Stats */}
        <div className="flex items-center gap-6 mr-auto">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-[hsl(var(--risk-low)/0.1)]">
              <CheckCircle className="w-4 h-4 text-[hsl(var(--risk-low))]" />
            </div>
            <div>
              <span className="text-xl font-bold text-foreground">{completedMonth}</span>
              <span className="text-xs text-muted-foreground ml-1.5">this month</span>
            </div>
          </div>
          <div className="w-px h-8 bg-border" />
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-accent/10">
              <Clock className="w-4 h-4 text-accent" />
            </div>
            <div>
              <span className="text-xl font-bold text-foreground">{completedYear}</span>
              <span className="text-xs text-muted-foreground ml-1.5">total 2026</span>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-2">
          <Input
            placeholder="Search..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-card pl-3 w-[180px] h-9 text-sm"
          />
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-[140px] bg-card h-9 text-sm"><SelectValue placeholder="Status" /></SelectTrigger>
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
            <SelectTrigger className="w-[150px] bg-card h-9 text-sm"><SelectValue placeholder="Sort" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="recent">Most Recent</SelectItem>
              <SelectItem value="risk">Highest Risk</SelectItem>
              <SelectItem value="oldest">Oldest First</SelectItem>
              <SelectItem value="awaiting">Awaiting Decision</SelectItem>
            </SelectContent>
          </Select>
        </div>
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
          </div>
        )}
      </div>
    </div>
  );
}