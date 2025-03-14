import dotenv from "dotenv";
import { Octokit } from "@octokit/rest";
import csv from "csv-parser";
import fs from "fs";
import { promisify } from "util";
import { exec } from "child_process";

dotenv.config();

const destinationPAT = process.env.GITHUB_TOKEN_DESTINATION;
const destinationOrgName = process.env.ORG_NAME_DESTINATION;
const sourceOrgName = process.env.ORG_NAME_SOURCE;
const repo_file = process.env.REPO_FILE;

const execPromise = promisify(exec);

const octokitDestination = new Octokit({
  auth: destinationPAT,
  userAgent: "org-search",
  timeZone: "UTC",
  baseUrl: "https://api.github.com",
  log: {
    debug: () => {},
    info: console.info,
    warn: console.warn,
    error: console.error,
  },
  request: {
    agent: undefined,
    fetch: undefined,
    timeout: 0,
  },
});

async function getTeamIds(teamNames) {
  const teams = teamNames.split(" ");
  let teamIds = [];


  for(var team of teams) {
    let response = await octokitDestination.request(
      "GET /orgs/{org}/teams/{team_slug}",
      {
        org: destinationOrgName,
        team_slug: team,
        headers: {
          "X-GitHub-Api-Version": "2022-11-28",
        },
      }
    );
    teamIds.push(response.data.id);
  }
    
  return teamIds;
}

function formatTeamSyntaxForQuery(teamIds) {
  let syntax = "";
  for(var teamId of teamIds) {
    syntax += `-F "team_ids[]=${teamId}" `
  }
  return syntax;
}

async function transferRepo(repoName, teamIds) {
  console.log(`transferring repo ${repoName}`);
  const teamSyntax = formatTeamSyntaxForQuery(teamIds);
  const { err, stdout, stderr } = await execPromise(
    `gh api --method POST -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" /repos/${sourceOrgName}/${repoName}/transfer -f new_owner=${destinationOrgName} ${teamSyntax}`
  );

  if (err) {
    console.err(err);
    throw err;
  }

  if (stderr) {
    console.error("Error:", stderr);
    throw Error(`Error transferring repo ${repoName}`);
  }
}

async function transferRepos() {
  const stream = fs.createReadStream(repo_file).pipe(csv());

  for await (const data of stream) {
    try {
      let teamIds = await getTeamIds(data.TEAMS); 

      if (teamIds.length > 0) {
        await transferRepo(data.REPO, teamIds); 
      } else {
        throw new Error(`Could not find teamIds for ${data.REPO}`);
      }
    } catch (error) {
      console.error(`Error processing ${data.REPO}. Error: ${error.message}`);
    }
  }
}

async function start() {
  await transferRepos();
}

start();
