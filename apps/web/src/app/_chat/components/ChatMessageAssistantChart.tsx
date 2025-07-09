import { motion } from 'motion/react';

import BarChart from '@/app/_charts/components/BarChart';
import LineChart from '@/app/_charts/components/LineChart';
import PieChart from '@/app/_charts/components/PieChart';
import StackedBarChart from '@/app/_charts/components/StackedBarChart';
import { InternalChartConfig } from '@/app/_charts/schemas/internalChartConfigSchema';

export interface ChatMessageAssistantChartProps {
  config: InternalChartConfig;
}

const ChatMessageAssistantChart = ({
  config
}: ChatMessageAssistantChartProps) => {
  const renderChart = () => {
    switch (config.type) {
      case 'stacked-bar':
        return <StackedBarChart config={config} />;
      case 'bar':
        return <BarChart config={config} />;
      case 'line':
        return <LineChart config={config} />;
      case 'pie':
        return <PieChart config={config} />;
      default:
        return null;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2, ease: 'easeInOut' }}
    >
      {renderChart()}
    </motion.div>
  );
};

export default ChatMessageAssistantChart;
