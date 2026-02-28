import ProjectDescription

let project = Project(
    name: "AiMeditation",
    options: .options(
        automaticSchemesOptions: .disabled
    ),
    settings: .settings(
        base: [
            "DEVELOPMENT_TEAM": "E6GA9X89TN",
        ],
        configurations: [
            .debug(name: "Debug"),
            .release(name: "Release"),
        ]
    ),
    targets: [
        .target(
            name: "AiMeditation",
            destinations: [.iPhone, .iPad],
            product: .app,
            bundleId: "com.gabemontague.aimeditation",
            deploymentTargets: .iOS("18.0"),
            infoPlist: .extendingDefault(with: [
                "UILaunchScreen": .dictionary([:]),
                "NSAppTransportSecurity": .dictionary([
                    "NSAllowsArbitraryLoads": .boolean(true),
                ]),
            ]),
            sources: ["AiMeditation/**"],
            resources: ["AiMeditation/Assets.xcassets", "AiMeditation/Preview Content/**"],
            dependencies: [
                .external(name: "OpenbaseShared"),
            ],
            settings: .settings(
                base: [
                    "CODE_SIGN_STYLE": "Automatic",
                    "ENABLE_PREVIEWS": "YES",
                ]
            )
        ),
        .target(
            name: "AiMeditationTests",
            destinations: [.iPhone, .iPad],
            product: .unitTests,
            bundleId: "com.gabemontague.aimeditation.tests",
            deploymentTargets: .iOS("18.0"),
            sources: ["AiMeditationTests/**"],
            dependencies: [
                .target(name: "AiMeditation"),
            ]
        ),
        .target(
            name: "AiMeditationUITests",
            destinations: [.iPhone, .iPad],
            product: .uiTests,
            bundleId: "com.gabemontague.aimeditation.uitests",
            deploymentTargets: .iOS("18.0"),
            sources: ["AiMeditationUITests/**"],
            dependencies: [
                .target(name: "AiMeditation"),
            ]
        ),
    ],
    schemes: [
        .scheme(
            name: "AiMeditation",
            shared: true,
            buildAction: .buildAction(targets: ["AiMeditation"]),
            testAction: .targets(["AiMeditationTests", "AiMeditationUITests"]),
            runAction: .runAction(configuration: "Debug", executable: "AiMeditation")
        ),
    ]
)
