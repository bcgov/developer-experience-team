import { logger } from './logger.js';
import { constants } from 'http2'
import { GH_API_HEADER } from '@bcgov/github-common';

async function assignTeamsToRepo(octokit, org, repo) {
  let hasError = false;
    for (const team of repo.teams ?? []) {
      try {
        const result = await octokit.request('PUT /orgs/{org}/teams/{team_slug}/repos/{owner}/{repo}', {
          org: org,
          team_slug: team.slug,
          owner: org,
          repo: repo.name,
          permission: team.permission,
          headers: {
            ...GH_API_HEADER,
          },
        });

        if (result?.status !== constants.HTTP_STATUS_NO_CONTENT) {
          hasError = true;
          logger.error(`Failed to assign team ${team.slug} to repo ${repo.name}`);
        } else {
          logger.info(`Assigned team ${team.slug} to repo ${repo.name} with permission '${team.permission}'`);
        }    
    } catch (error) {
      logger.error({ err: error }, `Error assigning team ${team.slug} to repo ${repo.name}.`);
      hasError = true;
    }
  }
  return hasError;
}

async function assignUsersToRepo(octokit, org, repo) {
  let hasError = false;
  for (const user of repo.users ?? []) {
    try {
      const result = await octokit.request('PUT /repos/{owner}/{repo}/collaborators/{username}', {
        owner: org,
        repo: repo.name,
        username: user.name,
        permission: user.permission,
        headers: {
          ...GH_API_HEADER,
        },
      });
      
      if(result?.status === constants.HTTP_STATUS_NO_CONTENT) {
        logger.info(`Assigned user ${user.name} to repo ${repo.name} with permission '${user.permission}'`);
      }else if(result?.status === constants.HTTP_STATUS_CREATED) {
        hasError = true;
        logger.error(`ERROR: Invited user ${user.name} as outside collaborator to repo ${repo.name}. CANCEL THEIR INVITE.`);
      }else {
        hasError = true;
        logger.error({ err: error }, `Error assigning user ${user.name} to repo ${repo.name}:`);
      }
      
    } catch (error) {
      hasError = true;
      logger.error({ err: error }, `Error assigning user ${user.name} to repo ${repo.name}:`);
    }
  }
  return hasError;
}

async function assignUsersAndTeams(octokit, org, repo) {
  logger.info(`assigning users and teams for repo ${repo.name}`);
  let hasError = await assignUsersToRepo(octokit, org, repo) 
  hasError = await assignTeamsToRepo(octokit, org, repo) || hasError;
  return hasError;
}

async function createRepo(octokit, org, repo) {

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
      return { success: true, url: response.data.html_url };
    } else {
      logger.error(`Failed to create repo ${repo.name}. Status: ${response.status}`);
      return { success: false };
    }
  } catch (error) {
    logger.error({ err: error }, `Error creating repo: ${repo.name}`);
    return { success: false };
  }
}


export async function createRepos(octokit, org, json) {
  let numCreated = 0;
  const repoUrls = [];
  let hadFailures = false;

  for (const repo of json) {
    try {
      const created = await createRepo(octokit, org, repo);
      if (created.success) {
        numCreated++;
        repoUrls.push(created.url);
        hadFailures = await assignUsersAndTeams(octokit, org, repo) || hadFailures;
      } else {
        hadFailures = true;
      }
    } catch (error) {
      hadFailures = true;
      logger.error({ err: error }, `Error creating repo ${repo.name}:`);
    }
  }
  logger.info(`Finished creating repos for org ${org} from JSON data. Created: ${numCreated}/${json.length}`);
  return { repoUrls, hadFailures };
}