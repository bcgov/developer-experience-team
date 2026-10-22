import { throttling } from '@octokit/plugin-throttling';
import { Octokit } from 'octokit';

const ThrottledOctokit = Octokit.plugin(throttling);

export const GH_API_HEADER = { 'X-GitHub-Api-Version': '2026-03-10' };

export function createOctokit({
  token,
  userAgent,
  logger,
  baseUrl = 'https://api.github.com',
  timeZone = 'UTC',
  maxRateLimitRetries = 5,
  maxSecondaryRateLimitRetries = 5,
}) {
  return new ThrottledOctokit({
    auth: token,
    userAgent,
    timeZone,
    baseUrl,
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

        if (retryCount < maxRateLimitRetries) {
          octokit.log.warn(`Retrying after ${retryAfter} seconds!`);
          return true;
        }
        return false;
      },
      onSecondaryRateLimit: (retryAfter, options, octokit, retryCount) => {
        octokit.log.warn(
          `SecondaryRateLimit detected for request ${options.method} ${options.url}.`
        );
        if (retryCount < maxSecondaryRateLimitRetries) {
          octokit.log.warn(`Retrying after ${retryAfter} seconds!`);
          return true;
        }
        return false;
      },
    },
  });
}