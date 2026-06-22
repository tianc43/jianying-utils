# jy-downloader

本机剪映草稿导入器。服务端只生成占位符无关的便携 ZIP；jy-downloader 在用户电脑上完成下载、解压、占位符扫描、JSON 重写和草稿安装。

## 技术栈

- Tauri 2
- React
- Jotai
- Mantine

## 开发

```powershell
npm install
npm run dev
```

前端预览地址：

```text
http://localhost:1420
```

完整桌面端运行需要安装 Rust 工具链后执行：

```powershell
npm run tauri dev
```

## 当前功能

- 记住用户首次选择的剪映草稿目录
- 扫描本机已有剪映草稿，占位符 ID 自动发现
- 支持远程 URL 或本地 ZIP
- 显示下载进度、已读取大小和文件总大小
- 安全解压草稿包
- 导入到剪映草稿目录
- 重写 `draft_content.json`、`draft_info.json`、`draft_meta_info.json`
- 支持同名草稿覆盖或自动递增命名

配置文件保存在系统应用配置目录的 `jy-downloader/config.json`。用户通过界面选择草稿目录后，应用会写入该配置；下次启动会优先使用已保存目录。
