import { HEADERS } from './config.js';
import { logger } from './logger.js';


/**
 * Get the orgs for a user based on their member roles.
 * Only include active orgs to avoid API lookups calls to inactive/archived orgs.
 * @param {Array<string>} memberRoles Member roles are formatted as `org:role`
 * @returns {Array<string>}
 */
export function getUserOrgs(memberRoles = [], orgsToInclude = []) {
  const includedOrgs = orgsToInclude ?? [];

  return memberRoles
    .map((role) => role.match(/^([^:]+):/)?.[1]?.trim().toLowerCase())
    .filter(
      (org) =>
        org &&
        (includedOrgs.length === 0 ||
          includedOrgs.some(
            (includedOrg) => includedOrg.toLowerCase() === org
          ))
    );
}

/**
 * Returns all members that have consumed a license in the enterprise.
 * @param {import('octokit').Octokit} octokit
 * @returns {Promise<Array<Member>>}
 */
export async function getEnterpriseMembers(octokit, enterprise, orgsToInclude) {
  logger.info('Retrieving consumed license results from the enterprise...');

  const results = await octokit.paginate('GET /enterprises/{enterprise}/consumed-licenses', {
    enterprise: enterprise,
    per_page: 100,
    headers: HEADERS,
  });

  const members = results.flatMap((result) =>
    result.users.map((user) => new Member(
      user.github_com_login,
      user.github_com_saml_name_id,
      getUserOrgs(user.github_com_member_roles, orgsToInclude),
      user.github_com_member_roles
    ))
  );

  logger.info(`Retrieved ${members.length} members from the ${enterprise} enterprise.`);
  return members;
}

export class Member { 
  constructor(userName, email, orgs, membership) {
    this.userName = userName;
    this.email = email;
    this.orgs = orgs;
    this.membership = membership;
  }
}


