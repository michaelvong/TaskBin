import { useLocation, useParams } from "react-router-dom";
import { useApi } from "../hooks/useApi";
import { useEffect, useState } from "react";
import TaskCard from "../components/TaskCard";

export default function Board() {
  const { id } = useParams(); // boardId
  const location = useLocation();
  const api = useApi();

  const [board, setBoard] = useState(location.state?.board || null);
  const [tasks, setTasks] = useState([]);
  const [newTaskTitle, setNewTaskTitle] = useState("");

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
      const created = await api.createTask(id, {
        title: newTaskTitle.trim(),
        description: "",
        due: null,
        assignee: null,
        status: "todo",
      });
      // In mock mode, createTask returns full object; in real mode it returns ids only.
      // Easiest is to just refetch tasks after creation:
      setNewTaskTitle("");
      const refreshed = await api.listBoardTasks(id);
      setTasks(refreshed);
    } catch (err) {
      console.error("Failed to create task:", err);
    }
  }

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-4">
        {board?.name || "Board"}
      </h1>

      <form className="flex gap-2 mb-4" onSubmit={handleCreateTask}>
        <input
          className="border rounded px-3 py-2 flex-1"
          placeholder="New task title"
          value={newTaskTitle}
          onChange={(e) => setNewTaskTitle(e.target.value)}
        />
        <button className="bg-blue-600 text-white px-4 py-2 rounded">
          Add Task
        </button>
      </form>

      <div className="grid grid-cols-3 gap-4">
        {tasks.map((t) => (
          <TaskCard key={t.id} task={t} />
        ))}
      </div>
    </div>
  );
}
