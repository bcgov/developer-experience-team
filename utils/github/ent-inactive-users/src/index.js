#!/usr/bin/env node

import { getInactiveMembers } from './inactive-users.js';
import { createOctokit } from './octokit.js';
import { logger } from './logger.js';
import { writeReport } from './report.js';
import { parseArgs } from 'node:util';

export async function main() {
  const token = process.env.GITHUB_TOKEN;

  if (!token) {
    console.error('Error: GITHUB_TOKEN environment variable is required.');
    process.exitCode = 1;
    return;
  }

  const options = {
    enterprise: {
      type: 'string',
      short: 'e',
    },
    org: {
      type: 'string',
      short: 'o',
      multiple: true,
    },
    inactiveDays: {
      type: 'string',
      short: 'd',
    },
  };
  const {
    values,
  } = parseArgs({ options, strict: true, allowPositionals: false });

  const { enterprise, org, inactiveDays } = values;
  if (!enterprise) {
    console.error('Error:  --enterprise must be specified.');
    process.exitCode = 1;
    return;
  }

  const inactiveDaysInt = inactiveDays ? parseInt(inactiveDays) : 90;
  
  if (isNaN(inactiveDaysInt) || inactiveDaysInt <= 0 || inactiveDaysInt > 180) {
    console.error('Error: --inactiveDays must be between 1 and 180 (inclusive).');
    process.exitCode = 1;
    return;
  }

  if (!org || org.length === 0) {
      logger.info('No organizations specified. Defaulting to all organizations in the enterprise.');
  }

  const octokit = createOctokit(token);

  logger.info(`Getting inactive members in the last ${inactiveDaysInt} days for enterprise: ${enterprise} and orgs: ${org || 'all'}`);

  try {
    const inactiveMembers = await getInactiveMembers(octokit, enterprise, org, inactiveDaysInt);
    await writeReport(inactiveMembers);
  } catch (error) {
    logger.error(`Error occurred: ${error.message}`);
    process.exitCode = 1;
  }
}

await main();
