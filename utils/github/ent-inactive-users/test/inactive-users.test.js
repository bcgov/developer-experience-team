import assert from 'node:assert/strict';
import { mock, test, beforeEach, afterEach, describe } from 'node:test';
import { Member } from '../src/enterprise.js';
import {
  getInactiveMembers,
  getRecentCommitsInOrg,
  getSinceDate,
  hasAuditLogActivity,
  hasAuditLogActivityInOrg,
  hasRecentCommits,
} from '../src/inactive-users.js';


describe("getSinceDate tests", () => {
  const FIXED_NOW = new Date('2026-08-14T12:00:00.000Z');

  beforeEach(() => {
    mock.timers.enable({ apis: ['Date'], now: FIXED_NOW });
  });

  afterEach(() => {
    mock.timers.reset();
  });

  
  test('getSinceDate returns an ISO date and timestamp 50 days ago', () => {

    const result = getSinceDate(50);

    assert.equal(result, '2026-06-25');
  });

  test('getSinceDate returns an ISO date and timestamp 90 days ago by default', () => {
    const result = getSinceDate();

    assert.equal(result, '2026-05-16');
  });

});

describe("activity check tests", () => {

  test('getRecentCommitsInOrg returns true when the search finds commits', async () => {
    const request = mock.fn(async () => ({ data: { total_count: 1 } }));
    const octokit = { request };

    const result = await getRecentCommitsInOrg(octokit, 'alice', 'org-a', '2026-05-16');

    assert.equal(result, true);
    assert.equal(request.mock.calls.length, 1);
    assert.deepEqual(request.mock.calls[0].arguments, [
      'GET /search/commits',
      {
        q: 'author:alice author-date:>2026-05-16 org:org-a',
        headers: { 'X-GitHub-Api-Version': '2026-03-10' },
        per_page: 1,
      },
    ]);
  });

  test('getRecentCommitsInOrg returns false when the search finds no commits', async () => {
    const octokit = { request: mock.fn(async () => ({ data: { total_count: 0 } })) };

    assert.equal(
      await getRecentCommitsInOrg(octokit, 'alice', 'org-a', '2026-05-16'),
      false
    );
  });

  test('getRecentCommitsInOrg treats GitHub 404 and 409 responses as no activity', async () => {
    for (const status of [404, 409]) {
      const error = Object.assign(new Error('not available'), { status });
      const octokit = { request: mock.fn(async () => { throw error; }) };

      assert.equal(
        await getRecentCommitsInOrg(octokit, 'alice', 'org-a', '2026-05-16'),
        false
      );
    }
  });

  test('hasRecentCommits stops after the first organization with activity', async () => {
    const request = mock.fn(async (_route, options) => ({
      data: { total_count: options.q.includes('org-b') ? 1 : 0 },
    }));

    const member = new Member('alice', 'alice@example.com', ['org-a:member', 'org-b:member', 'org-c:member']);

    assert.equal(await hasRecentCommits({ request }, member, '2026-05-16'), true);
    assert.equal(request.mock.calls.length, 2);
  });

  test('hasAuditLogActivityInOrg returns true when the audit log has events', async () => {
    const request = mock.fn(async () => ({ data: [{ action: 'repo.create' }] }));
    const member = { userName: 'alice' };

    assert.equal(
      await hasAuditLogActivityInOrg({ request }, member, 'org-a', '2026-05-16'),
      true
    );
    assert.match(request.mock.calls[0].arguments[1].phrase, /^actor:alice created:>=2026-05-16$/);
  });

  test('hasAuditLogActivity returns false for an empty audit log and API errors', async () => {
    const request = mock.fn(async () => ({ data: [] }));
    const member = new Member('alice', 'alice@example.com', ['org-a:member']);

    assert.equal(await hasAuditLogActivity({ request }, member, '2026-05-16'), false);

    const error = Object.assign(new Error('forbidden'), { status: 403 });
    const failingRequest = mock.fn(async () => { throw error; });
    assert.equal(await hasAuditLogActivity({ request: failingRequest }, member, '2026-05-16'), false);
  });

});

describe("getInactiveMembers tests", () => {

  let request, graphql;

  beforeEach(() => {
    
    request = mock.fn(async (route, options) => {
      if (route === 'GET /orgs/{org}/audit-log') {
        return { data: options.phrase.includes(`actor:audit-active`) ? [{ action: 'pull_request.create' }] : [] };
      }else if (route === 'GET /search/commits') {
        return { data: { total_count: options.q.includes('commit-active') ? 1 : 0 } };
      }else if (route === 'GET /orgs/{org}/outside_collaborators') {
        return { data: [ {login: 'outside-collaborator-1'}, {login: 'outside-collaborator-2'} ]};
      }
    });
    graphql = mock.fn(async () => ({
      enterprise: {
        organizations: {
          nodes: [{ login: 'org-a' }, { login: 'org-b' }, { login: 'org-c' }],
        },
      },
    }));
  });

  afterEach(() => {
    request = null;
    graphql = null;
  });


  test('getInactiveMembers returns only members with no audit or commit activity', async () => {
    
    const paginate = mock.fn(async () => [{
      users: [
        {
          github_com_login: 'audit-active',
          github_com_saml_name_id: 'audit@example.com',
          github_com_member_roles: ['org-a:member'],
        },
        {
          github_com_login: 'commit-active',
          github_com_saml_name_id: 'commit@example.com',
          github_com_member_roles: ['org-b:member'],
        },
        {
          github_com_login: 'inactive',
          github_com_saml_name_id: 'inactive@example.com',
          github_com_member_roles: ['org-c:member'],
        },
        {
          github_com_login: 'outside-collaborator-1',
          github_com_saml_name_id: 'outside-collaborator-1@example.com',
          github_com_member_roles: ['org-a/repo1:Collaborator'],
        },
        {
          github_com_login: 'outside-collaborator-2',
          github_com_saml_name_id: 'outside-collaborator-2@example.com',
          github_com_member_roles: ['org-b/repo2:Collaborator'],
        }
      ],
    }]);
    const inactive = await getInactiveMembers({ paginate, request, graphql }, "default-enterprise", [], 90);

    assert.deepEqual(inactive, [
      new Member(
        'inactive',
        'inactive@example.com',
        ['org-c:member']
      )
    ]);
    assert.equal(paginate.mock.calls.length, 1); // 1 call to get enterprise members
    assert.equal(request.mock.calls.length, 8); // 3 calls to get outside collaborators (1 call for each orgs), 3 calls to get audit logs, 2 calls to get commits
    assert.equal(graphql.mock.calls.length, 1); //1 call to graphql because the orgs list is empty, so we need to get all orgs in the enterprise
  });

  test('getInactiveMembers for specified orgs', async () => {
    
    const paginate = mock.fn(async () => [{
      users: [
        {
          github_com_login: 'audit-active',
          github_com_saml_name_id: 'audit@example.com',
          github_com_member_roles: ['org-a:member'],
        },
        {
          github_com_login: 'commit-active',
          github_com_saml_name_id: 'commit-active@example.com',
          github_com_member_roles: ['org-c:member'],
        },
        {
          github_com_login: 'inactive',
          github_com_saml_name_id: 'inactive@example.com',
          github_com_member_roles: ['org-c:member'],
        },
        {
          github_com_login: 'outside-collaborator-1',
          github_com_saml_name_id: 'outside-collaborator-1@example.com',
          github_com_member_roles: ['org-a/repo1:Collaborator'],
        },
      ],
    }]);

    const inactive = await getInactiveMembers({ paginate, request, graphql }, "default-enterprise", ['org-a', 'org-c'], 90);

    assert.deepEqual(inactive, [
      new Member(
        'inactive',
        'inactive@example.com',
        ['org-c:member']
      )
    ]);
    assert.equal(paginate.mock.calls.length, 1); // 1 call to get enterprise members
    assert.equal(request.mock.calls.length, 7); // 2 calls to get outside collaborators (1 call for each org), 3 calls to get audit logs, 2 calls to get commits
    assert.equal(graphql.mock.calls.length, 0); // 0 calls to graphql because the orgs list is specified, so we don't need to get all orgs in the enterprise
  });

});