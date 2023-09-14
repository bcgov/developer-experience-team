import { Octokit } from "octokit";
import fs from 'fs';

const org = "bcgov";
const orgc = "bcgov-c";

const headers = { 'X-GitHub-Api-Version': '2022-11-28' };

/****** A GitHub token is required ******/
/* Full control of private repositories is required for bcgov-c commands */
const token = "GITHUB_TOKEN";

const octokit = new Octokit({ auth: token });

function roundToTwo(num) {
  return +(Math.round(num + "e+2")  + "e-2");
}

/*
 * getJobTime: takes a repo name and run id and finds jobs that match the run id
 * it then sums and returns the total time for each job that's part of that run.
 */
const getJobTime = async (repoName, run_id) => {
  const iter = octokit.paginate.iterator(`GET /repos/${org}/${repoName}/actions/runs/${run_id}/jobs`, {
      owner: org,
      repo: repoName,
      run_id: run_id,
      per_page: 100,
      headers: headers,
  });

  let jobTimeSum = 0;

  for await (const { data: jobs } of iter) {
    for (const j of jobs) {
      let jobStartTime = new Date(Date.parse(j.started_at));
      let jobCompleteTime = new Date(Date.parse(j.completed_at));

      let jobTimeRan = jobCompleteTime - jobStartTime;

      if (isNaN(jobTimeRan))
        jobTimeRan = 0;

      jobTimeSum += jobTimeRan;
    }
  }

  return jobTimeSum;
}

/*
 * getRepoDetails: takes a repo name and displays details about successful workflow runs, it can also take start and end dates.
 * the function outputs workflow run data from the jobs associated with each run id.
 */
const getRepoDetails = async (repoName, startDate = null, endDate = null, isBatch = false) => {
  let dateStr = undefined;
  if (startDate && endDate)
    dateStr = startDate + ".." + endDate;

  const iter = octokit.paginate.iterator(`GET /repos/${org}/${repoName}/actions/runs`, {
    org: org,
    repo: repoName,
    status: 'success',
    per_page: 100,
    created: dateStr,
    headers: headers
  });

  if (!isBatch)
    console.log("repo-name, time-span, action-name, job-minutes, started-at, event");

  console.log(repoName + ", " + (dateStr || "all time") + ", , , ,");
  for await (const { data: runs } of iter) {
    for (const r of runs) {
      let jobTime = await getJobTime(repoName, r.id);
      console.log(", , " + r.name + ", " + roundToTwo(jobTime / 1000 / 60) + ", " + r.run_started_at + ", " + r.event);
    }
  }
};

/*
 * getDetailsBatch: a wrapper function that takes a list of repos and displays details for each.
 */
const getDetailsBatch = async (RepoList, rangeStart, RangeEnd) => {
  console.log("repo-name, time-span, action-name, job-minutes, started-at, event");
  for (const r of RepoList)
    await getRepoDetails(r, rangeStart, RangeEnd, true);
}

/*
 * getOrgData: takes an organization name and displays related info
 */
const getOrgData = async (orgName) => {
  const orgData = await octokit.request(`GET /orgs/${orgName}`, {
    org: orgName,
    headers: headers,
  });

  console.log(orgData.data.name);
  console.log("Created at: " + orgData.data.created_at);
  console.log("Public Repo Count: " + orgData.data.public_repos);
  console.log("Private Repo Count: " + orgData.data.total_private_repos);
}

/*
 * getAllUsageData: displays workflow run data for all repos under the bcgov organization.
 * Uses workflow run data rather than the underlying job data due to the API cost of doing org wide scans
 * displays as a csv
 */
const getAllUsageData = async (startDate = null, endDate = null) => {
  let dateStr = undefined;
  if (startDate && endDate)
    dateStr = startDate + ".." + endDate;

  const iter = octokit.paginate.iterator(`GET /orgs/${org}/repos`, {
    org: org,
    per_page: 100,
    sort: 'full_name',
    headers: headers
  });

  console.log('repo-name, workflow-runs');
  for await (const { data: repos } of iter) {
    for (const r of repos) {
      let runData = await octokit.request(`GET /repos/${org}/${r.name}/actions/runs`, {
        org: org,
        repo: r.name,
        created: dateStr,
        headers: headers,
      });

      if (runData.data.total_count > 0)
        console.log(r.name + ", " + runData.data.total_count);
    }
  }
};

/*
 * getAllUserData: takes an organization name and displays repo, admin, and user info as a csv
 */
const getAllUserData = async (orgName) => {
  const iter = octokit.paginate.iterator(`GET /orgs/${orgName}/repos`, {
    org: orgName,
    per_page: 100,
    sort: 'full_name',
    headers: headers
  });

  let orgAdminFilter = [];
  let orgAdminIter = octokit.paginate.iterator(`GET /orgs/${orgName}/members`, {
    org: orgName,
    role: 'admin',
    per_page: 100,
    headers: headers,
  });
  for await (const { data: orgAdmins } of orgAdminIter) {
    for (const oa of orgAdmins) {
      orgAdminFilter.push(oa.login);
    }
  }

  console.log('repo-name, description, last-updated, owner, admin, admin-url, contributors');
  for await (const { data: repos } of iter) {
    for (const r of repos) {
      let desc = (r.description || "<blank>").replaceAll(',', ' ');
      console.log(`${r.name}, ${desc}, ${r.updated_at}, ${r.owner.login}, , ,`);

      let adminIter = octokit.paginate.iterator(`GET /repos/${orgName}/${r.name}/collaborators`, {
        owner: orgName,
        repo: r.name,
        permission: 'admin',
        per_page: 100,
        headers: headers,
      });
      for await (const { data: admins } of adminIter) {
        for (const a of admins) {
          if (!orgAdminFilter.includes(a.login))
            console.log(`, , , , ${a.login}, ${a.html_url},`);
        }
      }

      let anonUsers = [];
      let userIter = octokit.paginate.iterator(`GET /repos/${orgName}/${r.name}/contributors`, {
        owner: orgName,
        repo: r.name,
        anon: 1,
        per_page: 100,
        headers: headers,
      });
      for await (const { data: users } of userIter) {
        for (const u of users) {
          let name = u.login;
          if (name === undefined) {
            name = (u.name + " (anon)").replaceAll(',', ' ');
            if (anonUsers.includes(name))
              continue;
            anonUsers.push(name);
          }
          console.log(", , , , , , " + name);
        }
      }
    }
  }
};

/*
 * getRateLimit: Displays the rate limit status for the authenticated user
 */
const getRateLimit = async () => {
  const limitData = await octokit.request('GET /rate_limit', {
    headers: headers,
  });

  let resetTime = new Date(limitData.data.rate.reset * 1000);
  console.log("Limit: " + limitData.data.rate.limit);
  console.log("Used: " + limitData.data.rate.used);
  console.log("Remaining: " + limitData.data.rate.remaining);
  console.log("Reset: " + resetTime.toString());
}

function displayAppUsage() {
  console.log("usage:");
  console.log("\t -o -- Display Organization info for bcgov");
  console.log("\t -a -- Display all repo workflow usage as csv");
  console.log("\t -a 2023-05-15 2023-08-14 -- Display all repo workflow usage between specified dates as csv");
  console.log("\t -d <repo name> -- Display workflow details for specified repo as csv");
  console.log("\t -d <repo name> 2023-05-15 2023-08-14 -- Display workflow details for specified repo between specified dates");
  console.log("\t -f <file name> -- Same as '-d' but will process a series of repos from a json file");
  console.log("\t -c -- Display Organization info for bcgov-c");
  console.log("\t -u -- Display repo & user info for bcgov-c as csv");
  console.log("\t -r -- Display current API rate limit\n");
}

if (process.argv.length === 2) {
  displayAppUsage();
  process.exit();
}

if (process.argv[2] && process.argv[2] === '-o') {
  getOrgData(org);
} else if (process.argv[2] && process.argv[2] === '-a') {
  getAllUsageData(process.argv[3], process.argv[4]);
} else if (process.argv[2] && process.argv[2] === '-d' && process.argv[3]) {
  getRepoDetails(process.argv[3], process.argv[4], process.argv[5]);
} else if (process.argv[2] && process.argv[2] === '-f' && process.argv[3]) {
  fs.readFile(process.argv[3], 'utf8', (err, data) => {
    getDetailsBatch(JSON.parse(data), process.argv[4], process.argv[5])
  });
} else if (process.argv[2] && process.argv[2] === '-c') {
  getOrgData(orgc);
} else if (process.argv[2] && process.argv[2] === '-u') {
  getAllUserData(orgc);
} else if (process.argv[2] && process.argv[2] === '-r') {
  getRateLimit();
} else {
  displayAppUsage();
}