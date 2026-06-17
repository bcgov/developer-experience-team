import dotenv from "dotenv";
import csv from "csv-parser";
import fs from "fs";
import { Octokit } from "@octokit/rest";

dotenv.config();

const token = process.env.GITHUB_TOKEN_DESTINATION;
const csvFile = process.argv[2] || process.env.USER_ACCESS_FILE;

const allowedAccessLevels = new Set(["pull", "push", "admin", "maintain", "triage"]);

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

function parseRepoUrl(rawUrl) {
  if (!rawUrl || typeof rawUrl !== "string") {
    throw new Error("REPO is empty");
  }

  let parsed;
  try {
    parsed = new URL(rawUrl.trim());
  } catch {
    throw new Error("REPO is not a valid URL");
  }

  const hostname = parsed.hostname.toLowerCase();
  const allowedHosts = new Set(["github.com", "www.github.com"]);
  if (!allowedHosts.has(hostname)) {
    throw new Error("REPO must be a GitHub URL");
  }

  const segments = parsed.pathname
    .replace(/^\/+/, "")
    .replace(/\.git$/, "")
    .split("/")
    .filter(Boolean);

  if (segments.length < 2) {
    throw new Error("REPO URL must include owner and repository name");
  }

  const owner = segments[0];
  const repo = segments[1];
  return { owner, repo };
}

async function ensureUserExists(username) {
  await octokit.request("GET /users/{username}", {
    username,
    headers: { "X-GitHub-Api-Version": "2022-11-28" },
  });
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

    const repoUrl = (row.REPO || "").trim();
    const username = (row.USER || "").trim();
    const access = (row.ACCESS || "").trim().toLowerCase();

    if (!repoUrl || !username || !access) {
      errorCount += 1;
      console.error(
        `[row ${rowNumber}] Missing required value(s). Expected REPO, USER, ACCESS. Got REPO='${repoUrl}', USER='${username}', ACCESS='${access}'`
      );
      continue;
    }

    if (!allowedAccessLevels.has(access)) {
      errorCount += 1;
      console.error(
        `[row ${rowNumber}] Invalid ACCESS '${access}' for ${repoUrl} / ${username}. Allowed values: ${Array.from(allowedAccessLevels).join(", ")}`
      );
      continue;
    }

    let owner;
    let repo;
    try {
      const parsed = parseRepoUrl(repoUrl);
      owner = parsed.owner;
      repo = parsed.repo;
    } catch (error) {
      errorCount += 1;
      console.error(`[row ${rowNumber}] Invalid REPO '${repoUrl}': ${formatError(error)}`);
      continue;
    }

    try {
      await ensureUserExists(username);
    } catch (error) {
      errorCount += 1;
      console.error(`[row ${rowNumber}] Invalid USER '${username}': ${formatError(error)}`);
      continue;
    }

    try {
      await ensureRepoExists(owner, repo);
    } catch (error) {
      errorCount += 1;
      console.error(`[row ${rowNumber}] Could not access REPO '${repoUrl}': ${formatError(error)}`);
      continue;
    }

    try {
      await setUserAccess(owner, repo, username, access);
      successCount += 1;
      console.log(`[row ${rowNumber}] Updated ${username} on ${owner}/${repo} with '${access}' access`);
    } catch (error) {
      errorCount += 1;
      console.error(
        `[row ${rowNumber}] Failed updating ${username} on ${owner}/${repo} with '${access}' access: ${formatError(error)}`
      );
    }
  }

  console.log(`Done. Successful rows: ${successCount}. Failed rows: ${errorCount}.`);
}

processCsvRows().catch((error) => {
  console.error(`Fatal error: ${formatError(error)}`);
  process.exit(1);
});