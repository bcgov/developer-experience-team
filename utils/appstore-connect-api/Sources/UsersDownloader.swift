import Foundation
import AppStoreConnect_Swift_SDK

/// Downloads and exports users and their app access from App Store Connect
struct UsersDownloader {
    let provider: APIProvider
    
    /// Initializes the downloader with the given provider
    init(provider: APIProvider) {
        self.provider = provider
    }
    
    /// Fetches all users and their visible apps, then exports to CSV
    func downloadUsersAndApps(outputFileName: String) async throws {
        // Get all data at once using the paged API
        var users: [User] = []
        for try await page in provider.paged(APIEndpoint.v1.users.get()) {
            users.append(contentsOf: page.data)
        }
        print("Fetched \(users.count) users")
        
        var appsAndUsers: [String: [MyAppStoreUser]] = [:]
        print("Getting apps and users...", terminator: " ")
        fflush(stdout)
        
        for (index, user) in users.enumerated() {
            if (index % 10 == 0) {
                print(".", terminator: " ")
                fflush(stdout)
            }
            
            let email = user.attributes?.username ?? ""
            let name = (user.attributes?.firstName ?? "") + " " + (user.attributes?.lastName ?? "")
            let role = user.attributes?.roles?.map { $0.rawValue }.joined(separator: "; ") ?? ""
            let userId = user.id
            
            do {
                let visibleApps = try await getVisibleAppsForUser(userId: userId)
                for app in visibleApps {
                    let appName = app.attributes?.name ?? ""
                    if !appName.isEmpty {
                        appsAndUsers[appName, default: []].append(
                            MyAppStoreUser(name: name, email: email, role: role)
                        )
                    } else {
                        print("App Name is empty for user \(email)")
                    }
                }
            } catch {
                print("Could not fetch visible apps for user \(email): \(error)")
            }
        }
        
        print() // newline
        try exportAppsAndUsersToFile(appsAndUsers: appsAndUsers, outputFileName: outputFileName)
    }
    
    /// Fetches visible apps for a specific user with retry logic
    private func getVisibleAppsForUser(userId: String) async throws -> [App] {
        return try await APIUtilities.retryRequest {
            let visibleAppsResponse = try await self.provider.request(
                APIEndpoint.v1.users.id(userId).visibleApps.get()
            )
            return visibleAppsResponse.data
        }
    }
    
    /// Exports the apps and users mapping to a CSV file
    private func exportAppsAndUsersToFile(
        appsAndUsers: [String: [MyAppStoreUser]],
        outputFileName: String
    ) throws {
        var csvRows: [String] = [APIUtilities.csvRow([
            "App Name",
            "User Email",
            "User Name",
            "Role"
        ])]
        for (appName, users) in appsAndUsers.sorted(by: { $0.key < $1.key }) {
            for user in users {
                csvRows.append(APIUtilities.csvRow([
                    appName,
                    user.email,
                    user.name,
                    user.role
                ]))
            }
        }
        
        try APIUtilities.writeCSVToFile(rows: csvRows, fileName: outputFileName)
        print("Exported app-user access to \(outputFileName)")
    }
}
