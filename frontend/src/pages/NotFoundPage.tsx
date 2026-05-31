import { Link } from "react-router-dom";

export function NotFoundPage(): JSX.Element {
  return (
    <div className="space-y-3 p-6">
      <h1 className="text-xl font-semibold">Page not found</h1>
      <Link className="text-blue-700 underline" to="/cases">
        Go to cases
      </Link>
    </div>
  );
}
