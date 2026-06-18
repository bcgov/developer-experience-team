import dotenv from "dotenv";
import csv from "csv-parser";
import fs from "fs";
import { Octokit } from "@octokit/rest";

dotenv.config();

const token = process.env.GITHUB_TOKEN_DESTINATION;
const destinationOrgName = process.env.ORG_NAME_DESTINATION;
const csvFile = process.argv[2] || process.env.USER_ACCESS_FILE;

const allowedAccessLevels = new Set(["pull", "push", "admin", "maintain", "triage", "read"]);

const orgMembers = new Map();


if (!token) {
  console.error("Missing required environment variable: GITHUB_TOKEN_DESTINATION");
  process.exit(1);
}

if (!csvFile) {
  console.error("Usage: node user-permissions.js <path-to-csv>");
  console.error("Or set USER_ACCESS_FILE in your .env file.");
  process.exit(1);
}

const octokit = new Octokit({
  auth: token,
  userAgent: "github-user-repo-permissions",
  baseUrl: "https://api.github.com",
});


async function isUserOrgMember(username, org = destinationOrgName) {
  let isMember = false;
  if (orgMembers.has(username)) {
    isMember = orgMembers.get(username);  
  }else {
    try {
      await octokit.request("GET /orgs/{org}/members/{username}", {
        org,
        username,
        headers: { "X-GitHub-Api-Version": "2022-11-28" },
      });
      isMember = true;
    } catch (error) {
      isMember = false;
    }
    orgMembers.set(username, isMember);
  }
  return isMember;
}

async function ensureRepoExists(owner, repo) {
  await octokit.request("GET /repos/{owner}/{repo}", {
    owner,
    repo,
    headers: { "X-GitHub-Api-Version": "2022-11-28" },
  });
}

async function setUserAccess(owner, repo, username, permission) {
  await octokit.request("PUT /repos/{owner}/{repo}/collaborators/{username}", {
    owner,
    repo,
    username,
    permission,
    headers: { "X-GitHub-Api-Version": "2022-11-28" },
  });
}

function formatError(error) {
  if (!error) {
    return "Unknown error";
  }

  if (typeof error === "string") {
    return error;
  }

  if (error.status && error.message) {
    return `HTTP ${error.status}: ${error.message}`;
  }

  return error.message || "Unknown error";
}

async function processCsvRows() {
  let rowNumber = 1;
  let successCount = 0;
  let errorCount = 0;

  const stream = fs.createReadStream(csvFile).pipe(csv());

  for await (const row of stream) {
    rowNumber += 1;

    const repo = (row.REPO || "").trim();
    const username = (row.USER || "").trim();
    const access = (row.ACCESS || "").trim().toLowerCase();

    if (!repo || !username || !access) {
      errorCount += 1;
      console.error(
        `[row ${rowNumber}] Missing required value(s). Expected REPO, USER, ACCESS. Got REPO='${repo}', USER='${username}', ACCESS='${access}'`
      );
      continue;
    }

    if (!allowedAccessLevels.has(access)) {
      errorCount += 1;
      console.error(
        `[row ${rowNumber}] Invalid ACCESS '${access}' for ${repo} / ${username}. Allowed values: ${Array.from(allowedAccessLevels).join(", ")}`
      );
      continue;
    }
    

    if (!(await isUserOrgMember(username))) {
      errorCount += 1;
      console.error(`[row ${rowNumber}] Invalid USER '${username}': ${formatError("User is not a member of the organization")}`);
      continue;
    }

    try {
      await ensureRepoExists(destinationOrgName, repo);
    } catch (error) {
      errorCount += 1;
      console.error(`[row ${rowNumber}] Could not access REPO '${repo}': ${formatError(error)}`);
      continue;
    }

    try {
      await setUserAccess(destinationOrgName, repo, username, access);
      successCount += 1;
      console.log(`[row ${rowNumber}] Updated ${username} on ${destinationOrgName}/${repo} with '${access}' access`);
    } catch (error) {
      errorCount += 1;
      console.error(
        `[row ${rowNumber}] Failed updating ${username} on ${destinationOrgName}/${repo} with '${access}' access: ${formatError(error)}`
      );
    }
  }

  console.log(`Done. Successful rows: ${successCount}. Failed rows: ${errorCount}.`);
}

processCsvRows().catch((error) => {
  console.error(`Fatal error: ${formatError(error)}`);
  process.exit(1);
});