import { logger } from './logger.js';
import { constants } from 'http2'
import { GH_API_HEADER } from '@bcgov/github-common';

const VALID_PERMISSIONS = ['pull', 'triage', 'push', 'maintain', 'admin'];

function isValidPermission(permission) {
  return permission && VALID_PERMISSIONS.includes(permission);
}

async function assignTeamsToRepo(octokit, org, repo) {
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
          ...GH_API_HEADER,
        },
      });

      if (result?.status !== constants.HTTP_STATUS_NO_CONTENT) {
        logger.warn(`Failed to assign team ${team.name} to repo ${repo.name}`);
      }
    }
  } catch (error) {
    logger.error({ err: error }, `Error assigning teams to repo ${repo.name}:`);
    throw error;
  }
}

async function checkUserMembership(octokit, org, username) {
  try {
    const results = await octokit.request('GET /orgs/{org}/members/{username}', {
      org: org,
      username: username,
      headers: {
        ...GH_API_HEADER,
      }
    });
    return results?.status === constants.HTTP_STATUS_NO_CONTENT;
  } catch (error) {
    logger.error({ err: error }, `Error checking user membership in org ${org}:`);
    throw error;
  }
}

async function assignUsersToRepo(octokit, org, repo, userCache) {
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
      if (userCache.has(user.name)) {
        isMember = userCache.get(user.name);
      } else {
        isMember = await checkUserMembership(octokit, org, user.name);
        userCache.set(user.name, isMember);
      }

      if (!isMember) {
        logger.warn(`Skipping user ${user.name} in repo ${repo.name}: User is not a member of the org ${org}`);
        continue;
      }

      await octokit.request('PUT /repos/{owner}/{repo}/collaborators/{username}', {
        owner: org,
        repo: repo.name,
        username: user.name,
        permission: user.permission,
        headers: {
          ...GH_API_HEADER,
        },
      });
    }
  } catch (error) {
    logger.error({ err: error }, `Error assigning users to repo ${repo.name}:`);
    throw error;
  }
}

async function assignUsersAndTeams(octokit, org, repo, userCache) {
  logger.info(`assigning users and teams for repo ${repo.name}`);
  for (const user of repo.users) {
    logger.info(`processing user ${user.name} with permission "${user.permission}" for repo ${repo.name}`);
    await assignUsersToRepo(octokit, org, repo, userCache);
  }
  for (const team of repo.teams) {
    logger.info(`processing team ${team.name} with permission "${team.permission}" for repo ${repo.name}`);
    await assignTeamsToRepo(octokit, org, repo);
  }
}

async function createRepo(octokit, org, repo, userCache) {
  if (!repo || !repo.name) {
    logger.error(`Invalid repo object: ${JSON.stringify(repo)}`);
    return false;
  }

  if (!repo.users) {
    repo.users = [];
  }
  if (!repo.teams) {
    repo.teams = [];
  }

  if (repo.users.length === 0 && repo.teams.length === 0) {
    logger.warn(`Repo ${repo.name} has no users or teams specified.`);
    return false;
  }

  logger.info(`creating repo ${repo.name}`);
  try {
    const response = await octokit.request('POST /orgs/{org}/repos', {
      org: org,
      name: repo.name,
      private: true,
      headers: {
        ...GH_API_HEADER,
      },
    });

    if (response.status === constants.HTTP_STATUS_CREATED) {
      logger.info(`Successfully created repo ${repo.name}`);
      await assignUsersAndTeams(octokit, org, repo, userCache);
      return true;
    } else {
      logger.error(`Failed to create repo ${repo.name}. Status: ${response.status}`);
      return false;
    }
  } catch (error) {
    logger.error({ err: error }, `Error creating repo ${repo.name}:`);
    return false;
  }
}


export async function createRepos(octokit, org, json) {
  let numCreated = 0;
  const userCache = new Map();

  for (const repo of json) {
    try {
      const created = await createRepo(octokit, org, repo, userCache);
      if (created) {
        numCreated++;
      }
    } catch (error) {
      logger.error({ err: error }, `Error creating repo ${repo.name}:`);
    }
  }
  logger.info(`Finished creating repos for org ${org} from JSON data. Created: ${numCreated}/${json.length}`);
}