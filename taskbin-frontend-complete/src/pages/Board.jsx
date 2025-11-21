import { useParams, useLocation, Link } from "react-router-dom";
import { useApi } from "../hooks/useApi";
import { useState, useEffect } from "react";
import TaskCard from "../components/TaskCard";

export default function Board() {
  const { id } = useParams();
  const { state } = useLocation();
  const api = useApi();

  const [board] = useState(state?.board || null);
  const [tasks, setTasks] = useState([]);
  const [newTitle, setNewTitle] = useState("");
  const [newStatus, setNewStatus] = useState("todo");

  // -----------------------------
  // Load tasks (AWS or MOCK)
  // -----------------------------
  async function loadTasks() {
    try {
      const result = await api.listTasks(id);
      const arr = Array.isArray(result)
        ? result
        : (result?.tasks || []);
      setTasks(arr);
    } catch (err) {
      console.error("Failed to load tasks:", err);
      setTasks([]);
    }
  }

  useEffect(() => {
    loadTasks();
  }, [id]);

  // -----------------------------
  // Create task
  // -----------------------------
  async function createTask(e) {
    e.preventDefault();
    if (!newTitle.trim()) return;

    await api.createTask(id, {
      title: newTitle,
      status: newStatus,
      description: "",
      finish_by: null,
    });

    await loadTasks();
    setNewTitle("");
    setNewStatus("todo");
  }

  // -----------------------------
  // Delete task
  // -----------------------------
  async function deleteTask(taskId) {
    await api.deleteTask(id, taskId);
    setTasks((prev) => prev.filter((t) => t.id !== taskId));
  }

  return (
    <div className="max-w-5xl mx-auto p-4 space-y-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <Link to="/" className="text-blue-600 text-sm hover:underline">
          ← Back to boards
        </Link>
        <h1 className="text-2xl font-bold">{board?.name || "Board"}</h1>
      </div>

      {/* Create Task */}
      <section className="bg-white rounded-xl shadow p-4 space-y-3">
        <h2 className="font-semibold text-lg">Create a Task</h2>

        <form onSubmit={createTask} className="space-y-3">
          <input
            className="w-full border rounded-lg px-3 py-2 text-sm"
            placeholder="Task title"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
          />

          <select
            className="w-full border rounded-lg px-3 py-2 text-sm"
            value={newStatus}
            onChange={(e) => setNewStatus(e.target.value)}
          >
            <option value="todo">To Do</option>
            <option value="in_progress">In Progress</option>
            <option value="done">Done</option>
          </select>

          <button className="px-4 py-2 bg-gray-900 text-white rounded-lg text-sm">
            Create Task
          </button>
        </form>
      </section>

      {/* Tasks */}
      <section>
        {tasks.length === 0 ? (
          <p className="text-sm text-gray-500">No tasks yet. Create one above.</p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {tasks.map((t) => (
              <TaskCard key={t.id} task={{ ...t, onDelete: deleteTask }} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
