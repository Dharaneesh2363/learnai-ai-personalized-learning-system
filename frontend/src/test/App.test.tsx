import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import App from '../App';

describe('LearnAI Full-Stack Application Frontend', () => {
  it('renders login page with demo evaluation switcher', () => {
    render(<App />);
    expect(screen.getByText('LearnAI')).toBeInTheDocument();
    expect(screen.getByText('Demo Student')).toBeInTheDocument();
    expect(screen.getByText('Demo Admin')).toBeInTheDocument();
  });
});
