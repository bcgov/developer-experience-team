import { Octokit } from "@octokit/rest";
import { createAppAuth, createOAuthUserAuth } from "@octokit/auth-app";
import { readFile, writeFile } from "node:fs/promises";
import {parse} from "csv-parse/sync";

// authenticate as GitHub App because increased API rate limits are needed
const octokit = new Octokit({
	authStrategy: createAppAuth,
	auth: {
		appId: `${process.env.GITHUB_APP_ID}`,
		installationId: `${process.env.GITHUB_APP_INSTALLATION_ID}`,
		privateKey: `${process.env.GITHUB_APP_PRIVATE_KEY}`,
	},
});

async function get_linked_members(input_file) {
	const content = await readFile(`${process.cwd()}/${input_file}`);

	// Parse the CSV content
	const records = parse(content, {bom: true});
	const linked_member_map = {};

	for (const record of records) {
		// console.log(record[0])
		linked_member_map[record[1]] = record;
	}

	return linked_member_map;
}

async function get_collaborators_for_repo(repo, org, affiliation, member_map) {

	console.debug(`Retrieving collaborators for '${repo.name}' repo...`);

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
		for (const repo_ream of teams) {
			const org_team = organization_teams[repo_ream.slug];
			for (const member of org_team.members) {
				const collaborator = {
					login: member.login,
					role_name: repo_ream.permission,
					is_member: true,
					association_type: "team_member"
				}
				team_members_for_repo.push(collaborator)
			}
		}
	}


	return team_members_for_repo;
}

async function get_organization_members(org) {
// @todo load members and indicate whether collaborators are members or outside
	const member_iterator = octokit.paginate.iterator(octokit.rest.orgs.listMembers, {
		org: org, per_page: 100
	});

	const member_map = {}

	for await (const {data: members} of member_iterator) {
		for (const member of members) {
			// add to map, keyed on login for easy retrieval later
			member_map[member.login] = member
		}
	}

	return member_map;
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

async function get_workflows_for_repo(org, repo) {
	const workflow_iterator = octokit.paginate.iterator(octokit.rest.actions.listRepoWorkflows, {
		owner: org, repo: repo, per_page: 100
	});

	const workflow_cache = [];

	for await (const {data: workflows} of workflow_iterator) {
		for (const workflow of workflows) {
			workflow_cache.push(workflow)
		}
	}

	return workflow_cache;
}

async function get_webhooks_for_repo(org, repo) {
	const webhook_iterator = octokit.paginate.iterator(octokit.rest.repos.listWebhooks, {
		owner: org, repo: repo, per_page: 100
	});

	const webhook_cache = [];

	for await (const {data: webhooks} of webhook_iterator) {
		for (const webhook of webhooks) {
			webhook_cache.push(webhook)
		}
	}

	return webhook_cache;
}

async function assemble_repo_collaboration_details(org, repositories, member_map, org_teams_map, linked_member_map) {
	const repo_collaboration_details = [];

	for (const repo of repositories) {
		console.debug(`Retrieving information about '${repo.name}' repo...`);

		let collaborators_for_repo = await get_collaborators_for_repo(repo, org, "direct", member_map);
		console.debug(`Retrieved ${collaborators_for_repo.length} collaborators for '${repo.name}' repo...`);

		const team_members_for_repo = await get_team_members_for_repo(repo, org, org_teams_map);
		console.debug(`Retrieved ${team_members_for_repo.length} team members for '${repo.name}' repo...`);

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

async function get_organization_collaboration_details(org, linked_members_file) {

	const linked_member_map = await get_linked_members(linked_members_file);
	console.debug(`Retrieved '${Object.keys(linked_member_map).length}' linked organization members....`);

	const member_map = await get_organization_members(org);
	console.debug(`Retrieved '${Object.keys(member_map).length}' organization members....`);

	const org_teams_map = await get_organization_teams(org);
	console.debug(`Retrieved '${Object.keys(org_teams_map).length}' organization teams....`);

	const org_repositories = await get_org_repositories(org);
	console.debug(`Retrieved '${org_repositories.length}' organization repositories....`);

	return await assemble_repo_collaboration_details(org, org_repositories, member_map, org_teams_map, linked_member_map);
}

const linked_members_file = process.argv[2];
console.debug(`Reading linked members from '${linked_members_file}'...`)

const fileName = process.argv[3];
console.debug(`Writing to '${fileName}'...`)

const target_org = process.argv[4];
console.debug(`Target organization is '${target_org}'...`)

const details = await get_organization_collaboration_details(target_org, linked_members_file)

try {
	await writeFile(fileName, JSON.stringify(details));
} catch (err) {
	console.error(err);
}
