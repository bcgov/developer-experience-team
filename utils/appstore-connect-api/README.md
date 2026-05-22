# App Store Connect API Swift Tool

This tool connects to the Apple App Store Connect API using the [AppStoreConnect-Swift-SDK](https://github.com/AvdLee/appstoreconnect-swift-sdk). It can retrieve two types of data from your Apple Developer account:

- **Users**: Download a list of users and their access levels for each app
- **Devices**: Download a list of registered devices used for testing

Results are written to a CSV file for easy analysis and reporting.

## Prerequisites

- Swift 6.1 or later
- An Apple Developer account with App Store Connect API access
- Your API credentials:
  - **Issuer ID**
  - **Key ID**
  - **Private Key (.p8 file)**
  
 Refer to Apple's [Creating API Keys for App Store Connect API](https://developer.apple.com/documentation/appstoreconnectapi/creating-api-keys-for-app-store-connect-api) for instructions on how to create the API key. 

**NOTE:** Use a team API key, not an individual key. Delete the key after usage.

## Setup

1. **Clone the repository and navigate to the project directory:**

   ```sh
   git clone https://github.com/bcgov/developer-experience-team.git
   cd utils/appstore-connect-api
   ```

2. **Set up environment variables with your App Store Connect API credentials:**

   ```sh
   export APPSTORE_ISSUER_ID="12345678-aaaa-bbbb-cccc-1234567890ab"
   export APPSTORE_PRIVATE_KEY_ID="ABCDEFGHIJ"
   export APPSTORE_KEY_PATH="./env/AuthKey_ABCDEFGHIJ.p8"
   ```

   Alternatively, create a `.env` file in the project directory and source it before running the tool:

   ```sh
   # .env file
   export APPSTORE_ISSUER_ID="12345678-aaaa-bbbb-cccc-1234567890ab"
   export APPSTORE_PRIVATE_KEY_ID="ABCDEFGHIJ"
   export APPSTORE_KEY_PATH="./env/AuthKey_ABCDEFGHIJ.p8"
   ```

   Then run:

   ```sh
   source .env
   ```

## Building and Running

### Basic Command Syntax

```sh
swift build
swift run appstore-connect-api [--type <type>] <output_csv_file>
```

### Options

- `--type` - Type of data to download: `users` (default) or `devices`
- `<output_csv_file>` - Desired name for the output CSV file

### Environment Variables Required

- `APPSTORE_ISSUER_ID` - Your App Store Connect API Issuer ID
- `APPSTORE_PRIVATE_KEY_ID` - Your App Store Connect API Key ID
- `APPSTORE_KEY_PATH` - Path to your `.p8` private key file

### Examples

**Download users and their app access (default):**

```sh
swift run appstore-connect-api users.csv
```

**Download registered devices:**

```sh
swift run appstore-connect-api --type devices devices.csv
```

## Output

The output CSV file format depends on the data type downloaded:

### Users Output
- **Columns**: App Name, User Email, User Name, Role
- Contains a list of all users with access to each app in your developer account, along with their assigned role (Admin, Developer, Marketing, etc.)

### Devices Output
- **Columns**: Device ID, Device Name, Device UDID, Device Status, Device Class
- Contains a list of all registered devices used for testing, including their status (enabled/disabled) and device class (iPad, iPhone, etc.)

## Troubleshooting

**Error: "Missing required environment variable: APPSTORE_ISSUER_ID"**

Ensure you have set all required environment variables before running the tool:
```sh
export APPSTORE_ISSUER_ID="your-issuer-id"
export APPSTORE_PRIVATE_KEY_ID="your-key-id"
export APPSTORE_KEY_PATH="path/to/key.p8"
```

**Error: invalidPrivateKey** 

Ensure the path to the `.p8` file is valid and the file exists at the specified location.

## License

MIT
