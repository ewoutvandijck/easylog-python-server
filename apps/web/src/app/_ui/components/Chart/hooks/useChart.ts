import { useContext } from 'react';

import { ChartContext } from '../ChartContainer';

const useChart = () => {
  const context = useContext(ChartContext);

  if (!context) {
    throw new Error('useChart must be used within a <ChartContainer />');
  }

  return context;
};

export default useChart;
