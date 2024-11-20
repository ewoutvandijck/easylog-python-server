import connectionsAtom, {
  activeConnectionAtom,
  Connection
} from '@/atoms/connections';
import { useAtom } from 'jotai/react';

const useConnections = () => {
  const [activeConnectionName, setActiveConnectionName] =
    useAtom(activeConnectionAtom);

  const [connections, setConnections] = useAtom(connectionsAtom);

  const activeConnection = connections.find(
    (connection) => connection.name === activeConnectionName
  );

  if (!activeConnection) {
    throw new Error('No active connection found');
  }

  const setActiveConnection = (name: string) => {
    setActiveConnectionName(name);
  };

  const addConnection = (connection: Connection) => {
    setConnections([...connections, connection]);
  };

  const removeConnection = (name: string) => {
    setConnections(
      connections.filter((connection) => connection.name !== name)
    );
  };

  return {
    connections,
    activeConnection,
    setActiveConnection,
    addConnection,
    removeConnection
  };
};

export default useConnections;
