'use client';

import { useState, useCallback, useEffect } from 'react';
import WelcomeScreen from '../components/WelcomeScreen';
import SimulationDashboard from '../components/SimulationDashboard';
import PersonaManagerPage from '../components/PersonaCreator';
import AdImageCreator from '../components/AdImageCreator';
import { fetchPersonas, createPersona, updatePersona, deletePersona } from '../api/simulationApi';

function loadLS(key, fallback) {
  try { return JSON.parse(localStorage.getItem(key) ?? 'null') ?? fallback; }
  catch { return fallback; }
}

export default function Home() {
  const [view, setView] = useState('welcome');
  const [initialContent, setInitialContent] = useState('');

  const [myPersonas, setMyPersonas] = useState([]);
  const [activePersonaIds, setActivePersonaIds] = useState(() => new Set());

  useEffect(() => {
    setActivePersonaIds(new Set(loadLS('active_persona_ids', [])));
    fetchPersonas().then(setMyPersonas).catch(console.error);
  }, []);

  const refreshPersonas = useCallback(async () => {
    const list = await fetchPersonas();
    setMyPersonas(list);
  }, []);

  const persistActiveIds = useCallback((ids) => {
    setActivePersonaIds(ids);
    localStorage.setItem('active_persona_ids', JSON.stringify([...ids]));
  }, []);

  const handleStart = useCallback((content) => {
    setInitialContent(content);
    setView('simulation');
  }, []);

  const handleNavigate = useCallback((dest) => {
    setView(dest);
  }, []);

  const handleBack = useCallback(() => {
    setView('welcome');
    setInitialContent('');
  }, []);

  const handleAddPersona = useCallback(async (persona) => {
    await createPersona(persona);
    await refreshPersonas();
    persistActiveIds(new Set([...activePersonaIds, persona.persona_id]));
  }, [activePersonaIds, persistActiveIds, refreshPersonas]);

  const handleDeletePersona = useCallback(async (id) => {
    await deletePersona(id);
    await refreshPersonas();
    const next = new Set(activePersonaIds);
    next.delete(id);
    persistActiveIds(next);
  }, [activePersonaIds, persistActiveIds, refreshPersonas]);

  const handleUpdatePersona = useCallback(async (updated) => {
    await updatePersona(updated);
    await refreshPersonas();
  }, [refreshPersonas]);

  const handleTogglePersona = useCallback((id) => {
    const next = new Set(activePersonaIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    persistActiveIds(next);
  }, [activePersonaIds, persistActiveIds]);

  const handleSetActivePersonaIds = useCallback((ids) => {
    persistActiveIds(ids);
  }, [persistActiveIds]);

  if (view === 'welcome') {
    return <WelcomeScreen onStart={handleStart} onNavigate={handleNavigate} />;
  }

  if (view === 'ad-image') {
    return <AdImageCreator onBack={handleBack} />;
  }

  if (view === 'personas') {
    return (
      <PersonaManagerPage
        personas={myPersonas}
        activeIds={activePersonaIds}
        onAdd={handleAddPersona}
        onDelete={handleDeletePersona}
        onToggle={handleTogglePersona}
        onSetActiveIds={handleSetActivePersonaIds}
        onUpdate={handleUpdatePersona}
        onBack={handleBack}
        onGoSimulate={() => setView('simulation')}
      />
    );
  }

  return (
    <SimulationDashboard
      initialContent={initialContent}
      onBack={handleBack}
      personas={myPersonas}
      activePersonaIds={activePersonaIds}
onManagePersonas={() => setView('personas')}
    />
  );
}
