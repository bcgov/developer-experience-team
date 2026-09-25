import dotenv from "dotenv";
import fs from 'node:fs/promises';
import { parseArgs } from 'node:util';
import { createOctokit } from './octokit.js';
import { logger } from './logger.js';
import { createRepos } from './repository-service.js';
import { readFile } from 'node:fs/promises';

dotenv.config();

async function loadJSON(file) {
  try {
    const data = await fs.readFile(file, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    logger.error({ err: error }, `Error loading JSON from file ${file}:`);
    throw error;
  }
}

async function main() {

  const token = process.env.GITHUB_TOKEN;

  if (!token) {
    console.error('Error: GITHUB_TOKEN environment variable is required.');
    process.exitCode = 1;
    return;
  }

  const options = {
      org: {
        type: 'string',
        short: 'o',
      },
      file: {
        type: 'string',
        short: 'f',
      },
    };
    const {
      values,
    } = parseArgs({ options, strict: true, allowPositionals: false });
  
    const { org, file } = values;
    if (!org) {
      console.error('Error:  --org must be specified.');
      process.exitCode = 1;
      return;
    }
  
    if (!file || !(await fs.stat(file)).isFile()) {
      console.error('Error:  --file must be specified and must be a valid file.');
      process.exitCode = 1;
      return;
    }
  
    logger.info("***** Starting ******");
    logger.info(`Processing file: ${file}...`);
    try {
      const octokit = createOctokit(token);
      const json = await loadJSON(file);
      await createRepos(octokit, org, json);
      logger.info(`Finished creating repos from file ${file}`);
    } catch (error) {
      logger.error({ err: error }, `Error creating repos from file ${file}:`);
      process.exitCode = 1;
    }
  }

await main();
