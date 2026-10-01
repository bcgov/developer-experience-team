import zod from 'zod';  
import { constants } from 'http2'
import { GH_API_HEADER } from '@bcgov/github-common';

const VALID_PERMISSIONS = ['pull', 'triage', 'push', 'maintain', 'admin'];

const ERROR_USERS = "name is required - it is the GitHub username";
const ERROR_TEAMS = "slug is required - it is the GitHub team slug";
const ERROR_STRICT = "Extra fields are not allowed";
  
export const repoSchema = zod.array(zod.object({
  name: zod.string().min(1),
  users: zod.array(zod.object({
    name: zod.string(ERROR_USERS).min(1, ERROR_USERS),
    permission: zod.enum(VALID_PERMISSIONS, "Permission is required"),
  }).strict(ERROR_STRICT)).optional(),
  teams: zod.array(zod.object({
    slug: zod.string(ERROR_TEAMS).min(1, ERROR_TEAMS),
    permission: zod.enum(VALID_PERMISSIONS, "Permission is required"),
  }).strict(ERROR_STRICT)).optional()
})
.refine((data) => (data.users?.length > 0 || data.teams?.length > 0), {
    message: "You must specify at least one user or team."
})
.strict(ERROR_STRICT));
    
export async function validateJSONFile(octokit, org, json) {
  const result = repoSchema.safeParse(json);
  if (!result.success) {
    throw result.error;   
  }

  const teamCache = new Set();
  const userCache = new Set();
  for(const repo of result.data) {
    await validateUsers(octokit, org, repo, userCache);
    await validateTeams(octokit, org, repo, teamCache);
  }

  return result.data;    
}

async function validateTeamExists(octokit, org, team_slug) {
  const result = await octokit.request('GET /orgs/{org}/teams/{team_slug}', {
    org: org,
    team_slug: team_slug,
    headers: {
      ...GH_API_HEADER,
    }
  });
  return result?.status === constants.HTTP_STATUS_OK;

}

async function validateTeams(octokit, org, repo, teamCache) {
  for (const team of (repo.teams ?? [])) {
    try {
      if (!teamCache.has(team.slug)) {
        if (!await validateTeamExists(octokit, org, team.slug)) {
          throw Error(`Team ${team.slug} does not exist in the org ${org}`);
        }
        teamCache.add(team.slug);
      }
    } catch (error) {
      throw Error(`Error validating team ${team.slug} in repo ${repo.name}: ${error.message}`);
    }
  }
}

async function checkUserMembership(octokit, org, username) {
  const results = await octokit.request('GET /orgs/{org}/members/{username}', {
    org: org,
    username: username,
    headers: {
      ...GH_API_HEADER,
    }
  });
  return results?.status === constants.HTTP_STATUS_NO_CONTENT;
}

async function validateUsers(octokit, org, repo, userCache) {
  for (const user of (repo.users ?? [])) {
    try {
      if (!userCache.has(user.name)) {
        if (!await checkUserMembership(octokit, org, user.name)) {
          throw Error(`User ${user.name} is not a member of the org ${org}`);
        }
        userCache.add(user.name);
      }
    } catch (error) {
      throw Error(`Error validating user ${user.name} in repo ${repo.name}: ${error.message}`);
    }
  }
}
