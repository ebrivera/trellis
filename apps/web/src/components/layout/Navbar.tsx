'use client'

import Link from 'next/link'

export default function Navbar() {
  return (
    <div className="fixed left-0 right-0 z-50 flex justify-center px-6 top-6">
      <nav className="w-full h-16 max-w-5xl border shadow-2xl rounded-3xl bg-white/10 backdrop-blur-xl border-white/20 shadow-black/10">
        <div className="flex items-center justify-between h-full gap-8 px-6">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 shrink-0">
            <span className="hidden text-lg font-semibold text-white sm:block">trellis.</span>
          </Link>

          {/* Nav Items */}
          <div className="flex items-center justify-center flex-1 gap-1 sm:gap-2">
            <NavLink href="/">dashboard.</NavLink>
            <NavLink href="/goals">goals.</NavLink>
            <NavLink href="/approvals">approvals.</NavLink>
          </div>

          {/* Profile */}
          <button className="flex items-center justify-center w-10 h-10 font-medium text-white transition-transform rounded-full shrink-0 hover:scale-105">
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
              />
            </svg>
          </button>
        </div>
      </nav>
    </div>
  )
}

function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className="px-3 py-2 text-sm font-medium text-white transition-colors rounded-lg sm:px-4 sm:text-base hover:bg-white/10"
    >
      {children}
    </Link>
  )
}
