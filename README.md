# 🗺️ GPS 影像定位儀 (GPS Image Locator)

這是一個基於 **Streamlit** 與 **Python** 開發的輕量化網頁地理資訊工具（Web GIS），專為戶外考察、旅遊足跡記錄設計。使用者上傳包含手機 GPS 定位資訊的照片後，系統能自動解析其經緯度，並疊加於台灣官方或國際地圖圖資上，支援照片預覽、圖資切換、自訂浮水印與成果打包匯出。

---

## 🚀 核心功能與特點

1. **自動 EXIF 座標解析**
   * 自動讀取 JPEG/JPG 照片中的 EXIF 資料。
   * 將原始度分秒（DMS）格式精準轉換為十進位經緯度（精確至小數點後 7 位）。
2. **豐富的台灣官方與國際地圖底圖**
   * 內政部正射影像圖（臺灣航空空照圖）
   * 內政部通用電子地圖套疊正射圖（空照 + 地名）
   * 內政部臺灣通用電子地圖 (EMAP)
   * Esri 全球衛星影像圖 (World Imagery)
   * OpenStreetMap 國際標準街圖
3. **互動式彈出視窗預覽**
   * 點擊地圖上的定位點，可即時預覽照片縮圖與檔名。
   * 縮圖經過 Base64 編碼與效能最佳化，確保網頁載入流暢。
4. **地圖專屬浮水印 / Logo 設定**
   * 支援自訂文字或上傳透明背景 PNG Logo。
   * 可自由調整放置於地圖的四個角落。
5. **成果打包與資料匯出**
   * **HTML 互動網頁**：將地圖、標記、圖片與浮水印完整打包，離線也能單獨開啟使用。
   * **CSV 座標清單**：輸出檔名與十進位經緯度，可直接匯入 QGIS 或 Excel。

---

## 📦 專案技術堆疊 (Dependencies)

本專案運行所需的 Python 套件清單 (`requirements.txt`)：
* `streamlit`：網頁互動介面框架
* `pillow`：圖片處理與 EXIF 解析
* `pandas`：座標資料結構處理
* `folium`：網頁互動地圖繪製
* `streamlit-folium`：將 Folium 地圖渲染至 Streamlit 介面

---

## 🛠️ 程式碼結構與主要函式說明

* **`convert_to_decimal(value, ref)`**：處理 EXIF 中的 GPS 度分秒陣列，轉換為十進位浮點數，並自動處理南半球/西半球的負號轉換。
* **`get_gps_coordinates(image)`**：走訪影像 EXIF 標籤尋找 `GPSInfo`，萃取緯度（`GPSLatitude`）與經度（`GPSLongitude`）。
* **`get_image_base64(image, max_size)`**：將上傳的大圖縮製為指定尺寸的 JPEG 格式，並轉換為 Base64 字串，供 Folium 彈出視窗（IFrame）嵌入顯示。
* **前端渲染邏輯**：利用 `folium.Map` 結合自訂 WMTS 圖資圖層，透過 `folium.Marker` 與 `plugins.Fullscreen` 擴充地圖互動體驗。