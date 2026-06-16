// FotoAlert – Kartenansicht

import SwiftUI
import MapKit

struct MapView: View {
    @EnvironmentObject var store: OpportunityStore
    @State private var selectedLocation: PhotoLocation? = nil
    @State private var region = MKCoordinateRegion(
        center: CLLocationCoordinate2D(latitude: 52.52, longitude: 13.40),
        span: MKCoordinateSpan(latitudeDelta: 1.5, longitudeDelta: 1.5)
    )

    var body: some View {
        NavigationStack {
            Map(coordinateRegion: $region, annotationItems: store.locations) { location in
                MapAnnotation(coordinate: location.coordinate) {
                    LocationMapPin(location: location, isSelected: selectedLocation?.id == location.id)
                        .onTapGesture {
                            withAnimation(.spring()) {
                                selectedLocation = location
                            }
                        }
                }
            }
            .ignoresSafeArea(edges: .bottom)
            .navigationTitle("Karte")
            .navigationBarTitleDisplayMode(.inline)
            .overlay(alignment: .bottom) {
                if let loc = selectedLocation {
                    LocationBottomCard(location: loc) {
                        selectedLocation = nil
                    }
                    .padding()
                    .transition(.move(edge: .bottom).combined(with: .opacity))
                }
            }
        }
    }
}

struct LocationMapPin: View {
    let location: PhotoLocation
    let isSelected: Bool

    var pinColor: Color {
        switch location.category {
        case _ where location.category.contains("Schloss"): return .purple
        case _ where location.category.contains("Wasser"): return .blue
        case _ where location.category.contains("Natur"): return .green
        case _ where location.category.contains("Astro"): return .indigo
        default: return .orange
        }
    }

    var body: some View {
        VStack(spacing: 0) {
            ZStack {
                Circle()
                    .fill(pinColor)
                    .frame(width: isSelected ? 40 : 30, height: isSelected ? 40 : 30)
                Image(systemName: "camera.fill")
                    .font(isSelected ? .subheadline : .caption)
                    .foregroundStyle(.white)
            }
            Triangle()
                .fill(pinColor)
                .frame(width: 8, height: 6)

            if isSelected {
                Text(location.name)
                    .font(.caption.bold())
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(.regularMaterial)
                    .clipShape(Capsule())
                    .shadow(radius: 2)
            }
        }
        .animation(.spring(), value: isSelected)
    }
}

struct Triangle: Shape {
    func path(in rect: CGRect) -> Path {
        Path { p in
            p.move(to: CGPoint(x: rect.midX, y: rect.maxY))
            p.addLine(to: CGPoint(x: rect.minX, y: rect.minY))
            p.addLine(to: CGPoint(x: rect.maxX, y: rect.minY))
            p.closeSubpath()
        }
    }
}

struct LocationBottomCard: View {
    let location: PhotoLocation
    let onDismiss: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                VStack(alignment: .leading) {
                    Text(location.category)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Text(location.name)
                        .font(.headline)
                }
                Spacer()
                Button(action: onDismiss) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundStyle(.secondary)
                        .font(.title3)
                }
            }

            Text(location.description)
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .lineLimit(2)

            HStack(spacing: 8) {
                ForEach(location.focal_length_suggestions.prefix(3), id: \.self) { fl in
                    Text("\(fl)mm")
                        .font(.caption.bold())
                        .padding(.horizontal, 8)
                        .padding(.vertical, 3)
                        .background(Color.blue.opacity(0.1))
                        .foregroundStyle(.blue)
                        .clipShape(Capsule())
                }

                DifficultyBadge(difficulty: location.difficulty, label: location.difficultyLabel)
            }

            if !location.access_note.isEmpty {
                Label(location.access_note, systemImage: "figure.walk")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
            }
        }
        .padding()
        .background(.regularMaterial)
        .clipShape(RoundedRectangle(cornerRadius: 20))
        .shadow(radius: 8)
    }
}

struct DifficultyBadge: View {
    let difficulty: Int
    let label: String

    var color: Color {
        switch difficulty {
        case 1: return .green
        case 2: return .orange
        default: return .red
        }
    }

    var body: some View {
        Text(label)
            .font(.caption)
            .foregroundStyle(color)
            .padding(.horizontal, 8)
            .padding(.vertical, 3)
            .background(color.opacity(0.1))
            .clipShape(Capsule())
    }
}
