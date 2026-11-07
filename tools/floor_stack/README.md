# 北車 B1–B4 疊圖（原型）

把臺北捷運台北車站 B1–B4 四張資訊圖去背、斜角疊起來，用來討論「跨樓層路線」要怎麼呈現。這是看效果用的原型，不是 App 的程式碼。

## 打開

直接用瀏覽器開 `taipei_station_stack.html`（圖片已內嵌，單一檔案即可）。

- **總覽**：四層斜角疊起來，看電梯和路線怎麼跨層。可調層距、傾斜、旋轉。
- **單層平面**：點某一層的板子、點左側 B1–B4，或用 ◀ ▶／方向鍵沿路線逐層看；Esc 回總覽。只顯示該層的平面圖和該層的路線，換層處標「搭電梯 X ↓ 往 BX」「從 BX 抵達」。
- 網址參數（截圖測試用）：`#static` 不播開場動畫、`#f0`–`#f3` 直接開某一層、`#go1` 從總覽動畫切到 B2。

## 重新產生

需要 Python + `opencv-python`、`numpy`（可直接用 `../../../ocr_test/.venv`）。

```bash
cd tools/floor_stack
python scripts/build_layers.py images layers.json   # 去背、裁掉標題列與圖例、輸出 WebP 圖層
python scripts/assemble.py .                        # 把圖層嵌進 template.html → taipei_station_stack.html
```

改畫面或資料就改 `template.html`，再跑 `assemble.py`。

## 資料怎麼來的

| 檔案 | 用途 |
|---|---|
| `images/b1.png`–`b4.png` | 原始資訊圖（BL12R10-SW(26.05)） |
| `scripts/analyze.py` | 抓各層紅點（電梯位置）和車站外框範圍 |
| `scripts/measure_bands.py` | 量 B1、B2 板南線大廳黃色區塊的兩端 |
| `scripts/fit.py` | 用對應點算 B1 → B2–B4 的對齊矩陣，印出誤差 |
| `scripts/check_route.py` | 確認示範路線的點落在黃色走廊上 |

`template.html` 裡的常數：

- `FLOORS[].M`：每層對到共同座標（以 B3 為準）的仿射矩陣。B2、B4 用電梯 1、2、6 平移對齊；B1 畫法比例不同（約 1.24 倍），用電梯 3、4、7 和板南線大廳兩端做最小平方法，誤差約 30–70px。
- `ELEV`：無障礙電梯編號 → 各層停靠點（各層圖片的像素座標）。
- `ROUTE`／`PASS`：示範路線與每層說明文字，**是編的示意，不是實際資料**。之後換成節點圖的真實路線。

## 注意

圖資來源為臺北捷運台北車站資訊圖，**授權尚未確認**。這些示意圖不是等比例，跨層對齊只是近似。
