// FotoAlert – API-Service
// Kommuniziert mit dem Python FastAPI Backend

import Foundation
import Combine

// MARK: - Konfiguration
// Backend-URL hier anpassen:
let BACKEND_URL = "http://localhost:8000"

// MARK: - API Errors

enum APIError: LocalizedError {
    case networkError(Error)
    case decodingError(Error)
    case serverError(Int, String)
    case notConfigured

    var errorDescription: String? {
        switch self {
        case .networkError(let e): return "Netzwerkfehler: \(e.localizedDescription)"
        case .decodingError(let e): return "Datenfehler: \(e.localizedDescription)"
        case .serverError(let code, let msg): return "Server-Fehler \(code): \(msg)"
        case .notConfigured: return "Backend-URL nicht konfiguriert."
        }
    }
}

// MARK: - APIService

@MainActor
class APIService: ObservableObject {
    static let shared = APIService()

    private let decoder = JSONDecoder.fotoAlert
    private var cancellables = Set<AnyCancellable>()

    // MARK: Locations

    func fetchLocations(category: String? = nil) async throws -> [PhotoLocation] {
        var url = URL(string: "\(BACKEND_URL)/locations")!
        if let cat = category {
            url = URL(string: "\(BACKEND_URL)/locations?category=\(cat.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? cat)")!
        }
        return try await fetch(url: url)
    }

    func fetchLocation(id: String) async throws -> PhotoLocation {
        let url = URL(string: "\(BACKEND_URL)/locations/\(id)")!
        return try await fetch(url: url)
    }

    // MARK: Opportunities

    func fetchOpportunities(
        minScore: Double = 0.35,
        days: Int = 7,
        locationId: String? = nil,
        priority: Int? = nil
    ) async throws -> [PhotoOpportunity] {
        var components = URLComponents(string: "\(BACKEND_URL)/opportunities")!
        var items: [URLQueryItem] = [
            URLQueryItem(name: "min_score", value: String(minScore)),
            URLQueryItem(name: "days", value: String(days)),
        ]
        if let lid = locationId { items.append(URLQueryItem(name: "location_id", value: lid)) }
        if let p = priority { items.append(URLQueryItem(name: "priority", value: String(p))) }
        components.queryItems = items
        return try await fetch(url: components.url!)
    }

    func fetchTodayOpportunities() async throws -> [PhotoOpportunity] {
        let url = URL(string: "\(BACKEND_URL)/opportunities/today")!
        return try await fetch(url: url)
    }

    func fetchDailyBriefing(date: Date? = nil) async throws -> DailyBriefing {
        var urlStr = "\(BACKEND_URL)/daily-briefing"
        if let d = date {
            let f = DateFormatter()
            f.dateFormat = "yyyy-MM-dd"
            urlStr += "?target_date=\(f.string(from: d))"
        }
        let url = URL(string: urlStr)!
        return try await fetch(url: url)
    }

    func triggerRefresh() async throws {
        let url = URL(string: "\(BACKEND_URL)/refresh")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        let (_, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
            throw APIError.serverError(0, "Refresh fehlgeschlagen")
        }
    }

    // MARK: Push Registration

    func registerDeviceToken(_ token: String) async {
        guard let url = URL(string: "\(BACKEND_URL)/register-device?token=\(token)&platform=ios") else { return }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        do {
            let (_, _) = try await URLSession.shared.data(for: request)
        } catch {
            print("Push-Token-Registrierung fehlgeschlagen: \(error)")
        }
    }

    // MARK: Generic fetch

    private func fetch<T: Decodable>(url: URL) async throws -> T {
        do {
            let (data, response) = try await URLSession.shared.data(from: url)
            guard let http = response as? HTTPURLResponse else {
                throw APIError.serverError(0, "Keine HTTP-Antwort")
            }
            guard http.statusCode == 200 else {
                let msg = String(data: data, encoding: .utf8) ?? "Unbekannt"
                throw APIError.serverError(http.statusCode, msg)
            }
            return try decoder.decode(T.self, from: data)
        } catch let e as APIError {
            throw e
        } catch let e as DecodingError {
            throw APIError.decodingError(e)
        } catch {
            throw APIError.networkError(error)
        }
    }
}
