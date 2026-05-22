import Foundation
import AppStoreConnect_Swift_SDK

/// Common utilities for App Store Connect API operations
struct APIUtilities {
    /// Creates an APIProvider configured with the given credentials
    static func createAPIProvider(issuerID: String, privateKeyID: String, privateKeyURL: URL) throws -> APIProvider {
        let configuration = try APIConfiguration(
            issuerID: issuerID,
            privateKeyID: privateKeyID,
            privateKeyURL: privateKeyURL
        )
        return APIProvider(configuration: configuration)
    }
    
    /// Generic retry logic for API requests
    static func retryRequest<T>(
        maxRetries: Int = 5,
        delayBaseSeconds: Int = 20,
        operation: () async throws -> T
    ) async throws -> T {
        var retryNum = 0
        
        repeat {
            do {
                let result = try await operation()
                return result
            } catch {
                retryNum += 1
                if retryNum > maxRetries {
                    throw error
                }
                print("Retry \(retryNum) of \(maxRetries)...")
                try await Task.sleep(for: .seconds(delayBaseSeconds * retryNum))
            }
        } while retryNum <= maxRetries
        
        throw APIError.maxRetriesExceeded
    }
    
    /// Writes data to a CSV file
    static func writeCSVToFile(rows: [String], fileName: String) throws {
        let csv = rows.joined(separator: "\n")
        let outputURL = URL(fileURLWithPath: fileName)
        try csv.write(to: outputURL, atomically: true, encoding: .utf8)
        print("Exported to \(outputURL.path)")
    }

    /// Normalizes display text from the API into a stable ASCII-friendly form.
    static func normalizeText(_ text: String) -> String {
        text
            .precomposedStringWithCompatibilityMapping
            .replacingOccurrences(of: "\u{2018}", with: "'")
            .replacingOccurrences(of: "\u{2019}", with: "'")
            .replacingOccurrences(of: "\u{201C}", with: "\"")
            .replacingOccurrences(of: "\u{201D}", with: "\"")
            .replacingOccurrences(of: "\u{2013}", with: "-")
            .replacingOccurrences(of: "\u{2014}", with: "-")
    }

    /// Formats a single field as valid CSV.
    static func csvField(_ text: String) -> String {
        let normalized = normalizeText(text)
        let escaped = normalized.replacingOccurrences(of: "\"", with: "\"\"")
        let requiresQuoting = escaped.contains(",") || escaped.contains("\"") || escaped.contains("\n") || escaped.contains("\r")

        if requiresQuoting {
            return "\"\(escaped)\""
        }

        return escaped
    }

    /// Formats a row of fields as valid CSV.
    static func csvRow(_ fields: [String]) -> String {
        fields.map(csvField).joined(separator: ",")
    }
}

/// Custom error types for API operations
enum APIError: Error {
    case maxRetriesExceeded
}
