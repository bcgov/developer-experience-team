import Foundation
import ArgumentParser
@preconcurrency import AppStoreConnect_Swift_SDK


struct MyAppStoreUser {
    var name: String
    var email: String
    var role: String
}


@main
struct AppstoreConnectAPI: AsyncParsableCommand {
    enum DataType: String, ExpressibleByArgument {
        case users
        case devices
        
        var help: String {
            switch self {
            case .users:
                return "Download users and their app access (default)"
            case .devices:
                return "Download registered devices"
            }
        }
    }
    
    @Option(name: .shortAndLong, help: "Type of data to download: users (default) or devices")
    public var type: DataType = .users
    
    @Argument(help: "The name of the output file. The output will be a CSV file.")
    public var outputFileName: String
    
    
    public func run() async throws {
        // Read credentials from environment variables
        guard let issuerID = ProcessInfo.processInfo.environment["APPSTORE_ISSUER_ID"] else {
            throw ValidationError("Missing required environment variable: APPSTORE_ISSUER_ID")
        }
        
        guard let privateKeyID = ProcessInfo.processInfo.environment["APPSTORE_PRIVATE_KEY_ID"] else {
            throw ValidationError("Missing required environment variable: APPSTORE_PRIVATE_KEY_ID")
        }
        
        guard let keyPath = ProcessInfo.processInfo.environment["APPSTORE_KEY_PATH"] else {
            throw ValidationError("Missing required environment variable: APPSTORE_KEY_PATH")
        }
        
        let provider = try APIUtilities.createAPIProvider(
            issuerID: issuerID,
            privateKeyID: privateKeyID,
            privateKeyURL: URL(fileURLWithPath: keyPath)
        )
        
        switch type {
        case .users:
            let usersDownloader = UsersDownloader(provider: provider)
            try await usersDownloader.downloadUsersAndApps(outputFileName: self.outputFileName)
        case .devices:
            let devicesDownloader = DevicesDownloader(provider: provider)
            try await devicesDownloader.downloadDevices(outputFileName: self.outputFileName)
        }
    }
}

