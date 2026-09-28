import dotenv from "dotenv";
import fs from 'node:fs/promises';
import { parseArgs } from 'node:util';
import { createOctokit } from './octokit.js';
import { logger } from './logger.js';
import { createRepos } from './repository-service.js';

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

async function writeRepoResultFile(repoUrls, output) {
  if (!repoUrls || repoUrls.length === 0) { 
    logger.error('No repos were created, skipping writing result file.');
    return;
  }
  try {
    const filePath = output;
    await fs.writeFile(filePath, repoUrls.join('\n'), 'utf8');
    logger.info(`Repo result file written to ${filePath}`);
  } catch (error) {
    logger.error({ err: error }, `Error writing repo result file:`);
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
      input: {
        type: 'string',
        short: 'i',
      },
      output: {
        type: 'string',
        short: 'u',
      }
    };
    const {
      values,
    } = parseArgs({ options, strict: true, allowPositionals: false });
  
    const { org, input: inputFile, output: outputFile } = values;
    if (!org) {
      console.error('Error:  --org must be specified.');
      process.exitCode = 1;
      return;
    }
  
    if (!inputFile) {
      console.error('Error:  --input must be specified');
      process.exitCode = 1;
      return;
    }

    try {
      (await fs.stat(inputFile)).isFile();
    }catch (error) {  
      console.error(`Error: Input file ${inputFile} is not accessible. Error: ${error.code} - ${error.message}`);
      process.exitCode = 1;
      return;
    }
  
    if (!outputFile) {
      console.error('Error:  --output must be specified.');
      process.exitCode = 1;
      return;
    }
  
    logger.info("***** Starting ******");
    logger.info(`Processing input file: ${inputFile}...`);
    try {
      const octokit = createOctokit(token);
      const json = await loadJSON(inputFile);
      const { repoUrls, hadFailures } = await createRepos(octokit, org, json);
      await writeRepoResultFile(repoUrls, outputFile);
      logger.info(`Finished creating repos from input file ${inputFile}`);
      if (hadFailures) {
        process.exitCode = 1;
      }
    } catch (error) {
      logger.error({ err: error }, `Error creating repos from input file ${inputFile}:`);
      process.exitCode = 1;
    }
  }

await main();
