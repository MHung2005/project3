import { SiteHeader } from "@/components/layout/site-header";
import { RoleGuard } from "@/components/layout/role-guard";
import { WorkspaceNav } from "@/components/layout/shell";

const ITEMS = [
  { href: "/admin/courses", label: "Kiểm duyệt khóa học" },
  { href: "/admin/users", label: "Người dùng" },
  { href: "/admin/categories", label: "Danh mục" },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <SiteHeader />
      <RoleGuard roles={["ADMIN"]}>
        <WorkspaceNav items={ITEMS} />
        <main className="container py-10">{children}</main>
      </RoleGuard>
    </>
  );
}
