'use client'

import Link from 'next/link'
import { useState } from 'react'

export default function Navbar() {
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

    return (
        <div className="fixed left-0 right-0 z-50 flex justify-center px-6 top-6">
            <nav className="relative w-full max-w-5xl">
                <div className="border shadow-2xl rounded-3xl bg-white/10 backdrop-blur-xl border-white/20 shadow-black/10">
                    <div className="flex items-center justify-between h-16 gap-4 px-6">
                        {/* Logo */}
                        <Link href="/" className="flex items-center gap-2 shrink-0">
                            <span className="text-lg font-semibold text-white">trellis.</span>
                        </Link>

                        {/* Nav Items - Desktop */}
                        <div className="items-center justify-center flex-1 hidden gap-1 md:flex sm:gap-2">
                            <NavLink href="/">dashboard.</NavLink>
                            <NavLink href="/goals">goals.</NavLink>
                            <NavLink href="/approvals">approvals.</NavLink>
                        </div>

                        <div className="flex items-center gap-3">
                            {/* Hamburger Menu - Mobile */}
                            <button
                                className="flex items-center justify-center w-10 h-10 text-white transition-transform rounded-lg md:hidden hover:bg-white/10"
                                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                                aria-label="Toggle menu"
                            >
                                {mobileMenuOpen ? (
                                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                    </svg>
                                ) : (
                                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                                    </svg>
                                )}
                            </button>

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
                    </div>

                    {/* Mobile Menu Dropdown */}
                    {mobileMenuOpen && (
                        <div className="border-t md:hidden border-white/20">
                            <div className="flex flex-col gap-1 p-4">
                                <MobileNavLink href="/" onClick={() => setMobileMenuOpen(false)}>
                                    dashboard.
                                </MobileNavLink>
                                <MobileNavLink href="/goals" onClick={() => setMobileMenuOpen(false)}>
                                    goals.
                                </MobileNavLink>
                                <MobileNavLink href="/approvals" onClick={() => setMobileMenuOpen(false)}>
                                    approvals.
                                </MobileNavLink>
                            </div>
                        </div>
                    )}
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

function MobileNavLink({ 
    href, 
    children, 
    onClick 
}: { 
    href: string
    children: React.ReactNode
    onClick: () => void 
}) {
    return (
        <Link
            href={href}
            onClick={onClick}
            className="px-4 py-3 text-base font-medium text-white transition-colors rounded-lg hover:bg-white/10"
        >
            {children}
        </Link>
    )
}
