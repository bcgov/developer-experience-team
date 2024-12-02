import dotenv from "dotenv";
import { Octokit } from "@octokit/rest";
import fs from "fs";
import readline from "readline";
import Mustache from "mustache";
import winston from "winston";


dotenv.config();

const { combine, timestamp, json } = winston.format;
const myTimeZone = () => {
  return new Date().toLocaleString("en-CA", {
    timeZone: "America/Vancouver",
  });
};

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || "info",
  format: combine(timestamp({ format: myTimeZone }), json()),
  transports: [new winston.transports.File({ filename: "info.log" })],
});

const personalAccessToken = process.env.GITHUB_TOKEN;
const listOfRepos = process.env.FILE;
const org = process.env.ORG;
const issueTitle =
  ":rotating_light: ACTION REQUIRED: Confirm Repository Status for Migration by Dec 20 :rotating_light:";

const octokit = new Octokit({
  auth: personalAccessToken,
  userAgent: "auto-issue",
  timeZone: "UTC",
  baseUrl: "https://api.github.com",
  log: {
    debug: () => {},
    info: logger.info.bind(logger),
    warn: logger.warn.bind(logger),
    error: logger.error.bind(logger),
  },
  request: {
    agent: undefined,
    fetch: undefined,
    timeout: 0,
  },
});

async function getOrgOwners() {
  let orgOwners = [];
  const orgResponse = await octokit.request("GET /orgs/{org}/members", {
    org: org,
    headers: {
      "X-GitHub-Api-Version": "2022-11-28",
    },
    role: "admin"
  });
 
  if(orgResponse.data && orgResponse.data.length) {
    orgResponse.data.forEach((user) => {
      orgOwners.push(user.login);
      logger.info(`admin user ${user.login}`)
     });
  }else {
    throw new error("*****NO ADMIN members*******");
  }
 return orgOwners;
}

async function getRepoCollaborators(repo, orgOwners) {
  let collabs = [];
  try {
    const response = await octokit.paginate(
      "GET /repos/{org}/{repo}/collaborators",
      {
        org: org,
        repo: repo,
        per_page: 100,
        permission: "push",
        headers: {
          "X-GitHub-Api-Version": "2022-11-28",
        },
      }
    );

    response.forEach((user) => {
      if (!orgOwners.includes(user.login)) {
        collabs.push(user.login);
      }
    });
  } catch (error) {
    logger.error(`Error getting collaborators for: ${repo}`, error);
  }
  return collabs;
}

async function processRepos(orgOwners, templateName) {
  const file = readline.createInterface({
    input: fs.createReadStream(listOfRepos),
    output: process.stdout,
  });


  file.on("line", async (repo) => {
    let users = await getRepoCollaborators(repo, orgOwners);
    if (!users || !users.length) {
      logger.warn(`No users to mention for repo ${repo}`);
    } 
    const body = getTemplateBody(users, templateName);
    if (isCreateIssue(templateName)) {
      await createIssue(body, repo);
    } else {
      await commentOnIssue(body, repo);
    }

  });
}

async function createIssue(body, repo) {
 try {
    const response = await getIssue(repo);
    if(response?.data?.items?.length) {
      logger.warn(`Skipping ${repo}, issue already exists.`);
    }else {
      await octokit.request("POST /repos/{org}/{repo}/issues", {
        org: org,
        repo: repo,
        title: issueTitle,
        body: body,
        headers: {
          "X-GitHub-Api-Version": "2022-11-28",
        },
      });
    }
 } catch (error) {
   logger.error(`Error processing: ${repo}`, error);
 }
}

async function getIssue(repo) {
  try {
    const query = `repo:${org}/${repo} in:title ${issueTitle} is:issue is:open sort:author-date-desc`;
    const response = await octokit.rest.search.issuesAndPullRequests({
      q: query,
    });
    return response;
  } catch (error) {
    logger.error("Request failed:", error.request);
    logger.error(error.message);
  }

}

async function commentOnIssue(body, repo) {
  try {
    const response = await getIssue(repo);
 
    if (response?.data?.items?.length) {
      const issue = response.data.items[0];
      await octokit.request(
        "POST /repos/{org}/{repo}/issues/{issue_number}/comments",
        {
          org: org,
          repo: repo,
          issue_number: issue.number,
          body: body,
          headers: {
            "X-GitHub-Api-Version": "2022-11-28",
          },
        }
      );
    } else {
      logger.error(`Could not find issue for repo: ${repo}`);
    }
   
 }catch (error) {
   logger.error("Request failed:", error.request);
   logger.error(error.message);
 }
}


function getTemplateBody(users, templateName) {
  const template = fs.readFileSync(templateName, "utf8");
  return Mustache.render(template, { users });
}

function isCreateIssue(templateName) {
  return templateName === "issue.mustache";
}

function getArgs() {
 const args = process.argv.slice(2);
 return args?.length ? args[0] : null;
}

async function start() {
  logger.info("***** Starting ******")
  const templateName = getArgs();
  if(!templateName) {
    throw error("Template not provided");
  }
  const orgOwners = await getOrgOwners();
  await processRepos(orgOwners, templateName);
}

start();
