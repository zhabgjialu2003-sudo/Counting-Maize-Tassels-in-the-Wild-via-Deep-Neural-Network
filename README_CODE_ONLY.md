# Code-only Runtime / 纯代码运行版

本文件夹只保留系统运行与验证所必需的内容：

- `backend/`：Flask API、数据库访问、权限、玉米穗推理、叶片筛查及两套模型；
- `frontend/`：桌面端和中英双语移动端 PWA；
- `database/`：PostgreSQL 建表及迁移 SQL；
- `tests/`：自动化回归测试；
- 根目录入口、依赖说明和安全配置示例。

已排除训练数据集、历史上传图片、Notebook、课程提交材料、截图、验收报告、
模型训练过程清单和 Python 缓存。模型文件虽不是源代码，但属于产生相同运行结果的
必要运行资产，因此予以保留。

## 运行

建议使用 Python 3.11 或 3.12。在本机环境变量中配置 PostgreSQL、`SECRET_KEY`
和 `FILE_ENCRYPTION_KEY`，不要把密码写进本文件夹。

```powershell
python -m pip install -r backend/requirements.txt
python backend/server.py
```

打开：

```text
http://127.0.0.1:5000/frontend/pages/login.html
```

## 验证

```powershell
python -m unittest discover -s tests -v
```

建立本文件夹时，完整测试为 **38/38 通过**。运行模型文件与完整项目逐字节一致，
因此在相同软件环境、相同阈值和相同输入图片下，模型输出保持一致。

---

This folder contains only the source, database migrations, tests, frontend
assets, and model files required to run the application. Datasets, notebooks,
course artefacts, reports, historical uploads, and caches are intentionally
excluded. Configure secrets through local environment variables before running.
