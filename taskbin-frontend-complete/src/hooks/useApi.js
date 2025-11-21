import { useMemo } from "react";

// ------------------------------------------------------
// LOCAL MOCK DB
// ------------------------------------------------------
const mockDB = {
  boards: [],
  tasks: {},
};

export function useApi() {
  const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";
  const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";
  const TEST_USER_ID =
    import.meta.env.VITE_TEST_USER_ID || "testuser@example.com";

  // 🔥 Control which functions use AWS INDEPENDENTLY
  const FORCE_AWS = {
    listBoards: true,        // <-- ENABLE AWS listBoards
    createBoard: true,      // <-- MOCK createBoard
    listTasks: false,        // <-- MOCK listTasks
    createTask: false,       // <-- MOCK createTask
    deleteTask: false,       // <-- MOCK deleteTask
    deleteBoard: false,      // <-- MOCK deleteBoard
  };

  function delay(ms) {
    return new Promise((res) => setTimeout(res, ms));
  }

  // ------------------------------------------------------
  // MOCK IMPLEMENTATION
  // ------------------------------------------------------
  const mock = {
    async listBoards() {
      await delay(150);
      return [...mockDB.boards];
    },

    async createBoard({ name, description }) {
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
    },

    async deleteBoard(boardId) {
      await delay(150);
      mockDB.boards = mockDB.boards.filter((b) => b.id !== boardId);
      delete mockDB.tasks[boardId];
      return { ok: true };
    },

    async listTasks(boardId) {
      await delay(150);
      return mockDB.tasks[boardId] || [];
    },

    async createTask(boardId, data) {
      await delay(150);
      const task = {
        id: crypto.randomUUID(),
        created_at: new Date().toISOString(),
        ...data,
      };
      if (!mockDB.tasks[boardId]) mockDB.tasks[boardId] = [];
      mockDB.tasks[boardId].push(task);
      return task;
    },

    async deleteTask(boardId, taskId) {
      await delay(150);
      if (mockDB.tasks[boardId]) {
        mockDB.tasks[boardId] = mockDB.tasks[boardId].filter(
          (t) => t.id !== taskId
        );
      }
      return { ok: true };
    },
  };

  // ------------------------------------------------------
  // AWS IMPLEMENTATION
  // ------------------------------------------------------
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

  const aws = {
    async listBoards() {
      const result = await awsRequest(`/users/${TEST_USER_ID}/boards`, {
        method: "GET",
      });
      return result?.boards || [];
    },

    async createBoard({ name, description }) {
      const result = await awsRequest(`/boards/create`, {
        method: "POST",
        body: JSON.stringify({
          user_id: TEST_USER_ID,
          name: name,      // REQUIRED by AWS
          description: description ?? "",
        }),
      });
      return result?.board || result;
    },

    async deleteBoard(boardId) {
      return awsRequest(`/boards/${boardId}`, {
        method: "DELETE",
        body: JSON.stringify({ user_id: TEST_USER_ID }),
      });
    },

    async listTasks(boardId) {
      const result = await awsRequest(`/boards/${boardId}/tasks`, {
        method: "GET",
      });
      return result?.tasks || [];
    },

    async createTask(boardId, data) {
      return awsRequest(`/boards/${boardId}/tasks/create`, {
        method: "POST",
        body: JSON.stringify({ user_id: TEST_USER_ID, ...data }),
      });
    },

    async deleteTask(boardId, taskId) {
      return awsRequest(`/boards/${boardId}/tasks/${taskId}`, {
        method: "DELETE",
        body: JSON.stringify({ user_id: TEST_USER_ID }),
      });
    },
  };

  // ------------------------------------------------------
  // FINAL API WRAPPER — FUNCTION-BY-FUNCTION SWITCHING
  // ------------------------------------------------------
  const api = {
    listBoards: (...args) =>
      !USE_MOCK || FORCE_AWS.listBoards
        ? aws.listBoards(...args)
        : mock.listBoards(...args),

    createBoard: (...args) =>
      !USE_MOCK || FORCE_AWS.createBoard
        ? aws.createBoard(...args)
        : mock.createBoard(...args),

    deleteBoard: (...args) =>
      !USE_MOCK || FORCE_AWS.deleteBoard
        ? aws.deleteBoard(...args)
        : mock.deleteBoard(...args),

    listTasks: (...args) =>
      !USE_MOCK || FORCE_AWS.listTasks
        ? aws.listTasks(...args)
        : mock.listTasks(...args),

    createTask: (...args) =>
      !USE_MOCK || FORCE_AWS.createTask
        ? aws.createTask(...args)
        : mock.createTask(...args),

    deleteTask: (...args) =>
      !USE_MOCK || FORCE_AWS.deleteTask
        ? aws.deleteTask(...args)
        : mock.deleteTask(...args),
  };

  return useMemo(() => api, [USE_MOCK, BASE_URL]);
}
