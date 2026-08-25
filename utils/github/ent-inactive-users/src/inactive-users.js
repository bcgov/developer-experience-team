import { HEADERS } from './config.js';
import { logger } from './logger.js';
import { getEnterpriseMembers, Member } from './enterprise.js';


/**
 * Returns the cutoff date for activity checks.
 * @returns {string} ISO date string (YYYY-MM-DD)
 */
export function getSinceDate(inactiveDays = 90) {
  const since = new Date();
  since.setDate(since.getDate() - inactiveDays);

  const isoDate = since.toISOString().slice(0, 10);
  logger.info(`Checking for activity since: ${isoDate}`);

  return isoDate;
}

export async function getRecentCommitsInOrg(octokit, userName, org, sinceDate) {
    try {

        const { data } = await octokit.request('GET /search/commits', {
            q: `author:${userName} author-date:>${sinceDate} org:${org}`,
            headers: HEADERS,
            per_page: 1,
        });
        return data.total_count > 0;
    } catch (error) {
        if (error.status !== 409 && error.status !== 404) {
            logger.warn(
                `Unable to read commits for ${userName} in org ${org}: ${error.message}`
            );
        }
        return false;
    }
}

/**
 * Returns true if the member has any commits in the enterprise organizations since `sinceDate`.
 * @param {*} octokit 
 * @param {*} member 
 * @param {*} sinceDate 
 * @returns 
 */
export async function hasRecentCommits(octokit, member, sinceDate, orgsToInclude = []) {
    // api doesn't allow logical "OR" in the search query, so we have to check each org separately
    for (const org of member.getUserOrgs(orgsToInclude)) {
        if (await getRecentCommitsInOrg(octokit, member.userName, org, sinceDate)) {
            return true;
        }
    }
    return false;
}

export async function hasAuditLogActivityInOrg(octokit, member, org, sinceDate) {
    try {
        const { data } = await octokit.request('GET /orgs/{org}/audit-log', {
            org: org,
            phrase: `actor:${member.userName} created:>=${sinceDate}`,
            include: 'all',
            per_page: 1,
            headers: HEADERS,
        });
        return data.length > 0;
    } catch (error) {
        if (error.status !== 409 && error.status !== 404) {
            logger.warn(
                `Unable to read audit log for ${member.userName} in org ${org}: ${error.message}`
            );
        }
        return false;
    }
}

/**
 * Returns true if the member has any enterprise audit log activity since `sinceDate`.
 * @param {import('octokit').Octokit} octokit
 * @param {Member} member
 * @param {string} sinceDate ISO date string (YYYY-MM-DD)
 * @returns {Promise<boolean>}
 */
export async function hasAuditLogActivity(octokit, member, sinceDate, orgsToInclude = []) {
  //using the org audit log api to check for activity, since some audit log events
  // are not captured in the enterprise audit log api
  for (const org of member.getUserOrgs(orgsToInclude)) {
    if (await hasAuditLogActivityInOrg(octokit, member, org, sinceDate)) {
      return true;
    }
  }
  return false;
}


/**
 * Returns members with no audit log activity and no commit history in any repository
 * they can write to.
 *
 * @param {import('octokit').Octokit} octokit
 * @param {string} enterprise
 * @param {Array<string>} orgs
 * @param {number} inactiveDays
 * @returns {Promise<Array<Member>>}
 */
export async function getInactiveMembers(octokit, enterprise, orgs, inactiveDays = 90) {
  const members = await getEnterpriseMembers(octokit, enterprise, orgs);
  const  isoDate = getSinceDate(inactiveDays);
  const inactive = [];

  for (const member of members) {
    if (await hasAuditLogActivity(octokit, member, isoDate, orgs)) {
      logger.info(`${member.userName}: active (audit log).`);
      continue;
    }

    if (await hasRecentCommits(octokit, member, isoDate, orgs)) {
      logger.info(`${member.userName}: active (commit history).`);
      continue;
    }

    logger.info(`${member.userName}: inactive.`);
    inactive.push(member);
  }

  logger.info(`Found ${inactive.length} inactive member(s) of ${members.length}.`);
  return inactive;
}
