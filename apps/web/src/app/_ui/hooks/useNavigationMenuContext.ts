import { useContext } from 'react';

import { NavigationMenuContext } from '../components/NavigationMenu/NavigationMenuProvider';

const useNavigationMenuContext = () => {
  const context = useContext(NavigationMenuContext);

  if (!context) {
    throw new Error(
      'useNavigationMenuContext must be used within a NavigationMenuProvider'
    );
  }

  return context;
};

export default useNavigationMenuContext;
