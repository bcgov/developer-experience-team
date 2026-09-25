import dotenv from "dotenv";
import { createOctokit } from './octokit.js';
import { logger } from './logger.js';
import { parseArgs } from 'node:util';
import { readFile } from 'node:fs/promises';
import fs from 'node:fs/promises';

dotenv.config();

const HEADER = { 'X-GitHub-Api-Version': '2026-03-10' };
const VALID_PERMISSIONS = ['pull', 'triage', 'push', 'maintain', 'admin'];
const SUCCESS = 204;

let userCache = {};
function isValidPermission(permission) {
  return permission && VALID_PERMISSIONS.includes(permission);
}


async function assignTeamsToRepo(octokit, org, repo){
  try {
    for (const team of repo.teams) {
      if (!team.name) {
        logger.warn(`Skipping team with missing name in repo ${repo.name}`);
        continue;
      }
      if (!isValidPermission(team.permission)) {
        logger.warn(`Skipping team ${team.name} in repo ${repo.name}: No permission specified or invalid permission`);
        continue;
      }
      const result = await octokit.request('PUT /orgs/{org}/teams/{team_slug}/repos/{owner}/{repo}', {
        org: org,
        team_slug: team.name,
        owner: org,
        repo: repo.name,
        permission: team.permission,
        headers: {
          ...HEADER,
        },
      });
      
      if (result?.status !== SUCCESS) {
        logger.warn(`Failed to assign team ${team.name} to repo ${repo.name}`);
      }
    }
  } catch (error) {
    logger.error({ err: error },`Error assigning teams to repo ${repo.name}:`);
    throw error;
  }
}

async function checkUserMembership(octokit, org, username) {
  try {
    const results = await octokit.request('GET /orgs/{org}/members/{username}', {
      org: org,
      username: username,
      headers: {
        ...HEADER,
      }
    });
    return results?.status === SUCCESS;
  }catch(error){
    logger.error({ err: error },`Error checking user membership in org ${org}:`);
    throw error;
  }
}

async function assignUsersToRepo(octokit, org, repo) {
  try {
    for (const user of repo.users) {
      if (!user.name) {
        logger.warn(`Skipping user with missing name in repo ${repo.name}`);
        continue;
      }
      if (!isValidPermission(user.permission)) {
        logger.warn(`Skipping user ${user.name} in repo ${repo.name}: No permission specified or invalid permission`);
        continue;
      }

      let isMember;
      if (userCache.hasOwnProperty(user.name)) {
        isMember = userCache[user.name];
      } else {
        isMember = await checkUserMembership(octokit, org, user.name);
        userCache[user.name] = isMember;
      }

      if (!isMember) {
        userCache[user.name] = false;
        logger.warn(`Skipping user ${user.name} in repo ${repo.name}: User is not a member of the org ${org}`);
        continue;
      }

      await octokit.request('PUT /repos/{owner}/{repo}/collaborators/{username}', {
        owner: org,
        repo: repo.name,
        username: user.name,
        permission: user.permission,
        headers: {
          ...HEADER,
        },
      });
    }
  } catch (error) {
    logger.error({ err: error },`Error assigning users to repo ${repo.name}:`);
    throw error;
  }
}

async function assignUsersAndTeams(octokit, org, repo) {
  logger.info(`assigning users and teams for repo ${repo.name}`);
  for (const user of repo.users) {
    logger.info(`processing user ${user.name} with permissions ${user.permission} for repo ${repo.name}`);
    await assignUsersToRepo(octokit, org, repo);
  }
  for (const team of repo.teams) {
    logger.info(`processing team ${team.name} with permissions ${team.permission} for repo ${repo.name}`);
    await assignTeamsToRepo(octokit, org, repo);
  }
}

async function createRepo(octokit, org, repo) {
  if (!repo || !repo.name) {
    logger.error(`Invalid repo object: ${JSON.stringify(repo)}`);
    return;
  }

  if (!repo.users) {
    repo.users = [];
  }
  if (!repo.teams) {
    repo.teams = [];
  }

  if (repo.users.length === 0 && repo.teams.length === 0) {
    logger.warn(`Repo ${repo.name} has no users or teams specified.`);
    return;
  }

  logger.info(`creating repo ${repo.name}`);
  try {
   
    const response = await octokit.request('POST /orgs/{org}/repos', {
      org: org,
      name: repo.name,
      private: true,
      headers: {
        ...HEADER,
      },
    });

    if (response.status === 201) {
      logger.info(`Successfully created repo ${repo.name}`);
      await assignUsersAndTeams(octokit, org, repo);
    }
    else {
      logger.error(`Failed to create repo ${repo.name}. Status: ${response.status}`);
    }
    
  } catch (error) {
    logger.error({ err: error },`Error creating repo ${repo.name}:`);
  }
}


async function loadJSON(file) {
  try {
    const data = await readFile(file, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    logger.error({ err: error },`Error loading JSON from file ${file}:`);
    throw error;
  }
}

async function createRepos(octokit, org, file) {
  const json = await loadJSON(file);
  for (const repo of json) {
    await createRepo(octokit, org, repo);
  }
  logger.info(`Finished creating repos from file ${file}`);
}


async function main() {
  logger.info("***** Starting ******");
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
  
    const octokit = createOctokit(token);
    await createRepos(octokit, org, file);
 
}

main();
