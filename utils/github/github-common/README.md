# GitHub Common

Shared logging and Octokit utilities for the Node.js projects under `utils/github`.

## Requirements

- Node.js 26 or later
- An ECMAScript module project (`"type": "module"`)

## Add to a Project

Add the package as a local dependency in the consuming project's `package.json`:

```json
{
  "dependencies": {
    "@bcgov/github-common": "file:../github-common"
  }
}
```

Add an `.npmrc` file to the consuming project so npm installs the local package and
its dependencies as a regular package instead of creating a symbolic link:

```ini
install-links=true
```

Then install dependencies from the consuming project directory:

```bash
npm install
```

## Logger

Create a Pino logger with the default configuration:

```js
import { createLogger } from '@bcgov/github-common';

export const logger = createLogger();
```

By default, logs are written to `info.log`. Logging is disabled when
`NODE_ENV=test`, and `LOG_LEVEL` controls the log level when it is set.

The logger can also write to the console or use a different log file:

```js
const logger = createLogger({
  logFile: 'github.log',
  logToConsole: true,
  silentInTest: true,
});
```

Set `logFile` to `null` to disable file logging.

## Octokit

Create an authenticated Octokit client with throttling and shared logging:

```js
import { createOctokit, createLogger } from '@bcgov/github-common';

const logger = createLogger();
const octokit = createOctokit({
  token: process.env.GITHUB_TOKEN,
  userAgent: 'my-github-utility',
  logger,
});
```

`createOctokit` also accepts these optional settings:

- `baseUrl`: GitHub API URL; defaults to `https://api.github.com`.
- `timeZone`: Request time zone; defaults to `UTC`.
- `maxRateLimitRetries`: Number of primary rate-limit retries; defaults to `5`.

Use the shared GitHub API version header when making requests:

```js
import { GH_API_HEADER } from '@bcgov/github-common';

await octokit.request('GET /orgs/{org}/members', {
  org,
  headers: GH_API_HEADER,
});
```

## Updating the Package

Because `install-links=true` installs a packaged snapshot, edits to `github-common`
do not immediately appear in a consuming project's `node_modules` directory. Bump
the package version and reinstall it whenever its exported code changes.

From the `github-common` directory, choose the appropriate semantic version bump:

```bash
npm version patch --no-git-tag-version
```

Use `minor` for backward-compatible new functionality or `major` for breaking API
changes.

Then refresh the dependency from each consuming project directory:

```bash
npm uninstall @bcgov/github-common
npm install @bcgov/github-common@file:../github-common
npm test
```

Commit the updated `github-common/package.json` and each consumer's `package.json`
and `package-lock.json` files.