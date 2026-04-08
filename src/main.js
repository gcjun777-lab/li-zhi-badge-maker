const path = require("path");
const { app, BrowserWindow } = require("electron");

function createWindow() {
  const window = new BrowserWindow({
    width: 1360,
    height: 860,
    minWidth: 1120,
    minHeight: 700,
    backgroundColor: "#070b14",
    title: "离职厂牌制作助手",
    autoHideMenuBar: true,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  window.loadFile(path.join(__dirname, "index.html"));
}

app.whenReady().then(() => {
  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});
