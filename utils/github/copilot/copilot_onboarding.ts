import {Octokit} from "@octokit/rest";
import * as readline from 'readline';
// @ts-ignore
import consoleLogLevel from 'console-log-level';


// Function to assign Copilot license to a user
async function assignCopilotLicense(octokit: Octokit, org: string, githubId: string) {
	console.log(`Assigning Copilot license to '${githubId}'...`);
	try {
		await octokit.request('POST /orgs/{org}/copilot/billing/selected_users', {
			org: org,
			selected_usernames: [
				`${githubId}`,
			],
			headers: {
				'X-GitHub-Api-Version': '2022-11-28'
			}
		})
		console.log(`Successfully assigned Copilot license to ${githubId}`);
	} catch (error: any) {
		console.error(
			`Failed to assign Copilot license to ${githubId}: ${error.message}`
		);
	}
}

// Check if a user is a member of the organization
async function isUserInOrg(octokit: Octokit, org: string, githubId: string): Promise<boolean> {
	try {
		await octokit.orgs.checkMembershipForUser({ org, username: githubId });
		return true;
	} catch (error: any) {
		if (error.status === 404) {
			console.log(`${githubId} is not a member of the organization '${org}'`);
			return false;
		}
		throw error;
	}
}

// Invite a user to the organization by username (fetch user id first)
async function inviteUserToOrg(octokit: Octokit, org: string, githubId: string) {
	try {
		const { data: user } = await octokit.users.getByUsername({ username: githubId });
		await octokit.orgs.createInvitation({
			org,
			invitee_id: user.id,
			role: 'direct_member',
		});
		console.log(`Invited ${githubId} to organization '${org}'`);
	} catch (error: any) {
		console.error(`Failed to invite ${githubId} to organization '${org}': ${error.message}`);
	}
}

// Add a user to a team within an organization
async function addUserToTeam(
	octokit: Octokit,
	org: string,
	teamName: string,
	githubId: string
) {
	try {
		await octokit.teams.addOrUpdateMembershipForUserInOrg({
			org: org,
			team_slug: teamName,
			username: githubId,
			role: 'member'
		});
		console.log(`Added ${githubId} to team '${teamName}' in org '${org}'`);
	} catch (error: any) {
		console.error(
			`Failed to add ${githubId} to team '${teamName}' in org '${org}': ${error.message}`
		);
	}
}

async function configureUserForCopilot(octokit: Octokit, org: string, cohortOrgName: string, cohortTeamName: string, githubIds: string[],) {
	for (const githubId of githubIds) {
		await assignCopilotLicense(octokit, org, githubId);

		const isMember = await isUserInOrg(octokit, cohortOrgName, githubId);
		if (isMember) {
			await addUserToTeam(octokit, cohortOrgName, cohortTeamName, githubId);
			console.log(`${githubId} is a member. Added to team '${cohortTeamName}' in org '${cohortOrgName}'.`);
		} else {
			await inviteUserToOrg(octokit, cohortOrgName, githubId);
			console.log(`${githubId} is not a member. Invitation sent to join '${cohortOrgName}'. Not adding to team yet.`);
		}
	}
}

async function processLineByLine(): Promise<string[]> {
	return new Promise((resolve, reject) => {
		const github_ids: string[] = [];

		const rl = readline.createInterface({
			input: process.stdin,
			crlfDelay: Infinity, // Ensure correct handling of line endings
		});

		rl.on('line', (line) => {
			// Process each line of input here
			console.log(`Received: ${line}`);

			// Example: Splitting comma-separated values
			const values = line.split(',');
			console.log(`Values: ${values}`);
			github_ids.push(values[0].trim());
		});

		rl.on('close', () => {
			// Perform actions after all lines are read
			console.log('Finished reading input.');
			resolve(github_ids);
		});

		rl.on('error', (error) => {
			console.error(`Error reading input: ${error.message}`);
			reject(error);
		});
	})

}

// Function to process CSV file
async function processCsvFile(filePath: string): Promise<string[]> {
	const fs = require('fs');
	const csv = require('csv-parser');

	return new Promise((resolve, reject) => {
		const github_ids: string[] = [];

		fs.createReadStream(filePath)
			.pipe(csv())
			.on('data', (row: any) => {
				console.debug(`Received row: ${JSON.stringify(row)}`);
				github_ids.push(row['github_id']);
			})
			.on('end', () => {
				console.debug('Finished reading CSV file.');
				resolve(github_ids);
			})
			.on('error', (error: any) => {
				console.error(`Error reading CSV file: ${error.message}`);
				reject(error);
			});
	});
}

// Main function to determine input source and assign licenses
async function main() {
	// Read GitHub token from environment variable
	const GITHUB_TOKEN = process.env.GITHUB_TOKEN;

	if (!GITHUB_TOKEN) {
		console.error("Error: GITHUB_TOKEN environment variable is not set.");
		process.exit(1);
	}

// Check for mandatory command-line arguments
	const args = process.argv.slice(2);
	if (args.length < 2) {
		console.error("Usage: node script.js <org_name> [csv_file_path]");
		process.exit(1);
	} else {
		console.log(`Organization name: '${args[0]}', Cohort org name: '${args[1]}', Cohort team name: '${args[2]}', file path: '${args[3]}'`);
	}

	const [org_name, cohortOrgName, cohortTeamName, csvFilePath] = args;

	// Initialize Octokit with authentication
	const octokit = new Octokit({
		auth: GITHUB_TOKEN,
		log: consoleLogLevel({level: "error"}),
	});

	try {
		const githubIds = csvFilePath
			? await processCsvFile(csvFilePath)
			: await processLineByLine();

		await configureUserForCopilot(octokit, org_name, cohortOrgName, cohortTeamName, githubIds);
	} catch (error: any) {
		console.error(`Error: ${error.message}`);
	}
}

main();
