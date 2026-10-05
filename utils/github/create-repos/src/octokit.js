import { createOctokit as createSharedOctokit } from '@bcgov/github-common';
import { logger } from './logger.js';

/**
 * Builds a throttled Octokit client.
 * @param {string} token
 * @returns {import('octokit').Octokit}
 */
export function createOctokit(token) {
  return createSharedOctokit({
    token,
    userAgent: 'auto-create-repos',
    logger,
  });
}
