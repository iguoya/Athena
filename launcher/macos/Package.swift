// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "AthenaLauncher",
    platforms: [.macOS(.v14)],
    targets: [
        .executableTarget(
            name: "AthenaLauncher",
            path: "Sources/AthenaLauncher"
        )
    ]
)
