'use client'

import { useState, useEffect } from 'react'

interface StreamingTextProps {
  text: string
  speed?: number // milliseconds per character
  onComplete?: () => void
}

export function StreamingText({ text, speed = 15, onComplete }: StreamingTextProps) {
  const [displayedText, setDisplayedText] = useState('')
  const [currentIndex, setCurrentIndex] = useState(0)

  useEffect(() => {
    // Reset when text changes
    setDisplayedText('')
    setCurrentIndex(0)
  }, [text])

  useEffect(() => {
    if (currentIndex < text.length) {
      const timeout = setTimeout(() => {
        setDisplayedText(text.slice(0, currentIndex + 1))
        setCurrentIndex(currentIndex + 1)
      }, speed)

      return () => clearTimeout(timeout)
    } else if (currentIndex === text.length && onComplete) {
      onComplete()
    }
  }, [currentIndex, text, speed, onComplete])

  return (
    <span className="whitespace-pre-wrap">
      {displayedText}
      {currentIndex < text.length && (
        <span className="inline-block w-[2px] h-[1em] ml-[1px] bg-current animate-pulse" />
      )}
    </span>
  )
}

export default StreamingText
