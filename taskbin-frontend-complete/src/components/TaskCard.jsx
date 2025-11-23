export default function TaskCard({ task }) {
  console.log("TaskCard debug:", {
    id: task?.id,
    title: task?.title,
    raw_status: task?.task_status,
    full_task: task
  });

  const rawStatus =
    task?.task_status ??
    task?.full_task?.task_status ??
    null;

  const normalized = rawStatus
    ? rawStatus.toLowerCase().replace(/[-\s]/g, "_")
    : "unknown";


  const statusColors = {
    todo: "bg-gray-200 text-gray-700",
    in_progress: "bg-amber-300 text-amber-900",
    done: "bg-green-200 text-green-700",
  };

  const color = statusColors[normalized] || "bg-gray-200 text-gray-700";

  const formattedDue = task.finish_by
    ? new Date(task.finish_by).toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
      })
    : null;

  return (
    <div className="p-4 bg-white rounded-xl shadow hover:shadow-md transition">
      <div className="flex items-center justify-between gap-2 mb-2">
        <h2 className="font-semibold text-sm flex-1 truncate">{task.title}</h2>

        {/* Edit */}
        <button
          className="text-blue-600 text-sm"
          onClick={task.onEdit}
        >
          Edit
        </button>

        {/* Delete */}
        <button
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            if (confirm("Delete this task?")) task.onDelete?.(task.id);
          }}
          className="text-[11px] px-2 py-0.5 rounded-full bg-red-50 text-red-500 hover:bg-red-100 hover:text-red-600 transition font-medium"
        >
          Delete
        </button>

        {/* Status badge */}
        <span
          className={`text-[11px] px-2 py-0.5 rounded-full font-medium whitespace-nowrap ${color}`}
        >
          {normalized.replace("_", " ")}
        </span>
      </div>

      {/* Due date */}
      {formattedDue && (
        <p className="text-xs text-gray-500 mb-1">Due: {formattedDue}</p>
      )}

      {/* Assignee */}
      {task.assignee_id && (
        <p className="text-xs text-gray-600">Assigned: {task.assignee_id}</p>
      )}
    </div>
  );
}
