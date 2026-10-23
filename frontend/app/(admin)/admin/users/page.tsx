"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { errorMessage } from "@/lib/api-client";
import { adminApi } from "@/lib/endpoints";
import { useAuth } from "@/hooks/use-auth";
import type { Role, User } from "@/lib/types";
import { formatDate, ROLE_LABEL } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/dialog";
import { Input, Select } from "@/components/ui/input";
import { Avatar, EmptyState, ErrorNote, PageHeader, Pagination, Spinner } from "@/components/ui/misc";
import { Table, Td, Th } from "@/components/ui/table";

const ROLES: Role[] = ["STUDENT", "INSTRUCTOR", "ADMIN"];

type Pending = { kind: "role"; user: User; role: Role } | { kind: "status"; user: User } | null;

export default function AdminUsersPage() {
  const me = useAuth((s) => s.user);
  const qc = useQueryClient();
  const [page, setPage] = React.useState(1);
  const [role, setRole] = React.useState<Role | "">("");
  const [active, setActive] = React.useState<"" | "true" | "false">("");
  const [search, setSearch] = React.useState("");
  const [term, setTerm] = React.useState("");
  const [pending, setPending] = React.useState<Pending>(null);

  React.useEffect(() => {
    const t = setTimeout(() => {
      setTerm(search.trim());
      setPage(1);
    }, 300);
    return () => clearTimeout(t);
  }, [search]);

  const list = useQuery({
    queryKey: ["admin-users", page, role, active, term],
    queryFn: () =>
      adminApi.users({
        page,
        limit: 15,
        role: role || undefined,
        search: term || undefined,
        is_active: active === "" ? undefined : active === "true",
      }),
  });

  const apply = useMutation({
    mutationFn: (p: NonNullable<Pending>) =>
      p.kind === "role" ? adminApi.setRole(p.user.id, p.role) : adminApi.setStatus(p.user.id, !p.user.is_active),
    onSuccess: ({ message }) => {
      toast.success(message);
      setPending(null);
      qc.invalidateQueries({ queryKey: ["admin-users"] });
    },
    onError: (e) => {
      setPending(null);
      toast.error(errorMessage(e));
    },
  });

  return (
    <>
      <PageHeader title="Người dùng" description="Phân quyền vai trò và khóa hoặc mở khóa tài khoản." />

      <div className="mb-6 grid gap-3 sm:grid-cols-[minmax(0,1fr)_180px_180px]">
        <Input
          placeholder="Tìm theo tên hoặc email"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          aria-label="Tìm người dùng"
        />
        <Select
          aria-label="Lọc theo vai trò"
          value={role}
          onChange={(e) => {
            setRole(e.target.value as Role | "");
            setPage(1);
          }}
        >
          <option value="">Mọi vai trò</option>
          {ROLES.map((r) => (
            <option key={r} value={r}>
              {ROLE_LABEL[r]}
            </option>
          ))}
        </Select>
        <Select
          aria-label="Lọc theo trạng thái"
          value={active}
          onChange={(e) => {
            setActive(e.target.value as "" | "true" | "false");
            setPage(1);
          }}
        >
          <option value="">Mọi trạng thái</option>
          <option value="true">Đang hoạt động</option>
          <option value="false">Đã khóa</option>
        </Select>
      </div>

      {list.isLoading ? (
        <Spinner />
      ) : list.error ? (
        <ErrorNote message={errorMessage(list.error)} />
      ) : list.data!.items.length === 0 ? (
        <EmptyState title="Không có người dùng phù hợp" description="Thử bỏ bớt bộ lọc." />
      ) : (
        <>
          <p className="mb-3 text-sm text-ink-muted">{list.data!.total} người dùng</p>
          <Table>
            <thead>
              <tr>
                <Th>Người dùng</Th>
                <Th>Tham gia</Th>
                <Th>Vai trò</Th>
                <Th>Trạng thái</Th>
                <Th />
              </tr>
            </thead>
            <tbody>
              {list.data!.items.map((u) => {
                const self = u.id === me?.id;
                return (
                  <tr key={u.id}>
                    <Td>
                      <div className="flex items-center gap-3">
                        <Avatar name={u.full_name} src={u.avatar_url} size={32} />
                        <div className="min-w-0">
                          <p className="truncate font-medium">
                            {u.full_name}
                            {self && <span className="ml-2 text-xs text-ink-muted">(bạn)</span>}
                          </p>
                          <p className="truncate text-xs text-ink-muted">{u.email}</p>
                        </div>
                      </div>
                    </Td>
                    <Td className="text-ink-muted">{formatDate(u.created_at)}</Td>
                    <Td>
                      <Select
                        aria-label={`Vai trò của ${u.full_name}`}
                        value={u.role}
                        disabled={self}
                        className="h-9 w-40"
                        onChange={(e) => setPending({ kind: "role", user: u, role: e.target.value as Role })}
                      >
                        {ROLES.map((r) => (
                          <option key={r} value={r}>
                            {ROLE_LABEL[r]}
                          </option>
                        ))}
                      </Select>
                    </Td>
                    <Td>{u.is_active ? <span className="text-blue">Hoạt động</span> : <span className="text-red">Đã khóa</span>}</Td>
                    <Td className="text-right">
                      {!self && (
                        <Button
                          variant={u.is_active ? "danger" : "outline"}
                          size="sm"
                          onClick={() => setPending({ kind: "status", user: u })}
                        >
                          {u.is_active ? "Khóa tài khoản" : "Mở khóa"}
                        </Button>
                      )}
                    </Td>
                  </tr>
                );
              })}
            </tbody>
          </Table>
          <Pagination page={page} pages={list.data!.pages} onChange={setPage} />
        </>
      )}

      <ConfirmDialog
        open={!!pending}
        onOpenChange={(o) => !o && setPending(null)}
        title={
          pending?.kind === "role"
            ? `Đổi vai trò của ${pending.user.full_name} thành ${ROLE_LABEL[pending.role].toLowerCase()}?`
            : pending?.user.is_active
              ? `Khóa tài khoản ${pending.user.full_name}?`
              : `Mở khóa tài khoản ${pending?.user.full_name ?? ""}?`
        }
        description={
          pending?.kind === "role"
            ? "Quyền truy cập thay đổi từ lần đăng nhập hoặc làm mới phiên tiếp theo của người này."
            : pending?.user.is_active
              ? "Người này sẽ không đăng nhập được cho đến khi được mở khóa."
              : "Người này có thể đăng nhập lại ngay."
        }
        confirmLabel={
          pending?.kind === "role" ? "Đổi vai trò" : pending?.user.is_active ? "Khóa tài khoản" : "Mở khóa"
        }
        destructive={pending?.kind === "status" && pending.user.is_active}
        loading={apply.isPending}
        onConfirm={() => pending && apply.mutate(pending)}
      />
    </>
  );
}
