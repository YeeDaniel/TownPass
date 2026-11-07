# 北車樓層圖資料管線

`source_data/051.pdf` 是四頁點陣 PDF，頁面依序為 B1、B2、B3、B4。它沒有文字層，也不是 CAD／向量圖，因此不能可靠地用 PDF 解析器直接得到走道拓樸。

本專案將資料拆成兩種用途：

- 樓層底圖與黃色區域遮罩：顯示、人工標註及電腦視覺輔助。
- 節點／邊圖：路徑計算使用的唯一依據。

## 產生資料

在專案根目錄執行：

```powershell
python -m pip install -r tools/floorplan/requirements.txt
python tools/floorplan/convert_floorplans.py
python tools/floorplan/validate_floorplans.py
```

輸出位於 `assets/floorplans/taipei_main_station/`：

- `b1.png` 至 `b4.png`：保留原始頁面尺寸的樓層圖。
- `b1_walkable_mask.png` 至 `b4_walkable_mask.png`：從黃色區域產生、背景透明的二值遮罩。
- `manifest.json`：樓層、圖片、節點、邊、目的地及來源雜湊。

腳本優先直接抽取頁面內嵌圖片；若未來換成向量 PDF，則以 2 倍解析度渲染。產生物可以重建，不應手動編輯。

## 修改機器可讀語意

原始標註位於 `source_data/051.annotations.json`。座標採左上角為原點的正規化座標，因此不依賴圖片實際像素：

```json
{
  "floorId": "B2",
  "position": { "x": 0.635, "y": 0.837 }
}
```

節點用於出口、岔路、月台、樓梯及電梯。邊表示可走的連線：

- `kind`: `corridor`、`stairs`、`escalator`、`elevator` 或 `platform`。
- `accessible`: 行李、輪椅或推車模式能否使用。
- `cost`: 目前是相對成本，不是假裝精準的公尺或秒數。
- `verified`: 是否已完成現場確認。

修改標註後重新執行轉換腳本，`manifest.json` 會同時加入對應的像素座標。

## Flutter 使用方式

```dart
final dataset = await FloorPlanDataset.loadFromAssets();
final route = dataset.shortestPath(
  'b1_m4_entry',
  'b4_r_platform',
  accessibleOnly: true,
);
```

畫節點時，將 `node.x * 顯示寬度`、`node.y * 顯示高度` 作為位置。切換樓層時依 `floorId` 換底圖；跨樓層邊則顯示「搭電梯到 B3」之類的步驟。

## 2D／3D HTML 檢視器

靜態檢視器位於 `floorplan_viewer/`，直接讀取本管線產生的 `manifest.json`、樓層 PNG 與可通行區遮罩。它不需要 Node.js、套件安裝或網路連線。

請從**專案根目錄**啟動本機 HTTP server：

```powershell
python -m http.server 4173 --bind 127.0.0.1
```

接著在瀏覽器開啟：

```text
http://127.0.0.1:4173/floorplan_viewer/
```

若要直接進入 3D 分層模式，使用：

```text
http://127.0.0.1:4173/floorplan_viewer/?mode=3d
```

請勿直接以 `file://` 開啟 `floorplan_viewer/index.html`，瀏覽器會阻擋它讀取 `manifest.json`。使用 `Ctrl+C` 可停止 HTTP server。

- **2D 平面**：點 B1–B4 切換樓層；拖曳平移、滾輪縮放。
- **3D 分層**：拖曳旋轉、滾輪縮放；點 B1–B4 顯示或隱藏樓層，並可調整樓層間距。
- **圖層**：可開關原始 PNG、黃色可通行區遮罩、語意節點與節點名稱；點節點可查看座標及驗證狀態。

3D 畫面是依 B1 到 B4 順序堆疊的資料模型，不代表實際樓高、比例或建築結構。

## 重要限制

黃色遮罩包含圖例、標誌及被文字切斷的區域，不能直接當導航網格。現有節點與跨樓層關係是依官方資訊圖人工判讀的原型資料，所有 `verified: false` 的項目都必須在正式導航前由站方資料或現場勘查確認。照片導航仍需另外為各節點建立面向、參考照片及逐步指令；樓層圖只能提供拓樸骨架。
