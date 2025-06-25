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
    @Option(name: .shortAndLong, help: "Specify the issuer ID. This ID is found in AppStoreConnect.")
    public var issuerID: String
    
    @Option(name: .shortAndLong, help: "Specify the private key ID. This ID is found in AppStoreConnect.")
    public var privateKeyID: String
    
    @Option(name: .shortAndLong, help: "Specify the path to the private key .p8 file. Download this file from AppStoreConnect.")
    public var keyPath: String
    
    @Argument(help: "The name of the output file. The output will be a CSV file.")
    public var outputFileName: String
    
    
    public func run() async throws {
        let configuration = try APIConfiguration(issuerID: self.issuerID, privateKeyID: self.privateKeyID, privateKeyURL: URL(fileURLWithPath: self.keyPath))
        let provider = APIProvider(configuration: configuration)

        // Get all data at once using the paged API, we don't need to page through the data and operate
        // on each page because there aren't that many users. It's fine to get them all and then
        // work on all the data
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
                let visibleAppsResponse = try await getVisibleAppsForUser(userId: userId, provider: provider)
                for app in visibleAppsResponse {
                    let appName = app.attributes?.name ?? ""
                    if !appName.isEmpty {
                        appsAndUsers[appName, default: []].append(MyAppStoreUser(name: name, email: email, role: role))
                    }else {
                        print("App Name is empty for user \(email)")
                    }
                }
            } catch {
                print("Could not fetch visible apps for user \(email): \(error)")
            }
        }
        writeToFile(appsAndUsers: appsAndUsers)
    }
    
    func getVisibleAppsForUser(userId: String, provider: APIProvider) async throws -> [App] {
        var shouldRetry: Bool = true
        var retryNum: Int = 0
        let maxRetryNum: Int = 5
        var appResponse: [App] = []
        repeat {
            do {
                let visibleAppsResponse = try await provider.request(APIEndpoint.v1.users.id(userId).visibleApps.get())
                shouldRetry = false
                appResponse = visibleAppsResponse.data
            } catch {
                print("Could not fetch visible apps for user \(userId): \(error)")
                retryNum+=1
                if retryNum > maxRetryNum {
                    throw error
                }
                print("Retrying...\(retryNum) of \(maxRetryNum)")
                try await Task.sleep(for: .seconds(20 * retryNum))
            }
        } while shouldRetry && retryNum <= maxRetryNum
        return appResponse
    }
    
    func writeToFile(appsAndUsers: [String: [MyAppStoreUser]]){
        var csvRows: [String] = ["App Name,User Email,User Name,Role"]
        for (appName, users) in appsAndUsers.sorted(by: { $0.key < $1.key }) {
            for user in users {
                let row = "\(appName),\(user.email),\(user.name),\(user.role)"
                csvRows.append(row)
            }
        }

        let csv = csvRows.joined(separator: "\n")
        let outputURL = URL(fileURLWithPath: outputFileName)
        do {
            try csv.write(to: outputURL, atomically: true, encoding: .utf8)
            print("Exported app-user access to \(outputURL.path)")
        }catch {
            print("Error creating file! \(error)")
        }
        
    }
}

