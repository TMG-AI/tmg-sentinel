import { Plus, LayoutDashboard, Clock, Shield } from "lucide-react";
import { NavLink } from "@/components/NavLink";
import { cn } from "@/lib/utils";

const navItems = [
  { title: "New Vetting", url: "/submit", icon: Plus },
  { title: "Dashboard", url: "/", icon: LayoutDashboard },
  { title: "History", url: "/history", icon: Clock },
];

export function TopNav() {
  return (
    <header className="sticky top-0 z-50 border-b bg-card">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-primary flex items-center justify-center">
              <Shield className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="text-lg font-bold text-foreground tracking-tight">Client Vetting System</span>
          </div>

          {/* Navigation */}
          <nav className="flex items-center gap-1">
            {navItems.map((item) => (
              <NavLink
                key={item.title}
                to={item.url}
                end={item.url === "/"}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-muted-foreground",
                  "hover:text-foreground hover:bg-muted transition-all duration-150"
                )}
                activeClassName="text-primary bg-primary/8 hover:bg-primary/10 hover:text-primary"
              >
                <item.icon className="w-4 h-4" />
                <span>{item.title}</span>
              </NavLink>
            ))}
          </nav>
        </div>
      </div>
    </header>
  );
}
