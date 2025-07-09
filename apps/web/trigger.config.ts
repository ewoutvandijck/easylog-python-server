import { sentryEsbuildPlugin } from '@sentry/esbuild-plugin';
import { esbuildPlugin } from '@trigger.dev/build/extensions';
import { syncVercelEnvVars } from '@trigger.dev/build/extensions/core';
import { defineConfig } from '@trigger.dev/sdk';

if (!process.env.SENTRY_AUTH_TOKEN) {
  console.warn('SENTRY_AUTH_TOKEN not set, no source maps will be uploaded');
}

export const machineConfig = {
  default: 'small-1x',
  casafariInsert: 'medium-1x'
} as const;

export default defineConfig({
  project: 'proj_pggrqndlxlqrizkrcfbx',
  build: {
    extensions: [
      syncVercelEnvVars(),
      esbuildPlugin(
        sentryEsbuildPlugin({
          org: 'byont-ventures',
          project: 'easylog-ai-chat',
          authToken: process.env.SENTRY_AUTH_TOKEN
        }),
        { placement: 'last', target: 'deploy' }
      )
    ],
    external: ['sharp']
  },
  logLevel: 'log',
  runtime: 'node',
  machine: machineConfig.default,
  // The max compute seconds a task is allowed to run. If the task run exceeds this duration, it will be stopped.
  // You can override this on an individual task.
  // See https://trigger.dev/docs/runs/max-duration
  maxDuration: 5 * 60 * 60,
  retries: {
    enabledInDev: true,
    default: {
      maxAttempts: 5,
      factor: 1.8,
      minTimeoutInMs: 500,
      maxTimeoutInMs: 30_000,
      randomize: false
    }
  },
  dirs: ['./src/jobs']
});
