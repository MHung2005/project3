"use client";

import { create } from "zustand";

/** Client UI state (SDD §6.4). */
interface UiState {
  sidebarExpanded: boolean;
  setSidebarExpanded: (v: boolean) => void;
  toggleSidebar: () => void;
}

export const useUi = create<UiState>((set) => ({
  sidebarExpanded: true,
  setSidebarExpanded: (sidebarExpanded) => set({ sidebarExpanded }),
  toggleSidebar: () => set((s) => ({ sidebarExpanded: !s.sidebarExpanded })),
}));
