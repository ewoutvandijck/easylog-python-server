import { syncVercelEnvVars } from '@trigger.dev/build/extensions/core';
import { defineConfig } from '@trigger.dev/sdk/v3';

export default defineConfig({
  project: 'proj_ftsvskzqqxximmftlqiv',
  build: {
    extensions: [syncVercelEnvVars()],
    external: ['sharp', 'pg']
  },
  logLevel: 'log',
  runtime: 'node',
  maxDuration: 3600,
  retries: {
    enabledInDev: false,
    default: {
      maxAttempts: 3,
      minTimeoutInMs: 1000,
      maxTimeoutInMs: 10000,
      factor: 2,
      randomize: true
    }
  },
  dirs: ['./src/jobs']
});
