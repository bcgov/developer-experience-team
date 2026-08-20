import assert from 'node:assert/strict';
import { mock, test, beforeEach, afterEach, after, describe } from 'node:test';
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
        headers: { 'X-GitHub-Api-Version': '2022-11-28' },
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
    const member = { userName: 'alice', orgs: ['org-a', 'org-b', 'org-c'] };

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
    const member = { userName: 'alice', orgs: ['org-a'] };

    assert.equal(await hasAuditLogActivity({ request }, member, '2026-05-16'), false);

    const error = Object.assign(new Error('forbidden'), { status: 403 });
    const failingRequest = mock.fn(async () => { throw error; });
    assert.equal(await hasAuditLogActivity({ request: failingRequest }, member, '2026-05-16'), false);
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
      ],
    }]);
    const request = mock.fn(async (route, options) => {
      if (route === 'GET /orgs/{org}/audit-log') {
        return { data: options.org === 'org-a' ? [{ action: 'member.added' }] : [] };
      }
      return { data: { total_count: options.q.includes('commit-active') ? 1 : 0 } };
    });

    const inactive = await getInactiveMembers({ paginate, request }, "default-enterprise", [], 90);

    assert.deepEqual(inactive, [
      new Member(
        'inactive',
        'inactive@example.com',
        ['org-c']
      )
    ]);
    assert.equal(paginate.mock.calls.length, 1);
    assert.equal(request.mock.calls.length, 5);
  });
});