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
  const [newTaskStatus, setNewTaskStatus] = useState("todo");
  const [newTaskAssignee, setNewTaskAssignee] = useState("");
  const [newTaskDue, setNewTaskDue] = useState(""); // e.g. "2025-11-20"


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
        status: newTaskStatus,                     // 👈 from state
        assignee: newTaskAssignee || null,        // 👈 null if empty
        due: newTaskDue ? new Date(newTaskDue).toISOString() : null,
      });

      // reset form fields
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
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-4">
        {board?.name || "Board"}
      </h1>
      <form onSubmit={handleCreateTask}>
        <input
          type="text"
          placeholder="Task title"
          value={newTaskTitle}
          onChange={(e) => setNewTaskTitle(e.target.value)}
        />

        <select
          value={newTaskStatus}
          onChange={(e) => setNewTaskStatus(e.target.value)}
        >
          <option value="todo">To Do</option>
          <option value="in_progress">In Progress</option>
          <option value="done">Done</option>
        </select>

        <input
          type="text"
          placeholder="Assignee (email or name)"
          value={newTaskAssignee}
          onChange={(e) => setNewTaskAssignee(e.target.value)}
        />

        <input
          type="date"
          value={newTaskDue}
          onChange={(e) => setNewTaskDue(e.target.value)}
        />

        <button type="submit">Create task</button>
      </form>
      <div className="grid grid-cols-3 gap-4">
        {tasks.map((t) => (
          <TaskCard key={t.id} task={t} />
        ))}
      </div>
    </div>
  );
}
