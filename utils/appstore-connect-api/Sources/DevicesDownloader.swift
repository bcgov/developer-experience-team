import Foundation
import AppStoreConnect_Swift_SDK

/// Downloads and exports device information from App Store Connect
struct DevicesDownloader {
    let provider: APIProvider
    
    /// Initializes the downloader with the given provider
    init(provider: APIProvider) {
        self.provider = provider
    }
    
    /// Fetches all devices and exports them to a CSV file
    func downloadDevices(outputFileName: String) async throws {
        var devices: [Device] = []
        
        print("Fetching devices from App Store Connect...")
        for try await page in provider.paged(APIEndpoint.v1.devices.get()) {
            devices.append(contentsOf: page.data)
        }
        print("Fetched \(devices.count) devices")
        
        try exportDevicesToFile(devices: devices, outputFileName: outputFileName)
    }
    
    /// Exports devices to a CSV file
    private func exportDevicesToFile(devices: [Device], outputFileName: String) throws {
        var csvRows: [String] = [APIUtilities.csvRow([
            "Device ID",
            "Device Name",
            "Device UDID",
            "Device Status",
            "Device Class"
        ])]
        
        for device in devices.sorted(by: { ($0.attributes?.name ?? "") < ($1.attributes?.name ?? "") }) {
            csvRows.append(APIUtilities.csvRow([
                device.id,
                device.attributes?.name ?? "",
                device.attributes?.udid ?? "",
                device.attributes?.status?.rawValue ?? "",
                device.attributes?.deviceClass?.rawValue ?? ""
            ]))
        }
        
        try APIUtilities.writeCSVToFile(rows: csvRows, fileName: outputFileName)
    }
}
