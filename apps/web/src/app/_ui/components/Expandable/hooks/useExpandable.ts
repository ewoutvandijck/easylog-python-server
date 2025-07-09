'use client';

import { useContext } from 'react';

import { ExpandableContext } from '../Expandable';

export const useExpandable = () => {
  const context = useContext(ExpandableContext);
  if (!context) {
    throw new Error('useExpandable must be used within an ExpandableProvider');
  }
  return context;
};
