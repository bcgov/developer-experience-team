import { Octokit } from "octokit";
import fs from 'fs';

const org = "bcgov";
const headers = { 'X-GitHub-Api-Version': '2022-11-28' };

/*************/
const token = "GITHUB_TOKEN";
/*************/

const octokit = new Octokit({ auth: token });

function roundToTwo(num) {
  return +(Math.round(num + "e+2")  + "e-2");
}

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

const getRepoDetails = async (repoName, startDate = null, endDate = null, showRunDetails = false) => {
  let dateStr = undefined;
  if (startDate && endDate)
    dateStr = startDate + ".." + endDate;

  const runSuccessData = await octokit.request(`GET /repos/${org}/${repoName}/actions/runs`, {
    org: org,
    repo: repoName,
    status: 'success',
    created: dateStr,
    headers: headers,
  });
  
  let totalTimeRan = 0;
  let totalJobTimeRan = 0;
  let runCounter = 0;

  const iter = octokit.paginate.iterator(`GET /repos/${org}/${repoName}/actions/runs`, {
    org: org,
    repo: repoName,
    status: 'success',
    per_page: 100,
    created: dateStr,
    headers: headers
  });

  for await (const { data: runs } of iter) {
    for (const r of runs) {
      runCounter++;
      let createTime = new Date(Date.parse(r.created_at));

      let jobTime = await getJobTime(repoName, r.id);
      totalJobTimeRan += jobTime;

      if (showRunDetails)
        console.log(r.name + ", " + roundToTwo(jobTime / 1000 / 60) + ", " + r.created_at);

      let completeTime = new Date(Date.parse(r.updated_at));
      let timeRan = completeTime - createTime;

      if (isNaN(timeRan))
        timeRan = 0;

      totalTimeRan += timeRan;
    }
  }

  totalTimeRan = roundToTwo(totalTimeRan / 1000 / 60);
  totalJobTimeRan = roundToTwo(totalJobTimeRan / 1000 / 60);

  if (startDate === null) {
    startDate = 'creation';
    endDate = 'today';
  }

  console.log('---');
  console.log(repoName + ` - Successful run count from ${startDate} - ${endDate}: ${runCounter}`);
  console.log(repoName + ` - Job time (min) from ${startDate} - ${endDate}: ${totalJobTimeRan}`);
  console.log(repoName + " - Successful run count: " + runSuccessData.data.total_count);
  console.log(repoName + " - Time ran (min): " + totalTimeRan);
};

const getOrgData = async () => {
  const orgData = await octokit.request(`GET /orgs/${org}`, {
    org: org,
    headers: headers,
  });

  console.log("Public Repo Count: " + orgData.data.public_repos);
}

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

const getDetailsBatch = async (RepoList, rangeStart, RangeEnd) => {
  for (const r of RepoList)
    await getRepoDetails(r, rangeStart, RangeEnd);
}

function displayAppUsage() {
  console.log("usage:");
  console.log("\t -o -- Display Organization info");
  console.log("\t -a -- Display all repo workflow usage as csv");
  console.log("\t -a 2023-05-15 2023-08-14 -- Display all repo workflow usage between specified dates as csv");
  console.log("\t -d <repo name> -- Display workflow details for specified repo");
  console.log("\t -d <repo name> 2023-05-15 2023-08-14 -- Display workflow details for specified repo between specified dates");
  console.log("\t -dd -- Same as '-d' but will also display workflow run details");
  console.log("\t -f <file name> -- Same as '-d' but will process a series of repos from a json file\n");
}

if (process.argv.length === 2) {
  displayAppUsage();
  process.exit();
}

if (process.argv[2] && process.argv[2] === '-o') {
  getOrgData();
} else if (process.argv[2] && process.argv[2] === '-a') {
  getAllUsageData(process.argv[3], process.argv[4]);
} else if (process.argv[2] && (process.argv[2] === '-d' || process.argv[2] === '-dd') && process.argv[3]) {
  getRepoDetails(process.argv[3], process.argv[4], process.argv[5], (process.argv[2] === '-dd'));
} else if (process.argv[2] && process.argv[2] === '-f' && process.argv[3]) {
  fs.readFile(process.argv[3], 'utf8', (err, data) => {
    getDetailsBatch(JSON.parse(data), process.argv[4], process.argv[5])
  });
} else {
  displayAppUsage();
}