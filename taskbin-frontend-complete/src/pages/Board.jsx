import { Link, useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { useApi } from "../hooks/useApi";
import { useAuth } from "../hooks/useAuth";
import TaskCard from "../components/TaskCard";

export default function Board() {
  const { id } = useParams();
  const { user } = useAuth();
  const api = useApi(user?.email);

  const [board, setBoard] = useState(null);
  const [tasks, setTasks] = useState([]);

  const [newTaskTitle, setNewTaskTitle] = useState("");
  const [newTaskStatus, setNewTaskStatus] = useState("todo");
  const [newTaskAssignee, setNewTaskAssignee] = useState("");
  const [newTaskDue, setNewTaskDue] = useState("");

  useEffect(() => {
    if (!user?.email) return;

    api.getBoard(id).then(setBoard).catch(console.error);
    api.listTasks(id).then((ts) => {
      // normalize IDs (task_id → id)
      const normalized = ts.map((t) => ({
        ...t,
        id: t.id || t.task_id
      }));
      setTasks(normalized);
    });
  }, [id, user?.email]);

  async function handleCreateTask(e) {
    e.preventDefault();
    if (!newTaskTitle.trim()) return;

    await api.createTask(id, {
      title: newTaskTitle.trim(),
      description: "",
      status: newTaskStatus,
      assignee_id: newTaskAssignee || null,
      finish_by: newTaskDue ? new Date(newTaskDue).toISOString() : null,
    });

    setNewTaskTitle("");
    setNewTaskStatus("todo");
    setNewTaskAssignee("");
    setNewTaskDue("");

    const refreshed = await api.listTasks(id);
    setTasks(refreshed.map((t) => ({ ...t, id: t.id || t.task_id })));
  }

  async function handleDeleteTask(taskId) {
    await api.deleteTask(id, taskId);
    setTasks((prev) => prev.filter((t) => (t.id || t.task_id) !== taskId));
  }

  return (
    <div className="max-w-5xl mx-auto p-4 space-y-6">
      <Link to="/" className="text-sm text-blue-600 hover:underline">← Back</Link>

      <header className="space-y-1">
        <h1 className="text-2xl font-bold">{board?.name || "Board"}</h1>
        {board?.description && (
          <p className="text-sm text-gray-500">{board.description}</p>
        )}
      </header>

      {/* CREATE TASK FORM */}
      <section className="bg-white rounded-xl shadow p-4 space-y-3">
        <h2 className="text-lg font-semibold">Create a new task</h2>

        <form
          onSubmit={handleCreateTask}
          className="grid grid-cols-1 md:grid-cols-5 gap-3 items-end"
        >
          <div className="flex flex-col">
            <label>Title</label>
            <input className="border p-2 rounded"
              value={newTaskTitle}
              onChange={(e) => setNewTaskTitle(e.target.value)}
            />
          </div>

          <div className="flex flex-col">
            <label>Status</label>
            <select className="border p-2 rounded"
              value={newTaskStatus}
              onChange={(e) => setNewTaskStatus(e.target.value)}
            >
              <option value="todo">Todo</option>
              <option value="in_progress">In Progress</option>
              <option value="done">Done</option>
            </select>
          </div>

          <div className="flex flex-col">
            <label>Assignee</label>
            <input className="border p-2 rounded"
              value={newTaskAssignee}
              onChange={(e) => setNewTaskAssignee(e.target.value)}
            />
          </div>

          <div className="flex flex-col">
            <label>Due date</label>
            <input type="date" className="border p-2 rounded"
              value={newTaskDue}
              onChange={(e) => setNewTaskDue(e.target.value)}
            />
          </div>

          <button className="bg-black text-white px-4 py-2 rounded-lg">
            Create Task
          </button>
        </form>
      </section>

      <section>
        {tasks.length === 0 ? (
          <p>No tasks yet.</p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {tasks.map((t) => (
              <TaskCard
                key={t.id}
                task={{ ...t, onDelete: () => handleDeleteTask(t.id) }}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
