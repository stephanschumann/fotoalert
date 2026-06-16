// FotoAlert – Datenmodelle
// Spiegeln die FastAPI-Schemas wider

import Foundation
import CoreLocation

// MARK: - Location

struct PhotoLocation: Codable, Identifiable {
    let id: String
    let name: String
    let description: String
    let category: String
    let observer_lat: Double
    let observer_lon: Double
    let subject_name: String
    let subject_height_m: Double?
    let distance_m: Double?
    let focal_length_suggestions: [Int]
    let special_notes: String
    let solar_alignment_note: String
    let lunar_alignment_note: String
    let access_note: String
    let locationscout_url: String
    let difficulty: Int

    var coordinate: CLLocationCoordinate2D {
        CLLocationCoordinate2D(latitude: observer_lat, longitude: observer_lon)
    }

    var difficultyLabel: String {
        switch difficulty {
        case 1: return "Einfach"
        case 2: return "Mittel"
        case 3: return "Anspruchsvoll"
        default: return "Mittel"
        }
    }
}

// MARK: - Camera Hint

struct CameraHint: Codable {
    let focal_length_mm: Int
    let aperture_suggestion: String
    let shutter_suggestion: String
    let iso_suggestion: String
    let tripod_required: Bool
    let extra_tip: String
}

// MARK: - Opportunity

struct PhotoOpportunity: Codable, Identifiable {
    let id: String
    let location_id: String
    let location_name: String
    let event_type: String
    let title: String
    let description: String
    let shoot_time: Date
    let shoot_window_start: Date
    let shoot_window_end: Date
    let overall_score: Double
    let astronomy_score: Double
    let weather_score: Double
    let location_score: Double
    let camera_hints: [CameraHint]
    let subject_azimuth: Double?
    let celestial_azimuth: Double?
    let celestial_altitude: Double?
    let alert_priority: Int
    let weather_description: String
    let moon_phase: String?
    let moon_illumination_pct: Double?
    let sunrise_utc: Date?
    let sunset_utc: Date?

    // MARK: Computed

    var scoreColor: String {
        switch overall_score {
        case 0.8...: return "ScoreHigh"
        case 0.6..<0.8: return "ScoreMedium"
        default: return "ScoreLow"
        }
    }

    var scorePercent: Int { Int(overall_score * 100) }

    var eventIcon: String {
        switch event_type {
        case "Goldene Stunde Abend", "Goldene Stunde Morgen": return "sun.horizon.fill"
        case "Blaue Stunde": return "moon.stars.fill"
        case "Mondaufgang": return "moon.fill"
        case "Mond-Alignment": return "moon.circle.fill"
        case "Sonnen-Alignment": return "sun.max.fill"
        case "Milchstraße": return "sparkles"
        case "Meteoritenschauer": return "sparkle"
        case "Sonnenfinsternis": return "circle.righthalf.filled"
        default: return "camera.fill"
        }
    }

    var formattedShootTime: String {
        let f = DateFormatter()
        f.dateFormat = "HH:mm"
        f.timeZone = TimeZone(identifier: "Europe/Berlin")
        return f.string(from: shoot_time) + " Uhr"
    }

    var formattedDate: String {
        let f = DateFormatter()
        f.locale = Locale(identifier: "de_DE")
        f.dateFormat = "EEE, d. MMMM"
        f.timeZone = TimeZone(identifier: "Europe/Berlin")
        return f.string(from: shoot_time)
    }

    var isToday: Bool {
        Calendar.current.isDateInToday(shoot_time)
    }

    var isTomorrow: Bool {
        Calendar.current.isDateInTomorrow(shoot_time)
    }

    var relativeDayLabel: String {
        if isToday { return "Heute" }
        if isTomorrow { return "Morgen" }
        return formattedDate
    }

    var priorityLabel: String {
        switch alert_priority {
        case 3: return "Außergewöhnlich"
        case 2: return "Besonders"
        case 1: return "Gut"
        default: return ""
        }
    }
}

// MARK: - Daily Briefing

struct DailyBriefing: Codable {
    let date: String
    let location_count: Int
    let top_opportunities: [PhotoOpportunity]
    let highest_score: Double
    let alert_count: Int
    let summary: String
}

// MARK: - JSON Decoder

extension JSONDecoder {
    static var fotoAlert: JSONDecoder {
        let d = JSONDecoder()
        d.dateDecodingStrategy = .custom { decoder in
            let s = try decoder.singleValueContainer().decode(String.self)
            let f = ISO8601DateFormatter()
            f.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
            if let date = f.date(from: s) { return date }
            f.formatOptions = [.withInternetDateTime]
            if let date = f.date(from: s) { return date }
            throw DecodingError.dataCorruptedError(
                in: try decoder.singleValueContainer(),
                debugDescription: "Ungültiges Datum: \(s)"
            )
        }
        return d
    }
}
