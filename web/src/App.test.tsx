import { render, screen } from '@testing-library/react'
import App from './App'

test('shows the core question', () => {
  render(<App />)
  expect(screen.getByRole('heading', { name: 'Is my building OK?' })).toBeInTheDocument()
  expect(screen.getByAltText('VILPE')).toBeInTheDocument()
})
