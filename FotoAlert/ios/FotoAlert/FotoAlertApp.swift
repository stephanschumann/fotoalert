// FotoAlert – App Entry Point

import SwiftUI
import UserNotifications

@main
struct FotoAlertApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    @StateObject private var store = OpportunityStore()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(store)
                .onReceive(NotificationCenter.default.publisher(for: .openOpportunity)) { notification in
                    if let oppId = notification.userInfo?["opportunity_id"] as? String {
                        store.selectedOpportunityId = oppId
                    }
                }
        }
    }
}

// MARK: - AppDelegate (Push Notifications)

class AppDelegate: NSObject, UIApplicationDelegate {
    func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil
    ) -> Bool {
        NotificationService.shared  // Initialisierung
        Task {
            let granted = await NotificationService.shared.requestAuthorization()
            if granted {
                await MainActor.run {
                    UIApplication.shared.registerForRemoteNotifications()
                }
            }
        }
        return true
    }

    func application(
        _ application: UIApplication,
        didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data
    ) {
        let token = deviceToken.map { String(format: "%02x", $0) }.joined()
        print("APNs-Token: \(token)")
        Task {
            await APIService.shared.registerDeviceToken(token)
        }
    }

    func application(
        _ application: UIApplication,
        didFailToRegisterForRemoteNotificationsWithError error: Error
    ) {
        print("Push-Registration fehlgeschlagen: \(error)")
    }
}

// MARK: - Opportunity Store

@MainActor
class OpportunityStore: ObservableObject {
    @Published var opportunities: [PhotoOpportunity] = []
    @Published var locations: [PhotoLocation] = []
    @Published var isLoading = false
    @Published var error: String?
    @Published var selectedOpportunityId: String?
    @Published var lastRefresh: Date?

    func load() async {
        isLoading = true
        error = nil
        do {
            async let opps = APIService.shared.fetchOpportunities(days: 7)
            async let locs = APIService.shared.fetchLocations()
            let (fetchedOpps, fetchedLocs) = try await (opps, locs)
            opportunities = fetchedOpps
            locations = fetchedLocs
            lastRefresh = Date()
        } catch {
            self.error = error.localizedDescription
        }
        isLoading = false
    }

    func refresh() async {
        try? await APIService.shared.triggerRefresh()
        // Kurz warten damit der Server fertig ist
        try? await Task.sleep(nanoseconds: 3_000_000_000)
        await load()
    }

    var todayOpportunities: [PhotoOpportunity] {
        opportunities.filter { $0.isToday }.sorted { $0.overall_score > $1.overall_score }
    }

    var upcomingOpportunities: [PhotoOpportunity] {
        opportunities.filter { !$0.isToday }.sorted { $0.shoot_time < $1.shoot_time }
    }

    var highPriorityOpportunities: [PhotoOpportunity] {
        opportunities.filter { $0.alert_priority >= 2 }.sorted { $0.overall_score > $1.overall_score }
    }
}
