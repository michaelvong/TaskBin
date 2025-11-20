import { useLocation, useParams, Link } from "react-router-dom";
import { useApi } from "../hooks/useApi";
import { useEffect, useState } from "react";
import TaskCard from "../components/TaskCard";

export default function Board() {
  const { id } = useParams();
  const location = useLocation();
  const api = useApi();

  const [board, setBoard] = useState(location.state?.board || null);
  const [tasks, setTasks] = useState([]);

  const [newTaskTitle, setNewTaskTitle] = useState("");
  const [newTaskStatus, setNewTaskStatus] = useState("todo");
  const [newTaskAssignee, setNewTaskAssignee] = useState("");
  const [newTaskDue, setNewTaskDue] = useState("");

  useEffect(() => {
    api.listBoardTasks(id).then(setTasks).catch(console.error);
  }, [id]);

  async function handleCreateTask(e) {
    e.preventDefault();
    if (!newTaskTitle.trim()) return;

    await api.createTask(id, {
      title: newTaskTitle.trim(),
      description: "",
      status: newTaskStatus,
      assignee: newTaskAssignee || null,
      due: newTaskDue ? new Date(newTaskDue).toISOString() : null,
    });

    setNewTaskTitle("");
    setNewTaskStatus("todo");
    setNewTaskAssignee("");
    setNewTaskDue("");

    const refreshed = await api.listBoardTasks(id);
    setTasks(refreshed);
  }

  async function handleDeleteTask(taskId) {
    try {
      await api.deleteTask(id, taskId);
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
              type="text"
              className="border rounded-lg px-3 py-2 text-sm"
              placeholder="Task title"
              value={newTaskTitle}
              onChange={(e) => setNewTaskTitle(e.target.value)}
            />
          </div>

          {/* Status */}
          <div className="flex flex-col">
            <label className="text-sm font-medium mb-1">Status</label>
            <select
              className="border rounded-lg px-3 py-2 text-sm"
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
              type="text"
              className="border rounded-lg px-3 py-2 text-sm"
              placeholder="Email or name"
              value={newTaskAssignee}
              onChange={(e) => setNewTaskAssignee(e.target.value)}
            />
          </div>

          {/* Due date */}
          <div className="flex flex-col">
            <label className="text-sm font-medium mb-1">Due date</label>
            <input
              type="date"
              className="border rounded-lg px-3 py-2 text-sm"
              value={newTaskDue}
              onChange={(e) => setNewTaskDue(e.target.value)}
            />
          </div>

          {/* Submit button */}
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
              <TaskCard key={t.id} task={{ ...t, onDelete: handleDeleteTask }} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
