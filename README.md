<div align="center">
  <h1>pyproxy</h1>
</div>


**pyproxy** is a lightweight, fast, and customizable Python-based web proxy server designed to handle both HTTP and HTTPS traffic efficiently. It can be used for various purposes, including web scraping, traffic monitoring, and content filtering.

<p align="center">
  <img src="https://img.shields.io/github/license/pyproxytools/pyproxy?style=for-the-badge">
  <img src="https://img.shields.io/github/issues/pyproxytools/pyproxy?style=for-the-badge">
  <img src="https://img.shields.io/github/issues-closed/pyproxytools/pyproxy?style=for-the-badge">
  <br>
  <img src="https://img.shields.io/github/forks/pyproxytools/pyproxy?style=for-the-badge">
  <img src="https://img.shields.io/github/stars/pyproxytools/pyproxy?style=for-the-badge">
  <img src="https://img.shields.io/github/commit-activity/w/pyproxytools/pyproxy?style=for-the-badge">
  <img src="https://img.shields.io/github/contributors/pyproxytools/pyproxy?style=for-the-badge">
  <br>
  <img src="https://img.shields.io/pypi/v/pyproxytools?style=for-the-badge">
  <img src="https://img.shields.io/pypi/pyversions/pyproxytools?style=for-the-badge">
</p>

---

## ⚡ **Features**

| Feature                                      | Supported |
|----------------------------------------------|-----------|
| HTTP & HTTPS                                 | ✅        |
| Web request logging                          | ✅        |
| Domain & URL blacklist                       | ✅        |
| SSL inspection                               | ✅        |
| Custom 403 Forbidden page                    | ✅        |
| Remote (HTTP) blacklist support              | ✅        |
| Shortcut support                             | ✅        |
| Disable inspection for banking websites      | ✅        |
| Custom headers                               | ✅        |
| Web interface monitoring                     | ✅        |
| Lightweight Docker image                     | ✅        |
| Proxy chaining (multi-proxy forwarding)      | ✅        |
| IP whitelist with subnet support             | ✅        |

## 📦 **Installation**

### Install from package
```bash
pip install pyproxytools
```

### Install from source
```bash
git clone https://github.com/pyproxytools/pyproxy.git
cd pyproxy
pip install -r requirements.txt
```

### Install with Docker
```bash
docker pull ghcr.io/pyproxytools/pyproxy:latest
docker run -d ghcr.io/pyproxytools/pyproxy:latest
```
You can use slim images by adding `-slim` to the end of the tags

### Install with Compose
```bash
wget https://raw.githubusercontent.com/pyproxytools/pyproxy/main/docker-compose.yml
docker-compose up -d
```

## 🚀 **Usage**

### Start the proxy
```bash
python3 -m pyproxy
```
The proxy will be available at: `0.0.0.0:8080`.
The access log will be available at `./logs/access.log`.

## 📚 **Documentation**
If you encounter any problems, or if you want to use the program in a particular way, I advise you to read the [documentation](https://github.com/pyproxytools/pyproxy/wiki).

## 🔧 **To do**

- Support content analysis
- Caching of latest and most searched pages

## 🏎️ **Benchmark**

If you're interested in benchmarking the performance of the proxy or comparing request times with and without a proxy, please refer to the [Benchmark README](benchmark/README.md) for detailed instructions on how to run the benchmarking tests and generate reports.

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 **Contributing**

Contributions are welcome and appreciated! If you'd like to improve this project, feel free to fork the repository and submit a pull request. Whether it's fixing bugs, adding new features, improving documentation, or suggesting enhancements, every bit helps. Please make sure to follow the coding standards and test your changes before submitting. Let's build something great together!

## 📦 Deployment with Ansible

If you want to deploy **pyproxy** automatically to remote servers (via source or Docker), an official [Ansible role](https://github.com/pyproxytools/pyproxy-ansible) is available:

* 🔧 Install from source or run as a Docker container
* 📁 Supports customization of ports, versions, and paths
* 🚀 Easily integrable into your infrastructure or CI/CD pipelines

👉 Check out the [pyproxy-ansible](https://github.com/pyproxytools/pyproxy-ansible) repository for more details and usage instructions.

## 🧩 **Python SDK for Administration and Monitoring**

A dedicated Python SDK is available to interact programmatically with the **pyproxy** administration and monitoring interface: [**pyproxy-sdk-py**](https://github.com/pyproxytools/pyproxy-sdk-py).
This SDK provides a simple and consistent API to manage your proxy configuration remotely — allowing you to add or delete domains, manage URLs, create and remove clients, and perform other administrative tasks. It is designed to integrate easily into automation scripts, dashboards, or backend systems that need to control and monitor pyproxy instances.

---