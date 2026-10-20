export default function Footer() {
  return (
    <footer className="bg-gray-800 text-gray-200 py-8">
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-4 text-center md:text-left">
        <div>
          <h4 className="font-bold mb-2">Quick Links</h4>
          <ul>
            <li><a href="#about" className="hover:underline">About</a></li>
            <li><a href="#features" className="hover:underline">Features</a></li>
            <li><a href="#contact" className="hover:underline">Contact</a></li>
          </ul>
        </div>
        <div>
          <h4 className="font-bold mb-2">Contact</h4>
          <p>info@institution.edu</p>
          <p>+1‑234‑567‑890</p>
        </div>
        <div className="flex justify-center space-x-4">
          <a href="#" aria-label="Twitter" className="hover:text-primaryBlue">🐦</a>
          <a href="#" aria-label="LinkedIn" className="hover:text-primaryBlue">🔗</a>
        </div>
      </div>
      <p className="mt-4 text-center text-sm">© 2026 Institution Portal. All rights reserved.</p>
    </footer>
  );
}

