import React from 'react';

export default function StatsCounter() {
  // Static demo numbers – replace with API call when backend is ready
  const stats = [
    { label: 'Students', value: 1240 },
    { label: 'Staff', value: 85 },
    { label: 'Courses', value: 32 },
  ];
  return (
    <section className="py-12 bg-white">
      <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
        {stats.map((s) => (
          <div key={s.label} className="p-4 border rounded shadow">
            <div className="text-4xl font-bold text-primaryBlue">{s.value}</div>
            <div className="mt-2 text-lg font-medium">{s.label}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

