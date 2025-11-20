import { useLocation, useParams } from "react-router-dom";
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
    api
      .listBoardTasks(id)
      .then(setTasks)
      .catch(console.error);
  }, [id]);

  async function handleCreateTask(e) {
    e.preventDefault();
    if (!newTaskTitle.trim()) return;

    try {
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
    } catch (err) {
      console.error("Failed to create task:", err);
    }
  }

  return (
    <div className="max-w-5xl mx-auto p-4 space-y-6">
      {/* Header */}
      <header className="mb-2">
        <h1 className="text-2xl font-bold">{board?.name || "Board"}</h1>
        {board?.description && (
          <p className="text-sm text-gray-500 mt-1">{board.description}</p>
        )}
      </header>

      {/* Create task form */}
      <section className="bg-white rounded-xl shadow p-4 space-y-3">
        <h2 className="text-lg font-semibold">Create a new task</h2>
        <form
          onSubmit={handleCreateTask}
          className="grid grid-cols-1 md:grid-cols-5 gap-3 items-end"
        >
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

          <div className="flex flex-col">
            <label className="text-sm font-medium mb-1">Due date</label>
            <input
              type="date"
              className="border rounded-lg px-3 py-2 text-sm"
              value={newTaskDue}
              onChange={(e) => setNewTaskDue(e.target.value)}
            />
          </div>

          <button
            type="submit"
            className="mt-1 md:mt-6 inline-flex items-center px-4 py-2 rounded-lg text-sm font-semibold border bg-gray-900 text-white disabled:opacity-60"
          >
            Create task
          </button>
        </form>
      </section>

      {/* Task list */}
      <section>
        {tasks.length === 0 ? (
          <p className="text-sm text-gray-500">No tasks yet — create one above.</p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {tasks.map((t) => (
              <TaskCard key={t.id} task={t} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
