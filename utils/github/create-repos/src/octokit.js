import { Octokit } from 'octokit';
import { throttling } from '@octokit/plugin-throttling';
import { logger } from './logger.js';

const ThrottledOctokit = Octokit.plugin(throttling);

/**
 * Builds a throttled Octokit client.
 * @param {string} token
 * @returns {import('octokit').Octokit}
 */
export function createOctokit(token) {
  return new ThrottledOctokit({
    auth: token,
    userAgent: 'auto-create-repos',
    timeZone: 'UTC',
    baseUrl: 'https://api.github.com',
    log: {
      debug: () => {},
      info: logger.info.bind(logger),
      warn: logger.warn.bind(logger),
      error: logger.error.bind(logger),
    },
    throttle: {
      onRateLimit: (retryAfter, options, octokit, retryCount) => {
        octokit.log.warn(
          `Request quota exhausted for request ${options.method} ${options.url}`
        );

        if (retryCount < 5) {
          octokit.log.warn(`Retrying after ${retryAfter} seconds!`);
          return true;
        }
        return false;
      },
      onSecondaryRateLimit: (retryAfter, options, octokit) => {
        octokit.log.warn(
          `SecondaryRateLimit detected for request ${options.method} ${options.url}. Retrying after ${retryAfter} seconds`
        );
        return true;
      },
    },
  });
}
