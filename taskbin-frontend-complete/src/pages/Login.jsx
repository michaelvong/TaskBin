import { useAuth } from "../hooks/useAuth";

export default function Login() {
  const { signIn } = useAuth();

  return (
    <div className="h-screen flex items-center justify-center bg-gray-100">
      <div className="p-6 bg-white shadow rounded-xl w-80">
        <h1 className="text-2xl font-bold mb-4">TaskBin Login</h1>
        <p className="text-sm text-gray-600 mb-4">
          This demo uses a mock login. Click below to continue.
        </p>
        <button
          className="bg-blue-600 text-white p-2 w-full rounded"
          onClick={() => signIn()}
        >
          Continue
        </button>
      </div>
    </div>
  );
}
