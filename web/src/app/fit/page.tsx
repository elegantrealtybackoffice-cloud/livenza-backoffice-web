import type { Metadata } from 'next';
import { FitApp } from './fit-app';

export const metadata: Metadata = {
  title: 'livenza.fit — Fitness OS',
  description: 'Workouts, exercise coaching, smart counters, health tracking, music and connected fitness by Livenza.',
  manifest: '/fit.webmanifest',
};

export default function FitPage() {
  return <FitApp />;
}
