'use client';

import { ImperativePanelHandle, PanelProps } from 'react-resizable-panels';

import usePersistentPanelsContext from './usePersistentPanelsContext';
import ResizablePanel from '../Resizable/ResizablePanel';

export interface PersistentPanelProps extends Omit<PanelProps, 'defaultSize'> {
  order: number;
  id: string;
  ref?: React.Ref<ImperativePanelHandle>;
}

const PersistentPanel = ({ id, order = 1, ...props }: PersistentPanelProps) => {
  const { layout } = usePersistentPanelsContext();
  return (
    <ResizablePanel
      defaultSize={layout[order - 1]}
      id={id}
      order={order}
      {...props}
    />
  );
};

export default PersistentPanel;
