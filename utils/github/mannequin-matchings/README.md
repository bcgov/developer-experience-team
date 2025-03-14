# Readme


When the [gh-migration-scripts](https://github.com/martins-vds/gh-migration-scripts) reclaim mannequin process is run it creates a file of all mannequins in the destination org. We don't want to reclaim all mannequins, only those that were part of the migration process.

This script creates a new file that only contains the mannequins we want to reclaim.

## Setup

An `.env` file with the following keys is required:

* MANNEQUIN_FILE = this is the file produced from the [gh-migration-scripts](https://github.com/martins-vds/gh-migration-scripts) mannequin process 
* MAPPING_FILE = this is a file created by the user of the script. It must map EMU users to GitHub public users. Don't include blank mappings
* OUTPUT_FILE = The new mannequin file. Use this as input for the [gh-migration-scripts](https://github.com/martins-vds/gh-migration-scripts)  reclaim mannequin process.

### Example mapping file:

```text
origin,destination
User1_bcgovent,MyCoolGitHubUser
User2_bcgovent,Bravo1
```

* origin - the GitHub user name in the EMU environment for a given user
* destination - the public GitHub user name for that user


## Running the script

```
npm start
```