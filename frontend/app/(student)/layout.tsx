import { SiteHeader } from "@/components/layout/site-header";
import { RoleGuard } from "@/components/layout/role-guard";

export default function StudentLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <SiteHeader />
      <main>
        <RoleGuard>{children}</RoleGuard>
      </main>
    </>
  );
}
