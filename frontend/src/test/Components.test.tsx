import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { Badge } from '../components/Badge';
import { ProgressBar } from '../components/ProgressBar';
import { StatCard } from '../components/StatCard';
import { Award, Zap } from 'lucide-react';

describe('UI Primitives and Reusable Components', () => {
  describe('Badge Component', () => {
    it('renders with default slate style', () => {
      render(<Badge>Default Tag</Badge>);
      const badge = screen.getByText('Default Tag');
      expect(badge).toBeInTheDocument();
      expect(badge.className).toContain('bg-slate-800');
    });

    it('renders emerald variant for mastered tiers', () => {
      render(<Badge variant="emerald">Mastered</Badge>);
      const badge = screen.getByText('Mastered');
      expect(badge.className).toContain('text-emerald-400');
    });

    it('renders amber variant for developing tiers', () => {
      render(<Badge variant="amber">Developing</Badge>);
      const badge = screen.getByText('Developing');
      expect(badge.className).toContain('text-amber-400');
    });

    it('renders rose variant for critical weak tiers', () => {
      render(<Badge variant="rose">Beginner</Badge>);
      const badge = screen.getByText('Beginner');
      expect(badge.className).toContain('text-rose-400');
    });
  });

  describe('ProgressBar Component', () => {
    it('renders clamped percentage label when showLabel is true', () => {
      render(<ProgressBar value={74.2} showLabel={true} />);
      expect(screen.getByText('74%')).toBeInTheDocument();
      expect(screen.getByText('Mastery')).toBeInTheDocument();
    });

    it('clamps values above 100% to 100%', () => {
      render(<ProgressBar value={120} showLabel={true} />);
      expect(screen.getByText('100%')).toBeInTheDocument();
    });

    it('clamps negative values to 0%', () => {
      render(<ProgressBar value={-15} showLabel={true} />);
      expect(screen.getByText('0%')).toBeInTheDocument();
    });

    it('applies emerald color for mastery >= 80%', () => {
      const { container } = render(<ProgressBar value={85} />);
      const bar = container.querySelector('.bg-emerald-500');
      expect(bar).not.toBeNull();
    });

    it('applies rose color for mastery < 40%', () => {
      const { container } = render(<ProgressBar value={30} />);
      const bar = container.querySelector('.bg-rose-500');
      expect(bar).not.toBeNull();
    });
  });

  describe('StatCard Component', () => {
    it('renders title, value, subtext, and trend badge', () => {
      render(
        <StatCard
          title="Overall Mastery"
          value="74.5%"
          subtext="Across 11 topics"
          icon={Award}
          trend="+5.2%"
          trendPositive={true}
        />
      );

      expect(screen.getByText('Overall Mastery')).toBeInTheDocument();
      expect(screen.getByText('74.5%')).toBeInTheDocument();
      expect(screen.getByText('Across 11 topics')).toBeInTheDocument();
      expect(screen.getByText('+5.2%')).toBeInTheDocument();
    });

    it('renders negative trend style properly', () => {
      render(
        <StatCard
          title="Forgetting Decay"
          value="42%"
          icon={Zap}
          trend="-3.1%"
          trendPositive={false}
        />
      );

      const trend = screen.getByText('-3.1%');
      expect(trend.className).toContain('text-rose-400');
    });
  });
});
