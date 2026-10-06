import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { Sidebar } from '../components/Sidebar';
import * as AuthContextModule from '../context/AuthContext';

describe('Sidebar Navigation Component', () => {
  it('renders student navigation items and hides Admin Portal for students', () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: {
        id: 1,
        email: 'student@learnai.dev',
        full_name: 'Alex Chen',
        role: 'student',
        is_active: true,
        created_at: '2026-01-01',
        updated_at: '2026-01-01',
      },
      token: 'mock-token',
      login: vi.fn(),
      loginAsDemo: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      loading: false,
    });

    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    );

    expect(screen.getByText('LearnAI')).toBeInTheDocument();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Courses')).toBeInTheDocument();
    expect(screen.getByText('Quizzes')).toBeInTheDocument();
    expect(screen.getByText('Recommendations')).toBeInTheDocument();
    expect(screen.getByText('AI Tutor')).toBeInTheDocument();
    expect(screen.getByText('Analytics')).toBeInTheDocument();

    // Admin Portal must NOT be visible for regular student
    expect(screen.queryByText('Admin Portal')).toBeNull();
  });

  it('renders Admin Portal link when user role is admin or teacher', () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: {
        id: 2,
        email: 'admin@learnai.dev',
        full_name: 'Professor Ada Lovelace',
        role: 'admin',
        is_active: true,
        created_at: '2026-01-01',
        updated_at: '2026-01-01',
      },
      token: 'mock-token',
      login: vi.fn(),
      loginAsDemo: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      loading: false,
    });

    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    );

    expect(screen.getByText('Admin Portal')).toBeInTheDocument();
  });
});
