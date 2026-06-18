import { useRef } from 'react'

interface ResizerProps {
  value: number
  onChange: (newValue: number) => void
  min?: number
  max?: number
}

export default function Resizer({ value, onChange, min = 0, max = Infinity }: ResizerProps) {
  const dragStart = useRef<{ x: number; width: number } | null>(null)

  const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    dragStart.current = { x: e.clientX, width: value }
    e.currentTarget.setPointerCapture(e.pointerId)
  }

  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!dragStart.current) return
    const { x, width } = dragStart.current
    const deltaX = e.clientX - x
    onChange(Math.max(min, Math.min(max, width + deltaX)))
  }

  const handlePointerUp = (e: React.PointerEvent<HTMLDivElement>) => {
    dragStart.current = null
    e.currentTarget.releasePointerCapture(e.pointerId)
  }

  return (
    <div
      className="resizer"
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerUp}
    />
  )
}
