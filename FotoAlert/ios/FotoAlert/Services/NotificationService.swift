// FotoAlert – Push-Notification-Service

import Foundation
import UserNotifications

class NotificationService: NSObject, UNUserNotificationCenterDelegate {
    static let shared = NotificationService()

    override init() {
        super.init()
        UNUserNotificationCenter.current().delegate = self
    }

    // MARK: Berechtigung anfragen

    func requestAuthorization() async -> Bool {
        do {
            return try await UNUserNotificationCenter.current()
                .requestAuthorization(options: [.alert, .badge, .sound])
        } catch {
            print("Notification-Berechtigung fehlgeschlagen: \(error)")
            return false
        }
    }

    // MARK: Lokale Erinnerung erstellen

    func scheduleLocalReminder(
        title: String,
        body: String,
        at date: Date,
        opportunityId: String
    ) {
        let content = UNMutableNotificationContent()
        content.title = title
        content.body = body
        content.sound = .default
        content.badge = 1
        content.userInfo = ["opportunity_id": opportunityId]

        // 30 Minuten vor dem optimalen Aufnahmezeitpunkt
        let triggerDate = Calendar.current.date(byAdding: .minute, value: -30, to: date) ?? date
        let components = Calendar.current.dateComponents(
            [.year, .month, .day, .hour, .minute],
            from: triggerDate
        )
        let trigger = UNCalendarNotificationTrigger(dateMatching: components, repeats: false)
        let request = UNNotificationRequest(
            identifier: "fotoalert_\(opportunityId)",
            content: content,
            trigger: trigger
        )

        UNUserNotificationCenter.current().add(request) { error in
            if let error { print("Erinnerung konnte nicht erstellt werden: \(error)") }
        }
    }

    func removeReminder(opportunityId: String) {
        UNUserNotificationCenter.current()
            .removePendingNotificationRequests(withIdentifiers: ["fotoalert_\(opportunityId)"])
    }

    // MARK: UNUserNotificationCenterDelegate

    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification
    ) async -> UNNotificationPresentationOptions {
        return [.banner, .badge, .sound]
    }

    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse
    ) async {
        let userInfo = response.notification.request.content.userInfo
        if let oppId = userInfo["opportunity_id"] as? String {
            // Deep-Link: App öffnet die Opportunity-Detail-Ansicht
            NotificationCenter.default.post(
                name: .openOpportunity,
                object: nil,
                userInfo: ["opportunity_id": oppId]
            )
        }
    }
}

extension Notification.Name {
    static let openOpportunity = Notification.Name("FotoAlertOpenOpportunity")
}
