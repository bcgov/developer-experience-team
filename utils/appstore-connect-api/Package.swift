// swift-tools-version: 6.1
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "appstore-connect-api",
    platforms: [
        .macOS(.v13)
    ],
    dependencies: [
      .package(url: "https://github.com/apple/swift-argument-parser", from: "1.0.0"),
      .package(url: "https://github.com/AvdLee/appstoreconnect-swift-sdk.git", .upToNextMajor(from: "3.7.1")),
    ],
    targets: [
        // Targets are the basic building blocks of a package, defining a module or a test suite.
        // Targets can depend on other targets in this package and products from dependencies.
        .executableTarget(
            name: "appstore-connect-api",
            dependencies: [
                .product(name: "ArgumentParser", package: "swift-argument-parser"),
                .product(name: "AppStoreConnect-Swift-SDK", package: "appstoreconnect-swift-sdk"),
            ],
            path: "Sources"),
    ]
)
