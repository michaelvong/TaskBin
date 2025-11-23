import { Link, useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { useApi } from "../hooks/useApi";
import { useAuth } from "../hooks/useAuth";
import TaskCard from "../components/TaskCard";
import EditTaskModal from "../components/EditTaskModal";

export default function Board() {
  const { id } = useParams();
  const { user } = useAuth();
  const api = useApi(user?.email);

  const [board, setBoard] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [members, setMembers] = useState([]);
  const [owner, setOwner] = useState(null);


  // create task form state
  const [newTaskTitle, setNewTaskTitle] = useState("");
  const [newTaskStatus, setNewTaskStatus] = useState("todo");
  const [newTaskAssignee, setNewTaskAssignee] = useState("");
  const [newTaskDue, setNewTaskDue] = useState("");

  // edit modal state
  const [editingTask, setEditingTask] = useState(null);

  // load board metadata + tasks
  useEffect(() => {
    if (!user?.email) return;

    async function init() {
      try {
        const meta = await api.getBoard(id);
        setBoard(meta);
        setMembers(meta?.members || []);
        setOwner(meta?.owner_id || null);
        
        const ts = await api.listTasks(id);
        const normalized = ts.map((t) => ({
          ...t,
          id: t.task_id, // normalize
        }));
        setTasks(normalized);
      } catch (err) {
        console.error("Failed loading board or tasks:", err);
      }
    }

    init();
  }, [id, user?.email]);

  // -------------------------------
  // GENERATE ACCESS CODE
  // -------------------------------
  async function handleGenerateCode() {
    try {
      const res = await api.generateCode(id);

      const code = res?.access_code;
      if (!code) {
        alert("Failed to generate code — backend returned no access_code");
        return;
      }
      alert(`Access Code for this board: ${code}`);

    } catch (err) {
      console.error("Error generating code:", err);
      alert("Failed to generate access code.");
    }
  }


  // -------------------------------
  // CREATE TASK
  // -------------------------------
  async function handleCreateTask(e) {
    e.preventDefault();
    if (!newTaskTitle.trim()) return;

    await api.createTask(id, {
      title: newTaskTitle.trim(),
      description: "",
      task_status: newTaskStatus,
      assignee_id: newTaskAssignee || null,
      finish_by: newTaskDue ? new Date(newTaskDue).toISOString() : null,
    });

    // reset form
    setNewTaskTitle("");
    setNewTaskStatus("todo");
    setNewTaskAssignee("");
    setNewTaskDue("");

    // refresh tasks
    const refreshed = await api.listTasks(id);
    setTasks(refreshed.map((t) => ({ ...t, id: t.id || t.task_id })));
  }

  // -------------------------------
  // DELETE TASK
  // -------------------------------
  async function handleDeleteTask(taskId) {
    await api.deleteTask(id, taskId);
    setTasks((prev) => prev.filter((t) => (t.id || t.task_id) !== taskId));
  }

  // -------------------------------
  // EDIT TASK
  // -------------------------------
  async function handleEditTask(taskId, updates) {
    await api.editTask(taskId, updates);

    const refreshed = await api.listTasks(id);
    setTasks(refreshed.map((t) => ({ ...t, id: t.id || t.task_id })));

    setEditingTask(null);
  }

  // -------------------------------
  // RENDER
  // -------------------------------
  return (
    <div className="max-w-5xl mx-auto p-4 space-y-6">
      <Link to="/" className="text-sm text-blue-600 hover:underline">
        ← Back
      </Link>

      <header className="space-y-1 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{board?.name || "Board"}</h1>
          {board?.description && (
            <p className="text-sm text-gray-500">{board.description}</p>
          )}
        </div>

        {/* 🔥 Generate Access Code Button */}
        <button
          onClick={handleGenerateCode}
          className="bg-purple-600 text-white px-3 py-2 rounded-lg shadow hover:bg-purple-700 transition"
        >
          Generate Access Code
        </button>
      </header>

      {/* MEMBERS LIST */}
      <section className="bg-white rounded-xl shadow p-4 space-y-3">
        <h2 className="text-lg font-semibold">Members</h2>

        {/* OWNER */}
        <div>
          <p className="text-sm font-semibold mb-1">Owner</p>
          <div className="bg-purple-50 px-3 py-2 rounded-lg flex justify-between">
            <span>{owner}</span>
            <span className="px-2 py-1 text-xs bg-purple-200 text-purple-800 rounded-full">
              owner
            </span>
          </div>
        </div>

        {/* MEMBERS */}
        <div>
          <p className="text-sm font-semibold mt-3 mb-1">Members</p>

          {members.filter((m) => m.user_id !== owner).length === 0 ? (
            <p className="text-sm text-gray-500">No other members.</p>
          ) : (
            <ul className="space-y-1 text-sm">
              {members
                .filter((m) => m.user_id !== owner)
                .map((m) => (
                  <li
                    key={m.user_id}
                    className="flex justify-between bg-gray-50 px-3 py-2 rounded-lg"
                  >
                    <span>{m.user_id}</span>
                    <span className="px-2 py-1 text-xs bg-gray-200 text-gray-600 rounded-full">
                      member
                    </span>
                  </li>
                ))}
            </ul>
          )}
        </div>
      </section>

      {/* CREATE TASK */}
      <section className="bg-white rounded-xl shadow p-4 space-y-3">
        <h2 className="text-lg font-semibold">Create a new task</h2>

        <form
          onSubmit={handleCreateTask}
          className="grid grid-cols-1 md:grid-cols-5 gap-3 items-end"
        >
          <div className="flex flex-col">
            <label>Title</label>
            <input
              className="border p-2 rounded"
              value={newTaskTitle}
              onChange={(e) => setNewTaskTitle(e.target.value)}
            />
          </div>

          <div className="flex flex-col">
            <label>Status</label>
            <select
              className="border p-2 rounded"
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
            <input
              className="border p-2 rounded"
              value={newTaskAssignee}
              onChange={(e) => setNewTaskAssignee(e.target.value)}
            />
          </div>

          <div className="flex flex-col">
            <label>Due date</label>
            <input
              type="date"
              className="border p-2 rounded"
              value={newTaskDue}
              onChange={(e) => setNewTaskDue(e.target.value)}
            />
          </div>

          <button className="bg-black text-white px-4 py-2 rounded-lg">
            Create Task
          </button>
        </form>
      </section>

      {/* TASK LIST */}
      <section>
        {tasks.length === 0 ? (
          <p>No tasks yet.</p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {tasks.map((t) => (
              <TaskCard
                key={t.id}
                task={{
                  ...t,
                  task_id: t.id,
                  onDelete: () => handleDeleteTask(t.id),
                  onEdit: () => setEditingTask(t),
                }}
              />
            ))}
          </div>
        )}
      </section>

      {/* EDIT MODAL */}
      {editingTask && (
        <EditTaskModal
          task={editingTask}
          onSave={(updates) => handleEditTask(editingTask.id, updates)}
          onClose={() => setEditingTask(null)}
        />
      )}
    </div>
  );
}
