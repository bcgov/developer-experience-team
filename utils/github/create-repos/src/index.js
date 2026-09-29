import dotenv from "dotenv";
import fs from "node:fs/promises";
import { parseArgs } from "node:util";
import { createOctokit } from "./octokit.js";
import { logger } from "./logger.js";
import { createRepos } from "./repository-service.js";
import { validateJSONFile } from "./validation.js";

dotenv.config();

async function loadJSON(file) {
  try {
    const data = await fs.readFile(file, "utf8");
    return JSON.parse(data);
  } catch (error) {
    logger.error({ err: error }, `Error loading JSON from file ${file}:`);
    throw error;
  }
}

async function writeRepoResultFile(repoUrls, output) {
  try {
    const filePath = output;
    await fs.writeFile(filePath, repoUrls.join("\n"), "utf8");
    logger.info(`Repo result file written to ${filePath}`);
  } catch (error) {
    logger.error({ err: error }, `Error writing repo result file:`);
    throw error;
  }
}

async function processFile(org, inputFile, outputFile, token) {
  logger.info("***** Starting ******");
  logger.info(`Loading input file: ${inputFile}...`);
  const json = await loadJSON(inputFile);
  logger.info(`Validating input file: ${inputFile}`);
  const octokit = createOctokit(token);
  await validateJSONFile(octokit, org, json);
  const { repoUrls, hadFailures } = await createRepos(octokit, org, json);
  await writeRepoResultFile(repoUrls, outputFile);
  logger.info(`Finished creating repos from input file ${inputFile}`);
  if (hadFailures) {
    throw new Error("ERROR: Process ran but had failures, check the logs for details.");
  }
  return;
}

async function main() {
  const token = process.env.GITHUB_TOKEN;

  if (!token) {
    console.error("Error: GITHUB_TOKEN environment variable is required.");
    process.exitCode = 1;
    return;
  }

  const options = {
    org: {
      type: "string",
      short: "o",
    },
    input: {
      type: "string",
      short: "i",
    },
    output: {
      type: "string",
      short: "u",
    },
  };
  const { values } = parseArgs({
    options,
    strict: true,
    allowPositionals: false,
  });

  const { org, input: inputFile, output: outputFile } = values;
  if (!org) {
    console.error("Error:  --org must be specified.");
    process.exitCode = 1;
    return;
  }

  if (!inputFile) {
    console.error("Error:  --input must be specified");
    process.exitCode = 1;
    return;
  }

  try {
    if (!(await fs.stat(inputFile)).isFile()) {
      throw new Error(`not a file`);
    }
  } catch (error) {
    console.error(`Error: Input file ${inputFile} - ${error.message}`);
    process.exitCode = 1;
    return;
  }

  if (!outputFile) {
    console.error("Error:  --output must be specified.");
    process.exitCode = 1;
    return;
  }

  try {
    await processFile(org, inputFile, outputFile, token);
  } catch (error) {
    console.error(`Error: ${error.message}`);
    logger.error({ err: error }, `Error: ${error.message}`);
    process.exitCode = 1;
  }
}

await main();
