"use client";

import * as React from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

export const Dialog = DialogPrimitive.Root;
export const DialogTrigger = DialogPrimitive.Trigger;
export const DialogClose = DialogPrimitive.Close;

export function DialogContent({
  title,
  description,
  children,
  className,
}: {
  title: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <DialogPrimitive.Portal>
      <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-[rgb(0_0_0/0.45)]" />
      <DialogPrimitive.Content
        className={cn(
          "fixed left-1/2 top-1/2 z-50 max-h-[90vh] w-[calc(100vw-2rem)] max-w-lg -translate-x-1/2 -translate-y-1/2 overflow-y-auto rounded-lg border border-line bg-paper-raised p-6 shadow-[0_1px_2px_rgb(22_25_29_/0.08),0_8px_24px_-6px_rgb(22_25_29_/0.14)] focus:outline-none",
          className,
        )}
      >
        <div className="mb-5 pr-8">
          <DialogPrimitive.Title className="font-serif text-xl font-medium">{title}</DialogPrimitive.Title>
          {description ? (
            <DialogPrimitive.Description className="mt-1 text-sm text-ink-muted">{description}</DialogPrimitive.Description>
          ) : (
            <DialogPrimitive.Description className="sr-only">{title}</DialogPrimitive.Description>
          )}
        </div>
        {children}
        <DialogPrimitive.Close
          className="absolute right-4 top-4 rounded p-1 text-ink-muted hover:bg-blue-soft hover:text-blue"
          aria-label="Đóng"
        >
          <X className="size-4" />
        </DialogPrimitive.Close>
      </DialogPrimitive.Content>
    </DialogPrimitive.Portal>
  );
}

export function DialogFooter({ children }: { children: React.ReactNode }) {
  return <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">{children}</div>;
}

/** Confirmation for destructive or irreversible actions. */
export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel,
  onConfirm,
  loading,
  destructive = true,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description: string;
  confirmLabel: string;
  onConfirm: () => void;
  loading?: boolean;
  destructive?: boolean;
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent title={title} description={description}>
        <DialogFooter>
          <DialogClose asChild>
            <button className="inline-flex h-10 items-center justify-center rounded border border-line-strong bg-paper-raised px-4 text-[15px] font-medium hover:bg-paper-sunk">
              Hủy
            </button>
          </DialogClose>
          <button
            disabled={loading}
            onClick={onConfirm}
            className={cn(
              "inline-flex h-10 items-center justify-center rounded border px-4 text-[15px] font-medium hover:border-ink hover:bg-ink hover:text-paper disabled:opacity-50",
              destructive ? "border-red bg-red text-on-red" : "border-blue bg-blue text-on-blue",
            )}
          >
            {loading ? "Đang xử lý…" : confirmLabel}
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
