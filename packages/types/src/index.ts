// Common types shared across the monorepo

export interface User {
  id: string
  email: string
  name: string
  createdAt: Date
  updatedAt: Date
}

export interface ApiResponse<T> {
  data: T
  message: string
  success: boolean
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  pagination: {
    page: number
    limit: number
    total: number
    totalPages: number
  }
}

export type Theme = 'light' | 'dark' | 'system'

export interface ComponentProps {
  className?: string
  children?: React.ReactNode
}
