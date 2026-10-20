import { Link } from 'react-router-dom';

export default function RoleCard({ role, color, description, loginPath }) {
  // The colour prop matches Tailwind colour names (primaryBlue, primaryGreen, primaryPurple)
  const bgClass = `bg-${color}-100`;
  const textClass = `text-${color}-800`;
  const btnClass = `bg-${color}-600 hover:bg-${color}-700`;
  return (
    <div className={`${bgClass} ${textClass} p-6 rounded-lg shadow text-center`}>
      <h3 className="text-2xl font-bold mb-2">{role}</h3>
      <p className="mb-4">{description}</p>
      <Link
        to={loginPath}
        className={`inline-block px-4 py-2 ${btnClass} text-white rounded transition`}
      >
        {role} Login
      </Link>
    </div>
  );
}

