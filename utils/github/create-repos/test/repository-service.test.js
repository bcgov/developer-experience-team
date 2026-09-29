import assert from 'node:assert/strict';
import { test } from 'node:test';
import { constants } from 'http2'
import { createRepos } from '../src/repository-service.js';
import { logger } from '../src/logger.js';

function createMockOctokit() {
  const calls = [];
  return {
    calls,
    request: async (route, parameters) => {
      calls.push({ route, parameters });
      return  route.startsWith('POST ') ? {status: constants.HTTP_STATUS_CREATED, data: {html_url: 'https://example.com/repo'} } : {status: constants.HTTP_STATUS_NO_CONTENT} ;
    },
  };
}

test('happy path', async () => {
  const json = [{
    name: 'example-repo',
    users: [{ name: 'octocat', permission: 'admin' }],
    teams: [{ slug: 'developers', permission: 'push' }],
  }];
  const octokit = createMockOctokit();

  await createRepos(octokit, 'example-org', json);

  assert.deepEqual(octokit.calls.map(({ route }) => route), [
    'POST /orgs/{org}/repos',
    'PUT /repos/{owner}/{repo}/collaborators/{username}',
    'PUT /orgs/{org}/teams/{team_slug}/repos/{owner}/{repo}',
  ]);
});


test('processes when users provided but teams not provided', async() =>{
  const json = [{
    name: 'example-repo',
    users: [{ name: 'user1', permission: 'pull' }],
  }];
  const octokit = createMockOctokit();
  await createRepos(octokit, 'example-org', json);

  assert.deepEqual(octokit.calls.map(({ route }) => route), [
    'POST /orgs/{org}/repos',
    'PUT /repos/{owner}/{repo}/collaborators/{username}',
  ]);
});

test('processes when teams provided but users not provided', async() =>{
  const json = [{
    name: 'example-repo',
    teams: [{ slug: 'developers', permission: 'pull' }],
  }];
  const octokit = createMockOctokit();
  await createRepos(octokit, 'example-org', json);

  assert.deepEqual(octokit.calls.map(({ route }) => route), [
    'POST /orgs/{org}/repos',
    'PUT /orgs/{org}/teams/{team_slug}/repos/{owner}/{repo}',
  ]);
});

test('logs an error for an outside collaborator invitation', async (t) => {
  const octokit = {
    request: async () => { return { status: constants.HTTP_STATUS_CREATED, data: { html_url: 'https://example.com/repo' } }; }
  };
  const logError = t.mock.method(logger, 'error', () => {});

  const result = await createRepos(octokit, 'example-org', [{
    name: 'example-repo',
    users: [{ name: 'outside-user', permission: 'pull' }],
  }]);

  assert.equal(result.hadFailures, true);
  assert.equal(logError.mock.callCount(), 1);
  assert.deepEqual(logError.mock.calls[0].arguments, [
    'ERROR: Invited user outside-user as outside collaborator to repo example-repo. CANCEL THEIR INVITE.',
  ]);
});

test('processes multiple repositories correctly', async () => {
  const json = [
    { name: 'example-repo', users: [{ name: 'octocat', permission: 'pull' }] },
    { name: 'example-repo-2', users: [{ name: 'octocat', permission: 'pull' }] },
  ];
  const octokit = createMockOctokit();

  await createRepos(octokit, 'example-org', json);

  assert.deepEqual(octokit.calls.map(({ route }) => route), [
    'POST /orgs/{org}/repos',
    'PUT /repos/{owner}/{repo}/collaborators/{username}',
    'POST /orgs/{org}/repos',
    'PUT /repos/{owner}/{repo}/collaborators/{username}',
  ]);
});

test('logs a 5xx error and continues processing the next repository', async (t) => {
  const error = Object.assign(new Error('Internal Server Error'), { status: 500 });
  const calls = [];
  const octokit = {
    calls,
    request: async (route, parameters) => {
      calls.push({ route, parameters });
      if (parameters.name === 'failing-repo') {
        throw error;
      }
      return { status: constants.HTTP_STATUS_CREATED, data: { html_url: 'https://example.com/successful-repo' } };
    },
  };
  const logError = t.mock.method(logger, 'error', () => {});

  const result = await createRepos(octokit, 'example-org', [
    { name: 'failing-repo' },
    { name: 'successful-repo' },
  ]);

  assert.deepEqual(calls.map(({ parameters }) => parameters.name), [
    'failing-repo',
    'successful-repo',
  ]);
  assert.deepEqual(result, {
    repoUrls: ['https://example.com/successful-repo'],
    hadFailures: true,
  });
  assert.equal(logError.mock.callCount(), 1);
  assert.deepEqual(logError.mock.calls[0].arguments, [
    { err: error },
    'Error creating repo: failing-repo',
  ]);
});
