// ------------------------------------------------------
// LOCAL MOCK DB
// ------------------------------------------------------
const mockDB = {
  boards: [],
  tasks: {},
};

function delay(ms) {
  return new Promise((res) => setTimeout(res, ms));
}

export function useApi(currentUser) {
  const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";
  const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

  const FORCE_AWS = {
    listBoards: true,
    createBoard: true,
    listTasks: true,
    createTask: true,
    deleteTask: true,
    deleteBoard: true,
  };

  async function awsRequest(path, options = {}) {
    const res = await fetch(BASE_URL + path, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });

    if (!res.ok) {
      console.error("AWS ERROR", res.status, path);
      throw new Error(`AWS Error: ${res.status}`);
    }

    return res.json();
  }

  return {
    async listBoards() {
      if (USE_MOCK && !FORCE_AWS.listBoards) {
        await delay(150);
        return [...mockDB.boards];
      }
      if (!currentUser) return [];
      const r = await awsRequest(`/users/${currentUser}/boards`);
      return r.boards || [];
    },

    async createBoard({ name, description }) {
      if (USE_MOCK && !FORCE_AWS.createBoard) {
        await delay(150);
        const board = {
          id: crypto.randomUUID(),
          name,
          description,
          joinedAt: new Date().toISOString(),
          role: "owner",
        };
        mockDB.boards.push(board);
        return board;
      }
      if (!currentUser) throw new Error("No user");
      const r = await awsRequest(`/boards/create`, {
        method: "POST",
        body: JSON.stringify({ user_id: currentUser, name, description }),
      });
      return r.board || r;
    },

    async deleteBoard(boardId) {
      if (USE_MOCK && !FORCE_AWS.deleteBoard) {
        await delay(150);
        mockDB.boards = mockDB.boards.filter((b) => b.id !== boardId);
        delete mockDB.tasks[boardId];
        return { ok: true };
      }
      if (!currentUser) throw new Error("No user");
      return awsRequest(`/boards/${boardId}`, {
        method: "DELETE",
        body: JSON.stringify({ user_id: currentUser }),
      });
    },

    async listTasks(boardId) {
      if (USE_MOCK && !FORCE_AWS.listTasks) {
        await delay(150);
        return mockDB.tasks[boardId] || [];
      }
      const r = await awsRequest(`/boards/${boardId}/tasks`);
      return r.tasks || [];
    },

    async createTask(boardId, data) {
      if (USE_MOCK && !FORCE_AWS.createTask) {
        await delay(150);
        const task = {
          id: crypto.randomUUID(),
          created_at: new Date().toISOString(),
          ...data,
        };
        if (!mockDB.tasks[boardId]) mockDB.tasks[boardId] = [];
        mockDB.tasks[boardId].push(task);
        return task;
      }
      if (!currentUser) throw new Error("No user");
      return awsRequest(`/boards/${boardId}/tasks/create`, {
        method: "POST",
        body: JSON.stringify({ user_id: currentUser, ...data }),
      });
    },

    async deleteTask(boardId, taskId) {
      if (USE_MOCK && !FORCE_AWS.deleteTask) {
        await delay(150);
        if (mockDB.tasks[boardId]) {
          mockDB.tasks[boardId] = mockDB.tasks[boardId].filter(
            (t) => t.id !== taskId
          );
        }
        return { ok: true };
      }
      if (!currentUser) throw new Error("No user");
      return awsRequest(`/boards/${boardId}/tasks/${taskId}`, {
        method: "DELETE",
        body: JSON.stringify({ user_id: currentUser }),
      });
    },

    async getBoard(boardId) {
      const r = await awsRequest(`/boards/${boardId}`, {
        method: "GET",
      });

      // backend returns batches → extract the first
      return r.boards?.[0] || null;
    },

    async editTask(taskId, updates) {
      if (!currentUser) throw new Error("No user");

      console.log("editTask request:", {
        url: `/boards/tasks/${taskId}`,
        user_id: currentUser,
        updates
      });

      return awsRequest(`/boards/tasks/${taskId}`, {
        method: "POST",
        body: JSON.stringify({
          user_id: currentUser,
          ...updates
        })
      });
    }


  };
}