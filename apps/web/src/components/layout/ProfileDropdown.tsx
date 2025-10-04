'use client'

import { useState, useRef, useEffect } from 'react'
import Link from 'next/link'
import { User, Settings, LogOut } from 'lucide-react'

export function ProfileDropdown() {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-center w-10 h-10 font-medium text-white transition-transform rounded-full shrink-0 hover:scale-105"
      >
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

      {isOpen && (
        <div className="absolute right-[-1rem] z-[60] mt-4 overflow-hidden border shadow-2xl w-60 rounded-2xl bg-black/50 backdrop-blur-xl border-white/20 shadow-black/10">
          {/* User Info */}
          <div className="px-4 py-3 border-b border-white/20">
            <p className="font-semibold text-white">Pastor John</p>
            <p className="text-sm text-white/60">john@church.org</p>
          </div>

          {/* Menu Items */}
          <div className="py-2">
            <DropdownItem href="/profile" icon={<User className="w-4 h-4" />} onClick={() => setIsOpen(false)}>
              Profile
            </DropdownItem>
            <DropdownItem href="/settings" icon={<Settings className="w-4 h-4" />} onClick={() => setIsOpen(false)}>
              Settings
            </DropdownItem>
            <DropdownItem
              href="/"
              icon={<LogOut className="w-4 h-4" />}
              onClick={() => setIsOpen(false)}
              className="text-red-400 hover:bg-red-400/10"
            >
              Log Out
            </DropdownItem>
          </div>
        </div>
      )}
    </div>
  )
}

function DropdownItem({
  href,
  icon,
  children,
  onClick,
  className = '',
}: {
  href: string
  icon: React.ReactNode
  children: React.ReactNode
  onClick?: () => void
  className?: string
}) {
  return (
    <Link
      href={href}
      onClick={onClick}
      className={`flex items-center gap-3 px-4 py-2 text-sm text-white transition-colors hover:bg-white/10 ${className}`}
    >
      {icon}
      {children}
    </Link>
  )
}

export default ProfileDropdown

