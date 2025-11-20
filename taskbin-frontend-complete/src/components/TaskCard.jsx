export default function TaskCard({ task }) {
  return (
    <div className="p-4 bg-white rounded-lg shadow">
      <h2 className="font-semibold">{task.title}</h2>
      <p className="text-sm text-gray-500">Status: {task.status}</p>
      {task.due && (
        <p className="text-xs text-gray-500 mt-1">Due: {task.due}</p>
      )}
      {task.assignee && (
        <p className="text-xs text-gray-600">Assigned: {task.assignee}</p>
      )}
    </div>
  );
}
