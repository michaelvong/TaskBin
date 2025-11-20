import { create } from "zustand";

export const useBoardStore = create((set) => ({
  board: null,
  tasks: [],
  setBoard: (board) => set({ board }),
  setTasks: (tasks) => set({ tasks }),

  applyRealtimeUpdate: (event) =>
    set((state) => {
      switch (event.type) {
        case "TASK_CREATED":
          return { tasks: [...state.tasks, event.data] };
        case "TASK_UPDATED":
          return {
            tasks: state.tasks.map((t) =>
              t.id === event.data.id ? event.data : t
            ),
          };
        case "TASK_DELETED":
          return {
            tasks: state.tasks.filter((t) => t.id !== event.data.id),
          };
        default:
          return state;
      }
    }),
}));
