import Cocoa
import FlutterMacOS

class MainFlutterWindow: NSWindow {
  private static let appTitle = "驾考学习"

  override func awakeFromNib() {
    let flutterViewController = FlutterViewController()
    self.contentViewController = flutterViewController
    RegisterGeneratedPlugins(registry: flutterViewController)
    super.awakeFromNib()
    applyChrome()
  }

  override func makeKeyAndOrderFront(_ sender: Any?) {
    super.makeKeyAndOrderFront(sender)
    applyChrome()
  }

  override var title: String {
    get { super.title }
    set { super.title = MainFlutterWindow.appTitle }
  }

  private func applyChrome() {
    super.title = MainFlutterWindow.appTitle
    minSize = NSSize(width: 1200, height: 760)
    if frame.width < 1400 || frame.height < 860 {
      setContentSize(NSSize(width: 1440, height: 900))
      center()
    }
  }
}
