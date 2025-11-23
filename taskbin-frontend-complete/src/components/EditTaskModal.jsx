import { useState, useEffect } from "react";

export default function EditTaskModal({ task, onSave, onClose }) {
  const [title, setTitle] = useState("");
  const [status, setStatus] = useState("todo");
  const [assignee, setAssignee] = useState("");
  const [finishBy, setFinishBy] = useState("");

  useEffect(() => {
    if (!task) return;

    setTitle(task.title || "");
    setStatus(task.task_status || "todo");
    setAssignee(task.assigned_to || "");
    setFinishBy(task.finish_by ? task.finish_by.substring(0, 10) : "");
  }, [task]);

  function handleSubmit(e) {
    e.preventDefault();
    onSave({
    task_id: task.id,     // 🔥 REQUIRED
    title,
    task_status: status,
    assigned_to: assignee || null,
    finish_by: finishBy ? new Date(finishBy).toISOString() : null,
    });
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center">
      <div className="bg-white p-6 rounded-xl w-full max-w-md space-y-4">
        <h2 className="text-xl font-bold">Edit Task</h2>

        <form className="space-y-3" onSubmit={handleSubmit}>
          <div>
            <label>Title</label>
            <input
              className="border p-2 rounded w-full"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          <div>
            <label>Status</label>
            <select
              className="border p-2 rounded w-full"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
            >
              <option value="todo">Todo</option>
              <option value="in_progress">In Progress</option>
              <option value="done">Done</option>
            </select>
          </div>

          <div>
            <label>Assignee</label>
            <input
              className="border p-2 rounded w-full"
              value={assignee}
              onChange={(e) => setAssignee(e.target.value)}
            />
          </div>

          <div>
            <label>Due date</label>
            <input
              type="date"
              className="border p-2 rounded w-full"
              value={finishBy}
              onChange={(e) => setFinishBy(e.target.value)}
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              onClick={onClose}
              type="button"
              className="px-4 py-2 bg-gray-200 rounded-md"
            >
              Cancel
            </button>
            <button
              className="px-4 py-2 bg-black text-white rounded-md"
              type="submit"
            >
              Save
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
