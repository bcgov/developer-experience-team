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

async function cancelInvitation(octokit, org, repo, invite_id, user) {
  const result = await octokit.request('DELETE /repos/{owner}/{repo}/invitations/{invitation_id}', {
    owner: org,
    repo: repo.name,
    invitation_id: invite_id,
    headers: {
      ...GH_API_HEADER,
    }
  });
  if (result?.status !== constants.HTTP_STATUS_NO_CONTENT) {
    throw new Error(`ERROR: Failed to cancel invitation for user ${user.name} on repo ${repo.name}. CANCEL INVITATION MANUALLY.`);
  }else {
    logger.info(`Successfully cancelled invitation for user ${user.name} on repo ${repo.name}`);
  }
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
        // This could happen if the user was removed from the org between the time of validation and the actual assignment.
        // This is a very low probability event. But, the API lets us easily check for this scenario.
        // If it happens, attempt to cancel the invitation, and if that fails log an error.
        // We'll mark as hasError so user knows there was an issue with the assignment.
        hasError = true;
        logger.error(`Error: Invited user ${user.name} as outside collaborator to repo ${repo.name}. Attempting to cancel invitation...`);
        await cancelInvitation(octokit, org, repo, result.data.id, user);
      }else {
        hasError = true;
        logger.error(`Error assigning user ${user.name} to repo: ${repo.name}. HTTP return status was: ${result?.status}`);
      }
      
    } catch (error) {
      hasError = true;
      logger.error({ err: error }, `Error assigning user ${user.name} to repo: ${repo.name}. Error ${error.message}`);
    }
  }
  return hasError;
}

async function assignUsersAndTeams(octokit, org, repo) {
  logger.info(`assigning users and teams for repo ${repo.name}`);
  let hasError = await assignUsersToRepo(octokit, org, repo);
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