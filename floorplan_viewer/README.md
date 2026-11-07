# Floorplan Viewer

這是一個不使用外部套件或 CDN 的靜態 2D／3D 樓層模型檢視器。它直接讀取：

- `assets/floorplans/taipei_main_station/manifest.json`
- `assets/floorplans/taipei_main_station/b1.png` 至 `b4.png`
- 對應的 `*_walkable_mask.png`

因瀏覽器不允許 `file://` 頁面任意讀取 JSON，請從專案根目錄啟動 HTTP server：

```powershell
python -m http.server 4173 --bind 127.0.0.1
```

然後開啟：

```text
http://127.0.0.1:4173/floorplan_viewer/
```

## 操作

- 2D：點 B1–B4 切換樓層；拖曳平移，滾輪縮放。
- 3D：拖曳旋轉，滾輪縮放；點 B1–B4 顯示或隱藏樓層。
- 圖層：可切換原始 PNG、黃色區域遮罩、語意節點及名稱。
- 節點：點擊後可查看正規化座標、種類及驗證狀態。

3D 模式是依樓層順序堆疊的資料模型，不代表實際樓高、比例或建築結構。

## 預覽

- [2D 預覽](./preview-2d.png)
- [3D 預覽](./preview-3d.png)
