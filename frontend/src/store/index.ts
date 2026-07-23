import { create } from 'zustand';
import type { ChatMessage, User } from '../types';

interface AppState {
  user: User | null;
  setUser: (user: User | null) => void;
  messages: ChatMessage[];
  addMessage: (msg: ChatMessage) => void;
  clearMessages: () => void;
  sessionId: string | null;
  setSessionId: (id: string) => void;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  sidebarOpen: boolean;
  toggleSidebar: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
  messages: [],
  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  clearMessages: () => set({ messages: [] }),
  sessionId: null,
  setSessionId: (id) => set({ sessionId: id }),
  isLoading: false,
  setIsLoading: (isLoading) => set({ isLoading }),
  sidebarOpen: true,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
}));
