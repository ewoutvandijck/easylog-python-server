import { atomWithStorage } from 'jotai/utils';

export type Connection = {
  name: string;
  url: string;
  secret: string;
};

const connectionsAtom = atomWithStorage<Connection[]>('connections', [
  {
    name: 'localhost',
    url: 'http://127.0.0.1:8000/api/v1',
    secret: 'secret'
  }
]);

export const activeConnectionAtom = atomWithStorage<string>(
  'activeConnection',
  'localhost'
);

export default connectionsAtom;
