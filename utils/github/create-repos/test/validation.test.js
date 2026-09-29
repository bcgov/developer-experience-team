import assert from 'node:assert/strict';
import { test, describe } from 'node:test';
import { validateJSONFile } from '../src/validation.js';

function assertValidationError(json, expectedPath, expectedMessage) {
  assert.throws(() => validateJSONFile(json), (error) => {
    assert.ok(Array.isArray(error.issues));
    assert.ok(error.issues.some((issue) =>
      JSON.stringify(issue.path) === JSON.stringify(expectedPath)
      && (!expectedMessage || issue.message === expectedMessage)
    ));
    return true;
  });
}

describe('validateJSONFile', () => {
    test('accepts repositories with valid users and teams', () => {
        const json = [{
            name: 'example-repo',
            users: [{ name: 'octocat', permission: 'admin' }],
            teams: [{ slug: 'developers', permission: 'push' }],
        }];

        assert.deepEqual(validateJSONFile(json), json);
    });

    test('accepts repositories with only users or only teams', () => {
        const json = [
            {
            name: 'user-repo',
            users: [{ name: 'octocat', permission: 'pull' }],
            },
            {
            name: 'team-repo',
            teams: [{ slug: 'developers', permission: 'maintain' }],
            },
        ];

        assert.deepEqual(validateJSONFile(json), json);
    });

    test('rejects a top-level value that is not an array', () => {
        assertValidationError({ name: 'example-repo', users: [] }, []);
        });

    test('rejects a missing or empty repository name', async (t) => {
        await t.test('missing name', () => {
            assertValidationError([{ users: [] }], [0, 'name']);
        });
        await t.test('empty name', () => {
            assertValidationError([{ name: '', users: [] }], [0, 'name']);
        });
    });

    test('requires at least one users or teams property', () => {
        assertValidationError(
            [{ name: 'example-repo' }],
            [0],
            'You must specify at least one user or team.'
        );

        assertValidationError(
            [{ name: 'example-repo', users: [], teams: [] }],
            [0],
            'You must specify at least one user or team.'
        );

        assertValidationError(
            [{ name: 'example-repo', users: [], }],
            [0],
            'You must specify at least one user or team.'
        );

        assertValidationError(
            [{ name: 'example-repo', teams: [], }],
            [0],
            'You must specify at least one user or team.'
        );
    });

    test('rejects a missing or empty GitHub username', async (t) => {
        await t.test('missing username', () => {
            assertValidationError(
            [{ name: 'example-repo', users: [{ permission: 'pull' }] }],
            [0, 'users', 0, 'name']
            );
        });
        await t.test('empty username', () => {
            assertValidationError(
            [{ name: 'example-repo', users: [{ name: '', permission: 'pull' }] }],
            [0, 'users', 0, 'name']
            );
        });
    });

    test('rejects a missing or empty team slug', async (t) => {
        await t.test('missing slug', () => {
            assertValidationError(
            [{ name: 'example-repo', teams: [{ permission: 'push' }] }],
            [0, 'teams', 0, 'slug']
            );
        });
        await t.test('empty slug', () => {
            assertValidationError(
            [{ name: 'example-repo', teams: [{ slug: '', permission: 'push' }] }],
            [0, 'teams', 0, 'slug']
            );
        });
    });

    test('rejects missing or unsupported permissions', async (t) => {
        await t.test('missing user permission', () => {
            assertValidationError(
            [{ name: 'example-repo', users: [{ name: 'octocat' }] }],
            [0, 'users', 0, 'permission']
            );
        });
        await t.test('unsupported user permission', () => {
            assertValidationError(
            [{ name: 'example-repo', users: [{ name: 'octocat', permission: 'write' }] }],
            [0, 'users', 0, 'permission']
            );
        });
        await t.test('missing team permission', () => {
            assertValidationError(
            [{ name: 'example-repo', teams: [{ slug: 'developers' }] }],
            [0, 'teams', 0, 'permission']
            );
        });
        await t.test('unsupported team permission', () => {
            assertValidationError(
            [{ name: 'example-repo', teams: [{ slug: 'developers', permission: 'write' }] }],
            [0, 'teams', 0, 'permission']
            );
        });
        await t.test('contains Upper case permission', () => {
           assertValidationError(
            [{ name: 'example-repo', teams: [{ slug: 'developers', permission: 'Admin' }] }],
            [0, 'teams', 0, 'permission']
            ); 
        })
    });
});