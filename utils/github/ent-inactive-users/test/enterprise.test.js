import assert from 'node:assert/strict';
import { mock, test } from 'node:test';
import { getUserOrgs } from '../src/enterprise.js';

test('getUserOrgs returns orgs from member roles that are in the allowed list', () => {
  const memberRoles = [
    'bcgov-c:member',
    'bcgov:admin',
    'otherorg:member',
  ];
  const orgsToInclude = ['bcgov-c', 'bcgov'];

  const result = getUserOrgs(memberRoles, orgsToInclude);

  assert.deepEqual(result, ['bcgov-c', 'bcgov']);
});

test('getUserOrgs returns empty array when no orgs match the allowed list', () => {
  const memberRoles = [
    'otherorg:member',
    'anotherorg:admin',
  ];
  const orgsToInclude = ['bcgov-c', 'bcgov'];

  const result = getUserOrgs(memberRoles, orgsToInclude);

  assert.deepEqual(result, []);
});

test('getUserOrgs returns all orgs when the orgsToInclude is empty', () => {
  const memberRoles = [
    'bcgov-c:member',
    'bcgov:admin',
    'otherorg:member',
  ];
  const orgsToInclude = [];

  const result = getUserOrgs(memberRoles, orgsToInclude);

  assert.deepEqual(result, ['bcgov-c', 'bcgov', 'otherorg']);
}); 

test('getUserOrgs returns all orgs when the orgsToInclude is null', () => {
    const memberRoles = [   
    'bcgov-c:member',
    'bcgov:admin',
    'otherorg:member',
  ];
  const orgsToInclude = null;           

    const result = getUserOrgs(memberRoles, orgsToInclude);     

  assert.deepEqual(result, ['bcgov-c', 'bcgov', 'otherorg']);
});

test('getUserOrgs returns all orgs when the orgsToInclude is undefined', () => {
    const memberRoles = [   
    'bcgov-c:member',
    'bcgov:admin',
    'otherorg:member',
    ];
    const orgsToInclude = undefined;          

    const result = getUserOrgs(memberRoles, orgsToInclude);

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

  const result = getUserOrgs(memberRoles, orgsToInclude);

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

  const result = getUserOrgs(memberRoles);

  assert.deepEqual(result, ['bcgov-c', 'bcgov', 'otherorg']);
});
