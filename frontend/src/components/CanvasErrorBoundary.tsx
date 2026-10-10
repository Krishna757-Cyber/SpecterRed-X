import { Component, type ReactNode } from 'react'

// Catches a thrown 3D canvas and lets the parent fall back to the 2D view.
export class CanvasErrorBoundary extends Component<
  { children: ReactNode; fallback: ReactNode },
  { hasError: boolean }
> {
  constructor(props: { children: ReactNode; fallback: ReactNode }) {
    super(props)
    this.state = { hasError: false }
  }
  static getDerivedStateFromError() {
    return { hasError: true }
  }
  componentDidCatch(error: unknown) {
    // eslint-disable-next-line no-console
    console.warn('3D canvas error, falling back to 2D view:', error)
  }
  render() {
    return this.state.hasError ? this.props.fallback : this.props.children
  }
}
