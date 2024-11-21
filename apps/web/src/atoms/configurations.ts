import { atomWithStorage } from 'jotai/utils';

export type Configuration = {
  name: string;
  agentConfig: {
    agent_class: string;
  } & Record<string, unknown>;
};

const configurationsAtom = atomWithStorage<Configuration[]>('configurations', [
  {
    name: 'Configuration 1',
    agentConfig: {
      agent_class: 'OpenAIAssistant',
      assistant_id: 'asst_1234567890'
    }
  }
]);

export const activeConfigurationAtom = atomWithStorage<string>(
  'activeConfiguration',
  'Configuration 1'
);

export default configurationsAtom;
