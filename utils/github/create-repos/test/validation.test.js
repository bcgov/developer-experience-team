import assert from "node:assert/strict";
import { test, describe, beforeEach, afterEach } from "node:test";
import { constants } from "http2";
import { validateJSONFile } from "../src/validation.js";

function createMockOctokit(handlers) {
  const calls = [];
  return {
    calls,
    request: async (route, parameters) => {
      calls.push({ route, parameters });
      const handler = handlers[route];
      return typeof handler === "function" ? handler(parameters) : handler;
    },
  };
}

async function assertValidationError(
  octokit,
  json,
  expectedPath,
  expectedMessage,
) {
  await assert.rejects(
    () => validateJSONFile(octokit, "example-org", json),
    (error) => {
      assert.ok(Array.isArray(error.issues));
      assert.ok(
        error.issues.some(
          (issue) =>
            JSON.stringify(issue.path) === JSON.stringify(expectedPath) &&
            (!expectedMessage || issue.message === expectedMessage),
        ),
      );
      return true;
    },
  );
}

describe("validateJSONFile - JSON structure", () => {
  let octokit;
  beforeEach(() => {
    octokit = createMockOctokit({});
  });

  afterEach(() => {
    octokit = null;
  });

  test("accepts repositories with valid users and teams", async () => {
    octokit = createMockOctokit({
      "GET /orgs/{org}/members/{username}": () => ({
        status: constants.HTTP_STATUS_NO_CONTENT,
      }),
      "GET /orgs/{org}/teams/{team_slug}": () => ({
        status: constants.HTTP_STATUS_OK,
      }),
    });
    const json = [
      {
        name: "example-repo",
        users: [{ name: "octocat", permission: "admin" }],
        teams: [{ slug: "developers", permission: "push" }],
      },
    ];

    assert.deepEqual(
      await validateJSONFile(octokit, "example-org", json),
      json,
    );
  });

  test("accepts repositories with only users or only teams", async () => {
    octokit = createMockOctokit({
      "GET /orgs/{org}/members/{username}": () => ({
        status: constants.HTTP_STATUS_NO_CONTENT,
      }),
      "GET /orgs/{org}/teams/{team_slug}": () => ({
        status: constants.HTTP_STATUS_OK,
      }),
    });
    const json = [
      {
        name: "user-repo",
        users: [{ name: "octocat", permission: "pull" }],
      },
      {
        name: "team-repo",
        teams: [{ slug: "developers", permission: "maintain" }],
      },
    ];

    assert.deepEqual(
      await validateJSONFile(octokit, "example-org", json),
      json,
    );
  });

  test("rejects a top-level value that is not an array", async () => {
    await assertValidationError(
      octokit,
      { name: "example-repo", users: [] },
      [],
    );
  });

  test("rejects a missing or empty repository name", async (t) => {
    await t.test("missing name", async () => {
      await assertValidationError(octokit, [{ users: [] }], [0, "name"]);
    });
    await t.test("empty name", async () => {
      await assertValidationError(
        octokit,
        [{ name: "", users: [] }],
        [0, "name"],
      );
    });
  });

  test("requires at least one users or teams property", async () => {
    await assertValidationError(
      octokit,
      [{ name: "example-repo" }],
      [0],
      "You must specify at least one user or team.",
    );

    await assertValidationError(
      octokit,
      [{ name: "example-repo", users: [], teams: [] }],
      [0],
      "You must specify at least one user or team.",
    );

    await assertValidationError(
      octokit,
      [{ name: "example-repo", users: [] }],
      [0],
      "You must specify at least one user or team.",
    );

    await assertValidationError(
      octokit,
      [{ name: "example-repo", teams: [] }],
      [0],
      "You must specify at least one user or team.",
    );
  });

  test("rejects a missing or empty GitHub username", async (t) => {
    await t.test("missing username", async () => {
      await assertValidationError(
        octokit,
        [{ name: "example-repo", users: [{ permission: "pull" }] }],
        [0, "users", 0, "name"],
      );
    });
    await t.test("empty username", async () => {
      await assertValidationError(
        octokit,
        [{ name: "example-repo", users: [{ name: "", permission: "pull" }] }],
        [0, "users", 0, "name"],
      );
    });
  });

  test("rejects a missing or empty team slug", async (t) => {
    await t.test("missing slug", async () => {
      await assertValidationError(
        octokit,
        [{ name: "example-repo", teams: [{ permission: "push" }] }],
        [0, "teams", 0, "slug"],
      );
    });
    await t.test("empty slug", async () => {
      await assertValidationError(
        octokit,
        [{ name: "example-repo", teams: [{ slug: "", permission: "push" }] }],
        [0, "teams", 0, "slug"],
      );
    });
  });

  test("rejects missing or unsupported permissions", async (t) => {
    await t.test("missing user permission", async () => {
      await assertValidationError(
        octokit,
        [{ name: "example-repo", users: [{ name: "octocat" }] }],
        [0, "users", 0, "permission"],
      );
    });
    await t.test("unsupported user permission", async () => {
      await assertValidationError(
        octokit,
        [
          {
            name: "example-repo",
            users: [{ name: "octocat", permission: "write" }],
          },
        ],
        [0, "users", 0, "permission"],
      );
    });
    await t.test("missing team permission", async () => {
      await assertValidationError(
        octokit,
        [{ name: "example-repo", teams: [{ slug: "developers" }] }],
        [0, "teams", 0, "permission"],
      );
    });
    await t.test("unsupported team permission", async () => {
      await assertValidationError(
        octokit,
        [
          {
            name: "example-repo",
            teams: [{ slug: "developers", permission: "write" }],
          },
        ],
        [0, "teams", 0, "permission"],
      );
    });
    await t.test("contains Upper case permission", async () => {
      await assertValidationError(
        octokit,
        [
          {
            name: "example-repo",
            teams: [{ slug: "developers", permission: "Admin" }],
          },
        ],
        [0, "teams", 0, "permission"],
      );
    });
  });

  test("rejects file that has extra fields", async (t) => {
    await t.test("extra field in user object", async () => {
      await assertValidationError(
        octokit,
        [
          {
            name: "example-repo",
            users: [{ name: "octocat", permission: "pull", extra: "field" }],
          },
        ],
        [0, "users", 0],
      );
    });

    await t.test("extra field in team object", async () => {
      await assertValidationError(
        octokit,
        [
          {
            name: "example-repo",
            teams: [{ slug: "developers", permission: "push", extra: "field" }],
          },
        ],
        [0, "teams", 0],
      );
    });

    await t.test("extra field in repo object", async () => {
      await assertValidationError(
        octokit,
        [
          {
            name: "example-repo",
            extra: "field",
            users: [{ name: "octocat", permission: "pull" }],
          },
        ],
        [0],
      );
    });
  });

  test("rejects file with unsupported format", async () => {
    await assertValidationError(
      octokit,
      [{ field1: "field1", field2: "field2" }],
      [0, "name"],
    );
  });
});

describe("validateJSONFile - GitHub API validation", () => {
  test("throws when a user is not a member of the org", async () => {
    const octokit = createMockOctokit({
      "GET /orgs/{org}/members/{username}": () => ({
        status: constants.HTTP_STATUS_NOT_FOUND,
      }),
    });
    const json = [
      { name: "repo1", users: [{ name: "octocat", permission: "pull" }] },
    ];

    await assert.rejects(
      () => validateJSONFile(octokit, "example-org", json),
      (error) => {
        assert.equal(
          error.message,
          "Error validating user octocat in repo repo1: User octocat is not a member of the org example-org",
        );
        return true;
      },
    );
  });

  test("throws when a team does not exist in the org", async () => {
    const octokit = createMockOctokit({
      "GET /orgs/{org}/teams/{team_slug}": () => ({
        status: constants.HTTP_STATUS_NOT_FOUND,
      }),
    });
    const json = [
      { name: "repo1", teams: [{ slug: "ghost-team", permission: "push" }] },
    ];

    await assert.rejects(
      () => validateJSONFile(octokit, "example-org", json),
      (error) => {
        assert.equal(
          error.message,
          "Error validating team ghost-team in repo repo1: Team ghost-team does not exist in the org example-org",
        );
        return true;
      },
    );
  });

  test("propagates 5xx errors raised while checking user membership", async () => {
    const octokit = createMockOctokit({
      "GET /orgs/{org}/members/{username}": () => {
        throw Object.assign(new Error("Internal Server Error"), {
          status: 500,
        });
      },
    });
    const json = [
      { name: "repo1", users: [{ name: "octocat", permission: "pull" }] },
    ];

    await assert.rejects(
      () => validateJSONFile(octokit, "example-org", json),
      (error) => {
        assert.equal(
          error.message,
          "Error validating user octocat in repo repo1: Internal Server Error",
        );
        return true;
      },
    );
  });

  test("propagates 5xx errors raised while checking team existence", async () => {
    const octokit = createMockOctokit({
      "GET /orgs/{org}/teams/{team_slug}": () => {
        throw Object.assign(new Error("Service Unavailable"), { status: 503 });
      },
    });
    const json = [
      { name: "repo1", teams: [{ slug: "developers", permission: "push" }] },
    ];

    await assert.rejects(
      () => validateJSONFile(octokit, "example-org", json),
      (error) => {
        assert.equal(
          error.message,
          "Error validating team developers in repo repo1: Service Unavailable",
        );
        return true;
      },
    );
  });

  test("caches a successful user membership lookup instead of calling the API again", async () => {
    const octokit = createMockOctokit({
      "GET /orgs/{org}/members/{username}": () => ({
        status: constants.HTTP_STATUS_NO_CONTENT,
      }),
    });
    const json = [
      { name: "repo1", users: [{ name: "octocat", permission: "pull" }] },
      { name: "repo2", users: [{ name: "octocat", permission: "push" }] },
    ];

    await validateJSONFile(octokit, "example-org", json);

    assert.deepEqual(
      octokit.calls.map(({ route }) => route),
      ["GET /orgs/{org}/members/{username}"],
    );
  });

  test("caches a successful team lookup instead of calling the API again", async () => {
    const octokit = createMockOctokit({
      "GET /orgs/{org}/teams/{team_slug}": () => ({
        status: constants.HTTP_STATUS_OK,
      }),
    });
    const json = [
      { name: "repo1", teams: [{ slug: "developers", permission: "pull" }] },
      { name: "repo2", teams: [{ slug: "developers", permission: "push" }] },
    ];

    await validateJSONFile(octokit, "example-org", json);

    assert.deepEqual(
      octokit.calls.map(({ route }) => route),
      ["GET /orgs/{org}/teams/{team_slug}"],
    );
  });

  test("stops validating users at the first error instead of checking every user", async () => {
    const octokit = createMockOctokit({
      "GET /orgs/{org}/members/{username}": () => ({
        status: constants.HTTP_STATUS_NOT_FOUND,
      }),
    });
    const json = [
      {
        name: "repo1",
        users: [{ name: "first-bad-user", permission: "pull" }],
      },
      {
        name: "repo2",
        users: [{ name: "second-bad-user", permission: "pull" }],
      },
    ];

    await assert.rejects(() => validateJSONFile(octokit, "example-org", json));

    assert.deepEqual(
      octokit.calls.map(({ route }) => route),
      ["GET /orgs/{org}/members/{username}"],
    );

    assert.equal(octokit.calls[0].parameters.username, "first-bad-user");
  });

  test("stops validating teams at the first error instead of checking every team", async () => {
    const octokit = createMockOctokit({
      "GET /orgs/{org}/teams/{team_slug}": () => ({
        status: constants.HTTP_STATUS_NOT_FOUND,
      }),
    });
    const json = [
      {
        name: "repo1",
        teams: [{ slug: "first-bad-team", permission: "pull" }],
      },
      {
        name: "repo2",
        teams: [{ slug: "second-bad-team", permission: "pull" }],
      },
    ];

    await assert.rejects(() => validateJSONFile(octokit, "example-org", json));

    assert.deepEqual(
      octokit.calls.map(({ route }) => route),
      ["GET /orgs/{org}/teams/{team_slug}"],
    );

    assert.equal(octokit.calls[0].parameters.team_slug, "first-bad-team");
  });
});
