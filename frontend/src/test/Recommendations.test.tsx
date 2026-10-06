import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { Recommendations } from '../pages/Recommendations';
import * as apiModule from '../api';

const mockRecommendations = [
  {
    id: 101,
    user_id: 1,
    topic_id: 3,
    lesson_id: 5,
    topic_title: 'Python Loops',
    course_id: 1,
    course_title: 'Python Mastery',
    title: 'Targeted Remediation: Python Loops',
    what_description: 'Prioritize practicing nested while loops.',
    why_description: 'Your mastery is currently 42% (Developing) with a declining trend.',
    evidence_description: 'You answered 3 of 7 questions correctly (42.8% accuracy) with repeated nested-loop mistakes.',
    action_description: 'Review the lesson and take a 5-question adaptive quiz at easy difficulty.',
    priority: 'high',
    recommendation_type: 'revision',
    difficulty: 'easy',
    estimated_duration_minutes: 25,
    is_completed: false,
    is_dismissed: false,
    created_at: '2026-10-06T10:00:00Z',
    updated_at: '2026-10-06T10:00:00Z',
  },
];

describe('Recommendations Page Component', () => {
  it('renders 4-factor explainable recommendation card', async () => {
    vi.spyOn(apiModule.recommendationsApi, 'getRecommendations').mockResolvedValue(mockRecommendations as any);

    render(
      <MemoryRouter>
        <Recommendations />
      </MemoryRouter>
    );

    // Await async API response rendering
    await waitFor(() => {
      expect(screen.getByText(/Explainable Recommendations/i)).toBeInTheDocument();
      expect(screen.getByText('Targeted Remediation: Python Loops')).toBeInTheDocument();
    });

    // Verify 4 Explainability Factor Labels
    expect(screen.getByText('WHAT:')).toBeInTheDocument();
    expect(screen.getByText(/WHY IS THIS RECOMMENDED/i)).toBeInTheDocument();
    expect(screen.getByText(/QUANTITATIVE EVIDENCE/i)).toBeInTheDocument();
    expect(screen.getByText('ACTION:')).toBeInTheDocument();

    // Verify evidence content
    expect(
      screen.getByText(/You answered 3 of 7 questions correctly/i)
    ).toBeInTheDocument();

    // Verify priority badge
    expect(screen.getByText(/HIGH\s+PRIORITY/i)).toBeInTheDocument();
  });

  it('triggers completion when clicking Mark Complete', async () => {
    const actMock = vi.spyOn(apiModule.recommendationsApi, 'actOnRecommendation').mockResolvedValue({} as any);
    vi.spyOn(apiModule.recommendationsApi, 'getRecommendations').mockResolvedValue(mockRecommendations as any);

    render(
      <MemoryRouter>
        <Recommendations />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Targeted Remediation: Python Loops')).toBeInTheDocument();
    });

    const markDoneBtn = screen.getByRole('button', { name: /mark complete/i });
    fireEvent.click(markDoneBtn);

    expect(actMock).toHaveBeenCalledWith(101, { is_completed: true });
  });
});
