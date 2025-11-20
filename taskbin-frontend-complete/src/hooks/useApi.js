const BASE_URL = import.meta.env.VITE_REST_API_URL;
const TEST_USER_ID = import.meta.env.VITE_TEST_USER_ID || "test-user-id";
const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true" || !BASE_URL;

/**
 * In-memory mock database so buttons actually work in mock mode.
 */
const mockDB = {
  boards: [
    {
      id: "1",
      name: "Demo Board",
      role: "owner",
      description: "Example board for mock mode",
      joinedAt: new Date().toISOString(),
    },
    {
      id: "2",
      name: "School Project",
      role: "member",
      description: "Tasks for CS class",
      joinedAt: new Date().toISOString(),
    },
  ],
  tasksByBoard: {
    "1": [
      {
        id: "t1",
        title: "Set up backend",
        description: "Wire API Gateway to Lambda + DynamoDB",
        status: "in-progress",
        due: "2025-01-22T00:00:00Z",
        assignee: "mockuser@example.com",
        createdAt: new Date().toISOString(),
      },
    ],
    "2": [
      {
        id: "t2",
        title: "Design UI",
        description: "Boards, tasks, invites",
        status: "todo",
        due: "2025-01-25T00:00:00Z",
        assignee: null,
        createdAt: new Date().toISOString(),
      },
    ],
  },
};

async function jsonRequest(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const text = await res.text();
  let body;
  try {
    body = text ? JSON.parse(text) : null;
  } catch {
    body = text;
  }
  if (!res.ok) {
    console.error("API error:", res.status, body);
    throw new Error(body?.error || "API error");
  }
  return body;
}

export function useApi() {
  // MOCK MODE: everything happens against mockDB above
  if (USE_MOCK) {
    return {
      listBoards: async () => {
        await new Promise((r) => setTimeout(r, 150));
        return [...mockDB.boards];
      },

      createBoard: async (name, description = "") => {
        await new Promise((r) => setTimeout(r, 150));
        const id = String(Date.now());
        const board = {
          id,
          name,
          role: "owner",
          description,
          joinedAt: new Date().toISOString(),
        };
        mockDB.boards.push(board);
        mockDB.tasksByBoard[id] = [];
        return board;
      },

      listBoardTasks: async (boardId) => {
        await new Promise((r) => setTimeout(r, 150));
        return [...(mockDB.tasksByBoard[boardId] || [])];
      },

      createTask: async (boardId, { title, description = "", due, assignee, status = "todo" }) => {
        await new Promise((r) => setTimeout(r, 150));
        const task = {
          id: String(Date.now()),
          title,
          description,
          status,
          due: due || null,
          assignee: assignee || null,
          createdAt: new Date().toISOString(),
        };
        if (!mockDB.tasksByBoard[boardId]) {
          mockDB.tasksByBoard[boardId] = [];
        }
        mockDB.tasksByBoard[boardId].push(task);
        return task;
      },

      deleteTask: async (boardId, taskId) => {
        await new Promise((r) => setTimeout(r, 100));
        if (mockDB.tasksByBoard[boardId]) {
          mockDB.tasksByBoard[boardId] = mockDB.tasksByBoard[boardId].filter(
            (t) => t.id !== taskId
          );
        }
        return true;
      },

      updateTaskStatus: async (boardId, taskId, newStatus) => {
        await new Promise((r) => setTimeout(r, 120));
        if (mockDB.tasksByBoard[boardId]) {
          mockDB.tasksByBoard[boardId] = mockDB.tasksByBoard[boardId].map((t) =>
            t.id === taskId ? { ...t, status: newStatus } : t
          );
        }
        return { id: taskId, status: newStatus };
      },
    };
  }

  // REAL BACKEND MODE
  return {
    listBoards: async () => {
      const body = await jsonRequest(`/users/${TEST_USER_ID}/boards`, {
        method: "GET",
        body: JSON.stringify({ user_id: TEST_USER_ID }),
      });

      return (body.boards || []).map((b) => ({
        id: b.board_id,
        name: b.board_name,
        role: b.role,
        description: b.description,
        joinedAt: b.joined_at,
      }));
    },

    createBoard: async (name, description = "") => {
      const body = await jsonRequest(`/boards/create`, {
        method: "POST",
        body: JSON.stringify({
          user_id: TEST_USER_ID,
          board_name: name,
          description,
        }),
      });

      return {
        id: body.board_id,
        name: body.board_name,
        description,
      };
    },

    listBoardTasks: async (boardId) => {
      const body = await jsonRequest(`/boards/${boardId}/tasks`, {
        method: "GET",
        body: JSON.stringify({ board_id: boardId }),
      });

      return (body.tasks || []).map((t) => ({
        id: t.task_id,
        title: t.title,
        description: t.description,
        status: t.status,
        due: t.finish_by,
        assignee: t.assigned_to,
        createdAt: t.created_at,
      }));
    },

    createTask: async (boardId, { title, description = "", due, assignee, status = "todo" }) => {
      const body = await jsonRequest(`/boards/task/create`, {
        method: "POST",
        body: JSON.stringify({
          user_id: TEST_USER_ID,
          board_id: boardId,
          title,
          description,
          finish_by: due,
          assigned_to: assignee,
          status,
        }),
      });

      return {
        id: body.task_id,
        boardId: body.board_id,
      };
    },

    deleteTask: async (boardId, taskId) => {
      await jsonRequest(`/boards/${boardId}/tasks/${taskId}`, {
        method: "DELETE",
        body: JSON.stringify({ board_id: boardId, task_id: taskId }),
      });
      return true;
    },

    updateTaskStatus: async (boardId, taskId, newStatus) => {
      const body = await jsonRequest(`/boards/${boardId}/tasks/${taskId}`, {
        method: "PATCH",
        body: JSON.stringify({
          user_id: TEST_USER_ID,
          board_id: boardId,
          task_id: taskId,
          new_status: newStatus,
        }),
      });

      return {
        id: body.task_id,
        status: body.new_status,
      };
    },
  };
}
