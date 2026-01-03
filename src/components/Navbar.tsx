'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Navbar({ lang }: { lang: any }) {
  const pathname = usePathname();

  const navItems = [
    { name: lang.nav_downloader, href: '/downloader', icon: 'bi-cloud-download' },
    { name: lang.nav_tasks, href: '/tasks', icon: 'bi-list-task' },
    { name: lang.nav_settings, href: '/settings', icon: 'bi-gear' },
  ];

  return (
    <nav className="bg-slate-900 text-white shadow-lg">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-8">
            <Link href="/" className="text-xl font-bold flex items-center">
              <i className="bi bi-box-seam me-2"></i>
              {lang.app_title}
            </Link>
            <div className="hidden md:flex space-x-4">
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    pathname === item.href ? 'bg-blue-600 text-white' : 'hover:bg-slate-700'
                  }`}
                >
                  {item.name}
                </Link>
              ))}
            </div>
          </div>
          <div className="flex items-center">
            <button className="text-sm bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded-lg transition-all">
              {lang.nav_logout}
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
