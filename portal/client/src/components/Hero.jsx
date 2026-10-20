import React from 'react';

export default function Hero() {
  return (
    <section className="bg-gradient-to-r from-primaryBlue to-indigo-600 text-white text-center py-20 px-4">
      <h1 className="text-5xl font-bold mb-4">Welcome to Institution Portal</h1>
      <p className="text-xl mb-8">Your one‑stop hub for attendance, results, notices & more.</p>
      <div className="flex justify-center gap-4">
        <a href="#features" className="px-6 py-3 bg-white text-primaryBlue rounded shadow hover:opacity-90 transition">
          Get Started
        </a>
        <a href="#how-it-works" className="px-6 py-3 border border-white rounded hover:bg-white hover:text-primaryBlue transition">
          Learn More
        </a>
      </div>
    </section>
  );
}

