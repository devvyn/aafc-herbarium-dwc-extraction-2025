// swift-tools-version:5.7
import PackageDescription

let package = Package(
    name: "VisionSwift",
    platforms: [
        .macOS(.v12)
    ],
    products: [
        .executable(name: "vision_swift", targets: ["VisionSwift"])
    ],
    dependencies: [],
    targets: [
        .executableTarget(
            name: "VisionSwift",
            dependencies: [],
            path: "Sources"
        )
    ]
)
