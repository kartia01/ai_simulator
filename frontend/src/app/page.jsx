'use client';

import { useState, useCallback } from 'react';
import WelcomeScreen from '../components/WelcomeScreen';
import SimulationDashboard from '../components/SimulationDashboard';

export default function Home() {
  const [started, setStarted] = useState(false);
  const [initialContent, setInitialContent] = useState('');

  const handleStart = useCallback((content) => {
    setInitialContent(content);
    setStarted(true);
  }, []);

  const handleBack = useCallback(() => {
    setStarted(false);
    setInitialContent('');
  }, []);

  if (!started) {
    return <WelcomeScreen onStart={handleStart} />;
  }

  return <SimulationDashboard initialContent={initialContent} onBack={handleBack} />;
}
