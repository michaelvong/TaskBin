export default function TaskCard({ task }) {
  // Normalize status for styling + display
  const normalized = task.status?.toLowerCase().replace(/[-\s]/g, "_");

  const statusColors = {
    todo: "bg-gray-200 text-gray-700",
    in_progress: "bg-amber-300 text-amber-900",
    done: "bg-green-200 text-green-700",
  };

  const color = statusColors[normalized] || "bg-gray-200 text-gray-700";

  const formattedDue = task.due
    ? new Date(task.due).toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
      })
    : null;

  return (
    <div className="p-4 bg-white rounded-xl shadow hover:shadow-md transition">
      {/* Title + Delete + Status */}
      <div className="flex items-center justify-between gap-2 mb-2">
        <h2 className="font-semibold text-sm flex-1 truncate">{task.title}</h2>

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
      {task.assignee && (
        <p className="text-xs text-gray-600">Assigned: {task.assignee}</p>
      )}
    </div>
  );
}
