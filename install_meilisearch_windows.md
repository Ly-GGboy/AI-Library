# 在Windows上安装MeiliSearch

本指南提供两种在Windows系统上安装MeiliSearch的方法：直接使用Windows二进制文件和通过WSL（Windows Subsystem for Linux）。

## 方法一：直接下载Windows二进制文件

1. 访问MeiliSearch的GitHub发布页面：https://github.com/meilisearch/meilisearch/releases

2. 找到最新版本（当前为v1.13.2），在Assets中下载Windows版本：
   - `meilisearch-windows-amd64.exe`（适用于64位Windows系统）

3. 下载完成后，将文件重命名为`meilisearch.exe`（可选）

4. 创建一个用于存储MeiliSearch数据的文件夹，例如：`C:\meilisearch-data`

5. 打开命令提示符(CMD)或PowerShell，切换到存放meilisearch.exe的目录

6. 运行MeiliSearch：
   ```
   .\meilisearch.exe --db-path=C:\meilisearch-data\data.ms --master-key=你的密钥
   ```

   参数说明：
   - `--db-path`：指定数据存储位置
   - `--master-key`：设置API密钥（强烈建议设置，用于安全保护）

7. 服务启动后，可以在浏览器访问：http://localhost:7700

## 方法二：通过WSL（Windows Subsystem for Linux）

如果您熟悉Linux环境，可以通过WSL来安装和运行MeiliSearch：

1. 安装WSL（如果尚未安装）
   - 以管理员身份打开PowerShell并运行：
   ```
   wsl --install
   ```
   - 重启电脑完成安装

2. 打开WSL终端（通常是Ubuntu）

3. 安装MeiliSearch：
   ```bash
   curl -L https://install.meilisearch.com | sh
   ```

4. 给MeiliSearch可执行权限：
   ```bash
   chmod +x meilisearch
   ```

5. 运行MeiliSearch：
   ```bash
   ./meilisearch --master-key=你的密钥
   ```

6. 服务启动后，同样可以在Windows系统的浏览器访问：http://localhost:7700

## 配置和使用

无论使用哪种安装方法，MeiliSearch都将在端口7700上运行。您可以使用以下参数自定义配置：

- `--http-addr`：指定监听地址（默认为`127.0.0.1:7700`）
- `--env`：设置环境（development或production）
- `--no-analytics`：禁用匿名分析收集

更多配置选项，请参考[官方文档](https://www.meilisearch.com/docs/learn/configuration/instance_options)。

## 将MeiliSearch设置为Windows服务

要将MeiliSearch作为Windows服务运行，可以使用NSSM（Non-Sucking Service Manager）：

1. 下载NSSM：https://nssm.cc/download

2. 解压后，在命令提示符中运行：
   ```
   nssm.exe install MeiliSearch
   ```

3. 在打开的GUI中配置：
   - Path：MeiliSearch可执行文件的完整路径
   - Startup directory：MeiliSearch可执行文件所在目录
   - Arguments：`--db-path=C:\meilisearch-data\data.ms --master-key=你的密钥`

4. 点击"Install service"完成安装

5. 服务将随Windows启动而自动运行

## 测试MeiliSearch安装

安装完成后，可以使用以下命令测试MeiliSearch是否正常工作：

```bash
# 使用curl测试API是否响应
curl http://localhost:7700/health

# 应返回类似内容
# {"status":"available"}
```

## 连接到AI-Library

在AI-Library的配置中，设置以下环境变量：

```
MEILISEARCH_HOST=http://localhost:7700
MEILISEARCH_API_KEY=你设置的master-key
```

这样AI-Library就可以使用MeiliSearch提供的搜索功能。 