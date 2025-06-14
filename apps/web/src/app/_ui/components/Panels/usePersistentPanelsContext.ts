import { useContext } from 'react';

import { PersistentPanelsContext } from './PersistentPanelsProvider';

const usePersistentPanelsContext = () => {
  const context = useContext(PersistentPanelsContext);
  if (!context) {
    throw new Error(
      'usePersistentPanelsContext must be used within a PersistentPanelsProvider'
    );
  }
  return context;
};

export default usePersistentPanelsContext;
