import assert from 'node:assert/strict';
import { test } from 'node:test';

import { createRepos } from '../src/repository-service.js';

function createMockOctokit() {
  const calls = [];
  return {
    calls,
    request: async (route, parameters) => {
      calls.push({ route, parameters });
      return { status: route.startsWith('POST ') ? 201 : 204 };
    },
  };
}

test('happy path', async () => {
  const json = [{
    name: 'example-repo',
    users: [{ name: 'octocat', permission: 'admin' }],
    teams: [{ name: 'developers', permission: 'push' }],
  }];
  const octokit = createMockOctokit();

  await createRepos(octokit, 'example-org', json);

  assert.deepEqual(octokit.calls.map(({ route }) => route), [
    'POST /orgs/{org}/repos',
    'GET /orgs/{org}/members/{username}',
    'PUT /repos/{owner}/{repo}/collaborators/{username}',
    'PUT /orgs/{org}/teams/{team_slug}/repos/{owner}/{repo}',
  ]);
});

test('ignores additional repository fields', async () => {
  const json = [{
    name: 'example-repo',
    description: 'must not be forwarded',
    visibility: 'public',
    arbitrary: { value: true },
    users: [],
    teams: [{ name: 'developers', permission: 'admin', extra: 'ignored' }],
  }];
  const octokit = createMockOctokit();

  await createRepos(octokit, 'example-org', json);

  assert.deepEqual(octokit.calls, [
    {
      route: 'POST /orgs/{org}/repos',
      parameters: {
        org: 'example-org',
        name: 'example-repo',
        private: true,
        headers: { 'X-GitHub-Api-Version': '2026-03-10' },
      },
    },
    {
      route: 'PUT /orgs/{org}/teams/{team_slug}/repos/{owner}/{repo}',
      parameters: {
        org: 'example-org',
        team_slug: 'developers',
        owner: 'example-org',
        repo: 'example-repo',
        permission: 'admin',
        headers: { 'X-GitHub-Api-Version': '2026-03-10' },
      },
    },
  ]);
});

test('skips users and teams with unsupported permission values', async () => {
  const json = [{
    name: 'example-repo',
    users: [{ name: 'octocat', permission: 'write' }],
    teams: [{ name: 'developers', permission: 'owner' }],
  }];
  const octokit = createMockOctokit();

  await createRepos(octokit, 'example-org', json);

  // only the repository creation call should be made, as the user and team permissions are unsupported
  assert.deepEqual(octokit.calls.map(({ route }) => route), [
    'POST /orgs/{org}/repos',
  ]);
});

test('treats mixed-case permission values as invalid', async () => {
  const json = [{
    name: 'example-repo',
    users: [{ name: 'octocat', permission: 'AdMiN' }],
    teams: [{ name: 'developers', permission: 'PuSh' }],
  }];
  const octokit = createMockOctokit();

  await createRepos(octokit, 'example-org', json);

  // only the repository creation call should be made, as the mixed-case permissions are treated as invalid
  assert.deepEqual(octokit.calls.map(({ route }) => route), [
    'POST /orgs/{org}/repos',
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
    'GET /orgs/{org}/members/{username}',
    'PUT /repos/{owner}/{repo}/collaborators/{username}',
  ]);
});

test('processes when teams provided but users not provided', async() =>{
  const json = [{
    name: 'example-repo',
    teams: [{ name: 'developers', permission: 'pull' }],
  }];
  const octokit = createMockOctokit();
  await createRepos(octokit, 'example-org', json);

  assert.deepEqual(octokit.calls.map(({ route }) => route), [
    'POST /orgs/{org}/repos',
    'PUT /orgs/{org}/teams/{team_slug}/repos/{owner}/{repo}',
  ]);
});

test('does not create repo when both users and teams are not provided', async() =>{
  const json = [{
    name: 'example-repo',
  }];
  const octokit = createMockOctokit();
  await createRepos(octokit, 'example-org', json);

  assert.deepEqual(octokit.calls.map(({ route }) => route), []);
});

test('checks membership only once per user within a run', async () => {
  const json = [
    { name: 'example-repo', users: [{ name: 'octocat', permission: 'pull' }] },
    { name: 'example-repo-2', users: [{ name: 'octocat', permission: 'pull' }] },
  ];
  const octokit = createMockOctokit();

  await createRepos(octokit, 'example-org', json);

  assert.deepEqual(octokit.calls.map(({ route }) => route), [
    'POST /orgs/{org}/repos',
    'GET /orgs/{org}/members/{username}',
    'PUT /repos/{owner}/{repo}/collaborators/{username}',
    'POST /orgs/{org}/repos',
    'PUT /repos/{owner}/{repo}/collaborators/{username}',
  ]);
});

test('does not share the membership cache between runs', async () => {
  const json = [{
    name: 'example-repo',
    users: [{ name: 'octocat', permission: 'pull' }],
  }];
  const octokit = createMockOctokit();

  await createRepos(octokit, 'example-org', json);
  octokit.calls.length = 0;
  await createRepos(octokit, 'example-org', json);

  assert.deepEqual(octokit.calls.map(({ route }) => route), [
    'POST /orgs/{org}/repos',
    'GET /orgs/{org}/members/{username}',
    'PUT /repos/{owner}/{repo}/collaborators/{username}',
  ]);
});