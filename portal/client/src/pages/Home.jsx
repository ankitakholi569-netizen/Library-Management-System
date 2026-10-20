import React from 'react';
import { FaCalendarCheck, FaFileAlt, FaMoneyBillWave, FaUserShield } from 'react-icons/fa';
import Hero from '../components/Hero';
import FeatureCard from '../components/FeatureCard';
import RoleCard from '../components/RoleCard';
import StatsCounter from '../components/StatsCounter';
import FAQ from '../components/FAQ';

const features = [
  { icon: <FaCalendarCheck size={32} />, title: 'Attendance', desc: 'Real‑time check‑in' },
  { icon: <FaFileAlt size={32} />, title: 'Results', desc: 'Instant grade view' },
  { icon: <FaMoneyBillWave size={32} />, title: 'Fees', desc: 'Secure payment portal' },
  { icon: <FaUserShield size={32} />, title: 'Notices', desc: 'Important announcements' },
];

export default function Home() {
  return (
    <div>
      <Hero />
      {/* Features */}
      <section id="features" className="py-16 bg-gray-100">
        <h2 className="text-3xl font-bold text-center mb-8">Features</h2>
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((f, i) => (
            <FeatureCard key={i} icon={f.icon} title={f.title} description={f.desc} />
          ))}
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="py-16 text-center">
        <h2 className="text-3xl font-bold mb-8">How it works</h2>
        <ol className="flex flex-col md:flex-row justify-center items-start md:items-center gap-8">
          <li className="flex-1">
            <div className="text-4xl font-bold text-primaryBlue">1</div>
            <p>Register / Login</p>
          </li>
          <li className="flex-1">
            <div className="text-4xl font-bold text-primaryBlue">2</div>
            <p>View your personalised dashboard</p>
          </li>
          <li className="flex-1">
            <div className="text-4xl font-bold text-primaryBlue">3</div>
            <p>Interact – upload marks, pay fees, read notices</p>
          </li>
        </ol>
      </section>

      {/* Role cards */}
      <section id="roles" className="py-16 bg-gray-50">
        <h2 className="text-3xl font-bold text-center mb-8">Choose your role</h2>
        <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6">
          <RoleCard
            role="Student"
            color="primaryBlue"
            description="Access your courses, results and fees."
            loginPath="/login/student"
          />
          <RoleCard
            role="Staff"
            color="primaryGreen"
            description="Manage classes, attendance and marks."
            loginPath="/login/staff"
          />
          <RoleCard
            role="Admin"
            color="primaryPurple"
            description="Full control over the institution."
            loginPath="/login/admin"
          />
        </div>
      </section>

      {/* Stats counters */}
      <StatsCounter />

      {/* FAQ */}
      <FAQ />
    </div>
  );
}

