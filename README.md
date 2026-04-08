# 离职厂牌制作助手

离职厂牌制作助手是一个基于 `Python + PySide6 + Pillow` 的桌面工具，用来批量导入透明人物图片、逐条编辑姓名与文案，并导出最终的离职厂牌图片。

## 功能

- 批量导入图片文件夹，自动生成记录列表
- GUI 中逐条编辑 `姓名 / 天数 / 主文案 / 副文案 / 输出名`
- 自动合成图层：`下层背景 -> 人物图 -> 上层覆盖 -> 文字`
- 提供人物微调参数：`缩放比例 / X 偏移 / Y 偏移`
- 支持工程文件保存与加载
- 支持命令行读取工程文件批量导出
- 提供 GitHub Actions Windows 打包流程，生成 GUI EXE 并发布 Release

## 目录结构

```text
离职厂牌制作助手/
├─ assets/
│  ├─ fonts/
│  └─ templates/
├─ examples/
│  ├─ input_images/
│  └─ output/
├─ src/li_zhi_badge_maker/
├─ tests/
└─ .github/workflows/
```

## 本地开发

推荐使用 Python 3.12。

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
python -m li_zhi_badge_maker
```

如果你只是想验证渲染逻辑，也可以直接运行：

```bash
python -m li_zhi_badge_maker render-project examples/sample_project.json --output-dir examples/output/generated
```

## GUI 使用方式

1. 点击“导入图片文件夹”，选择存放透明人物图的目录
2. 在左侧列表中选择记录
3. 在右侧表单中编辑姓名、天数、文案和微调参数
4. 预览确认后点击“批量导出”

默认输出名格式为：`01 姓名-离职厂牌-.png`

## 工程文件

工程文件是一个 JSON，保存当前记录列表，方便后续继续编辑。

```json
{
  "version": "1.0",
  "records": [
    {
      "image_path": "examples/input_images/冯兵.png",
      "name": "冯兵",
      "days": "1193",
      "headline": "和奥马一起走过1193天",
      "subheadline": "感恩有您  前程似锦",
      "output_name": "01 冯兵-离职厂牌-.png",
      "scale_adjust": 1.0,
      "x_offset": 0,
      "y_offset": 0
    }
  ]
}
```

## Windows EXE 打包

本地可执行：

```bash
pyinstaller --noconfirm --clean --windowed --name 离职厂牌制作助手 --paths src --add-data "assets:assets" src/li_zhi_badge_maker/main.py
```

Windows GitHub Actions 会自动执行等价命令，并把打包产物压缩后上传到 Release。

## GitHub 发布说明

当前工程已经包含：

- `windows-latest` 打包工作流
- `V*` Tag 触发发布
- `workflow_dispatch` 手动发布入口

如果要真正推送和发版，请先在本机重新完成 GitHub 登录：

```bash
gh auth login -h github.com
```

然后在新建的 GitHub 仓库中推送代码，并创建 `V1.0` tag。

## 字体说明

项目当前内置 `Alibaba-PuHuiTi-Medium.otf`。请确保你拥有该字体的分发权限。
