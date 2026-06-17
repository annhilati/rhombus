import { useRef } from 'react'

interface ResizerProps {
  onResize: (deltaX: number) => void
}

export default function Resizer({ onResize }: ResizerProps) {
  const isResizing = useRef(false)
  const lastX = useRef(0)

  const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    isResizing.current = true
    lastX.current = e.clientX
    e.currentTarget.setPointerCapture(e.pointerId)
  }

  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!isResizing.current) return
    const deltaX = e.clientX - lastX.current
    lastX.current = e.clientX
    onResize(deltaX)
  }

  const handlePointerUp = (e: React.PointerEvent<HTMLDivElement>) => {
    isResizing.current = false
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
