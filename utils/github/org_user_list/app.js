import {Octokit} from "octokit";
import {createAppAuth, createOAuthUserAuth} from "@octokit/auth-app";
import { readFile, writeFile } from "node:fs/promises";
import {parse} from "csv-parse/sync";


// authenticate as GitHub App for increased API rate limits
// const octokit = new Octokit({
// 	authStrategy: createAppAuth,
// 	auth: {
// 		appId: `${process.env.GITHUB_APP_ID}`,
// 		installationId: `${process.env.GITHUB_APP_INSTALLATION_ID}`,
// 		privateKey: `${process.env.GITHUB_APP_PRIVATE_KEY}`,
// 	},
// });

async function get_org_members(target_org = first_org) {
// const collaborator_iterator = octokit.paginate.iterator(octokit.rest.orgs.listOutsideCollaborators, {
	const member_iterator = octokit.paginate.iterator(octokit.rest.orgs.listMembers, {
			org: target_org,
			per_page: 100
		}
	);

	const member_cache = [];

	for await (const {data: members} of member_iterator) {
		for (const member of members) {
			member_cache.push(member.login)
		}
	}
	return member_cache;
}

async function get_user_details(user_list) {
	const user_details = [];

	for (const user_name of user_list) {
		const { data: user } = await octokit.rest.users.getByUsername({username: user_name});
		user_details.push(user);
	}

	return user_details;
}

async function get_collaborators_for_repo(repo, org, affiliation, member_map) {

	// console.debug(`Retrieving collaborators for '${repo.name}' repo...`);

	const collaborator_iterator = octokit.paginate.iterator(octokit.rest.repos.listCollaborators, {
		owner: org, repo: repo.name, affiliation: affiliation, per_page: 100
	});

	const collaborators_for_repo = [];

	for await (const {data: collaborators} of collaborator_iterator) {
		for (const collaborator of collaborators) {
			collaborator.is_member = member_map.hasOwnProperty(collaborator.login);
			collaborator.association_type = "direct";
			collaborators_for_repo.push(collaborator);
		}
	}

	return collaborators_for_repo;
}

async function get_team_members(team_slug, org) {
	const member_iterator = octokit.paginate.iterator(octokit.rest.teams.listMembersInOrg, {
		org: org, team_slug: team_slug, per_page: 100
	});

	const member_list = []

	for await (const {data: members} of member_iterator) {
		for (const member of members) {
			member_list.push(member)
		}
	}
	return member_list;
}

// list teams in org
// list members in team
// link them up locally
async function get_organization_teams(org) {
	const team_iterator = octokit.paginate.iterator(octokit.rest.teams.list, {
		org: org, per_page: 100
	});

	const teams_to_members = {}

	for await (const {data: teams} of team_iterator) {
		for (const team of teams) {
			teams_to_members[team.slug] = team
		}
	}

	for (const team_slug of Object.keys(teams_to_members)) {
		const members = await get_team_members(team_slug, org);
		teams_to_members[team_slug].members = members
	}

	return teams_to_members;
}


// for a given repo, check for teams with access
// check access level of team on repo
async function get_team_members_for_repo(repo, org, organization_teams) {

	const teams_for_repo_iterator = octokit.paginate.iterator(octokit.rest.repos.listTeams, {
		owner: org, repo: repo.name, per_page: 100
	});

	const team_members_for_repo = []

	for await (const {data: teams} of teams_for_repo_iterator) {
		for (const repo_team of teams) {
			const org_team = organization_teams[repo_team.slug];
			for (const member of org_team.members) {
				const collaborator = {
					login: member.login,
					role_name: repo_team.permission,
					is_member: true,
					association_type: "team_member"
				}
				team_members_for_repo.push(collaborator)
			}
		}
	}

	return team_members_for_repo;
}

async function get_org_repositories(org) {

	const repo_iterator = octokit.paginate.iterator(octokit.rest.repos.listForOrg, {
		org: org, per_page: 100
	});

	const repo_cache = [];

	for await (const {data: repos} of repo_iterator) {
		for (const repo of repos) {
			repo_cache.push(repo)
		}
	}

	return repo_cache;
}

async function assemble_repo_collaboration_details(org, repositories, member_map, org_teams_map, linked_member_map) {
	const repo_collaboration_details = [];

	for (const repo of repositories) {
		// console.debug(`Retrieving information about '${repo.name}' repo...`);

		let collaborators_for_repo = await get_collaborators_for_repo(repo, org, "direct", member_map);
		// console.debug(`Retrieved ${collaborators_for_repo.length} collaborators for '${repo.name}' repo...`);

		const team_members_for_repo = await get_team_members_for_repo(repo, org, org_teams_map);
		// console.debug(`Retrieved ${team_members_for_repo.length} team members for '${repo.name}' repo...`);

		let has_admin = false
		let has_member_admin = false

		for (const collaborator of collaborators_for_repo) {
			if (collaborator.role_name === "admin") {
				has_admin = true;
				if (member_map.hasOwnProperty(collaborator.login)) {
					has_member_admin = true;
				}
			}
		}

		let has_admin_team = false;

		for (const team_member of team_members_for_repo) {
			if (team_member.role_name === "admin") {
				has_admin = true
				has_admin_team = true
			}
		}

		collaborators_for_repo = collaborators_for_repo.concat(team_members_for_repo)

		let has_linked_collaborator = false

		for  (const collaborator of collaborators_for_repo) {
			if (linked_member_map.hasOwnProperty(collaborator.login)){
				has_linked_collaborator = true;
			}
		}

		// const workflows_for_repo = await get_workflows_for_repo(org, repo.name);
		// const webhooks_for_repo = await get_webhooks_for_repo(org, repo.name);
		//
		// if (collaborators_for_repo.length > 0) {
		const repo_map = {
			repo_name: repo.name,
			created_at: repo.created_at,
			updated_at: repo.updated_at,
			archived: repo.archived,
			disabled: repo.disabled,
			has_admin: has_admin,
			has_member_admin: has_member_admin,
			has_admin_team: has_admin_team,
			has_linked_collaborator : has_linked_collaborator,
			has_workflows: false,
			has_webhooks: false,
			collaborators: collaborators_for_repo
		}

		repo_collaboration_details.push(repo_map)
		// }
	}

	return repo_collaboration_details;
}

async function get_organization_collaboration_details(org) {

	const member_map = await get_org_members(org);
	// console.debug(`Retrieved '${Object.keys(member_map).length}' organization members....`);

	const org_teams_map = await get_organization_teams(org);
	// console.debug(`Retrieved '${Object.keys(org_teams_map).length}' organization teams....`);

	const org_repositories = await get_org_repositories(org);
	// console.debug(`Retrieved '${org_repositories.length}' organization repositories....`);

	return await assemble_repo_collaboration_details(org, org_repositories, member_map, org_teams_map, member_map);
}

async function find_collaborators(org) {
	const org_collaboration_details = await get_organization_collaboration_details(org);

	const org_collaborators = new Set();

	for (const repo of org_collaboration_details) {
		if (!repo.archived) {
			for (const collaborator of repo.collaborators) {
				if ( collaborator.is_member && collaborator.role_name !== "pull") {
					// const info = {
					// 	login: collaborator.login,
					// 	role_name: collaborator.role_name,
					// 	repo_name: repo.repo_name,
					// 	association_type: collaborator.association_type
					// }
					// org_collaborators.add(info);
					org_collaborators.add(collaborator.login);
				}
			}
		}
	}

	return org_collaborators;
}

async function get_bcgov_removed_members(input_file) {
	const content = await readFile(`${process.cwd()}/${input_file}`);

	// Parse the CSV content
	const records = parse(content, {bom: true});
	const removed_users = [];

	for (const record of records) {
		// console.log(`Removed user: ${record[0]}`);
		removed_users.push(record[0])
	}

	return removed_users;
}

Octokit.js
// https://github.com/octokit/core.js#readme
const octokit = new Octokit({
	auth: process.env.GITHUB_TOKEN
})

const first_org = process.argv[2];
const second_org = process.argv[3];

const invitee_file = process.argv[4];
const uninvitee_file = process.argv[5];
const removed_members_file_name = process.argv[6];

const org_repo_collaborators = Array.from(await find_collaborators(first_org)); // members who have write or higher on one or more repos in first_org
console.log(`There are ${org_repo_collaborators.length} collaborators in ${first_org}`)

const rc_only_users = [];

const members_removed_from_bcgov = await get_bcgov_removed_members(removed_members_file_name);
console.log(`There are ${members_removed_from_bcgov.length} removed members in ${second_org}`)

const first_org_members = await get_org_members(first_org);
console.log(`There are ${first_org_members.length} members in ${first_org}`)

const second_org_members = await get_org_members(second_org);
console.log(`There are ${second_org_members.length} members in ${second_org}`)

// we want to *invite* BCDevOps members to BCGov who aren't already members, who weren't removed from BCGov and who aren't RC only users
const bcdevops_members_excluding_rc_only_users = first_org_members.filter(x => !rc_only_users.includes(x));
const bcdevops_members_not_in_bcgov = bcdevops_members_excluding_rc_only_users.filter(x => !second_org_members.includes(x));
const users_to_invite = bcdevops_members_not_in_bcgov.filter(x => !members_removed_from_bcgov.includes(x));
console.log(`There are ${users_to_invite.length} members to invite to ${second_org}`)

// we want to *remove* users from BCDevOps who are already members of BCGov and who aren't repo collaborators or who aren't RC only users
const first_org_members_less_keepers = bcdevops_members_excluding_rc_only_users.filter(x => !org_repo_collaborators.includes(x));
console.log(`There are ${first_org_members_less_keepers.length} members who are not RC-only users or repo collaborators in ${first_org}`)
const existing_bcgov_users_to_remove = first_org_members_less_keepers.filter(x => second_org_members.includes(x))
const removed_bc_gov_users_to_remove = first_org_members_less_keepers.filter(x => members_removed_from_bcgov.includes(x));
const users_to_remove = existing_bcgov_users_to_remove.concat(removed_bc_gov_users_to_remove);
console.log(`There are ${users_to_remove.length} members to remove from ${first_org}`)

try {
	await writeFile(invitee_file, JSON.stringify(users_to_invite));
	await writeFile(uninvitee_file, JSON.stringify(users_to_remove));
} catch (err) {
	console.error(err);
}
