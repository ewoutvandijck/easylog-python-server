import configurationsAtom, {
  activeConfigurationAtom,
  Configuration
} from '@/atoms/configurations';
import { useAtom } from 'jotai/react';

const useConfigurations = () => {
  const [activeConfigurationName, setActiveConfigurationName] = useAtom(
    activeConfigurationAtom
  );

  const [configurations, setConfigurations] = useAtom(configurationsAtom);

  const activeConfiguration = configurations.find(
    (configuration) => configuration.name === activeConfigurationName
  );

  const setActiveConfiguration = (name: string) => {
    setActiveConfigurationName(name);
  };

  const addConfiguration = (configuration: Configuration) => {
    if (configurations.find((c) => c.name === configuration.name)) {
      return;
    }

    setConfigurations([...configurations, configuration]);
  };

  const removeConfiguration = (name: string) => {
    setConfigurations(
      configurations.filter((configuration) => configuration.name !== name)
    );
  };

  const updateConfiguration = (name: string, configuration: Configuration) => {
    setConfigurations(
      configurations.map((c) =>
        c.name === name ? { ...c, ...configuration } : c
      )
    );
  };

  return {
    configurations,
    activeConfiguration,
    setActiveConfiguration,
    addConfiguration,
    removeConfiguration,
    updateConfiguration
  };
};

export default useConfigurations;
