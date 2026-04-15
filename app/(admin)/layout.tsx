import { LogoutButton } from "@/components/LogoutButton";
import { Sidebar } from "@/components/Sidebar";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen bg-slate-100">
      <Sidebar />
      <main className="flex-1 p-6">
        <div className="mb-4 flex justify-end">
          <LogoutButton />
        </div>
        {children}
      </main>
    </div>
  );
}
