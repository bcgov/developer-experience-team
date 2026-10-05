---
name: create github repository input JSON file
description: Create a JSON input file assigning GitHub users and teams to a list of repositories. The input file is used with the utils/github/create-repos script.
argument-hint: Provide repository names, users, team slugs, permissions, and output JSON path.
agent: agent
---

Create or update a JSON input file for `utils/github/create-repos` using the repository names, users, team slugs, and permissions supplied in the request. Apply the supplied user and team assignments to every repository unless the request specifies different assignments for particular repositories.

Use this input shape, with one object per repository. Include `users` and/or `teams` only when they have entries:

```json
[
  {
    "name": "repository-name",
    "users": [
      { "name": "github-username-1", "permission": "push" },
      { "name": "github-username-2", "permission": "admin" }
    ],
    "teams": [
      { "slug": "team-slug-1", "permission": "admin" },
      { "slug": "team-slug-2", "permission": "maintain" }
    ]
  }
]
```

Requirements:
- Preserve every repository name exactly as provided, including capitalization and order.
- Add every supplied user and team to each repository, preserving the supplied names and order. Do not duplicate an assignment within a repository.
- Each user needs a GitHub username and permission; each team needs a team slug and permission. If one permission is explicitly given for all users and/or teams, apply it to those entries. If permissions differ, use the permission specified for each identity.
- Supported permissions are `pull`, `triage`, `push`, `maintain`, and `admin`.
- If a requested permission is 'read' it should be mapped to the supported `pull` permission.
- If a requested permission is 'write' it should be mapped to the supported `push` permission.
- Repository names must be unique within the input file.
- Repository names must be alphanumeric and may include hyphens, periods, and underscores, but must not contain spaces or other special characters.
- At least one user or team assignment is required for each repository. Omit an absent `users` or `teams` field; do not emit empty arrays or fields not shown in the input schema.
- Use the output path specified by the user. If no file path is specified prompt for a file path suggesting to create the file in the `utils/github/create-repos` directory.
- If repository names, all user/team assignments, or required permissions are missing or ambiguous, ask for the missing information before editing.
- Do not run the repository creation script or make GitHub API calls. This task only prepares the JSON input file.
- Validate that each requested repository appears exactly once, and every requested user/team appears exactly once per applicable repository with the correct permission.
- Validate the generated file against the exported `repoSchema` from `utils/github/create-repos/src/validation.js`, using `repoSchema.safeParse(...)`. From the workspace root, run a Node.js check like this, replacing the placeholder with the generated file path:

  ```sh
  node --input-type=module -e '
  import { readFile } from "node:fs/promises";
  import { repoSchema } from "./utils/github/create-repos/src/validation.js";

  const json = JSON.parse(await readFile(process.argv[1], "utf8"));
  const result = repoSchema.safeParse(json);
  if (!result.success) {
    console.error(result.error.issues);
    process.exit(1);
  }
  console.log("Input matches repoSchema.");
  ' "<generated-file-path>"
  ```

- Do not call `validateJSONFile` for this check; it performs GitHub API lookups. `repoSchema.safeParse` validates structure locally without those lookups.
- Do not include any fields other than `name`, `users`, and `teams` in the repository objects.
- Do not include any additional metadata or comments within the repository objects.
- Do not include any repository names, users, or team slugs that are not part of the requested assignments.

The utility rejects extra fields and permissions outside the supported list. Avoid scanning the project for schema details unless validation reveals a contradiction with these instructions.