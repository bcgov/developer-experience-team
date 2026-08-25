import assert from 'node:assert/strict';
import { describe, mock, test } from 'node:test';
import { Member, getEnterpriseMembers } from '../src/enterprise.js';

describe("test Member.getUserOrgs", () => {
  test('getUserOrgs returns orgs from member roles that are in the allowed list', () => {
    const memberRoles = [
      'bcgov-c:member',
      'bcgov:admin',
      'otherorg:member',
    ];
    const orgsToInclude = ['bcgov-c', 'bcgov'];
    const member = new Member('test', 'test@example.com', memberRoles);

    const result = member.getUserOrgs(orgsToInclude);

    assert.deepEqual(result, ['bcgov-c', 'bcgov']);
  });

  test('getUserOrgs returns empty array when no orgs match the allowed list', () => {
    const memberRoles = [
      'otherorg:member',
      'anotherorg:admin',
    ];
    const orgsToInclude = ['bcgov-c', 'bcgov'];
    const member = new Member('test', 'test@example.com', memberRoles);

    const result = member.getUserOrgs(orgsToInclude);

    assert.deepEqual(result, []);
  });

  test('getUserOrgs returns all orgs when the orgsToInclude is empty', () => {
    const memberRoles = [
      'bcgov-c:member',
      'bcgov:admin',
      'otherorg:member',
    ];
    const orgsToInclude = [];
    const member = new Member('test', 'test@example.com', memberRoles);

    const result = member.getUserOrgs(orgsToInclude);

    assert.deepEqual(result, ['bcgov-c', 'bcgov', 'otherorg']);
  }); 

  test('getUserOrgs returns all orgs when the orgsToInclude is null', () => {
      const memberRoles = [   
      'bcgov-c:member',
      'bcgov:admin',
      'otherorg:member',
    ];
    const orgsToInclude = null;          
    const member = new Member('test', 'test@example.com', memberRoles);

      const result = member.getUserOrgs(orgsToInclude);     

    assert.deepEqual(result, ['bcgov-c', 'bcgov', 'otherorg']);
  });

  test('getUserOrgs returns all orgs when the orgsToInclude is undefined', () => {
      const memberRoles = [   
      'bcgov-c:member',
      'bcgov:admin',
      'otherorg:member',
      ];
      const orgsToInclude = undefined;         
      const member = new Member('test', 'test@example.com', memberRoles);

      const result = member.getUserOrgs(orgsToInclude);

      assert.deepEqual(result, ['bcgov-c', 'bcgov', 'otherorg']);
  });

  test('getUserOrgs ignores malformed member roles', () => {
    const memberRoles = [
      'bcgov-c:member',
      'malformedrole',
      'bcgov:admin',
      ':missingorg',
      'otherorg:member',
    ];
    const orgsToInclude = ['bcgov-c', 'bcgov'];
    const member = new Member('test', 'test@example.com', memberRoles);

    const result = member.getUserOrgs(orgsToInclude);

    assert.deepEqual(result, ['bcgov-c', 'bcgov']);
  });

  test('getUserOrgs ignores malformed member roles when orgsToInclude is not specified', () => {
    const memberRoles = [
      'bcgov-c:member',
      'malformedrole',
      'bcgov:admin',
      ':missingorg',
      'otherorg:member',
    ];
    const member = new Member('test', 'test@example.com', memberRoles);

    const result = member.getUserOrgs();

    assert.deepEqual(result, ['bcgov-c', 'bcgov', 'otherorg']);
  });
}); 

describe('getEnterpriseMembers', () => {
  test('getEnterpriseMembers filters users who are outside collaborators', async () => {
    const paginate = mock.fn(async (route, params) => {
      assert.equal(route, 'GET /enterprises/{enterprise}/consumed-licenses');
      assert.equal(params.enterprise, 'example-enterprise');
      return [{
        users: [
          {
            github_com_login: 'outside-user1',
            github_com_saml_name_id: '',
            github_com_member_roles: ['bcgov/repo-1:Collaborator'],
          },
          {
            github_com_login: 'outside-user2',
            github_com_saml_name_id: '',
            github_com_member_roles: ['bcgov/repo-2:Collaborator'],
          },
          {
            github_com_login: 'user-with-access',
            github_com_saml_name_id: 'user-with-access@example.com',
            github_com_member_roles: ['bcgov:Member'],
          },
        ],
      }];
    });

    const request = mock.fn(async (route, params) => {
      assert.equal(route, 'GET /orgs/{org}/outside_collaborators');
      assert.equal(params.org, 'bcgov');
      return {
        data: [{ login: 'outside-user1' }, { login: 'outside-user2' }],
      };
    });

    const octokit = {
      paginate,
      request,
    };

    const members = await getEnterpriseMembers(octokit, 'example-enterprise', ['bcgov']);

    assert.equal(request.mock.calls.length, 1);
    assert.equal(members.length, 1);
    assert.equal(members[0].userName, 'user-with-access');
  });
});
