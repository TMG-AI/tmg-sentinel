import type { ReactNode } from "react";
import { TopNav } from "@/components/TopNav";

export function AppLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-background">
      <TopNav />
      <main className="flex-1">
        {children}
      </main>
    </div>
  );
}
