import fs from 'fs/promises';
import { parseArgs } from 'node:util';
import { createOctokit } from './octokit.js';
import { logger } from './logger.js';
import { stdin, stdout } from 'node:process';
import readline from 'node:readline/promises';
import { parse } from 'csv-parse/sync';


async function shouldProceed(usernames, enterprise, debugMode) {
  
  const rl = readline.createInterface({ input: stdin, output: stdout });

  // Prompt the user and wait for their input
  const text = debugMode ? `\u{1F41E} [DEBUG MODE] ${usernames.length} users will NOT be removed. Type "yes" to proceed: ` : `\u{1F4A3} Remove ${usernames.length} users from ${enterprise}? Are you SURE you want to do this??? Type "yes" to proceed \u{1F4A3}: `;
  const name = await rl.question(text);

  // Always close the interface when done
  rl.close();

  return name.toLowerCase() === 'yes';
}

async function getEnterpriseId(enterprise, octokit) {
    try {
        const query = `
            query ($enterprise: String!) {
                enterprise(slug: $enterprise) {
                    id
                }
            }`;
        const response = await octokit.graphql({
            query: query,
            enterprise: enterprise,
        });
        logger.info(`Enterprise ID for ${enterprise} is ${response.enterprise.id}`);
        return response.enterprise.id;
    } catch (error) {
        logger.error(`Failed to retrieve enterprise ID for ${enterprise}. Error: ${error.message}`);
        throw error;
    }
}

async function getGitHubUserId(username, octokit) {
    try {
        const query = `
            query ($username: String!) {
                user(login: $username) {
                    id
                }
            }`;
        const response = await octokit.graphql({
            query: query,
            username: username,
        });
        logger.debug(`GitHub User ID for ${username} is ${response.user.id}`);
        return response.user.id;
    } catch (error) {
        logger.error(`Failed to retrieve GitHub user ID for ${username}. Error: ${error.message}`);
        throw error;
    }
}

async function removeUserFromEnterprise(octokit, enterpriseId, userId, username) {
    try {
        const mutation = `
            mutation ($enterpriseId: ID!, $userId: ID!) {
             removeEnterpriseMember(input: {enterpriseId: $enterpriseId, userId: $userId}) {
              clientMutationId
              }
            }`;
        await octokit.graphql({
            query: mutation,
            enterpriseId: enterpriseId,
            userId: userId,
        });
        logger.info(`Successfully removed user ${username} with ID ${userId} from enterprise.`);
    } catch (error) {
        logger.error(`Failed to remove user ${username} with ID ${userId} from enterprise. Error: ${error.message}`);
        throw error;
    }
}

async function getUsersFromFile(filePath) {
  try {
    const fileContent = await fs.readFile(filePath, 'utf-8');
    const records = parse(fileContent, {
      skip_empty_lines: true,
      trim: true,
      columns: true,  
    });

    if (records.length > 0 && !Object.hasOwn(records[0], 'userName')) {
      throw new Error('CSV file must include a "userName" column.');
    }
  
    const users = records.map((row) => row.userName)
    return users;
  } catch (error) {
    logger.error(`Failed to read users from file ${filePath}. Error: ${error.message}`);
    throw error;
  }
}

async function removeUsersFromEnterprise(octokit, enterprise, usernames, debugMode) {

    logger.info(`Starting removal of ${usernames.length} users from enterprise ${enterprise}...`);
    const enterpriseId = await getEnterpriseId(enterprise, octokit);
    let errorNum = 0;
    let processedNum = 0;
    for (const username of usernames) {
      try {
        const userId = await getGitHubUserId(username, octokit);

        if (debugMode) {
          logger.info(`[DEBUG MODE] Would remove user: ${username}`);
          continue;
        } else {
          await removeUserFromEnterprise(octokit, enterpriseId, userId, username);
          processedNum += 1;
        }
      } catch (error) { 
        errorNum += 1;
      }
    }
    logger.info(`Completed removal process. Processed ${processedNum}/${usernames.length} users. ${errorNum}/${usernames.length} had errors.`);
}

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
    file: {
      type: 'string',
      short: 'f',
    },
    remove: {
      type: 'boolean',
      short: 'r',
    },
    
  };
  const {
    values,
  } = parseArgs({ options, strict: true, allowPositionals: false });

  const { enterprise, file } = values;
  if (!enterprise) {
    console.error('Error:  --enterprise must be specified.');
    process.exitCode = 1;
    return;
  }

  if (!file || !(await fs.stat(file)).isFile()) {
    console.error('Error:  --file must be specified and must be a valid file.');
    process.exitCode = 1;
    return;
  }

  const debugMode = !values.remove;

  if (debugMode) {
    logger.info('Debug mode enabled. Users will not be removed, but the script will simulate the removal process.');
  }

  try {
    const usernames = await getUsersFromFile(file);
    if (await shouldProceed(usernames, enterprise, debugMode)) {
      const octokit = createOctokit(token);
      await removeUsersFromEnterprise(octokit, enterprise, usernames, debugMode);
    }else {
      console.log('Operation cancelled by user.');
      process.exitCode = 0;
      return;
    }
  } catch (error) {
    logger.error('An unexpected error occurred:', error);
    process.exitCode = 1;
  }
}

await main();