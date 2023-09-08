## GitHub Actions Usage
This is a JavaScript app for querying the GitHub API via octokit and providing data on workflow usage for repos belonging to the bcgov organization.

### Getting Started
install:
```
# using npm
npm install
```

invoke:
```
node app.js <options>
```

available options:
```
# Display Organization info
-o

# Display all repo workflow usage as csv
-a

# Display all repo workflow usage between specified dates as csv
-a 2023-05-15 2023-08-14

# Display workflow details for specified repo
-d <repo name>

# Display workflow details for specified repo between specified dates
-d <repo name> 2023-05-15 2023-08-14

# Same as '-d' but will also display workflow run details
-dd

# Same as '-d' but will process a series of repos from a json file
-f <file name>
```

Using the "-f" option allows for batch processing of a series of repos from a file in json format. For example:
```
[
    "repo-1",
    "repo-2",
    "repo-3",
]
```
Additionally, using the batch option with repos running lots of actions will positively **burn** through the GitHub API limit. Consider narrowing down the timeframe to lower API calls.