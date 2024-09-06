import {Octokit} from "octokit";

// Octokit.js
// https://github.com/octokit/core.js#readme
const octokit = new Octokit({
	auth: process.env.GITHUB_TOKEN
})

const org_iterator = octokit.paginate.iterator(octokit.rest.search.users, {
		q: "bc in:name type:org",
		per_page: 100
	}
);

const org_cache = [];

// iterate through each response
for await (const {data: orgs} of org_iterator) {
	for (const org of orgs) {
		// console.log(org)
		if (org.login.includes("bc")) {
			org_cache.push(org)
		}
	}
}

console.log(JSON.stringify(org_cache));
