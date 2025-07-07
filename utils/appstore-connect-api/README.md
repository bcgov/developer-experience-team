# App Store Connect API Swift Tool

This tool connects to the Apple App Store Connect API using the [AppStoreConnect-Swift-SDK](https://github.com/AvdLee/appstoreconnect-swift-sdk). It retrieves users and their access levels for each app in your Apple Developer account and writes the results to a CSV file.

## Prerequisites

- Swift 6.1 or later
- An Apple Developer account with App Store Connect API access
- Your API credentials:
  - **Issuer ID**
  - **Key ID**
  - **Private Key (.p8 file)**
  
 Refer to Apple's [Creating API Keys for App Store Connect API](https://developer.apple.com/documentation/appstoreconnectapi/creating-api-keys-for-app-store-connect-api) for instructions on how to create the API key. 

## Setup

1. **Clone the repository and navigate to the project directory:**

   ```sh
   git clone https://github.com/bcgov/developer-experience-team.git
   cd utils/appstore-connect-api
   ```

## Building and Running


```sh
swift build
swift run appstore-connect-api --issuer-id <issuer_id> --private-key-id <key_id> --key-path <path_to_p8_file> <output_csv_file>
```

- Replace `<issuer_id>` with your App Store Connect API Issuer ID.
- Replace `<key_id>` with your App Store Connect API Key ID.
- Replace `<path_to_p8_file>` with the path to your `.p8` private key file.
- Replace `<output_csv_file>` with the desired name for the output CSV file (e.g., `results.csv`).

Example:

```sh
swift run appstore-connect-api --issuer-id 12345678-aaaa-bbbb-cccc-1234567890ab --private-key-id ABCDEFGHIJ --key-path ./env/AuthKey_ABCDEFGHIJ.p8 results.csv
```

## Output

- The output CSV file will contain a list of users and their access levels for each app in your Apple Developer account.
- The CSV columns are: App Name, Apple Account, Name, Role

## Troubleshooting

`Error: invalidPrivateKey` 

Ensure the path to the `p8` file is valid.

## License

MIT
