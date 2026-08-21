import { HEADERS } from './config.js';
import { logger } from './logger.js';


export async function getOutsideCollaboratorsInOrg(octokit, org) {
    try {
        const { data } = await octokit.request('GET /orgs/{org}/outside_collaborators', {
            org: org,
            headers: HEADERS,
            per_page: 100,
        });
        return data;
    } catch (error) {
        logger.error(
            `Unable to read outside collaborators for org ${org}: ${error.message}`
        );
        throw error;
    }
}

export async function getAllOrgsInEnterprise(octokit, enterprise) {
  logger.info(`Retrieving all organizations in enterprise: ${enterprise}`);
  try {
    const query = `
      query ($enterprise: String!) {
          enterprise(slug: $enterprise) {
              organizations(first: 100) {
                  nodes {
                      login
                  }
              }
          }
      }`;

    const response = await octokit.graphql({
      query: query,
      enterprise: enterprise,
    });
    const interim = response.enterprise.organizations.nodes.map((org) => org.login);
    return interim;
  } catch (error) {
    logger.error(`Unable to read organizations in enterprise: ${error.message}`);
    throw error;
  }
}

export async function getUsersToIgnore(octokit, orgsToInclude, enterprise) {
    const usersToIgnore = new Set();
    const orgsToScan = orgsToInclude && orgsToInclude.length > 0 ? orgsToInclude : await getAllOrgsInEnterprise(octokit, enterprise);
    for (const org of orgsToScan) {
        const outsideCollaborators = await getOutsideCollaboratorsInOrg(octokit, org);
        for (const collaborator of outsideCollaborators) {
            usersToIgnore.add(collaborator.login);
        }
    }

    return new Set(
      Array.from(usersToIgnore, (username) => username?.toLowerCase())
    );
}

/**
 * Returns all members that have consumed a license in the enterprise.
 * @param {import('octokit').Octokit} octokit
 * @returns {Promise<Array<Member>>}
 */
export async function getEnterpriseMembers(octokit, enterprise, orgsToInclude = []) {

  logger.info('Retrieving users to ignore from outside collaborators...');
  const ignoredUsernames = await getUsersToIgnore(octokit, orgsToInclude, enterprise);

  logger.info(`Users to ignore: ${Array.from(ignoredUsernames).join(', ')}`);


  logger.info('Retrieving consumed license results from the enterprise...');

  const results = await octokit.paginate('GET /enterprises/{enterprise}/consumed-licenses', {
    enterprise: enterprise,
    per_page: 100,
    headers: HEADERS,
  });

  const members = results.flatMap((result) =>
    result.users
      .filter((user) => !ignoredUsernames.has(user.github_com_login?.toLowerCase()))
      .map((user) => new Member(
        user.github_com_login,
        user.github_com_saml_name_id,
        user.github_com_member_roles,
        user.github_com_verified_domain_emails,
      ))
  );

  logger.info(`Will process ${members.length} members from the ${enterprise} enterprise.`);
  return members;
}

export class Member { 
  constructor(userName, email, membership, githubVerifiedDomainEmails = []) {
    this.userName = userName;
    this.email = email;
    this.membership = membership;
    this.githubVerifiedDomainEmails = githubVerifiedDomainEmails;
  }
  
  getUserOrgs(orgsToInclude = []) {
    const includedOrgs = orgsToInclude ?? [];
    return this.membership
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

}


