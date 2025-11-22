import { useEffect, useState } from "react";
import { useApi } from "../hooks/useApi";
import { useLocation, useParams, Link } from "react-router-dom";
import TaskCard from "../components/TaskCard";

export default function Board() {
  const api = useApi();
  const { boardId } = useParams(); // correct param name
  const location = useLocation();
  const initialBoard = location.state?.board;

  const [board, setBoard] = useState(initialBoard || null);
  const [tasks, setTasks] = useState([]);

  // Form state
  const [newTaskTitle, setNewTaskTitle] = useState("");
  const [newTaskStatus, setNewTaskStatus] = useState("todo");
  const [newTaskAssignee, setNewTaskAssignee] = useState("");
  const [newTaskDue, setNewTaskDue] = useState("");

  // -----------------------------
  // Load board metadata
  // -----------------------------
  async function loadBoard() {
    if (!board) {
      // Optional enhancement: fetch metadata from API
      setBoard({
        id: boardId,
        name: "Board",
        description: "",
      });
    }
  }

  // -----------------------------
  // Load tasks for this board
  // -----------------------------
  async function loadTasks() {
    try {
      const result = await api.listTasks(boardId);
      const arr = Array.isArray(result) ? result : result?.tasks || [];
      setTasks(arr);
    } catch (err) {
      console.error("Error loading tasks:", err);
      setTasks([]);
    }
  }

  useEffect(() => {
    loadBoard();
    loadTasks();
  }, [boardId]);

  // -----------------------------
  // Create task
  // -----------------------------
  async function handleCreateTask(e) {
    e.preventDefault();
    if (!newTaskTitle.trim()) return;

    try {
      await api.createTask(boardId, {
        title: newTaskTitle.trim(),
        description: "",
        status: newTaskStatus,
        assignee: newTaskAssignee || null,
        due: newTaskDue ? new Date(newTaskDue).toISOString() : null,
      });

      // Refresh tasks
      await loadTasks();

      // Reset form
      setNewTaskTitle("");
      setNewTaskStatus("todo");
      setNewTaskAssignee("");
      setNewTaskDue("");
    } catch (err) {
      console.error("Failed to create task:", err);
    }
  }

  // -----------------------------
  // Delete task
  // -----------------------------
  async function handleDeleteTask(taskId) {
    try {
      await api.deleteTask(boardId, taskId);
      setTasks((prev) => prev.filter((t) => t.id !== taskId));
    } catch (err) {
      console.error("Failed to delete task:", err);
    }
  }

  // ----- Task counts for header bar -----
  const total = tasks.length;
  const todo = tasks.filter((t) => t.status === "todo").length;
  const inProgress = tasks.filter((t) => t.status === "in_progress").length;
  const done = tasks.filter((t) => t.status === "done").length;

  return (
    <div className="max-w-5xl mx-auto p-4 space-y-6">
      {/* Back button */}
      <Link
        to="/"
        className="inline-flex items-center text-sm text-blue-600 hover:underline"
      >
        ← Back to boards
      </Link>

      {/* Board header */}
      <header className="space-y-1">
        <h1 className="text-2xl font-bold">{board?.name || "Board"}</h1>
        {board?.description && (
          <p className="text-sm text-gray-500">{board.description}</p>
        )}

        <div className="text-xs text-gray-500 flex gap-4 mt-1">
          <span>Total: {total}</span>
          <span>To Do: {todo}</span>
          <span>In Progress: {inProgress}</span>
          <span>Done: {done}</span>
        </div>
      </header>

      {/* Create task form */}
      <section className="bg-white rounded-xl shadow p-4 space-y-3">
        <h2 className="text-lg font-semibold">Create a new task</h2>

        <form
          onSubmit={handleCreateTask}
          className="grid grid-cols-1 md:grid-cols-5 gap-3 items-end"
        >
          {/* Title */}
          <div className="flex flex-col">
            <label className="text-sm font-medium mb-1">Title</label>
            <input
              className="w-full border rounded-lg px-3 py-2 text-sm"
              value={newTaskTitle}
              onChange={(e) => setNewTaskTitle(e.target.value)}
            />
          </div>

          {/* Status */}
          <div className="flex flex-col">
            <label className="text-sm font-medium mb-1">Status</label>
            <select
              className="w-full border rounded-lg px-3 py-2 text-sm"
              value={newTaskStatus}
              onChange={(e) => setNewTaskStatus(e.target.value)}
            >
              <option value="todo">To Do</option>
              <option value="in_progress">In Progress</option>
              <option value="done">Done</option>
            </select>
          </div>

          {/* Assignee */}
          <div className="flex flex-col">
            <label className="text-sm font-medium mb-1">Assignee</label>
            <input
              className="w-full border rounded-lg px-3 py-2 text-sm"
              value={newTaskAssignee}
              onChange={(e) => setNewTaskAssignee(e.target.value)}
            />
          </div>

          {/* Due date */}
          <div className="flex flex-col">
            <label className="text-sm font-medium mb-1">Due date</label>
            <input
              className="w-full border rounded-lg px-3 py-2 text-sm"
              type="date"
              value={newTaskDue}
              onChange={(e) => setNewTaskDue(e.target.value)}
            />
          </div>

          {/* Submit */}
          <button
            type="submit"
            className="mt-1 md:mt-6 inline-flex items-center px-4 py-2 rounded-lg text-sm font-semibold border bg-gray-900 text-white"
          >
            Create task
          </button>
        </form>
      </section>

      {/* Task list */}
      <section>
        {tasks.length === 0 ? (
          <p className="text-sm text-gray-500">
            No tasks yet — create one above.
          </p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {tasks.map((t) => (
              <TaskCard
                key={t.id}
                task={t}
                onDelete={() => handleDeleteTask(t.id)}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
