// "Print from iPhone & iPad": one window that turns AirPrint sharing on and off per printer.
// All the work is in airprint-share; this only shows its state and calls it.
import SwiftUI

#if DEBUG
let helper = ProcessInfo.processInfo.environment["AIRPRINT_SHARE"] ?? "/Library/Printers/Gutenprint/bin/airprint-share"
#else
let helper = "/Library/Printers/Gutenprint/bin/airprint-share"
#endif
let german = Locale.preferredLanguages.first?.hasPrefix("de") ?? false
func t(_ en: String, _ de: String) -> String { german ? de : en }

struct Printer: Identifiable {
    let id: String, name: String
    var shared: Bool
    let reachable: Bool
}

@discardableResult
func run(_ args: [String]) -> String {
    let p = Process(), out = Pipe()
    p.executableURL = URL(fileURLWithPath: helper)
    p.arguments = args
    p.standardOutput = out
    p.standardError = FileHandle.nullDevice
    guard (try? p.run()) != nil else { return "" }
    let data = out.fileHandleForReading.readDataToEndOfFile()
    p.waitUntilExit()
    return String(decoding: data, as: UTF8.self)
}

final class Model: ObservableObject {
    @Published var printers: [Printer] = []
    @Published var loaded = false

    func refresh() {
        DispatchQueue.global().async {
            let list = run(["info"]).split(separator: "\n").compactMap { line -> Printer? in
                let f = line.split(separator: "\t", omittingEmptySubsequences: false).map(String.init)
                return f.count == 4 ? Printer(id: f[0], name: f[1], shared: f[2] == "1", reachable: f[3] == "1") : nil
            }
            DispatchQueue.main.async { self.printers = list; self.loaded = true }
        }
    }

    func toggle(_ id: String, _ on: Bool) {
        guard let i = printers.firstIndex(where: { $0.id == id }) else { return }
        printers[i].shared = on
        let wanted = printers.filter(\.shared).map(\.id)
        DispatchQueue.global().async {
            run(["set"] + wanted)
            self.refresh()
        }
    }
}

struct Row: View {
    let printer: Printer
    @ObservedObject var model: Model

    var status: (String, Color) {
        if !printer.reachable { return (t("Your Mac can't reach this printer right now", "Dein Mac erreicht diesen Drucker gerade nicht"), .orange) }
        if printer.shared { return (t("Ready on your iPhone and iPad", "Bereit auf iPhone und iPad"), .green) }
        return (t("Not shared", "Nicht freigegeben"), .secondary)
    }

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: "printer.fill").font(.title2).foregroundColor(.secondary).frame(width: 30)
            VStack(alignment: .leading, spacing: 2) {
                Text(printer.name).font(.body.weight(.medium))
                Text(status.0).font(.caption).foregroundColor(status.1)
            }
            Spacer()
            Toggle("", isOn: Binding(get: { printer.shared }, set: { model.toggle(printer.id, $0) }))
                .toggleStyle(.switch).labelsHidden().accessibilityLabel(printer.name)
        }
        .padding(.vertical, 8)
    }
}

// SwiftUI on macOS 12 has no way to size a window to its content
func fitWindow() {
    DispatchQueue.main.async {
        guard let w = NSApp.windows.first, let v = w.contentView else { return }
        w.styleMask.remove(.resizable)
        w.setContentSize(v.fittingSize)
    }
}

struct ContentView: View {
    @StateObject var model = Model()

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text(t("Print from iPhone & iPad", "Vom iPhone & iPad drucken")).font(.title2.weight(.semibold))
            Text(t("Turn on a printer, then on your iPhone or iPad tap Share, then Print.",
                   "Schalte einen Drucker ein und tippe auf dem iPhone oder iPad auf Teilen und Drucken."))
                .foregroundColor(.secondary).fixedSize(horizontal: false, vertical: true)
            if model.loaded && model.printers.isEmpty {
                Text(t("No printers yet. Set your printer up on this Mac first.",
                       "Noch keine Drucker. Richte deinen Drucker zuerst auf diesem Mac ein."))
                    .frame(maxWidth: .infinity, minHeight: 100)
            } else {
                ScrollView {
                    VStack(spacing: 0) {
                        ForEach(model.printers) { p in
                            Row(printer: p, model: model)
                            if p.id != model.printers.last?.id { Divider() }
                        }
                    }
                    .padding(.horizontal, 12)
                }
                .frame(height: min(CGFloat(max(model.printers.count, 2)) * 49, 343))
                .background(Color(nsColor: .controlBackgroundColor))
                .cornerRadius(10)
            }
            Text(t("Your Mac has to stay on and awake. Anyone on the same Wi-Fi can print to shared printers.",
                   "Dein Mac muss eingeschaltet und wach bleiben. Alle im selben WLAN können auf freigegebenen Druckern drucken."))
                .font(.caption).foregroundColor(.secondary).fixedSize(horizontal: false, vertical: true)
            Divider()
            HStack(spacing: 4) {
                Text(t("☕ Printing again? It's free and always will be.", "☕ Druckt es wieder? Es ist kostenlos und bleibt es."))
                    .foregroundColor(.secondary)
                Link(t("Buy me a coffee", "Spendier mir einen Kaffee"), destination: URL(string: "https://github.com/sponsors/theshiver")!)
            }
            .font(.callout)
        }
        .padding(20)
        .frame(width: 440)
        .onAppear(perform: model.refresh)
        .onChange(of: model.printers.count) { _ in fitWindow() }
        .onReceive(NotificationCenter.default.publisher(for: NSApplication.didBecomeActiveNotification)) { _ in model.refresh() }
    }
}

final class Delegate: NSObject, NSApplicationDelegate {
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }
}

@main
struct ShareApp: App {
    @NSApplicationDelegateAdaptor(Delegate.self) var delegate
    var body: some Scene {
        WindowGroup("Print from iPhone & iPad") { ContentView() }
    }
}
