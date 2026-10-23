import { SiteHeader } from "@/components/layout/site-header";
import { RoleGuard } from "@/components/layout/role-guard";
import { WorkspaceNav } from "@/components/layout/shell";

const ITEMS = [
  { href: "/instructor/courses", label: "Khóa học của tôi" },
  { href: "/instructor/questions", label: "Ngân hàng câu hỏi" },
  { href: "/instructor/students", label: "Tiến độ học viên" },
];

export default function InstructorLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <SiteHeader />
      <RoleGuard roles={["INSTRUCTOR", "ADMIN"]}>
        <WorkspaceNav items={ITEMS} />
        <main className="container py-10">{children}</main>
      </RoleGuard>
    </>
  );
}
