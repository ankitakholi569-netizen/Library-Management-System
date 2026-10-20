import React from 'react';

const faqs = [
  { q: 'How do I register as a student?', a: 'Click the Student Login button and use the Register link.' },
  { q: 'Can staff view other staff members?', a: 'No, staff only see their own profile and assigned classes.' },
  { q: 'How is my data secured?', a: 'All passwords are hashed with bcrypt and API calls require JWT tokens.' },
];

export default function FAQ() {
  return (
    <section className="py-12 bg-gray-100" id="faq">
      <h2 className="text-3xl font-bold text-center mb-8">Frequently Asked Questions</h2>
      <div className="max-w-3xl mx-auto space-y-6">
        {faqs.map((item, idx) => (
          <details key={idx} className="bg-white p-4 rounded shadow">
            <summary className="font-medium cursor-pointer">{item.q}</summary>
            <p className="mt-2 text-gray-700">{item.a}</p>
          </details>
        ))}
      </div>
    </section>
  );
}

