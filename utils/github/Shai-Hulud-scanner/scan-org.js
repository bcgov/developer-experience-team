// require('dotenv').config();
require('dotenv').config();
const fs = require('fs');
const path = require('path');
const axios = require('axios');

// Parse known compromised packages
function loadCompromisedPackages(filePath) {
	console.log(`Loading known compromised packages from ${filePath}`);
	const content = fs.readFileSync(filePath, 'utf8');
	const lines = content.split('\n').slice(1); // skip header
	const compromised = {};

	for (const line of lines) {
		if (!line.trim()) continue;
		const parts = line.split('\t');
		if (parts.length < 2) continue;
		const pkg = parts[0].trim();
		const versions = parts[1].split(',').map(v => v.trim());
		compromised[pkg] = versions;
	}

	console.log(`Loaded ${Object.keys(compromised).length} known compromised packages`);
	// console.log(`Compromised package list: ${JSON.stringify(compromised, null, 2)}`);

	return compromised;
}

const compromisedPackages = loadCompromisedPackages(
	path.join(__dirname, 'known-compromised-packages.txt')
);

const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
const ORG_NAME = process.env.GITHUB_ORG;

if (!GITHUB_TOKEN || !ORG_NAME) {
	console.error('Set GITHUB_TOKEN and GITHUB_ORG env vars.');
	process.exit(1);
}

const githubApi = axios.create({
	baseURL: 'https://api.github.com',
	headers: {
		Authorization: `Bearer ${GITHUB_TOKEN}`,
		'User-Agent': 'Shai-Hulud-scanner',
		'Accept': 'application/vnd.github+json'
	}
});

// --- NEW: request helper with retries and rate-limit handling ---
function sleep(ms) {
	return new Promise(resolve => setTimeout(resolve, ms));
}

async function doRequestWithRetries(path, opts = {}) {
	const maxAttempts = 5;
	const baseDelayMs = 1000;
	let attempt = 0;

	while (true) {
		attempt++;
		try {
			const res = await githubApi.get(path, opts);

			// If headers indicate quota exhausted, wait until reset
			const remaining = res.headers && (res.headers['x-ratelimit-remaining'] || res.headers['X-Ratelimit-Remaining']);
			const reset = res.headers && (res.headers['x-ratelimit-reset'] || res.headers['X-Ratelimit-Reset']);
			if (remaining !== undefined && Number(remaining) === 0 && reset) {
				const waitMs = Math.max(0, Number(reset) * 1000 - Date.now() + 1000);
				console.warn(`Rate limit reached. Waiting ${waitMs}ms until reset.`);
				await sleep(waitMs);
			}

			return res;
		} catch (err) {
			const status = err.response && err.response.status;
			const headers = err.response && err.response.headers;

			// If 404, bubble up so caller can treat as "dependency graph disabled"
			if (status === 404) {
				throw err;
			}

			// If rate-limit response present, wait until reset then retry
			const rem = headers && (headers['x-ratelimit-remaining'] || headers['X-Ratelimit-Remaining']);
			const rst = headers && (headers['x-ratelimit-reset'] || headers['X-Ratelimit-Reset']);
			if (rem !== undefined && Number(rem) === 0 && rst) {
				const waitMs = Math.max(0, Number(rst) * 1000 - Date.now() + 1000);
				console.warn(`Rate limit hit. Sleeping ${waitMs}ms until reset.`);
				await sleep(waitMs);
				// retry without counting this as a hard failure
				continue;
			}

			if (attempt >= maxAttempts) {
				console.warn(`Request to ${path} failed after ${attempt} attempts: ${err.message}`);
				throw err;
			}

			const backoff = baseDelayMs * Math.pow(2, attempt - 1);
			console.warn(`Request to ${path} failed (status=${status || 'network'}). Retry ${attempt}/${maxAttempts} in ${backoff}ms.`);
			await sleep(backoff);
		}
	}
}

// --- END new helper ---

async function getOrgRepos(org) {
	let repos = [];
	let page = 1;
	while (true) {
		// use resilient request helper
		const res = await doRequestWithRetries(`/orgs/${org}/repos`, {params: {per_page: 100, page}});
		repos = repos.concat(res.data);
		if (res.data.length < 100) break;
		page++;
	}
	return repos.map(r => r.name);
}

// remove checkDependencyGraphEnabled usage and instead attempt SBOM directly
async function getRepoDependencyGraph(owner, repo) {
	try {
		const res = await doRequestWithRetries(`/repos/${owner}/${repo}/dependency-graph/sbom`);
		// console.log(JSON.stringify(res.data, null, 2));
		if (res.data.sbom && res.data.sbom.packages && Array.isArray(res.data.sbom.packages)) {
			console.log("SBOM data retrieved successfully.");
			return {packages: res.data.sbom.packages, enabled: true};
		}
		console.log("No dependency information available.");
		return {packages: [], enabled: true};
	} catch (e) {
		// Treat 404 as dependency graph disabled; other errors logged and treated as unavailable
		if (e.response && e.response.status === 404) {
			return {packages: [], enabled: false};
		}
		console.warn(`Failed to get dependency graph for ${owner}/${repo}: ${e.message}`);
		return {packages: [], enabled: false};
	}
}

function findCompromisedInGraph(packages, compromisedPackages) {
	const found = [];
	// Ensure packages is an array before iteration
	if (!packages || !Array.isArray(packages)) {
		console.warn('No packages or invalid packages format received');
		return found;
	} else {
		console.log(` Processing ${packages.length} packages in graph.`)
	}

	for (const pkg of packages) {
		try {
			// Only scan npm packages
			if (!pkg.SPDXID.includes("npm")) continue;
			const name = pkg.name;

			const version = pkg.versionInfo ? "" : pkg.versionInfo.replace(/[\\^:]+/, "");
			// console.debug(`Checking package: "${name}", ${version}`);
			if (compromisedPackages[name]) {
				// console.log(`A version of package "${name}" has been compromised. Comparing used version "${version}" with compromised version list ("${compromisedPackages[name]})...")`);
				if (compromisedPackages[name].includes(version)) {
					found.push({package: name, version});
				}
			}
		} catch (e) {
			console.warn(`Error processing package "${pkg.name}". Error: "${e.message}". Skipping.`);
		}
	}


	return found;
}

async function scanOrg(selectedRepos = null) {
	const results = [];
	let repos;
	if (selectedRepos && selectedRepos.length > 0) {
		repos = selectedRepos;
		console.log(`Scanning only specified repositories: ${repos.join(', ')}`);
	} else {
		repos = await getOrgRepos(ORG_NAME);
		console.log(`Found ${repos.length} repositories in ${ORG_NAME} organization`);
	}

	for (const repo of repos) {
		console.log(`Checking repository: ${repo}`);

		console.log(`  Retrieving dependency information (tries sbom endpoint)...`);
		const {packages, enabled} = await getRepoDependencyGraph(ORG_NAME, repo);
		console.log(`  Dependency graph enabled: ${enabled ? 'Yes' : 'No'}`);

		if (enabled) {
			console.log(`  Found ${packages.length} packages`);
			const compromised = findCompromisedInGraph(packages, compromisedPackages);
			if (compromised.length > 0) {
				console.log(`  ⚠️ Found ${compromised.length} compromised packages!`);
				results.push({repo, compromised});
			} else {
				console.log(`  ✓ No compromised packages found`);
			}
		} else {
			console.log(`  Skipping package processing: dependency graph not enabled or unavailable`);
		}

		console.log('');
	}

	return results;
}

(async () => {
	// Parse repo names from command line arguments (after node and script name)
	const repoArgs = process.argv.slice(2);
	let selectedRepos = null;
	if (repoArgs.length > 0) {
		selectedRepos = repoArgs;
	}

	console.log('Starting Shai-Hulud dependency scanner...');
	const findings = await scanOrg(selectedRepos);

	console.log('\n=== SCAN RESULTS ===');
	if (findings.length > 0) {
		console.log(`Found compromised packages in ${findings.length} repositories.`);
		console.log(JSON.stringify(findings, null, 2));
	} else {
		console.log('No compromised packages found in any repository.');
	}
	console.log('=== END RESULTS ===\n');
})();
