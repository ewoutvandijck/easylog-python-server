import { motion } from 'motion/react';

import StackedBarChart from '@/app/_charts/components/StackedBarChart';
import { InternalChartConfig } from '@/app/_charts/schemas/internalChartConfigSchema';

export interface ChatMessageAssistantChartProps {
  config: InternalChartConfig;
}

const ChatMessageAssistantChart = ({
  config
}: ChatMessageAssistantChartProps) => {
  if (config.type !== 'stacked-bar') {
    throw new Error('Invalid chart type');
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2, ease: 'easeInOut' }}
    >
      <StackedBarChart config={config} />
    </motion.div>
  );
};

export default ChatMessageAssistantChart;
