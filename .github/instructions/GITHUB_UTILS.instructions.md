---
applyTo: "utils/github/**/*"
---
The utilities in this directory are used by GitHub organization owners for infrequent tasks such as looking up user access, repo access, transferring repos in bulk etc., and performing other administrative actions. These utilities are run from the organization owner's local development environment.

When adding new utilities to this directory, ensure they follow the established patterns for authentication, error handling, and logging to maintain consistency and reliability. 

Use the octokit library for interacting with the GitHub REST API when REST API access is required. Use the github-common package in the utils/github/github-common directory for ocktokit and logging usage. Do not bypass these utilities for direct API calls or logging, as it may lead to inconsistencies and security risks. Use paging functionality when needed. Do not omit paging when dealing with paginated API responses.

Ensure that all utilities include proper error handling to gracefully manage API failures or unexpected conditions, and log relevant information for troubleshooting and auditing purposes.

Additionally, document the purpose and usage of each utility clearly, so that other organization owners can understand and utilize them effectively.

Ensure that any sensitive information, such as access tokens or credentials, is handled securely and not hard-coded into the utilities. Use environment variables or secure storage mechanisms to manage such information safely.

Follow the principle of least privilege when requesting access to GitHub resources, and always review and validate the permissions required by each utility to minimize security risks.

Never run API calls that modify, update or delete GitHub resources without explicit confirmation from the user.

Always provide clear prompts and warnings to the user before performing any destructive actions, and allow them to cancel the operation if needed.

Ensure that all user interactions are intuitive and informative, guiding the user through the necessary steps and providing feedback on the success or failure of the operations performed.
