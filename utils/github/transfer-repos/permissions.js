import dotenv from "dotenv";
import csv from "csv-parser";
import fs from "fs";
import { promisify } from "util";
import { exec } from "child_process";

dotenv.config();

const execPromise = promisify(exec);

const destinationOrgName = process.env.ORG_NAME_DESTINATION;
const repo_file = process.env.TEAMS_FILE;

async function updateTeamAccess(repoName, teamName, permission) {
  console.log(`Updating permissions for team ${teamName} - repo ${repoName}`);
  const { err, stdout, stderr } = await execPromise(
    `gh api --method PUT -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" /orgs/${destinationOrgName}/teams/${teamName}/repos/${destinationOrgName}/${repoName} -f "permission=${permission}"`
  );
  if (err) {
    console.err(err);
    throw err;
  }
  if (stderr) {
    console.error("Error:", stderr);
    throw Error(`Error updating permissions repo ${repoName}`);
  }
}



async function updatePermissions() {
  try {
    fs.createReadStream(repo_file)
      .pipe(csv())
      .on("data", async (data) => {
        try {
          await updateTeamAccess(data.REPO, data.TEAM, data.PERMISSION);
        } catch (error) {
          console.error(`Error processing ${data}. Error: ${error.message}`);
        }
      });
  } catch (error) {
    console.error(`Error: ${error.message}`);
  }
}

async function start() {
  await updatePermissions();
}

start();
