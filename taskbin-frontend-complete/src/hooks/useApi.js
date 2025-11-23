import { useMemo, useState } from "react";

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

  // ------------------------------------------------------
  // REMOVE TEST USER ENV — rely on real Cognito login
  // ------------------------------------------------------
  const [currentUser, setCurrentUser] = useState(null);

  // Expose setUser() for Dashboard to call after decoding id_token
  function setUser(email) {
    if (email) setCurrentUser(email);
  }

  // Your original function-specific AWS override config
  const FORCE_AWS = {
    listBoards: true,
    createBoard: true,
    listTasks: true,
    createTask: true,
    deleteTask: true,
    deleteBoard: true,
  };

  function delay(ms) {
    return new Promise((res) => setTimeout(res, ms));
  }

  // ------------------------------------------------------
  // MOCK IMPLEMENTATION (unchanged)
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
  // AWS IMPLEMENTATION (unchanged except user)
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
    if (!currentUser) return [];
    return awsRequest(`/users/${currentUser}/boards`).then(r => r.boards || []);
  },

  async createBoard({ name, description }) {
    if (!currentUser) throw new Error("No user");
    return awsRequest(`/boards/create`, {
      method: "POST",
      body: JSON.stringify({ user_id: currentUser, name, description })
    }).then(r => r.board || r);
  },

  async deleteBoard(boardId) {
    if (!currentUser) throw new Error("No user");
    return awsRequest(`/boards/${boardId}`, {
      method: "DELETE",
      body: JSON.stringify({ user_id: currentUser })
    });
  },

  async listTasks(boardId) {
    return awsRequest(`/boards/${boardId}/tasks`).then(r => r.tasks || []);
  },

  async createTask(boardId, data) {
    if (!currentUser) throw new Error("No user");
    return awsRequest(`/boards/${boardId}/tasks/create`, {
      method: "POST",
      body: JSON.stringify({ user_id: currentUser, ...data })
    });
  },

  async deleteTask(boardId, taskId) {
    if (!currentUser) throw new Error("No user");
    return awsRequest(`/boards/${boardId}/tasks/${taskId}`, {
      method: "DELETE",
      body: JSON.stringify({ user_id: currentUser })
    });
  },
};


  // ------------------------------------------------------
  // FINAL API WRAPPER (unchanged except user)
  // ------------------------------------------------------
  const api = {
    setUser,

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

  return useMemo(() => api, [USE_MOCK, BASE_URL, currentUser]);
}
