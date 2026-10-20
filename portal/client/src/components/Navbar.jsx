import { Link } from 'react-router-dom';
import { useState } from 'react';

export default function Navbar() {
  const [open, setOpen] = useState(false);
  return (
    <nav className="sticky top-0 bg-white shadow-md z-10">
      <div className="max-w-7xl mx-auto flex items-center justify-between p-4">
        <Link to="/" className="text-2xl font-bold text-primaryBlue">
          InstitutionPortal
        </Link>
        <ul className="hidden md:flex space-x-6">
          <li><Link to="/">Home</Link></li>
          <li><a href="#about">About</a></li>
          <li><a href="#features">Features</a></li>
          <li><a href="#contact">Contact</a></li>
          <li className="relative">
            <button onClick={() => setOpen(!open)} className="font-medium">
              Login ▼
            </button>
            {open && (
              <ul className="absolute top-full mt-1 bg-white border rounded shadow-lg">
                <li><Link to="/login/student" className="block px-4 py-2">Student Login</Link></li>
                <li><Link to="/login/staff" className="block px-4 py-2">Staff Login</Link></li>
                <li><Link to="/login/admin" className="block px-4 py-2">Admin Login</Link></li>
              </ul>
            )}
          </li>
        </ul>
        <button className="md:hidden" onClick={() => setOpen(!open)}>
          ☰
        </button>
      </div>
    </nav>
  );
}

