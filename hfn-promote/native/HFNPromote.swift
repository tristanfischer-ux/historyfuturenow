import Cocoa
import WebKit

class AppDelegate: NSObject, NSApplicationDelegate, WKUIDelegate {
    var window: NSWindow!
    var webView: WKWebView!
    var spinner: NSProgressIndicator!
    var retryCount = 0
    let maxRetries = 40  // 20 seconds

    func applicationDidFinishLaunching(_ notification: Notification) {
        ensureFlaskRunning()

        let config = WKWebViewConfiguration()
        config.preferences.setValue(true, forKey: "developerExtrasEnabled")

        webView = WKWebView(frame: .zero, configuration: config)
        webView.uiDelegate = self
        webView.customUserAgent = "HFNPromote/4.0 Safari"

        window = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 1400, height: 900),
            styleMask: [.titled, .closable, .miniaturizable, .resizable],
            backing: .buffered,
            defer: false
        )
        window.title = "HFN Promote"
        window.minSize = NSSize(width: 1000, height: 700)
        window.contentView = webView
        window.center()

        // Loading spinner
        spinner = NSProgressIndicator(frame: NSRect(x: 0, y: 0, width: 32, height: 32))
        spinner.style = .spinning
        spinner.controlSize = .regular
        spinner.translatesAutoresizingMaskIntoConstraints = false
        webView.addSubview(spinner)
        NSLayoutConstraint.activate([
            spinner.centerXAnchor.constraint(equalTo: webView.centerXAnchor),
            spinner.centerYAnchor.constraint(equalTo: webView.centerYAnchor)
        ])
        spinner.startAnimation(nil)

        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)

        // Standard menu bar — required for Cmd+C/V/X/A to work in WKWebView
        let mainMenu = NSMenu()

        let appMenuItem = NSMenuItem()
        let appMenu = NSMenu()
        appMenu.addItem(withTitle: "About HFN Promote", action: #selector(NSApplication.orderFrontStandardAboutPanel(_:)), keyEquivalent: "")
        appMenu.addItem(NSMenuItem.separator())
        appMenu.addItem(withTitle: "Quit HFN Promote", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        appMenuItem.submenu = appMenu
        mainMenu.addItem(appMenuItem)

        let editMenuItem = NSMenuItem()
        let editMenu = NSMenu(title: "Edit")
        editMenu.addItem(withTitle: "Undo", action: Selector(("undo:")), keyEquivalent: "z")
        editMenu.addItem(withTitle: "Redo", action: Selector(("redo:")), keyEquivalent: "Z")
        editMenu.addItem(NSMenuItem.separator())
        editMenu.addItem(withTitle: "Cut", action: #selector(NSText.cut(_:)), keyEquivalent: "x")
        editMenu.addItem(withTitle: "Copy", action: #selector(NSText.copy(_:)), keyEquivalent: "c")
        editMenu.addItem(withTitle: "Paste", action: #selector(NSText.paste(_:)), keyEquivalent: "v")
        editMenu.addItem(withTitle: "Select All", action: #selector(NSText.selectAll(_:)), keyEquivalent: "a")
        editMenuItem.submenu = editMenu
        mainMenu.addItem(editMenuItem)

        NSApp.mainMenu = mainMenu

        tryLoadPage()
    }

    func ensureFlaskRunning() {
        let task = Process()
        task.executableURL = URL(fileURLWithPath: "/bin/bash")
        let appDir = NSString(string: "~/Developer/History Future Now 260215/hfn-promote").expandingTildeInPath
        let script = """
        export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
        cd "\(appDir)" || exit 1
        if curl -s http://localhost:5050 > /dev/null 2>&1; then
            exit 0
        fi
        if [ -f "venv/bin/activate" ]; then
            source venv/bin/activate
        fi
        nohup python3 hfn.py dashboard > hfn-promote.log 2>&1 &
        """
        task.arguments = ["-c", script]
        try? task.run()
        task.waitUntilExit()
    }

    func tryLoadPage() {
        let url = URL(string: "http://localhost:5050")!
        let request = URLRequest(url: url, cachePolicy: .reloadIgnoringLocalCacheData, timeoutInterval: 2)

        let check = URLSession.shared.dataTask(with: request) { [weak self] data, response, error in
            guard let self = self else { return }
            if let http = response as? HTTPURLResponse, http.statusCode == 200 {
                DispatchQueue.main.async {
                    self.spinner.stopAnimation(nil)
                    self.spinner.removeFromSuperview()
                    self.webView.load(URLRequest(url: url))
                }
            } else {
                self.retryCount += 1
                if self.retryCount < self.maxRetries {
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                        self.tryLoadPage()
                    }
                } else {
                    DispatchQueue.main.async {
                        self.spinner.stopAnimation(nil)
                        self.showError()
                    }
                }
            }
        }
        check.resume()
    }

    func showError() {
        let html = """
        <html><body style="font-family:-apple-system;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;background:#1a1a2e;color:#e0e0e0">
        <div style="text-align:center"><h1 style="color:#f4845f">Could not connect</h1><p>Flask server not responding on port 5050.</p>
        <p style="color:#888">Check ~/Developer/History Future Now 260215/hfn-promote/hfn-promote.log</p>
        <button onclick="location.reload()" style="margin-top:20px;padding:10px 24px;background:#f4845f;color:white;border:none;border-radius:6px;cursor:pointer;font-size:14px">Retry</button></div></body></html>
        """
        webView.loadHTMLString(html, baseURL: nil)
    }

    // WKUIDelegate — JS alert/confirm/prompt dialogs
    func webView(_ webView: WKWebView, runJavaScriptAlertPanelWithMessage message: String,
                 initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping () -> Void) {
        let alert = NSAlert()
        alert.messageText = message
        alert.addButton(withTitle: "OK")
        alert.runModal()
        completionHandler()
    }

    func webView(_ webView: WKWebView, runJavaScriptConfirmPanelWithMessage message: String,
                 initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping (Bool) -> Void) {
        let alert = NSAlert()
        alert.messageText = message
        alert.addButton(withTitle: "OK")
        alert.addButton(withTitle: "Cancel")
        completionHandler(alert.runModal() == .alertFirstButtonReturn)
    }

    func webView(_ webView: WKWebView, runJavaScriptTextInputPanelWithPrompt prompt: String,
                 defaultText: String?, initiatedByFrame frame: WKFrameInfo,
                 completionHandler: @escaping (String?) -> Void) {
        let alert = NSAlert()
        alert.messageText = prompt
        let input = NSTextField(frame: NSRect(x: 0, y: 0, width: 260, height: 24))
        input.stringValue = defaultText ?? ""
        alert.accessoryView = input
        alert.addButton(withTitle: "OK")
        alert.addButton(withTitle: "Cancel")
        completionHandler(alert.runModal() == .alertFirstButtonReturn ? input.stringValue : nil)
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        return true
    }
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.run()
