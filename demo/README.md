# 画面试验（与比赛作品无关）

在网页里看"废弃屋子 + 窗外阳光 + 灰尘光柱 + 人物走路 + 越肩镜头"实际能做到什么程度，尤其手机上卡不卡。说明见 `docs/15-网页画面试验.md`。

- `index.html`、`main.js`：试验页面。three.js 场景，灯光、雾、光柱和灰尘都是实时的。
- `assets/character-glb.js`：同一个人物文件转成 base64 放进 JS 里，页面实际加载的是它。原因：临时链接用的 raw.githack 会把 .glb 文件转到 raw.githubusercontent.com，国内常打不开。
- `assets/character.glb`：人物。来自 Khronos 的 glTF 示例模型 [Cesium Man](https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models/CesiumMan)，作者 Cesium，许可 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)。改动：去掉了原贴图（含 Cesium 标志），改成纯色；缩放到 1.75 米高、落地、面数减半。改动脚本见 `tools/blender/trial/`。
- `vendor/`：three.js r186（MIT 许可，见 `vendor/LICENSE-three.txt`），从 npm 包原样复制，放在本地是为了不依赖国外 CDN。
