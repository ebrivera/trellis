import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import Plasma from '../components/layout/Background'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Trellis',
  description: 'A modern web application',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Plasma />
        {children}
      </body>
    </html>
  )
}
